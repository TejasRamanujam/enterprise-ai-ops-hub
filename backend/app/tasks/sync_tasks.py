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


@celery_app.task(name="app.tasks.sync_tasks.sync_integration", bind=True)
def sync_integration(self, integration_id: str):
    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.models.knowledge import Integration, KnowledgeSource
        from app.services.knowledge_service import KnowledgeService
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Integration).where(Integration.id == integration_id))
            integration = result.scalar_one_or_none()
            if not integration:
                return {"error": "Integration not found"}

            integration.last_sync_at = datetime.now(timezone.utc)

            try:
                connector = _get_connector(integration.integration_type, integration.config or {})
                data = await connector.fetch_data(**(integration.config or {}))

                service = KnowledgeService(db)
                source_result = await db.execute(
                    select(KnowledgeSource).where(KnowledgeSource.name == integration.name)
                )
                source = source_result.scalar_one_or_none()
                if not source:
                    source = KnowledgeSource(
                        name=integration.name,
                        source_type=integration.integration_type,
                    )
                    db.add(source)
                    await db.flush()

                chunks_ingested = await _ingest_integration_data(
                    service, source.id, integration.integration_type, data
                )

                integration.last_sync_status = "success"
                integration.sync_count += 1
                source.document_count = chunks_ingested
                source.last_synced_at = datetime.now(timezone.utc)
                await db.commit()

                return {"status": "success", "chunks_ingested": chunks_ingested}

            except Exception as e:
                integration.last_sync_status = "error"
                integration.last_error = str(e)
                await db.commit()
                logger.error("sync_error", integration_id=integration_id, error=str(e))
                return {"status": "error", "error": str(e)}

    return run_async(_run())


def _get_connector(integration_type: str, config: dict):
    if integration_type == "jira":
        from app.integrations.jira.connector import JiraConnector
        return JiraConnector()
    elif integration_type == "github":
        from app.integrations.github.connector import GitHubConnector
        return GitHubConnector()
    elif integration_type == "confluence":
        from app.integrations.confluence.connector import ConfluenceConnector
        return ConfluenceConnector()
    elif integration_type == "slack":
        from app.integrations.slack.connector import SlackConnector
        return SlackConnector()
    raise ValueError(f"Unknown integration type: {integration_type}")


async def _ingest_integration_data(service, source_id: str, integration_type: str, data: dict) -> int:
    count = 0
    if integration_type == "jira":
        for ticket in data.get("tickets", []):
            await service.ingest_chunk(
                source_id=source_id,
                title=f"[{ticket['id']}] {ticket['title']}",
                content=f"Status: {ticket['status']}\nType: {ticket['type']}\nPriority: {ticket['priority']}\nAssignee: {ticket.get('assignee','Unassigned')}",
                document_id=ticket["id"],
                tags=["jira", "ticket", ticket.get("type", "").lower()],
            )
            count += 1
    elif integration_type == "confluence":
        for page in data.get("pages", []):
            await service.ingest_chunk(
                source_id=source_id,
                title=page["title"],
                content=page.get("content", page["title"]),
                document_id=page["id"],
                document_url=page.get("url"),
                author=page.get("author"),
                tags=["confluence", "documentation"] + page.get("labels", []),
            )
            count += 1
    elif integration_type == "github":
        for pr in data.get("pull_requests", []):
            await service.ingest_chunk(
                source_id=source_id,
                title=f"PR #{pr['number']}: {pr['title']}",
                content=f"Status: {pr['status']}\nAuthor: {pr['author']}\nReviewers: {', '.join(pr.get('reviewers', []))}",
                document_id=str(pr["number"]),
                tags=["github", "pull_request", pr.get("status", "")],
            )
            count += 1
    return count
