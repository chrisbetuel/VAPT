from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from app.schemas.report import ReportCreate, ReportResponse, ReportListResponse
from app.services.report_service import ReportService
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=ReportListResponse)
async def list_reports(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    scan_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ReportService(db)
    items, total = await service.list_reports(page, size, scan_id)
    pages = max(1, (total + size - 1) // size)
    return ReportListResponse(items=items, total=total, page=page, size=size, pages=pages)


@router.post("/", response_model=ReportResponse, status_code=201)
async def generate_report(
    report: ReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ReportService(db)
    return await service.generate_report(report, current_user.id)


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ReportService(db)
    result = await service.get_report(report_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return result


@router.get("/{report_id}/download/{fmt}")
async def download_report(
    report_id: int,
    fmt: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    file_path, content_type = await service.download_report(report_id, fmt)
    if file_path is None:
        raise HTTPException(status_code=404, detail="Report file not found")
    return FileResponse(
        path=str(file_path),
        media_type=content_type,
        filename=f"report_{report_id}.{fmt}",
    )


@router.delete("/{report_id}", status_code=204)
async def delete_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ReportService(db)
    deleted = await service.delete_report(report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report not found")
