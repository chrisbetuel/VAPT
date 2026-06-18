from fastapi import APIRouter, Depends
from app.schemas.dashboard import DashboardStats, ScanSummary, VulnerabilitySummary
from app.services.dashboard_service import DashboardService
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    pass


@router.get("/scans/recent", response_model=list[ScanSummary])
async def get_recent_scans(db: AsyncSession = Depends(get_db)):
    pass


@router.get("/vulnerabilities/summary", response_model=VulnerabilitySummary)
async def get_vulnerability_summary(db: AsyncSession = Depends(get_db)):
    pass


@router.get("/vulnerabilities/trends")
async def get_vulnerability_trends(db: AsyncSession = Depends(get_db)):
    pass
