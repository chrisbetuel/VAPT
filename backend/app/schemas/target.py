from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class TargetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., max_length=2048)
    description: Optional[str] = None
    tags: Optional[list[str]] = None


class TargetCreate(TargetBase):
    pass


class TargetUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None


class TargetResponse(TargetBase):
    id: int
    status: str
    last_scanned_at: Optional[datetime] = None
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
