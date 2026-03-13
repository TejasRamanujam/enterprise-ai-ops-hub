from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user, require_permission
from app.services.knowledge_service import KnowledgeService
from app.schemas.knowledge import (
    KnowledgeQueryRequest, KnowledgeQueryResponse,
    KnowledgeSourceResponse, IntegrationConfig, IntegrationResponse,
    SyncTriggerResponse
)

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


@router.post("/query", response_model=KnowledgeQueryResponse)
async def query_knowledge(
    request: KnowledgeQueryRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    return await service.query(request, user_id=current_user.id)


@router.get("/sources", response_model=List[KnowledgeSourceResponse])
async def list_sources(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = KnowledgeService(db)
    return await service.get_sources()


@router.post("/integrations", response_model=IntegrationResponse, status_code=201)
async def create_integration(
    config: IntegrationConfig,
    current_user=Depends(require_permission("manage:integrations")),
    db: AsyncSession = Depends(get_db),
):
    from app.models.knowledge import Integration
    integration = Integration(
        name=config.name,
        integration_type=config.integration_type,
        config=config.config,
        is_enabled=True,
    )
    db.add(integration)
    await db.flush()
    await db.refresh(integration)
    return integration


@router.get("/integrations", response_model=List[IntegrationResponse])
async def list_integrations(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.models.knowledge import Integration
    result = await db.execute(select(Integration).order_by(Integration.name))
    return list(result.scalars().all())


@router.post("/integrations/{integration_id}/sync", response_model=SyncTriggerResponse)
async def trigger_sync(
    integration_id: str,
    current_user=Depends(require_permission("manage:integrations")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from app.models.knowledge import Integration
    from app.tasks.sync_tasks import sync_integration

    result = await db.execute(select(Integration).where(Integration.id == integration_id))
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    task = sync_integration.delay(integration_id=integration_id)
    return SyncTriggerResponse(
        task_id=task.id,
        integration_id=integration_id,
        status="queued",
        message=f"Sync started for {integration.name}",
    )
