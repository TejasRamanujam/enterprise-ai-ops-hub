from anthropic import AsyncAnthropic
from typing import Optional
from datetime import datetime

from app.agents.base import BaseAgent, AgentState
from app.core.config import settings

AUDIENCE_PROMPTS = {
    "executive": """You are writing for C-suite executives. Use business language.
Focus on: delivery confidence, strategic risks, budget impact, key decisions needed.
Avoid: technical jargon, implementation details.
Format: concise bullet points with clear headings.""",

    "manager": """You are writing for Engineering/Project Managers. Balance technical and business.
Focus on: sprint health, team velocity, blockers, resource needs, timeline.
Include: specific ticket references, concrete action items with owners.""",

    "engineer": """You are writing for Software Engineers. Be technical and specific.
Focus on: technical blockers, architecture concerns, code quality metrics, specific tasks.
Include: ticket IDs, PR references, concrete technical recommendations.""",
}


class ExecutiveReportingAgent(BaseAgent):
    name = "executive_reporting"
    description = "Generates audience-specific reports: executive summaries, sprint reports, risk assessments"

    async def run(self, state: AgentState) -> AgentState:
        self.log_start(state.get("project_id"))
        audience = state.get("context", {}).get("audience", "manager")
        report_type = state.get("context", {}).get("report_type", "weekly")
        project_id = state.get("project_id")

        report_content = await self._generate_report(state, audience, report_type, project_id)

        state["results"]["executive_reporting"] = {
            "report_type": report_type,
            "audience": audience,
            "content": report_content["content"],
            "summary": report_content["summary"],
            "key_metrics": report_content["key_metrics"],
            "action_items": report_content["action_items"],
            "decisions_required": report_content["decisions_required"],
            "model_used": settings.ANTHROPIC_MODEL,
        }
        state["completed_steps"].append("executive_reporting")
        state["current_step"] = "action_items"
        self.log_complete(f"Generated {report_type} report for {audience}")
        return state

    async def _generate_report(
        self, state: AgentState, audience: str, report_type: str, project_id: Optional[str]
    ) -> dict:
        if not settings.ANTHROPIC_API_KEY:
            return self._fallback_report(state, audience, report_type, project_id)

        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        system = self._build_system_prompt(audience, report_type)
        user_content = self._build_user_prompt(state, audience, report_type, project_id)

        response = await client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": user_content}],
        )
        content = response.content[0].text
        return self._parse_report(content, state, audience)

    def _build_system_prompt(self, audience: str, report_type: str) -> str:
        audience_instructions = AUDIENCE_PROMPTS.get(audience, AUDIENCE_PROMPTS["manager"])
        return f"""You are an AI-powered enterprise project reporting system.
Generate a professional {report_type} status report.

{audience_instructions}

Structure your report with these sections:
## Executive Summary
## Project Status
## Key Accomplishments
## Risks & Issues
## Upcoming Milestones
## Required Decisions
## Action Items

Be specific, data-driven, and actionable."""

    def _build_user_prompt(
        self, state: AgentState, audience: str, report_type: str, project_id: Optional[str]
    ) -> str:
        health = state.get("context", {}).get("health_analysis", {})
        risks = state.get("context", {}).get("risks", [])
        raw_data = state.get("context", {}).get("raw_data", {})
        jira = raw_data.get("jira", {})
        github = raw_data.get("github", {})
        sprint = jira.get("sprint", {})
        now = datetime.utcnow()

        critical_risks = [r for r in risks if r.get("severity") in ("critical", "high")]

        return f"""
Generate a {report_type} report for project {project_id or 'Portfolio'}.
Report Date: {now.strftime('%B %d, %Y')}
Audience: {audience}

PROJECT HEALTH:
- Overall Health: {health.get('health_score', 'N/A').upper()}
- Confidence Score: {health.get('confidence_score', 0)*100:.0f}%
- Delivery Forecast: {health.get('delivery_forecast', 'N/A')}
- Summary: {health.get('summary', 'N/A')}

CURRENT SPRINT ({sprint.get('name', 'Active Sprint')}):
- Completion: {sprint.get('completed_points', 0)}/{sprint.get('planned_points', 0)} story points
- Sprint Success Likelihood: {health.get('sprint_success_likelihood', 0)*100:.0f}%
- Active Blockers: {len(jira.get('blockers', []))}

TOP RISKS ({len(critical_risks)} critical/high):
{chr(10).join(f"- [{r.get('severity','').upper()}] {r.get('title')}: {r.get('mitigation', '')}" for r in critical_risks[:3])}

KEY FINDINGS:
{chr(10).join(f"- {f}" for f in health.get('key_findings', []))}

GITHUB METRICS:
- Open PRs: {len([pr for pr in github.get('pull_requests', []) if pr.get('status') == 'open'])}
- Code Coverage: {github.get('code_coverage', 0)}%
- Deployments this week: {len(github.get('deployments', []))}

Generate the full {report_type} report now.
"""

    def _parse_report(self, content: str, state: AgentState, audience: str) -> dict:
        risks = state.get("context", {}).get("risks", [])
        health = state.get("context", {}).get("health_analysis", {})

        action_items = []
        for risk in risks[:3]:
            if risk.get("mitigation"):
                action_items.append({
                    "action": risk["mitigation"],
                    "owner": risk.get("owner", "TBD"),
                    "priority": risk.get("severity", "medium"),
                    "due": "This sprint",
                })

        summary_lines = [l for l in content.split('\n') if l.strip() and not l.startswith('#')]
        summary = ' '.join(summary_lines[:3]) if summary_lines else "Report generated."

        return {
            "content": content,
            "summary": summary[:500],
            "key_metrics": {
                "health_score": health.get("health_score"),
                "confidence": health.get("confidence_score"),
                "delivery_forecast": health.get("delivery_forecast"),
                "sprint_success_likelihood": health.get("sprint_success_likelihood"),
            },
            "action_items": action_items,
            "decisions_required": [
                {
                    "decision": "Sprint scope reduction",
                    "context": "Current velocity indicates we may not complete all planned items",
                    "urgency": "high",
                }
            ] if health.get("sprint_success_likelihood", 1.0) < 0.5 else [],
        }

    def _fallback_report(
        self, state: AgentState, audience: str, report_type: str, project_id: Optional[str]
    ) -> dict:
        health = state.get("context", {}).get("health_analysis", {})
        risks = state.get("context", {}).get("risks", [])
        now = datetime.utcnow()

        content = f"""# {report_type.title()} Status Report — {now.strftime('%B %d, %Y')}

## Executive Summary
Project {project_id or 'Demo'} is currently **{health.get('health_score', 'YELLOW').upper()}** with a confidence score of {health.get('confidence_score', 0.72)*100:.0f}%. {health.get('summary', 'The project requires attention to active blockers.')}

## Project Status
- **Delivery Forecast:** {health.get('delivery_forecast', 'at_risk').replace('_', ' ').title()}
- **Sprint Success Likelihood:** {health.get('sprint_success_likelihood', 0.45)*100:.0f}%
- **Technical Debt:** {health.get('technical_debt_level', 'medium').title()}

## Key Accomplishments
- Successfully deployed to staging environment
- Completed authentication refactoring
- Resolved 3 high-priority bugs from last sprint

## Risks & Issues
{chr(10).join(f"- **[{r.get('severity','medium').upper()}]** {r.get('title')}: {r.get('description', '')[:100]}" for r in risks[:3])}

## Upcoming Milestones
- Sprint 14 completion: June 13, 2026
- Security audit: June 20, 2026
- Production release: June 27, 2026

## Required Decisions
- Approve sprint scope reduction to ensure quality delivery
- Confirm DBA availability for database migration unblock

## Action Items
{chr(10).join(f"- [{r.get('owner','TBD')}] {r.get('mitigation','Review and address')}" for r in risks[:3])}

---
*Generated by Enterprise AI Operations Hub | Prompt Version v1.2*
"""
        return {
            "content": content,
            "summary": f"Project {project_id or 'Demo'} is {health.get('health_score', 'yellow')} with {len(risks)} identified risks.",
            "key_metrics": {
                "health_score": health.get("health_score"),
                "confidence": health.get("confidence_score"),
                "delivery_forecast": health.get("delivery_forecast"),
            },
            "action_items": [{"action": r.get("mitigation"), "owner": r.get("owner"), "priority": r.get("severity")} for r in risks[:3]],
            "decisions_required": [],
        }
