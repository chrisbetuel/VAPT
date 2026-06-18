import time
import json
import logging
import shutil
import subprocess
import re
import httpx
from datetime import datetime, timezone
from urllib.parse import urlparse
from app.core.celery_app import celery_app
from app.core.database import SyncSession
from app.models.scan import Scan, ScanLog, ScanStatus, Vulnerability, VulnerabilitySeverity
from app.core.config import settings

logger = logging.getLogger(__name__)

INTERNAL_API_URL = settings.INTERNAL_API_URL or "http://localhost:8000/api/v1/internal/ws-emit"


def _ws_emit(event: str, data: dict):
    try:
        httpx.post(INTERNAL_API_URL, params={"event": event}, json=data, timeout=2)
    except Exception as e:
        logger.warning("WS emit failed (%s): %s", event, e)


def _add_log(session, scan_id: int, level: str, message: str, scanner: str | None = None):
    log = ScanLog(scan_id=scan_id, level=level, message=message, scanner=scanner)
    session.add(log)
    session.flush()
    session.refresh(log)
    _ws_emit("scan:log", {
        "scan_id": scan_id,
        "level": level,
        "message": message,
        "scanner": scanner,
    })


def _update_progress(session, scan_id: int, progress: float, message: str | None = None, status: str | None = None):
    scan = session.get(Scan, scan_id)
    if scan:
        scan.progress = progress
        if status:
            scan.status = ScanStatus(status)
        session.commit()
    _ws_emit("scan:progress", {
        "scan_id": scan_id,
        "status": status or "running",
        "progress": progress,
        "message": message,
    })


def _add_vulnerability(session, scan_id: int, scanner_name: str, vuln_data: dict):
    severity_map = {
        "critical": VulnerabilitySeverity.CRITICAL,
        "high": VulnerabilitySeverity.HIGH,
        "medium": VulnerabilitySeverity.MEDIUM,
        "low": VulnerabilitySeverity.LOW,
        "info": VulnerabilitySeverity.INFO,
    }
    severity = severity_map.get(vuln_data.get("severity", "low"), VulnerabilitySeverity.LOW)
    vuln = Vulnerability(
        scan_id=scan_id,
        title=vuln_data.get("title", "Unknown vulnerability"),
        description=vuln_data.get("description", ""),
        severity=severity,
        status="open",
        cvss_score=vuln_data.get("cvss_score"),
        cve_id=vuln_data.get("cve_id"),
        cwe_id=vuln_data.get("cwe_id"),
        remediation=vuln_data.get("remediation"),
        affected_component=vuln_data.get("affected_component"),
        scanner_source=scanner_name,
    )
    session.add(vuln)
    session.flush()
    session.refresh(vuln)
    _ws_emit("scan:vulnerability", {
        "scan_id": scan_id,
        "vulnerability": {
            "id": vuln.id,
            "scan_id": scan_id,
            "title": vuln.title,
            "description": vuln.description,
            "severity": vuln.severity.value,
            "status": vuln.status,
            "cvss_score": vuln.cvss_score,
            "cve_id": vuln.cve_id,
            "remediation": vuln.remediation,
            "affected_component": vuln.affected_component,
            "scanner_source": vuln.scanner_source,
            "created_at": vuln.created_at.isoformat() if vuln.created_at else datetime.now(timezone.utc).isoformat(),
        },
    })


# ---------------------------------------------------------------------------
# ZAP Scanner
# ---------------------------------------------------------------------------

ZAP_API_KEY = settings.SCANNER_ZAP_API_KEY
ZAP_HOST = settings.SCANNER_ZAP_HOST
ZAP_PORT = settings.SCANNER_ZAP_PORT


def _zap_get(path: str, params: dict | None = None) -> dict:
    url = f"http://{ZAP_HOST}:{ZAP_PORT}/JSON/{path}"
    p = dict(params or {})
    p["apikey"] = ZAP_API_KEY
    resp = httpx.get(url, params=p, timeout=120)
    resp.raise_for_status()
    return resp.json()


