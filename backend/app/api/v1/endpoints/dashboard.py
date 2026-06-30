from fastapi import APIRouter, Depends, Query
from app.schemas.dashboard import DashboardStats, ScanSummary, VulnerabilitySummary
from app.services.dashboard_service import DashboardService
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    service = DashboardService(db)
    return await service.get_stats()


@router.get("/scans/recent", response_model=list[ScanSummary])
async def get_recent_scans(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    return await service.get_recent_scans(limit)


@router.get("/vulnerabilities/summary", response_model=VulnerabilitySummary)
async def get_vulnerability_summary(db: AsyncSession = Depends(get_db)):
    service = DashboardService(db)
    return await service.get_vulnerability_summary()


@router.get("/vulnerabilities/trends")
async def get_vulnerability_trends(db: AsyncSession = Depends(get_db)):
    service = DashboardService(db)
    return await service.get_vulnerability_trends()
