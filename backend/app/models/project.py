from sqlalchemy import String, Boolean, DateTime, Text, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List
import uuid
import enum

from app.core.database import Base


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    AT_RISK = "at_risk"
    CANCELLED = "cancelled"


class ProjectHealthScore(str, enum.Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="active")
    health_score: Mapped[Optional[str]] = mapped_column(String(20))
    health_score_value: Mapped[Optional[float]] = mapped_column(Float)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)
    owner_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"))
    team_size: Mapped[int] = mapped_column(Integer, default=0)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    target_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    actual_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    budget: Mapped[Optional[float]] = mapped_column(Float)
    budget_spent: Mapped[Optional[float]] = mapped_column(Float)
    jira_project_key: Mapped[Optional[str]] = mapped_column(String(50))
    github_repo: Mapped[Optional[str]] = mapped_column(String(255))
    confluence_space: Mapped[Optional[str]] = mapped_column(String(100))
    slack_channel: Mapped[Optional[str]] = mapped_column(String(100))
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sprints: Mapped[List["Sprint"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    risks: Mapped[List["Risk"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    reports: Mapped[List["Report"]] = relationship(back_populates="project")
    metrics: Mapped[List["ProjectMetric"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Sprint(Base):
    __tablename__ = "sprints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sprint_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active")
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    planned_points: Mapped[int] = mapped_column(Integer, default=0)
    completed_points: Mapped[int] = mapped_column(Integer, default=0)
    carryover_points: Mapped[int] = mapped_column(Integer, default=0)
    velocity: Mapped[Optional[float]] = mapped_column(Float)
    completion_rate: Mapped[Optional[float]] = mapped_column(Float)
    success_likelihood: Mapped[Optional[float]] = mapped_column(Float)
    blocker_count: Mapped[int] = mapped_column(Integer, default=0)
    tickets_total: Mapped[int] = mapped_column(Integer, default=0)
    tickets_done: Mapped[int] = mapped_column(Integer, default=0)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project: Mapped["Project"] = relationship(back_populates="sprints")
    tickets: Mapped[List["Ticket"]] = relationship(back_populates="sprint", cascade="all, delete-orphan")


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sprint_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("sprints.id"))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(100), default="open")
    ticket_type: Mapped[str] = mapped_column(String(50), default="story")
    priority: Mapped[str] = mapped_column(String(50), default="medium")
    story_points: Mapped[Optional[int]] = mapped_column(Integer)
    assignee: Mapped[Optional[str]] = mapped_column(String(255))
    reporter: Mapped[Optional[str]] = mapped_column(String(255))
    labels: Mapped[Optional[list]] = mapped_column(JSON)
    is_blocker: Mapped[bool] = mapped_column(Boolean, default=False)
    blocked_by: Mapped[Optional[list]] = mapped_column(JSON)
    created_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    updated_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resolved_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(50), default="jira")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sprint: Mapped[Optional["Sprint"]] = relationship(back_populates="tickets")


class ProjectMetric(Base):
    __tablename__ = "project_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False)
    metric_type: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    metric_metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="metrics")