def _zap_alerts_to_vulns(alerts: list) -> list[dict]:
    severity_map = {
        0: "info",
        1: "low",
        2: "medium",
        3: "high",
    }
    seen = set()
    results = []
    for a in alerts:
        key = (a.get("name", ""), a.get("url", ""))
        if key in seen:
            continue
        seen.add(key)
        risk = a.get("risk", 0)
        risk_int = risk if isinstance(risk, int) else 0
        results.append({
            "title": a.get("name", "Unknown"),
            "description": a.get("description", ""),
            "severity": severity_map.get(risk_int, "info"),
            "cvss_score": None,
            "cve_id": a.get("cve", None),
            "cwe_id": a.get("cwe", None),
            "remediation": a.get("solution", ""),
            "affected_component": a.get("url", ""),
        })
    return results


def run_zap_scan(session, scan_id: int, target_url: str, progress_start: float, progress_end: float) -> bool:
    _add_log(session, scan_id, "INFO", "[ZAP] Starting OWASP ZAP scanner...", "zap")

    try:
        version = _zap_get("core/view/version")
        _add_log(session, scan_id, "INFO", f"[ZAP] Connected to ZAP {version.get('version', '?')}", "zap")
    except Exception as e:
        _add_log(session, scan_id, "WARNING", f"[ZAP] Could not connect to ZAP API: {e}", "zap")
        return False

    try:
        _zap_get("core/action/newSession", {"name": f"scan_{scan_id}", "overwrite": "true"})
        _add_log(session, scan_id, "INFO", "[ZAP] Created new session", "zap")
    except Exception as e:
        _add_log(session, scan_id, "WARNING", f"[ZAP] Failed to create session: {e}", "zap")

    progress_range = progress_end - progress_start
    _update_progress(session, scan_id, round(progress_start + progress_range * 0.05, 1),
                     "[ZAP] Spidering target...")

    spider_id = None
    try:
        resp = _zap_get("spider/action/scan", {"url": target_url, "maxChildren": "5", "recurse": "true"})
        spider_id = resp.get("scan")
        _add_log(session, scan_id, "INFO", f"[ZAP] Spider started (ID: {spider_id})", "zap")
    except Exception as e:
        _add_log(session, scan_id, "WARNING", f"[ZAP] Failed to start spider: {e}", "zap")

    if spider_id:
        while True:
            time.sleep(3)
            status_resp = _zap_get("spider/view/status", {"scanId": spider_id})
            status = int(status_resp.get("status", 0))
            spider_progress = progress_start + progress_range * 0.05 + progress_range * 0.25 * (status / 100.0)
            _update_progress(session, scan_id, round(spider_progress, 1),
                             f"[ZAP] Spidering... {status}%")
            _add_log(session, scan_id, "INFO", f"[ZAP] Spider progress: {status}%", "zap")
            if status >= 100:
                break

    _add_log(session, scan_id, "INFO", "[ZAP] Spider complete, starting active scan...", "zap")
    _update_progress(session, scan_id, round(progress_start + progress_range * 0.35, 1),
                     "[ZAP] Active scanning...")

    active_scan_id = None
    try:
        resp = _zap_get("ascanner/action/scan", {"url": target_url, "recurse": "true"})
        active_scan_id = resp.get("scan")
        _add_log(session, scan_id, "INFO", f"[ZAP] Active scan started (ID: {active_scan_id})", "zap")
    except Exception as e:
        _add_log(session, scan_id, "WARNING", f"[ZAP] Failed to start active scan: {e}", "zap")

    if active_scan_id:
        while True:
            time.sleep(5)
            status_resp = _zap_get("ascanner/view/status", {"scanId": active_scan_id})
            status = int(status_resp.get("status", 0))
            active_progress = progress_start + progress_range * 0.35 + progress_range * 0.55 * (status / 100.0)
            _update_progress(session, scan_id, round(active_progress, 1),
                             f"[ZAP] Active scanning... {status}%")
            _add_log(session, scan_id, "INFO", f"[ZAP] Active scan progress: {status}%", "zap")
            if status >= 100:
                break

    _update_progress(session, scan_id, round(progress_end - 2, 1), "[ZAP] Fetching results...")

    try:
        alerts_resp = _zap_get("core/view/alerts", {"baseurl": target_url})
        alerts = alerts_resp.get("alerts", [])
        vulns = _zap_alerts_to_vulns(alerts)
        _add_log(session, scan_id, "INFO", f"[ZAP] Found {len(vulns)} unique alerts", "zap")

        for i, vuln in enumerate(vulns):
            sev = vuln.get("severity", "info")
            _add_log(session, scan_id,
                     "WARNING" if sev in ("high", "critical") else "INFO",
                     f"[ZAP] {sev.upper()}: {vuln['title']}", "zap")
            _add_vulnerability(session, scan_id, "zap", vuln)
            time.sleep(0.2)

        _add_log(session, scan_id, "INFO", f"[ZAP] ZAP scan completed. {len(vulns)} vulnerabilities found.", "zap")
    except Exception as e:
        _add_log(session, scan_id, "WARNING", f"[ZAP] Failed to fetch alerts: {e}", "zap")

    _update_progress(session, scan_id, round(progress_end, 1), "[ZAP] Scan complete")
    return True


