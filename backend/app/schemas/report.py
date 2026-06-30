from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class ReportCreate(BaseModel):
    scan_id: int
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    formats: list[str] = Field(default=["pdf", "html"])
    include_screenshots: bool = True
    include_remediation: bool = True
    include_evidence: bool = True


class ReportResponse(BaseModel):
    id: int
    scan_id: int
    title: str
    description: Optional[str] = None
    status: str
    formats: dict
    generated_by: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    items: list[ReportResponse]
    total: int
    page: int
    size: int
    pages: int
