from sqlalchemy import String, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
import uuid

from app.core.database import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    report_type: Mapped[str] = mapped_column(String(100), nullable=False)
    audience: Mapped[str] = mapped_column(String(50), default="manager")
    period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_html: Mapped[Optional[str]] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    key_metrics: Mapped[Optional[dict]] = mapped_column(JSON)
    risks_identified: Mapped[Optional[list]] = mapped_column(JSON)
    action_items: Mapped[Optional[list]] = mapped_column(JSON)
    decisions_required: Mapped[Optional[list]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    generated_by_agent: Mapped[str] = mapped_column(String(100), default="executive_reporting")
    prompt_version: Mapped[Optional[str]] = mapped_column(String(50))
    token_cost: Mapped[Optional[int]] = mapped_column()
    model_used: Mapped[Optional[str]] = mapped_column(String(100))
    generation_time_ms: Mapped[Optional[int]] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project: Mapped[Optional["Project"]] = relationship(back_populates="reports")
    approver: Mapped[Optional["User"]] = relationship(foreign_keys=[approved_by])


class MeetingTranscript(Base):
    __tablename__ = "meeting_transcripts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("projects.id"))
    transcript_text: Mapped[str] = mapped_column(Text, nullable=False)
    meeting_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[Optional[int]] = mapped_column()
    participants: Mapped[Optional[list]] = mapped_column(JSON)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    decisions: Mapped[Optional[list]] = mapped_column(JSON)
    action_items: Mapped[Optional[list]] = mapped_column(JSON)
    risks: Mapped[Optional[list]] = mapped_column(JSON)
    follow_ups: Mapped[Optional[list]] = mapped_column(JSON)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    uploaded_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