# ---------------------------------------------------------------------------
# Nuclei Scanner
# ---------------------------------------------------------------------------

def run_nuclei_scan(session, scan_id: int, target_url: str, progress_start: float, progress_end: float) -> bool:
    if not shutil.which("nuclei"):
        _add_log(session, scan_id, "INFO", "[Nuclei] nuclei CLI not found, skipping", "nuclei")
        return False

    _add_log(session, scan_id, "INFO", f"[Nuclei] Scanning {target_url}...", "nuclei")
    _update_progress(session, scan_id, round(progress_start, 1), "[Nuclei] Scanning...")

    try:
        proc = subprocess.run(
            ["nuclei", "-u", target_url, "-json", "-silent"],
            capture_output=True, text=True, timeout=300,
        )

        results = []
        for line in proc.stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue

        progress_range = progress_end - progress_start
        n = len(results)
        for i, r in enumerate(results):
            info = r.get("info", {}) if isinstance(r.get("info"), dict) else {}
            sev = info.get("severity", "info")
            name = info.get("name", "Unknown")
            desc = info.get("description", "")
            ext_meta = info.get("extracted_results", [])
            classification = info.get("classification", {}) or {}
            cve_list = classification.get("cve-id", []) if isinstance(classification, dict) else []
            cve_id = cve_list[0] if cve_list else None

            _add_log(session, scan_id,
                     "WARNING" if sev in ("high", "critical") else "INFO",
                     f"[Nuclei] {sev.upper()}: {name}", "nuclei")

            _add_vulnerability(session, scan_id, "nuclei", {
                "title": name,
                "description": desc + (f"\nExtracted: {', '.join(ext_meta)}" if ext_meta else ""),
                "severity": sev,
                "cve_id": cve_id,
            })

            pct = progress_start + progress_range * ((i + 1) / max(n, 1))
            _update_progress(session, scan_id, round(pct, 1), f"[Nuclei] Found: {name}")

        _add_log(session, scan_id, "INFO", f"[Nuclei] Scan completed. {n} findings.", "nuclei")
        return True

    except subprocess.TimeoutExpired:
        _add_log(session, scan_id, "WARNING", "[Nuclei] Scan timed out", "nuclei")
        return False
    except Exception as e:
        _add_log(session, scan_id, "WARNING", f"[Nuclei] Scan error: {e}", "nuclei")
        return False


# ---------------------------------------------------------------------------
# Nmap Scanner
# ---------------------------------------------------------------------------

_NMAP_PORT_REGEX = re.compile(
    r"(\d+)/(tcp|udp)\s+open\s+(\S+)\s+(.+)$", re.MULTILINE
)


