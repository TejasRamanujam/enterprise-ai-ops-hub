from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.core.security import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview")
async def get_overview(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.project import Project, Sprint
    from app.models.risk import Risk
    from app.models.report import Report
    from app.models.audit import TokenUsage

    projects_result = await db.execute(select(func.count(Project.id)))
    active_result = await db.execute(
        select(func.count(Project.id)).where(Project.status == "active")
    )
    risks_result = await db.execute(
        select(func.count(Risk.id)).where(Risk.status == "open")
    )
    reports_result = await db.execute(
        select(func.count(Report.id)).where(
            Report.created_at >= datetime.now(timezone.utc) - timedelta(days=30)
        )
    )
    tokens_result = await db.execute(
        select(func.sum(TokenUsage.total_tokens)).where(
            TokenUsage.created_at >= datetime.now(timezone.utc) - timedelta(days=30)
        )
    )

    return {
        "total_projects": projects_result.scalar() or 0,
        "active_projects": active_result.scalar() or 0,
        "open_risks": risks_result.scalar() or 0,
        "reports_generated_30d": reports_result.scalar() or 0,
        "tokens_used_30d": tokens_result.scalar() or 0,
        "automation_efficiency": 87.3,
    }


@router.get("/velocity")
async def get_velocity_trends(
    project_id: Optional[str] = None,
    periods: int = Query(8, ge=1, le=20),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.project import Sprint
    query = (
        select(Sprint)
        .where(Sprint.status == "completed")
        .order_by(Sprint.end_date.desc())
        .limit(periods)
    )
    if project_id:
        query = query.where(Sprint.project_id == project_id)
    result = await db.execute(query)
    sprints = list(result.scalars().all())
    return [
        {
            "sprint_name": s.name,
            "planned": s.planned_points,
            "completed": s.completed_points,
            "velocity": s.velocity,
            "completion_rate": s.completion_rate,
            "end_date": s.end_date,
        }
        for s in reversed(sprints)
    ]


@router.get("/risk-heatmap")
async def get_risk_heatmap(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.risk import Risk
    result = await db.execute(
        select(Risk).where(Risk.status == "open").order_by(Risk.risk_score.desc())
    )
    risks = result.scalars().all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "category": r.category,
            "probability": r.probability,
            "impact": r.impact,
            "risk_score": r.risk_score,
            "severity": r.severity,
            "project_id": r.project_id,
        }
        for r in risks
    ]


@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = Query(50, le=500),
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.audit import AuditLog
    query = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if action:
        query = query.where(AuditLog.action.ilike(f"%{action}%"))
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    result = await db.execute(query)
    logs = result.scalars().all()
    return [
        {
            "id": l.id,
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "user_id": l.user_id,
            "status": l.status,
            "created_at": l.created_at,
        }
        for l in logs
    ]
