import json
import os
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.report import Report, ReportStatus
from app.models.scan import Scan, ScanLog, Vulnerability
from app.schemas.report import ReportCreate, ReportResponse
from app.core.config import settings
from app.tasks.report_tasks import generate_report as generate_report_task

REPORTS_DIR = Path(settings.REPORTS_DIR) if hasattr(settings, 'REPORTS_DIR') else Path("/app/reports")


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_report(self, data: ReportCreate, user_id: int) -> Report:
        db_report = Report(
            scan_id=data.scan_id,
            title=data.title,
            description=data.description,
            formats={fmt: f"pending" for fmt in data.formats},
            include_screenshots=data.include_screenshots,
            include_remediation=data.include_remediation,
            include_evidence=data.include_evidence,
            generated_by=user_id,
        )
        self.db.add(db_report)
        await self.db.flush()
        await self.db.refresh(db_report)

        try:
            generate_report_task.delay(db_report.id)
        except Exception:
            pass

        return db_report

    async def get_report(self, report_id: int) -> Report | None:
        result = await self.db.execute(
            select(Report).where(Report.id == report_id)
        )
        return result.scalar_one_or_none()

    async def list_reports(
        self, page: int = 1, size: int = 20, scan_id: int | None = None
    ) -> tuple[list[Report], int]:
        base_query = select(Report)
        if scan_id:
            base_query = base_query.where(Report.scan_id == scan_id)

        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        offset = (page - 1) * size
        query = (
            base_query
            .order_by(desc(Report.created_at))
            .offset(offset)
            .limit(size)
        )
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def download_report(self, report_id: int, fmt: str) -> tuple[Path | None, str]:
        report = await self.get_report(report_id)
        if report is None:
            return None, ""

        file_path = REPORTS_DIR / f"report_{report_id}.{fmt}"
        mime_map = {
            "pdf": "application/pdf",
            "html": "text/html",
            "json": "application/json",
        }
        content_type = mime_map.get(fmt, "application/octet-stream")

        if file_path.exists():
            return file_path, content_type

        formats = report.formats or {}
        if isinstance(formats, dict) and formats.get(fmt) == "completed":
            alt_path = REPORTS_DIR / f"report_{report_id}.{fmt}"
            if alt_path.exists():
                return alt_path, content_type

        return None, ""

    async def delete_report(self, report_id: int) -> bool:
        report = await self.get_report(report_id)
        if report is None:
            return False
        await self.db.delete(report)
        await self.db.flush()
        for file_path in REPORTS_DIR.glob(f"report_{report_id}.*"):
            try:
                file_path.unlink()
            except OSError:
                pass
        return True


async def build_report_data(report: Report) -> dict:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.core.database import SyncSession

    session: Session = SyncSession()
    try:
        scan = session.get(Scan, report.scan_id)
        if not scan:
            return {}

        target_url = scan.target.url if scan.target else ""
        config = scan.config or {}
        vulnerabilities = scan.vulnerabilities or []
        logs = scan.scan_logs or []

        critical = sum(1 for v in vulnerabilities if v.severity and v.severity.value == "critical")
        high = sum(1 for v in vulnerabilities if v.severity and v.severity.value == "high")
        medium = sum(1 for v in vulnerabilities if v.severity and v.severity.value == "medium")
        low = sum(1 for v in vulnerabilities if v.severity and v.severity.value == "low")
        info = sum(1 for v in vulnerabilities if v.severity and v.severity.value == "info")

        vuln_list = []
        for v in vulnerabilities:
            vuln_list.append({
                "title": v.title,
                "severity": v.severity.value if v.severity else "info",
                "cvss_score": v.cvss_score,
                "cve_id": v.cve_id,
                "affected_component": v.affected_component,
                "description": v.description,
                "remediation": v.remediation,
            })

        log_list = []
        for l in logs:
            log_list.append({
                "created_at": l.created_at.isoformat() if l.created_at else "",
                "level": l.level,
                "scanner": l.scanner or "",
                "message": l.message,
            })

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        return {
            "title": report.title,
            "scan_name": scan.name,
            "target_url": target_url,
            "generated_at": now_str,
            "total_vulnerabilities": len(vulnerabilities),
            "critical_count": critical,
            "high_count": high,
            "medium_count": medium,
            "low_count": low,
            "info_count": info,
            "scan_status": scan.status.value if scan.status else "unknown",
            "scan_type": config.get("scan_type", "quick"),
            "intensity": config.get("intensity", "normal"),
            "scanners": config.get("scanners", []),
            "started_at": scan.started_at.isoformat() if scan.started_at else None,
            "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
            "vulnerabilities": vuln_list,
            "logs": log_list,
        }
    finally:
        session.close()
