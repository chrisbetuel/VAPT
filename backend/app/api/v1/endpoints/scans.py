from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.scan import ScanCreate, ScanResponse, ScanUpdate, ScanListResponse
from app.services.scan_service import ScanService
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(redirect_slashes=False)


@router.get("", response_model=ScanListResponse)
async def list_scans(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    target_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ScanService(db)
    items, total = await service.list_scans(page, size, status, target_id)
    pages = max(1, (total + size - 1) // size)
    return ScanListResponse(items=items, total=total, page=page, size=size, pages=pages)


@router.post("", response_model=ScanResponse, status_code=201)
async def create_scan(
    scan: ScanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ScanService(db)
    return await service.create_scan(scan, current_user.id)


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ScanService(db)
    result = await service.get_scan(scan_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return result


@router.post("/{scan_id}/start", response_model=ScanResponse)
async def start_scan(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ScanService(db)
    result = await service.start_scan(scan_id)
    if result is None:
        raise HTTPException(status_code=400, detail="Scan cannot be started")
    return result


@router.post("/{scan_id}/stop", response_model=ScanResponse)
async def stop_scan(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ScanService(db)
    result = await service.stop_scan(scan_id)
    if result is None:
        raise HTTPException(status_code=400, detail="Scan cannot be stopped")
    return result


@router.delete("/{scan_id}", status_code=204)
async def delete_scan(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ScanService(db)
    deleted = await service.delete_scan(scan_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scan not found")
