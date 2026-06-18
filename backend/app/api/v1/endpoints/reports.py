from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from app.schemas.report import ReportCreate, ReportResponse
from app.services.report_service import ReportService
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=list[ReportResponse])
async def list_reports(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    scan_id: int = Query(None),
    db: AsyncSession = Depends(get_db),
):
    pass


@router.post("/", response_model=ReportResponse, status_code=201)
async def generate_report(report: ReportCreate, db: AsyncSession = Depends(get_db)):
    pass


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    pass


@router.get("/{report_id}/download/{format}")
async def download_report(report_id: int, format: str):
    pass


@router.delete("/{report_id}", status_code=204)
async def delete_report(report_id: int, db: AsyncSession = Depends(get_db)):
    pass