def run_nmap_scan(session, scan_id: int, target_url: str, progress_start: float, progress_end: float) -> bool:
    if not shutil.which("nmap"):
        _add_log(session, scan_id, "INFO", "[Nmap] nmap CLI not found, skipping", "nmap")
        return False

    host = urlparse(target_url).hostname or target_url
    _add_log(session, scan_id, "INFO", f"[Nmap] Scanning host {host}...", "nmap")
    _update_progress(session, scan_id, round(progress_start, 1), "[Nmap] Scanning ports...")

    try:
        proc = subprocess.run(
            ["nmap", "-sV", "-sC", "-T4", "-oG", "-", host],
            capture_output=True, text=True, timeout=600,
        )

        findings = []
        for match in _NMAP_PORT_REGEX.finditer(proc.stdout):
            port = match.group(1)
            proto = match.group(2)
            service = match.group(3)
            version = match.group(4).strip()
            findings.append({
                "port": port,
                "protocol": proto,
                "service": service,
                "version": version,
            })

        progress_range = progress_end - progress_start
        for i, f in enumerate(findings):
            title = f"Open Port {f['port']}/{f['protocol']} ({f['service']})"
            desc = f"Port {f['port']}/{f['protocol']} is open running {f['service']} {f['version']}"
            sev = "medium" if f["service"] in ("ssh", "telnet", "ftp") else "low"

            _add_log(session, scan_id, "INFO", f"[Nmap] Found: {f['port']}/{f['protocol']} {f['service']}", "nmap")
            _add_vulnerability(session, scan_id, "nmap", {
                "title": title,
                "description": desc,
                "severity": sev,
                "affected_component": f"{f['port']}/{f['protocol']}",
            })

            pct = progress_start + progress_range * ((i + 1) / max(len(findings), 1))
            _update_progress(session, scan_id, round(pct, 1), f"[Nmap] Port {f['port']}/{f['protocol']}")

        if not findings:
            _add_log(session, scan_id, "INFO", "[Nmap] No open ports found or scan incomplete", "nmap")

        _add_log(session, scan_id, "INFO", f"[Nmap] Scan completed. {len(findings)} open ports.", "nmap")
        return True

    except subprocess.TimeoutExpired:
        _add_log(session, scan_id, "WARNING", "[Nmap] Scan timed out", "nmap")
        return False
    except Exception as e:
        _add_log(session, scan_id, "WARNING", f"[Nmap] Scan error: {e}", "nmap")
        return False


# ---------------------------------------------------------------------------
# Subfinder Scanner
# ---------------------------------------------------------------------------

def run_subfinder_scan(session, scan_id: int, target_url: str, progress_start: float, progress_end: float) -> bool:
    if not shutil.which("subfinder"):
        _add_log(session, scan_id, "INFO", "[Subfinder] subfinder CLI not found, skipping", "subfinder")
        return False

    hostname = urlparse(target_url).hostname or target_url
    _add_log(session, scan_id, "INFO", f"[Subfinder] Enumerating subdomains for {hostname}...", "subfinder")
    _update_progress(session, scan_id, round(progress_start, 1), "[Subfinder] Enumerating...")

    try:
        proc = subprocess.run(
            ["subfinder", "-d", hostname, "-silent"],
            capture_output=True, text=True, timeout=120,
        )

        subs = [s.strip() for s in proc.stdout.strip().split("\n") if s.strip()]
        progress_range = progress_end - progress_start

        for i, s in enumerate(subs):
            _add_log(session, scan_id, "INFO", f"[Subfinder] Found subdomain: {s}", "subfinder")
            pct = progress_start + progress_range * ((i + 1) / max(len(subs), 1))
            _update_progress(session, scan_id, round(pct, 1), f"[Subfinder] Found: {s}")

        _add_log(session, scan_id, "INFO", f"[Subfinder] Found {len(subs)} subdomains", "subfinder")
        return True

    except subprocess.TimeoutExpired:
        _add_log(session, scan_id, "WARNING", "[Subfinder] Scan timed out", "subfinder")
        return False
    except Exception as e:
        _add_log(session, scan_id, "WARNING", f"[Subfinder] Scan error: {e}", "subfinder")
        return False


# ---------------------------------------------------------------------------
# FFUF Scanner
# ---------------------------------------------------------------------------

