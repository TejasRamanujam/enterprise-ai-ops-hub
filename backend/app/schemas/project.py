from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    key: str = Field(..., min_length=2, max_length=20, pattern=r'^[A-Z0-9]+$')
    description: Optional[str] = None
    owner_id: Optional[str] = None
    start_date: Optional[datetime] = None
    target_end_date: Optional[datetime] = None
    budget: Optional[float] = None
    jira_project_key: Optional[str] = None
    github_repo: Optional[str] = None
    confluence_space: Optional[str] = None
    slack_channel: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    owner_id: Optional[str] = None
    target_end_date: Optional[datetime] = None
    budget: Optional[float] = None
    budget_spent: Optional[float] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    key: str
    description: Optional[str]
    status: str
    health_score: Optional[str]
    health_score_value: Optional[float]
    confidence_score: Optional[float]
    team_size: int
    start_date: Optional[datetime]
    target_end_date: Optional[datetime]
    jira_project_key: Optional[str]
    github_repo: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectDetailResponse(ProjectResponse):
    budget: Optional[float]
    budget_spent: Optional[float]
    slack_channel: Optional[str]
    confluence_space: Optional[str]
    sprints: List["SprintResponse"] = []
    risks: List["RiskResponse"] = []


class SprintCreate(BaseModel):
    project_id: str
    name: str
    sprint_number: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    planned_points: int = 0


class SprintResponse(BaseModel):
    id: str
    project_id: str
    name: str
    sprint_number: int
    status: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    planned_points: int
    completed_points: int
    carryover_points: int
    velocity: Optional[float]
    completion_rate: Optional[float]
    success_likelihood: Optional[float]
    blocker_count: int
    tickets_total: int
    tickets_done: int
    ai_summary: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TicketResponse(BaseModel):
    id: str
    external_id: str
    title: str
    status: str
    ticket_type: str
    priority: str
    story_points: Optional[int]
    assignee: Optional[str]
    is_blocker: bool
    created_date: Optional[datetime]

    class Config:
        from_attributes = True


class RiskResponse(BaseModel):
    id: str
    project_id: str
    title: str
    description: str
    category: str
    severity: str
    probability: float
    impact: float
    risk_score: float
    status: str
    mitigation: Optional[str]
    owner: Optional[str]
    due_date: Optional[datetime]
    is_ai_generated: bool
    ai_confidence: Optional[float]
    ai_reasoning: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class RiskCreate(BaseModel):
    title: str
    description: str
    category: str
    severity: str
    probability: float = Field(..., ge=0.0, le=1.0)
    impact: float = Field(..., ge=0.0, le=1.0)
    mitigation: Optional[str] = None
    owner: Optional[str] = None
    due_date: Optional[datetime] = None


class PortfolioSummary(BaseModel):
    total_projects: int
    active_projects: int
    at_risk_projects: int
    on_hold_projects: int
    completed_projects: int
    total_open_risks: int
    critical_risks: int
    avg_health_score: float
    overall_confidence: float
    projects: List[ProjectResponse]
