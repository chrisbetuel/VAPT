import enum
from datetime import datetime
from sqlalchemy import String, Text, Float, Integer, DateTime, Enum, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    ERROR = "error"
    TIMEOUT = "timeout"


class ScanType(str, enum.Enum):
    QUICK = "quick"
    FULL = "full"
    CUSTOM = "custom"
    SCHEDULED = "scheduled"


class ScanIntensity(str, enum.Enum):
    LIGHT = "light"
    NORMAL = "normal"
    AGGRESSIVE = "aggressive"


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    target_id: Mapped[int] = mapped_column(Integer, ForeignKey("targets.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ScanStatus] = mapped_column(Enum(ScanStatus), default=ScanStatus.PENDING, index=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    scan_type: Mapped[ScanType] = mapped_column(Enum(ScanType), default=ScanType.QUICK)
    intensity: Mapped[ScanIntensity] = mapped_column(Enum(ScanIntensity), default=ScanIntensity.NORMAL)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    target = relationship("Target", back_populates="scans")
    created_by_user = relationship("User", back_populates="scans")
    vulnerabilities = relationship("Vulnerability", back_populates="scan", cascade="all, delete-orphan", lazy="selectin")
    scan_logs = relationship("ScanLog", back_populates="scan", cascade="all, delete-orphan", lazy="selectin")

    @property
    def logs(self):
        return self.scan_logs


class VulnerabilitySeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    FALSE_POSITIVE = "false_positive"
    ACCEPTED_RISK = "accepted_risk"


class Vulnerability(Base):
    __tablename__ = "vulnerabilities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    scan_id: Mapped[int] = mapped_column(Integer, ForeignKey("scans.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[VulnerabilitySeverity] = mapped_column(Enum(VulnerabilitySeverity), index=True)
    status: Mapped[VulnerabilityStatus] = mapped_column(Enum(VulnerabilityStatus), default=VulnerabilityStatus.OPEN)
    cvss_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    cve_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    cwe_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    affected_component: Mapped[str | None] = mapped_column(String(500), nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    scanner_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    scan = relationship("Scan", back_populates="vulnerabilities")


class ScanLog(Base):
    __tablename__ = "scan_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    scan_id: Mapped[int] = mapped_column(Integer, ForeignKey("scans.id"), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(20), default="INFO")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    scanner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    scan = relationship("Scan", back_populates="scan_logs")
