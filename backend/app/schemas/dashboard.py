from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class SeverityCount(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class DashboardStats(BaseModel):
    total_scans: int
    active_scans: int
    completed_scans: int
    total_targets: int
    total_vulnerabilities: int
    severity_distribution: SeverityCount
    scan_success_rate: float
    avg_scan_duration: Optional[float] = None


class ScanSummary(BaseModel):
    id: int
    name: str
    target_url: str
    status: str
    severity_counts: SeverityCount
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class VulnerabilitySummary(BaseModel):
    total: int
    severity_distribution: SeverityCount
    top_vulnerabilities: list[dict]
    trend_last_30_days: list[dict]
