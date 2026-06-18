from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class WebhookCreate(BaseModel):
    url: str = Field(..., max_length=2048)
    secret: Optional[str] = None
    events: list[str] = Field(default=["scan.completed"])
    is_active: bool = True


class WebhookEvent(BaseModel):
    event: str
    payload: dict
    timestamp: datetime


class WebhookResponse(BaseModel):
    id: int
    url: str
    events: list[str]
    is_active: bool
    created_by: int
    created_at: datetime

    model_config = {"from_attributes": True}
