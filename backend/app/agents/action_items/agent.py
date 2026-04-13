from anthropic import AsyncAnthropic
from typing import List
import json
from datetime import datetime, timedelta, timezone

from app.agents.base import BaseAgent, AgentState
from app.core.config import settings


class ActionItemAgent(BaseAgent):
    name = "action_items"
    description = "Generates follow-up tasks, assigns owners, and sets recommended deadlines"

    SYSTEM_PROMPT = """You are an expert project coordinator. Analyze risks and project state.
Generate a prioritized list of action items.

Output ONLY valid JSON array:
[
  {
    "title": "Action item title",
    "description": "Specific steps to take",
    "owner_role": "Engineering Manager|Tech Lead|Product Manager|Engineer|DevOps",
    "priority": "critical|high|medium|low",
    "category": "blocker_resolution|risk_mitigation|process|technical|communication",
    "estimated_hours": 0-40,
    "due_days": 1-14,
    "reasoning": "Why this action is needed"
  }
]
Generate 4-8 action items ordered by priority."""

    async def run(self, state: AgentState) -> AgentState:
        self.log_start(state.get("project_id"))
        risks = state.get("context", {}).get("risks", [])
        health = state.get("context", {}).get("health_analysis", {})
        raw_data = state.get("context", {}).get("raw_data", {})

        actions = await self._generate_actions(risks, health, raw_data)

        state["results"]["action_items"] = {
            "actions": actions,
            "critical_count": len([a for a in actions if a.get("priority") == "critical"]),
            "total_count": len(actions),
        }
        state["completed_steps"].append("action_items")
        state["current_step"] = "completed"
        self.log_complete(f"Generated {len(actions)} action items")
        return state

    async def _generate_actions(self, risks: list, health: dict, raw_data: dict) -> List[dict]:
        if not settings.ANTHROPIC_API_KEY:
            return self._fallback_actions(risks, health, raw_data)

        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        prompt = self._build_prompt(risks, health, raw_data)

        response = await client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=1500,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        try:
            actions = json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\[.*\]', text, re.DOTALL)
            actions = json.loads(match.group()) if match else self._fallback_actions(risks, health, raw_data)

        now = datetime.now(timezone.utc)
        for a in actions:
            a["due_date"] = (now + timedelta(days=a.get("due_days", 3))).strftime("%Y-%m-%d")
        return actions

    def _build_prompt(self, risks: list, health: dict, raw_data: dict) -> str:
        jira = raw_data.get("jira", {})
        return f"""
Generate prioritized action items based on:

RISKS ({len(risks)} identified):
{chr(10).join(f"- [{r.get('severity')}] {r.get('title')}: {r.get('mitigation', '')}" for r in risks[:5])}

HEALTH STATUS:
- Score: {health.get('health_score', 'yellow')}
- Delivery: {health.get('delivery_forecast', 'at_risk')}
- Team Capacity: {health.get('team_capacity_status', 'healthy')}

ACTIVE BLOCKERS: {jira.get('blockers', [])}
KEY FINDINGS: {health.get('key_findings', [])}

Generate concrete, specific, immediately actionable items with owners and deadlines.
"""

    def _fallback_actions(self, risks: list, health: dict, raw_data: dict) -> List[dict]:
        now = datetime.now(timezone.utc)
        jira = raw_data.get("jira", {})
        blockers = jira.get("blockers", [])

        actions = []
        if blockers:
            actions.append({
                "title": f"Resolve blocker on {blockers[0] if blockers else 'DEMO-102'}",
                "description": "Schedule immediate call with DBA team to unblock database migration. Escalate to VP Engineering if not resolved in 24h.",
                "owner_role": "Engineering Manager",
                "priority": "critical",
                "category": "blocker_resolution",
                "estimated_hours": 2,
                "due_days": 1,
                "due_date": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
                "reasoning": "Active blocker directly impacts sprint completion",
            })

        actions += [
            {
                "title": "Review and reduce sprint scope",
                "description": "Meet with PO to deprioritize 2-3 tickets to ensure quality delivery of remaining scope.",
                "owner_role": "Product Manager",
                "priority": "high",
                "category": "risk_mitigation",
                "estimated_hours": 1,
                "due_days": 1,
                "due_date": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
                "reasoning": "Sprint success likelihood below 50% requires scope adjustment",
            },
            {
                "title": "Assign reviewers to open PRs",
                "description": "Assign code reviewers to PRs #232 and #234. Set 24-hour review SLA.",
                "owner_role": "Tech Lead",
                "priority": "high",
                "category": "process",
                "estimated_hours": 0.5,
                "due_days": 1,
                "due_date": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
                "reasoning": "Unreviewed PRs block feature completion",
            },
            {
                "title": "Add unit tests to increase coverage",
                "description": "Write unit tests for auth module to bring coverage above 80% threshold before deployment.",
                "owner_role": "Engineer",
                "priority": "medium",
                "category": "technical",
                "estimated_hours": 4,
                "due_days": 3,
                "due_date": (now + timedelta(days=3)).strftime("%Y-%m-%d"),
                "reasoning": "Code coverage below 80% deployment gate threshold",
            },
            {
                "title": "Send stakeholder status update",
                "description": "Send proactive risk communication to stakeholders noting sprint delivery risk and mitigation plan.",
                "owner_role": "Product Manager",
                "priority": "medium",
                "category": "communication",
                "estimated_hours": 0.5,
                "due_days": 1,
                "due_date": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
                "reasoning": "Stakeholders should be informed of delivery risk proactively",
            },
        ]
        return actions
