from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.target import TargetCreate, TargetResponse, TargetUpdate
from app.services.target_service import TargetService
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(redirect_slashes=False)


@router.get("", response_model=list[TargetResponse])
async def list_targets(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TargetService(db)
    return await service.list_targets(page, size)


@router.post("", response_model=TargetResponse, status_code=201)
async def create_target(
    target: TargetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TargetService(db)
    return await service.create_target(target, current_user.id)


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TargetService(db)
    result = await service.get_target(target_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Target not found")
    return result


@router.put("/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: int,
    target: TargetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TargetService(db)
    result = await service.update_target(target_id, target)
    if result is None:
        raise HTTPException(status_code=404, detail="Target not found")
    return result


@router.delete("/{target_id}", status_code=204)
async def delete_target(
    target_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = TargetService(db)
    deleted = await service.delete_target(target_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Target not found")
