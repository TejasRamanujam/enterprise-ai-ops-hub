import asyncio
from typing import Optional, List
import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger()


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.agent_tasks.run_full_project_workflow", bind=True)
def run_full_project_workflow(
    self,
    project_id: str,
    include_agents: Optional[List[str]] = None,
    user_id: Optional[str] = None,
    audience: str = "manager",
    report_type: str = "weekly",
):
    logger.info("task_started", task="run_full_project_workflow", project_id=project_id)
    self.update_state(state="PROGRESS", meta={"step": "initializing"})

    async def _run():
        from app.agents.orchestrator.workflow import run_project_workflow
        from app.core.database import AsyncSessionLocal
        from app.models.project import Project
        from app.models.report import Report
        from sqlalchemy import select

        result = await run_project_workflow(
            project_id=project_id,
            user_id=user_id,
            include_agents=include_agents,
            audience=audience,
            report_type=report_type,
        )

        async with AsyncSessionLocal() as db:
            # Persist report
            report_data = result.get("results", {}).get("executive_reporting", {})
            if report_data.get("content"):
                report = Report(
                    project_id=project_id,
                    title=f"{report_type.title()} Report — {__import__('datetime').date.today()}",
                    report_type=report_type,
                    audience=audience,
                    content=report_data["content"],
                    summary=report_data.get("summary"),
                    key_metrics=report_data.get("key_metrics"),
                    action_items=result.get("results", {}).get("action_items", {}).get("actions", []),
                    status="published",
                    generated_by_agent="orchestrator",
                    model_used=report_data.get("model_used"),
                )
                db.add(report)

            # Update project health
            health = result.get("results", {}).get("project_health", {})
            if health.get("health_score"):
                proj_result = await db.execute(select(Project).where(Project.id == project_id))
                project = proj_result.scalar_one_or_none()
                if project:
                    project.health_score = health["health_score"]
                    project.health_score_value = health.get("health_value")
                    project.confidence_score = health.get("confidence_score")

            # Persist risks
            risk_data = result.get("results", {}).get("risk_detection", {})
            risks = risk_data.get("risks", [])
            from app.models.risk import Risk
            for r in risks:
                risk = Risk(
                    project_id=project_id,
                    title=r.get("title", ""),
                    description=r.get("description", ""),
                    category=r.get("category", "technical"),
                    severity=r.get("severity", "medium"),
                    probability=r.get("probability", 0.5),
                    impact=r.get("impact", 0.5),
                    risk_score=r.get("risk_score", 2.5),
                    mitigation=r.get("mitigation"),
                    owner=r.get("owner"),
                    is_ai_generated=True,
                    ai_confidence=r.get("ai_confidence"),
                    ai_reasoning=r.get("ai_reasoning"),
                )
                db.add(risk)

            await db.commit()
        return result

    return run_async(_run())


@celery_app.task(name="app.tasks.agent_tasks.run_agent_task", bind=True)
def run_agent_task(
    self,
    agent_name: str,
    project_id: Optional[str] = None,
    parameters: Optional[dict] = None,
    user_id: Optional[str] = None,
):
    logger.info("task_started", task="run_agent_task", agent=agent_name, project_id=project_id)

    agent_map = {
        "data_aggregation": "app.agents.data_aggregation.agent.DataAggregationAgent",
        "project_health": "app.agents.project_health.agent.ProjectHealthAgent",
        "risk_detection": "app.agents.risk_detection.agent.RiskDetectionAgent",
        "executive_reporting": "app.agents.executive_reporting.agent.ExecutiveReportingAgent",
        "action_items": "app.agents.action_items.agent.ActionItemAgent",
    }

    agent_path = agent_map.get(agent_name)
    if not agent_path:
        return {"error": f"Unknown agent: {agent_name}"}

    async def _run():
        module_path, class_name = agent_path.rsplit(".", 1)
        import importlib
        module = importlib.import_module(module_path)
        agent_class = getattr(module, class_name)
        agent = agent_class()

        from app.agents.base import AgentState
        state: AgentState = {
            "project_id": project_id,
            "user_id": user_id,
            "messages": [],
            "context": parameters or {},
            "results": {},
            "errors": [],
            "current_step": agent_name,
            "completed_steps": [],
        }
        result_state = await agent.run(state)
        return result_state.get("results", {}).get(agent_name, {})

    return run_async(_run())


@celery_app.task(name="app.tasks.agent_tasks.run_executive_report", bind=True)
def run_executive_report(
    self,
    project_id: Optional[str],
    report_type: str,
    audience: str,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    custom_instructions: Optional[str] = None,
    user_id: Optional[str] = None,
):
    return run_full_project_workflow(
        project_id=project_id or "portfolio",
        include_agents=["data_aggregation", "project_health", "executive_reporting"],
        user_id=user_id,
        audience=audience,
        report_type=report_type,
    )


@celery_app.task(name="app.tasks.agent_tasks.analyze_meeting_transcript", bind=True)
def analyze_meeting_transcript(self, transcript_id: str):
    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.models.report import MeetingTranscript
        from sqlalchemy import select
        from anthropic import AsyncAnthropic
        import json

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(MeetingTranscript).where(MeetingTranscript.id == transcript_id)
            )
            transcript = result.scalar_one_or_none()
            if not transcript:
                return {"error": "Transcript not found"}

            from app.core.config import settings
            client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

            prompt = f"""Analyze this meeting transcript and extract key information.

Transcript:
{transcript.transcript_text[:4000]}

Output JSON with this structure:
{{
  "summary": "2-3 sentence summary",
  "decisions": [{{"decision": "...", "owner": "...", "context": "..."}}],
  "action_items": [{{"action": "...", "owner": "...", "due": "...", "priority": "high|medium|low"}}],
  "risks": [{{"risk": "...", "severity": "...", "mitigation": "..."}}],
  "follow_ups": [{{"item": "...", "owner": "...", "due": "..."}}]
}}"""

            response = await client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text
            try:
                analysis = json.loads(text)
            except json.JSONDecodeError:
                import re
                match = re.search(r'\{.*\}', text, re.DOTALL)
                analysis = json.loads(match.group()) if match else {}

            transcript.summary = analysis.get("summary", "")
            transcript.decisions = analysis.get("decisions", [])
            transcript.action_items = analysis.get("action_items", [])
            transcript.risks = analysis.get("risks", [])
            transcript.follow_ups = analysis.get("follow_ups", [])
            transcript.processed = True
            await db.commit()

        return analysis

    return run_async(_run())
