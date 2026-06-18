import enum
from datetime import datetime
from sqlalchemy import String, Text, Boolean, Integer, DateTime, Enum, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    ERROR = "error"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    scan_id: Mapped[int] = mapped_column(Integer, ForeignKey("scans.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus), default=ReportStatus.PENDING)
    formats: Mapped[dict] = mapped_column(JSON, default=dict)
    include_screenshots: Mapped[bool] = mapped_column(Boolean, default=True)
    include_remediation: Mapped[bool] = mapped_column(Boolean, default=True)
    include_evidence: Mapped[bool] = mapped_column(Boolean, default=True)
    s3_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    generated_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
