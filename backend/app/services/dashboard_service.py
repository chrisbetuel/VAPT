from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, cast
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.scan import Scan, ScanStatus, Vulnerability, VulnerabilitySeverity
from app.models.target import Target
from app.schemas.dashboard import DashboardStats, SeverityCount, ScanSummary


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self) -> DashboardStats:
        total_scans = await self.db.scalar(select(func.count(Scan.id)))
        active_scans = await self.db.scalar(
            select(func.count(Scan.id)).where(Scan.status == ScanStatus.RUNNING)
        )
        completed_scans = await self.db.scalar(
            select(func.count(Scan.id)).where(Scan.status == ScanStatus.COMPLETED)
        )
        total_targets = await self.db.scalar(select(func.count(Target.id)))
        total_vulnerabilities = await self.db.scalar(select(func.count(Vulnerability.id)))

        severity_rows = await self.db.execute(
            select(Vulnerability.severity, func.count(Vulnerability.id).label("cnt"))
            .group_by(Vulnerability.severity)
        )
        sev_map = {row.severity.value if hasattr(row.severity, 'value') else row.severity: row.cnt for row in severity_rows}

        success_rate = (completed_scans / total_scans * 100) if total_scans and total_scans > 0 else 0.0

        avg_dur_row = await self.db.execute(
            select(
                func.avg(
                    func.extract('epoch', Scan.completed_at - Scan.started_at)
                )
            ).where(
                Scan.status == ScanStatus.COMPLETED,
                Scan.started_at.isnot(None),
                Scan.completed_at.isnot(None),
            )
        )
        avg_scan_duration = avg_dur_row.scalar()

        return DashboardStats(
            total_scans=total_scans or 0,
            active_scans=active_scans or 0,
            completed_scans=completed_scans or 0,
            total_targets=total_targets or 0,
            total_vulnerabilities=total_vulnerabilities or 0,
            severity_distribution=SeverityCount(
                critical=sev_map.get("critical", 0),
                high=sev_map.get("high", 0),
                medium=sev_map.get("medium", 0),
                low=sev_map.get("low", 0),
                info=sev_map.get("info", 0),
            ),
            scan_success_rate=round(success_rate, 1),
            avg_scan_duration=round(avg_scan_duration, 1) if avg_scan_duration else None,
        )

    async def get_recent_scans(self, limit: int = 10) -> list[ScanSummary]:
        result = await self.db.execute(
            select(Scan)
            .order_by(Scan.created_at.desc())
            .limit(limit)
        )
        scans = result.scalars().all()
        summaries = []
        for s in scans:
            sev_count = SeverityCount()
            for v in s.vulnerabilities:
                sev = v.severity.value if hasattr(v.severity, 'value') else v.severity
                if sev == "critical":
                    sev_count.critical += 1
                elif sev == "high":
                    sev_count.high += 1
                elif sev == "medium":
                    sev_count.medium += 1
                elif sev == "low":
                    sev_count.low += 1
                elif sev == "info":
                    sev_count.info += 1
            summaries.append(ScanSummary(
                id=s.id,
                name=s.name,
                target_url=s.target.url if s.target else "",
                status=s.status.value if hasattr(s.status, 'value') else s.status,
                severity_counts=sev_count,
                started_at=s.started_at,
                completed_at=s.completed_at,
            ))
        return summaries

    async def get_vulnerability_summary(self):
        total = await self.db.scalar(select(func.count(Vulnerability.id))) or 0

        severity_rows = await self.db.execute(
            select(Vulnerability.severity, func.count(Vulnerability.id).label("cnt"))
            .group_by(Vulnerability.severity)
        )
        sev_map = {row.severity.value if hasattr(row.severity, 'value') else row.severity: row.cnt for row in severity_rows}

        top_rows = await self.db.execute(
            select(Vulnerability.title, func.count(Vulnerability.id).label("cnt"))
            .group_by(Vulnerability.title)
            .order_by(func.count(Vulnerability.id).desc())
            .limit(10)
        )
        top_vulns = [{"title": row.title, "count": row.cnt} for row in top_rows]

        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        trend_rows = await self.db.execute(
            select(
                cast(Vulnerability.created_at, func.date).label("day"),
                func.count(Vulnerability.id).label("cnt"),
            )
            .where(Vulnerability.created_at >= thirty_days_ago)
            .group_by(cast(Vulnerability.created_at, func.date))
            .order_by(cast(Vulnerability.created_at, func.date))
        )
        trend = [{"date": str(row.day), "count": row.cnt} for row in trend_rows]

        return {
            "total": total,
            "severity_distribution": SeverityCount(
                critical=sev_map.get("critical", 0),
                high=sev_map.get("high", 0),
                medium=sev_map.get("medium", 0),
                low=sev_map.get("low", 0),
                info=sev_map.get("info", 0),
            ),
            "top_vulnerabilities": top_vulns,
            "trend_last_30_days": trend,
        }

    async def get_vulnerability_trends(self):
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        rows = await self.db.execute(
            select(
                cast(Vulnerability.created_at, func.date).label("day"),
                func.count(Vulnerability.id).label("cnt"),
            )
            .where(Vulnerability.created_at >= thirty_days_ago)
            .group_by(cast(Vulnerability.created_at, func.date))
            .order_by(cast(Vulnerability.created_at, func.date))
        )
        return [{"date": str(row.day), "count": row.cnt} for row in rows]
