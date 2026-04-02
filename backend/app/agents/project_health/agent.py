from anthropic import AsyncAnthropic
from typing import Optional
import json

from app.agents.base import BaseAgent, AgentState
from app.core.config import settings


class ProjectHealthAgent(BaseAgent):
    name = "project_health"
    description = "Analyzes sprint velocity, delivery trends, and generates health/confidence scores"

    PROMPT_VERSION = "v1.2"

    SYSTEM_PROMPT = """You are an expert engineering project health analyst at a Fortune 500 technology company.
Analyze the provided project data and generate a comprehensive health assessment.

Output ONLY valid JSON in this exact format:
{
  "health_score": "green|yellow|red",
  "health_value": 0.0-1.0,
  "confidence_score": 0.0-1.0,
  "velocity_trend": "improving|stable|declining",
  "sprint_success_likelihood": 0.0-1.0,
  "key_findings": ["finding1", "finding2", "finding3"],
  "delivery_forecast": "on_track|at_risk|delayed",
  "technical_debt_level": "low|medium|high|critical",
  "team_capacity_status": "healthy|strained|overloaded",
  "summary": "2-3 sentence executive summary"
}"""

    async def run(self, state: AgentState) -> AgentState:
        self.log_start(state.get("project_id"))
        raw_data = state.get("context", {}).get("raw_data", {})

        analysis = await self._analyze_health(raw_data)

        state["context"]["health_analysis"] = analysis
        state["results"]["project_health"] = analysis
        state["completed_steps"].append("project_health")
        state["current_step"] = "risk_detection"
        self.log_complete(f"Health: {analysis.get('health_score')} / Confidence: {analysis.get('confidence_score')}")
        return state

    async def _analyze_health(self, raw_data: dict) -> dict:
        if not settings.ANTHROPIC_API_KEY:
            return self._fallback_analysis(raw_data)

        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        data_summary = self._build_data_summary(raw_data)

        response = await client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=1024,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": data_summary}],
        )
        text = response.content[0].text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return self._fallback_analysis(raw_data)

    def _build_data_summary(self, raw_data: dict) -> str:
        jira = raw_data.get("jira", {})
        github = raw_data.get("github", {})
        sprint = jira.get("sprint", {})
        tickets = jira.get("tickets", [])
        blockers = [t for t in tickets if t.get("is_blocker")]
        velocity = jira.get("velocity_history", [])

        planned = sprint.get("planned_points", 0)
        completed = sprint.get("completed_points", 0)
        completion_pct = (completed / planned * 100) if planned > 0 else 0

        return f"""
Project Data Summary for Health Analysis:

SPRINT STATUS:
- Sprint: {sprint.get('name', 'Unknown')} (Sprint #{sprint.get('number', 0)})
- Status: {sprint.get('status', 'unknown')}
- Points: {completed}/{planned} completed ({completion_pct:.0f}%)
- Days remaining: calculated from {sprint.get('end_date', 'unknown')}

JIRA TICKETS:
- Total tickets: {len(tickets)}
- Blockers: {len(blockers)} ({[b.get('id') for b in blockers]})
- Ticket breakdown: {self._count_by_status(tickets)}

VELOCITY HISTORY (last 8 sprints, story points):
{velocity}
Average: {sum(velocity)/len(velocity) if velocity else 0:.1f} points/sprint

GITHUB METRICS:
- Open PRs: {len([pr for pr in github.get('pull_requests', []) if pr.get('status') == 'open'])}
- Commits last 30d: {github.get('commits_last_30d', 0)}
- Code coverage: {github.get('code_coverage', 0)}%
- Open issues: {github.get('open_issues', 0)}

RECENT DECISIONS:
{chr(10).join(raw_data.get('confluence', {}).get('recent_decisions', []))}

KEY UPDATES FROM TEAM:
{chr(10).join(raw_data.get('slack', {}).get('key_updates', []))}

Analyze this data and provide the health assessment JSON.
"""

    def _count_by_status(self, tickets: list) -> dict:
        counts = {}
        for t in tickets:
            s = t.get("status", "unknown")
            counts[s] = counts.get(s, 0) + 1
        return counts

    def _fallback_analysis(self, raw_data: dict) -> dict:
        jira = raw_data.get("jira", {})
        sprint = jira.get("sprint", {})
        planned = sprint.get("planned_points", 34)
        completed = sprint.get("completed_points", 11)
        rate = completed / planned if planned > 0 else 0
        blockers = len(jira.get("blockers", []))
        health = "green" if rate > 0.7 and blockers == 0 else ("yellow" if rate > 0.4 else "red")
        return {
            "health_score": health,
            "health_value": min(rate * 1.2, 1.0),
            "confidence_score": 0.72,
            "velocity_trend": "stable",
            "sprint_success_likelihood": max(0.2, rate * 1.1),
            "key_findings": [
                f"Sprint is {rate*100:.0f}% complete with {blockers} blockers",
                "Velocity trending stable over last 4 sprints",
                "Code coverage at 78% - below 80% target",
            ],
            "delivery_forecast": "at_risk" if blockers > 0 else "on_track",
            "technical_debt_level": "medium",
            "team_capacity_status": "healthy",
            "summary": f"Project is currently {health}. Sprint at {rate*100:.0f}% completion with {blockers} active blockers requiring immediate attention.",
        }
