from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.models.report import Report, MeetingTranscript
from app.schemas.report import (
    ReportGenerateRequest, ReportResponse,
    MeetingTranscriptUpload, MeetingAnalysisResponse,
    ApprovalRequest, AIApprovalResponse
)
from app.services.audit_service import AuditService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("", response_model=List[ReportResponse])
async def list_reports(
    project_id: Optional[str] = None,
    report_type: Optional[str] = None,
    limit: int = 20,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Report).order_by(Report.created_at.desc()).limit(limit)
    if project_id:
        query = query.where(Report.project_id == project_id)
    if report_type:
        query = query.where(Report.report_type == report_type)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    request: ReportGenerateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.tasks.agent_tasks import run_executive_report
    task = run_executive_report.delay(
        project_id=request.project_id,
        report_type=request.report_type,
        audience=request.audience,
        period_start=request.period_start.isoformat() if request.period_start else None,
        period_end=request.period_end.isoformat() if request.period_end else None,
        custom_instructions=request.custom_instructions,
        user_id=current_user.id,
    )
    audit = AuditService(db)
    await audit.log(
        action="report_generation_requested",
        resource_type="report",
        user_id=current_user.id,
        details={"report_type": request.report_type, "task_id": task.id},
    )
    return {
        "id": task.id,
        "title": f"Generating {request.report_type} report...",
        "report_type": request.report_type,
        "audience": request.audience,
        "content": "Report generation in progress. Check task status.",
        "status": "generating",
        "is_approved": False,
        "generated_by_agent": "executive_reporting",
        "created_at": __import__("datetime").datetime.utcnow(),
    }


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/meetings/analyze", response_model=MeetingAnalysisResponse)
async def analyze_meeting(
    data: MeetingTranscriptUpload,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.tasks.agent_tasks import analyze_meeting_transcript
    transcript = MeetingTranscript(
        title=data.title,
        project_id=data.project_id,
        transcript_text=data.transcript_text,
        meeting_date=data.meeting_date,
        duration_minutes=data.duration_minutes,
        participants=data.participants,
        uploaded_by=current_user.id,
    )
    db.add(transcript)
    await db.flush()
    task = analyze_meeting_transcript.delay(transcript_id=transcript.id)
    return {
        "id": transcript.id,
        "title": data.title,
        "summary": "Analysis in progress...",
        "decisions": [],
        "action_items": [],
        "risks": [],
        "follow_ups": [],
    }


@router.get("/approvals/pending", response_model=List[AIApprovalResponse])
async def get_pending_approvals(
    current_user=Depends(require_permission("approve:ai_actions")),
    db: AsyncSession = Depends(get_db),
):
    audit = AuditService(db)
    return await audit.get_pending_approvals()


@router.post("/approvals/{approval_id}")
async def process_approval(
    approval_id: str,
    body: ApprovalRequest,
    current_user=Depends(require_permission("approve:ai_actions")),
    db: AsyncSession = Depends(get_db),
):
    audit = AuditService(db)
    approval = await audit.process_approval(
        approval_id, current_user.id, body.decision, body.notes
    )
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return {"message": f"Approval {body.decision}d successfully", "id": approval.id}
