from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List


class ScanLogResponse(BaseModel):
    id: int
    scan_id: int
    level: str
    message: str
    scanner: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ScanConfig(BaseModel):
    scan_type: str = Field(..., pattern="^(quick|full|custom|scheduled)$")
    scanners: List[str] = Field(default=["nuclei", "zap", "nmap"])
    intensity: str = Field(default="normal", pattern="^(light|normal|aggressive)$")


class ScanCreate(BaseModel):
    target_id: int
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    config: ScanConfig
    scheduled_at: Optional[datetime] = None


class ScanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[ScanConfig] = None


class VulnerabilityBase(BaseModel):
    title: str
    description: str
    severity: str = Field(..., pattern="^(critical|high|medium|low|info)$")
    cvss_score: Optional[float] = Field(None, ge=0, le=10)
    cve_id: Optional[str] = None
    remediation: Optional[str] = None
    affected_component: Optional[str] = None


class VulnerabilityResponse(VulnerabilityBase):
    id: int
    scan_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ScanResponse(BaseModel):
    id: int
    target_id: int
    name: str
    description: Optional[str] = None
    status: str
    progress: float
    config: dict
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: int
    created_at: datetime
    vulnerabilities: List[VulnerabilityResponse] = []
    logs: List[ScanLogResponse] = []

    model_config = {"from_attributes": True}


class ScanListResponse(BaseModel):
    items: List[ScanResponse]
    total: int
    page: int
    size: int
    pages: int
