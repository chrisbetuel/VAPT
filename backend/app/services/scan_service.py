import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.scan import Scan, ScanStatus, ScanType, ScanIntensity
from app.schemas.scan import ScanCreate, ScanUpdate
from app.core.websocket import emit_scan_progress
from app.tasks import scan_tasks

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=4)


class ScanService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_scan(self, scan: ScanCreate, user_id: int) -> Scan:
        db_scan = Scan(
            target_id=scan.target_id,
            name=scan.name,
            description=scan.description,
            config=scan.config.model_dump() if scan.config else {},
            scan_type=ScanType(scan.config.scan_type) if scan.config else ScanType.QUICK,
            intensity=ScanIntensity(scan.config.intensity) if scan.config else ScanIntensity.NORMAL,
            created_by=user_id,
        )
        self.db.add(db_scan)
        await self.db.flush()
        await self.db.refresh(db_scan)
        await emit_scan_progress(db_scan.id, db_scan.status.value, 0.0)
        return db_scan

    async def get_scan(self, scan_id: int) -> Scan | None:
        result = await self.db.execute(
            select(Scan)
            .options(selectinload(Scan.vulnerabilities), selectinload(Scan.scan_logs))
            .where(Scan.id == scan_id)
        )
        scan = result.scalar_one_or_none()
        if scan and scan.scan_logs:
            scan.scan_logs.sort(key=lambda l: l.created_at or 0)
        return scan

    async def list_scans(
        self,
        page: int = 1,
        size: int = 20,
        status: str | None = None,
        target_id: int | None = None,
    ) -> tuple[list[Scan], int]:
        base_query = select(Scan)
        if status:
            base_query = base_query.where(Scan.status == ScanStatus(status))
        if target_id:
            base_query = base_query.where(Scan.target_id == target_id)

        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        offset = (page - 1) * size
        query = (
            base_query.options(selectinload(Scan.vulnerabilities), selectinload(Scan.scan_logs))
            .offset(offset)
            .limit(size)
            .order_by(Scan.created_at.desc())
        )
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def start_scan(self, scan_id: int) -> Scan | None:
        db_scan = await self.get_scan(scan_id)
        if db_scan is None or db_scan.status != ScanStatus.PENDING:
            return None
        db_scan.status = ScanStatus.RUNNING
        from datetime import datetime, timezone
        db_scan.started_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(db_scan)
        await emit_scan_progress(scan_id, ScanStatus.RUNNING.value, 0.0, "Scan started")

        logger.info("Running scan %d in background thread", scan_id)
        loop = asyncio.get_running_loop()
        loop.run_in_executor(_executor, scan_tasks.run_scan_in_process, scan_id)

        return db_scan

    async def stop_scan(self, scan_id: int) -> Scan | None:
        db_scan = await self.get_scan(scan_id)
        if db_scan is None or db_scan.status != ScanStatus.RUNNING:
            return None
        db_scan.status = ScanStatus.CANCELLED
        from datetime import datetime, timezone
        db_scan.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(db_scan)
        await emit_scan_progress(scan_id, ScanStatus.CANCELLED.value, 0.0, "Scan cancelled")
        return db_scan

    async def delete_scan(self, scan_id: int) -> bool:
        db_scan = await self.get_scan(scan_id)
        if db_scan is None:
            return False
        await self.db.delete(db_scan)
        await self.db.flush()
        return True