def run_ffuf_scan(session, scan_id: int, target_url: str, progress_start: float, progress_end: float) -> bool:
    if not shutil.which("ffuf"):
        _add_log(session, scan_id, "INFO", "[FFUF] ffuf CLI not found, skipping", "ffuf")
        return False

    _add_log(session, scan_id, "INFO", f"[FFUF] Fuzzing {target_url}...", "ffuf")
    _update_progress(session, scan_id, round(progress_start, 1), "[FFUF] Fuzzing...")

    try:
        proc = subprocess.run(
            ["ffuf", "-u", f"{target_url}/FUZZ", "-w", "/usr/share/wordlists/dirb/common.txt",
             "-json", "-silent"],
            capture_output=True, text=True, timeout=120,
        )

        results = []
        for line in proc.stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue

        progress_range = progress_end - progress_start
        n = len(results)
        for i, r in enumerate(results):
            url = r.get("url", "")
            status = r.get("status", 0)
            length = r.get("length", 0)

            sev = "medium" if status == 200 else "low"
            _add_log(session, scan_id, "INFO",
                     f"[FFUF] {status} {url} ({length} bytes)", "ffuf")

            _add_vulnerability(session, scan_id, "ffuf", {
                "title": f"Discovered endpoint: {url}",
                "description": f"Accessible URL found (HTTP {status}, {length} bytes). This endpoint may expose additional functionality or information.",
                "severity": sev,
                "affected_component": url,
            })

            pct = progress_start + progress_range * ((i + 1) / max(n, 1))
            _update_progress(session, scan_id, round(pct, 1), f"[FFUF] {status} {url}")

        _add_log(session, scan_id, "INFO", f"[FFUF] Fuzzing completed. {n} endpoints found.", "ffuf")
        return True

    except subprocess.TimeoutExpired:
        _add_log(session, scan_id, "WARNING", "[FFUF] Scan timed out", "ffuf")
        return False
    except Exception as e:
        _add_log(session, scan_id, "WARNING", f"[FFUF] Scan error: {e}", "ffuf")
        return False


# ---------------------------------------------------------------------------
# Main Scan Task
# ---------------------------------------------------------------------------

SCANNER_FUNCS = {
    "zap": run_zap_scan,
    "nuclei": run_nuclei_scan,
    "nmap": run_nmap_scan,
    "subfinder": run_subfinder_scan,
    "ffuf": run_ffuf_scan,
}


@celery_app.task(bind=True, max_retries=3)
def run_scan(self, scan_id: int):
    session = SyncSession()
    try:
        scan = session.get(Scan, scan_id)
        if not scan:
            return {"error": "Scan not found"}

        target = scan.target
        target_url = target.url if target else ""

        config = scan.config or {}
        enabled_scanners = config.get("scanners") or ["zap", "nuclei", "nmap", "subfinder", "ffuf"]
        intensity = config.get("intensity", "normal")

        scan.status = ScanStatus.RUNNING
        scan.started_at = datetime.now(timezone.utc)
        session.commit()

        _ws_emit("scan:progress", {
            "scan_id": scan_id,
            "status": "running",
            "progress": 0.0,
            "message": "Scan started",
        })

        _add_log(session, scan_id, "INFO", f"Starting scan on target: {target_url}", "system")
        _add_log(session, scan_id, "INFO", f"Enabled scanners: {', '.join(enabled_scanners)}", "system")
        _add_log(session, scan_id, "INFO", f"Intensity: {intensity}", "system")

        n_scanners = len(enabled_scanners)
        progress_per_scanner = 95.0 / max(n_scanners, 1)
        current_progress = 5.0

        for scanner_name in enabled_scanners:
            scanner_name = scanner_name.lower()
            scanner_func = SCANNER_FUNCS.get(scanner_name)

            if scanner_func:
                _add_log(session, scan_id, "INFO", f"[{scanner_name}] Starting...", scanner_name)
                scanner_func(
                    session, scan_id, target_url,
                    current_progress,
                    current_progress + progress_per_scanner,
                )
            else:
                _add_log(session, scan_id, "WARNING", f"[{scanner_name}] Unknown scanner, skipping", scanner_name)

            current_progress += progress_per_scanner

        scan.status = ScanStatus.COMPLETED
        scan.completed_at = datetime.now(timezone.utc)
        scan.progress = 100.0
        session.commit()

        _add_log(session, scan_id, "INFO", "Scan completed successfully.", "system")
        _ws_emit("scan:progress", {
            "scan_id": scan_id,
            "status": "completed",
            "progress": 100.0,
            "message": "Scan completed",
        })

        return {"status": "completed", "scan_id": scan_id}

    except Exception as exc:
        logger.exception("Scan %d failed", scan_id)
        session.rollback()
        try:
            scan = session.get(Scan, scan_id)
            if scan:
                scan.status = ScanStatus.ERROR
                scan.completed_at = datetime.now(timezone.utc)
                session.commit()
                _ws_emit("scan:progress", {
                    "scan_id": scan_id,
                    "status": "error",
                    "progress": 0.0,
                    "message": f"Scan failed: {str(exc)}",
                })
        except Exception:
            session.rollback()
        raise self.retry(exc=exc)
    finally:
        session.close()


