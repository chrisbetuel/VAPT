import asyncio
import logging
from typing import Any
import httpx
from app.scanners.base import BaseScanner
from app.core.config import settings

logger = logging.getLogger(__name__)

SEVERITY_MAP = {0: "info", 1: "low", 2: "medium", 3: "high"}


class ZAPScanner(BaseScanner):
    name = "zap"
    description = "OWASP ZAP - Web application security scanner"
    docker_image = "softwaresecurityproject/zap-stable:latest"

    def __init__(self):
        self.api_key = settings.SCANNER_ZAP_API_KEY
        self.host = settings.SCANNER_ZAP_HOST
        self.port = settings.SCANNER_ZAP_PORT
        self.base_url = f"http://{self.host}:{self.port}/JSON"

    async def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.base_url}/{path}"
        p = dict(params or {})
        p["apikey"] = self.api_key
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.get(url, params=p)
            resp.raise_for_status()
            return resp.json()

    async def _action(self, path: str, name: str, params: dict) -> str | None:
        try:
            resp = await self._get(f"{path}/action/{name}", params)
            return resp.get("scan")
        except Exception as e:
            logger.warning("ZAP action %s/%s failed: %s", path, name, e)
            return None

    async def _poll_status(self, path: str, scan_id: str, interval: int, callback: Any = None) -> None:
        while True:
            await asyncio.sleep(interval)
            resp = await self._get(f"{path}/view/status", {"scanId": scan_id})
            status = int(resp.get("status", 0))
            if callback:
                await callback(status)
            if status >= 100:
                break

    async def spider(self, target: str) -> list[str]:
        spider_id = await self._action("spider", "scan", {
            "url": target, "maxChildren": "5", "recurse": "true"
        })
        if spider_id:
            await self._poll_status("spider", spider_id, 3)

        resp = await self._get("spider/view/results", {"scanId": spider_id}) if spider_id else {}
        return resp.get("results", [])

    async def active_scan(self, target: str) -> list[dict]:
        scan_id = await self._action("ascanner", "scan", {
            "url": target, "recurse": "true"
        })
        if scan_id:
            await self._poll_status("ascanner", scan_id, 5)

        alerts_resp = await self._get("core/view/alerts", {"baseurl": target})
        raw = alerts_resp.get("alerts", [])
        return self._alerts_to_vulns(raw)

    async def scan(self, target: str, config: dict) -> list[dict]:
        logger.info("ZAP scan starting on %s", target)

        await self._get("core/action/newSession", {
            "name": f"scan_{int(asyncio.get_event_loop().time())}",
            "overwrite": "true"
        })

        await self.spider(target)
        results = await self.active_scan(target)
        logger.info("ZAP scan completed on %s: %d findings", target, len(results))
        return results

    async def validate_target(self, target: str) -> bool:
        try:
            resp = await self._get("core/view/version")
            return "version" in resp
        except Exception:
            return False

    @staticmethod
    def _alerts_to_vulns(alerts: list[dict]) -> list[dict]:
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
                "severity": SEVERITY_MAP.get(risk_int, "info"),
                "cvss_score": None,
                "cve_id": a.get("cve"),
                "cwe_id": a.get("cwe"),
                "remediation": a.get("solution", ""),
                "affected_component": a.get("url", ""),
            })
        return results
