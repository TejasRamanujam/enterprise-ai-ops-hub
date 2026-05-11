import asyncio
import structlog
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app

logger = structlog.get_logger()


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.scheduled_tasks.sync_all_integrations")
def sync_all_integrations():
    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.models.knowledge import Integration
        from app.tasks.sync_tasks import sync_integration
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Integration).where(Integration.is_enabled == True))
            integrations = result.scalars().all()

        for integration in integrations:
            sync_integration.delay(integration_id=integration.id)
            logger.info("scheduled_sync_queued", integration_id=integration.id)

        return {"queued": len(integrations)}

    return run_async(_run())


@celery_app.task(name="app.tasks.scheduled_tasks.generate_daily_health_reports")
def generate_daily_health_reports():
    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.models.project import Project
        from app.tasks.agent_tasks import run_full_project_workflow
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Project).where(Project.status == "active"))
            projects = result.scalars().all()

        for project in projects:
            run_full_project_workflow.delay(
                project_id=project.id,
                audience="manager",
                report_type="daily",
            )

        return {"projects_queued": len(projects)}

    return run_async(_run())


@celery_app.task(name="app.tasks.scheduled_tasks.cleanup_expired_approvals")
def cleanup_expired_approvals():
    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.models.audit import AIApproval
        from sqlalchemy import update

        async with AsyncSessionLocal() as db:
            await db.execute(
                update(AIApproval)
                .where(
                    AIApproval.status == "pending",
                    AIApproval.expires_at < datetime.now(timezone.utc),
                )
                .values(status="expired")
            )
            await db.commit()

    return run_async(_run())
