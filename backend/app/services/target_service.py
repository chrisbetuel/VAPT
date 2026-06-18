from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.target import Target
from app.schemas.target import TargetCreate, TargetUpdate


class TargetService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_target(self, target: TargetCreate, user_id: int) -> Target:
        db_target = Target(
            name=target.name,
            url=target.url,
            description=target.description,
            tags=target.tags,
            created_by=user_id,
        )
        self.db.add(db_target)
        await self.db.flush()
        await self.db.refresh(db_target)
        return db_target

    async def get_target(self, target_id: int) -> Target | None:
        result = await self.db.execute(select(Target).where(Target.id == target_id))
        return result.scalar_one_or_none()

    async def list_targets(self, page: int = 1, size: int = 20) -> list[Target]:
        offset = (page - 1) * size
        result = await self.db.execute(select(Target).offset(offset).limit(size))
        return list(result.scalars().all())

    async def update_target(self, target_id: int, target: TargetUpdate) -> Target | None:
        db_target = await self.get_target(target_id)
        if db_target is None:
            return None
        update_data = target.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_target, key, value)
        await self.db.flush()
        await self.db.refresh(db_target)
        return db_target

    async def delete_target(self, target_id: int) -> bool:
        db_target = await self.get_target(target_id)
        if db_target is None:
            return False
        await self.db.delete(db_target)
        await self.db.flush()
        return True