def run_scan_in_process(scan_id: int):
    """Execute scan directly in the current process (no Celery worker needed)."""
    session = SyncSession()
    try:
        scan = session.get(Scan, scan_id)
        if not scan:
            logger.error("Scan %d not found for in-process execution", scan_id)
            return {"error": "Scan not found"}

        target = scan.target
        target_url = target.url if target else ""

        config = scan.config or {}
        enabled_scanners = config.get("scanners") or ["zap", "nuclei", "nmap", "subfinder", "ffuf"]

        scan.status = ScanStatus.RUNNING
        scan.started_at = datetime.now(timezone.utc)
        session.commit()

        _ws_emit("scan:progress", {
            "scan_id": scan_id,
            "status": "running",
            "progress": 0.0,
            "message": "Scan started",
        })

        _add_log(session, scan_id, "INFO", f"Starting scan on target: {target_url}", "system")
        _add_log(session, scan_id, "INFO", f"Enabled scanners: {', '.join(enabled_scanners)}", "system")

        n_scanners = len(enabled_scanners)
        progress_per_scanner = 95.0 / max(n_scanners, 1)
        current_progress = 5.0

        for scanner_name in enabled_scanners:
            scanner_name = scanner_name.lower()
            scanner_func = SCANNER_FUNCS.get(scanner_name)

            if scanner_func:
                _add_log(session, scan_id, "INFO", f"[{scanner_name}] Starting...", scanner_name)
                scanner_func(
                    session, scan_id, target_url,
                    current_progress,
                    current_progress + progress_per_scanner,
                )
            else:
                _add_log(session, scan_id, "WARNING", f"[{scanner_name}] Unknown scanner, skipping", scanner_name)

            current_progress += progress_per_scanner

        scan.status = ScanStatus.COMPLETED
        scan.completed_at = datetime.now(timezone.utc)
        scan.progress = 100.0
        session.commit()

        _add_log(session, scan_id, "INFO", "Scan completed successfully.", "system")
        _ws_emit("scan:progress", {
            "scan_id": scan_id,
            "status": "completed",
            "progress": 100.0,
            "message": "Scan completed",
        })

        return {"status": "completed", "scan_id": scan_id}

    except Exception as exc:
        logger.exception("Scan %d failed (in-process)", scan_id)
        session.rollback()
        try:
            scan = session.get(Scan, scan_id)
            if scan:
                scan.status = ScanStatus.ERROR
                scan.completed_at = datetime.now(timezone.utc)
                session.commit()
                _ws_emit("scan:progress", {
                    "scan_id": scan_id,
                    "status": "error",
                    "progress": 0.0,
                    "message": f"Scan failed: {str(exc)}",
                })
        except Exception:
            session.rollback()
    finally:
        session.close()


@celery_app.task
def cleanup_old_scans():
    pass


@celery_app.task
def process_scan_results(scan_id: int, scanner_name: str, raw_results: dict):
    pass


@celery_app.task
def normalize_vulnerabilities(scan_id: int):
    pass
