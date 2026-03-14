from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
import uuid

from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.services.audit_service import AuditService

router = APIRouter(prefix="/agents", tags=["AI Agents"])


class AgentRunRequest(BaseModel):
    agent_name: str
    project_id: Optional[str] = None
    parameters: Optional[dict] = None
    require_approval: bool = False


class AgentRunResponse(BaseModel):
    task_id: str
    agent_name: str
    status: str
    message: str


class WorkflowRunRequest(BaseModel):
    project_id: str
    include_agents: List[str] = [
        "data_aggregation", "project_health", "risk_detection",
        "executive_reporting", "action_items"
    ]


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    request: AgentRunRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.tasks.agent_tasks import run_agent_task

    task = run_agent_task.delay(
        agent_name=request.agent_name,
        project_id=request.project_id,
        parameters=request.parameters or {},
        user_id=current_user.id,
    )
    audit = AuditService(db)
    await audit.log(
        action="agent_run_requested",
        resource_type="agent",
        user_id=current_user.id,
        details={"agent": request.agent_name, "project_id": request.project_id},
    )
    return AgentRunResponse(
        task_id=task.id,
        agent_name=request.agent_name,
        status="queued",
        message=f"Agent '{request.agent_name}' queued for execution",
    )


@router.post("/workflow/run", response_model=AgentRunResponse)
async def run_full_workflow(
    request: WorkflowRunRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.tasks.agent_tasks import run_full_project_workflow

    task = run_full_project_workflow.delay(
        project_id=request.project_id,
        include_agents=request.include_agents,
        user_id=current_user.id,
    )
    return AgentRunResponse(
        task_id=task.id,
        agent_name="orchestrator",
        status="queued",
        message=f"Full workflow queued for project {request.project_id}",
    )


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user=Depends(get_current_user),
):
    from app.tasks.celery_app import celery_app
    from celery.result import AsyncResult

    result = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
        "traceback": result.traceback if result.failed() else None,
    }


@router.get("/prompt-versions")
async def list_prompt_versions(
    agent_name: Optional[str] = None,
    current_user=Depends(require_permission("configure:agents")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.models.audit import PromptVersion
    query = select(PromptVersion).order_by(PromptVersion.created_at.desc())
    if agent_name:
        query = query.where(PromptVersion.agent_name == agent_name)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/token-usage")
async def get_token_usage(
    days: int = 30,
    current_user=Depends(require_permission("view:audit_logs")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select, func
    from app.models.audit import TokenUsage
    from datetime import datetime, timedelta, timezone

    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            TokenUsage.agent_name,
            TokenUsage.model,
            func.sum(TokenUsage.total_tokens).label("total_tokens"),
            func.sum(TokenUsage.estimated_cost_usd).label("total_cost"),
            func.count(TokenUsage.id).label("call_count"),
        )
        .where(TokenUsage.created_at >= since)
        .group_by(TokenUsage.agent_name, TokenUsage.model)
    )
    rows = result.all()
    return [
        {
            "agent_name": r.agent_name,
            "model": r.model,
            "total_tokens": r.total_tokens,
            "total_cost_usd": round(r.total_cost or 0, 4),
            "call_count": r.call_count,
        }
        for r in rows
    ]
