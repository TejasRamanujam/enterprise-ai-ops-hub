from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ReportGenerateRequest(BaseModel):
    project_id: Optional[str] = None
    report_type: str = Field(..., description="weekly|monthly|quarterly|sprint|executive|risk")
    audience: str = Field(default="manager", description="engineer|manager|executive")
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    custom_instructions: Optional[str] = None
    require_approval: bool = False


class ReportResponse(BaseModel):
    id: str
    project_id: Optional[str]
    title: str
    report_type: str
    audience: str
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    content: str
    summary: Optional[str]
    key_metrics: Optional[Dict[str, Any]]
    risks_identified: Optional[List[dict]]
    action_items: Optional[List[dict]]
    decisions_required: Optional[List[dict]]
    status: str
    is_approved: bool
    generated_by_agent: str
    model_used: Optional[str]
    token_cost: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class MeetingTranscriptUpload(BaseModel):
    title: str
    project_id: Optional[str] = None
    transcript_text: str
    meeting_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    participants: Optional[List[str]] = None


class MeetingAnalysisResponse(BaseModel):
    id: str
    title: str
    summary: str
    decisions: List[Dict[str, Any]]
    action_items: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]
    follow_ups: List[Dict[str, Any]]


class ApprovalRequest(BaseModel):
    approval_id: str
    decision: str = Field(..., description="approve|reject")
    notes: Optional[str] = None


class AIApprovalResponse(BaseModel):
    id: str
    agent_name: str
    action_type: str
    description: str
    proposed_data: Optional[Dict[str, Any]]
    ai_reasoning: Optional[str]
    confidence_score: Optional[float]
    status: str
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
