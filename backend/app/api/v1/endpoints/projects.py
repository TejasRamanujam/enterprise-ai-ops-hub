from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.services.project_service import ProjectService
from app.services.audit_service import AuditService
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetailResponse,
    SprintCreate, SprintResponse, RiskCreate, RiskResponse, PortfolioSummary
)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/portfolio", response_model=PortfolioSummary)
async def get_portfolio(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    return await service.get_portfolio_summary()


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    if status:
        from sqlalchemy import select
        from app.models.project import Project
        result = await db.execute(
            select(Project).where(Project.status == status).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
    return await service.get_all(skip=skip, limit=limit)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    current_user=Depends(require_permission("write:all")),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    audit = AuditService(db)
    if await service.get_by_key(data.key):
        raise HTTPException(status_code=400, detail=f"Project key '{data.key}' already exists")
    project = await service.create(data)
    await audit.log("project_created", "project", project.id, current_user.id)
    return project


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    project = await service.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    project = await service.update(project_id, data)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/{project_id}/sprints", response_model=List[SprintResponse])
async def get_sprints(
    project_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    project = await service.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return await service.get_sprints(project_id)


@router.post("/{project_id}/sprints", response_model=SprintResponse, status_code=201)
async def create_sprint(
    project_id: str,
    data: SprintCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data.project_id = project_id
    service = ProjectService(db)
    return await service.create_sprint(data)


@router.get("/{project_id}/risks", response_model=List[RiskResponse])
async def get_risks(
    project_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.models.risk import Risk
    result = await db.execute(
        select(Risk).where(Risk.project_id == project_id).order_by(Risk.risk_score.desc())
    )
    return list(result.scalars().all())


@router.post("/{project_id}/risks", response_model=RiskResponse, status_code=201)
async def create_risk(
    project_id: str,
    data: RiskCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.risk import Risk
    risk = Risk(
        project_id=project_id,
        risk_score=data.probability * data.impact * 10,
        is_ai_generated=False,
        **data.model_dump(),
    )
    db.add(risk)
    await db.flush()
    await db.refresh(risk)
    return risk
