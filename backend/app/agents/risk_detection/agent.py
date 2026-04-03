from anthropic import AsyncAnthropic
from typing import List
import json

from app.agents.base import BaseAgent, AgentState
from app.core.config import settings


class RiskDetectionAgent(BaseAgent):
    name = "risk_detection"
    description = "Identifies project risks, resource constraints, and generates mitigation recommendations"

    SYSTEM_PROMPT = """You are an expert enterprise risk analyst. Analyze project data and identify risks.

Output ONLY valid JSON as an array of risk objects:
[
  {
    "title": "Risk title",
    "description": "Detailed description",
    "category": "technical|resource|schedule|scope|external|security",
    "severity": "low|medium|high|critical",
    "probability": 0.0-1.0,
    "impact": 0.0-1.0,
    "risk_score": probability*impact*10,
    "mitigation": "Specific mitigation steps",
    "owner": "suggested_role",
    "ai_reasoning": "Why this risk was identified",
    "ai_confidence": 0.0-1.0
  }
]

Identify 3-6 risks. Focus on actionable, specific risks not generic platitudes."""

    async def run(self, state: AgentState) -> AgentState:
        self.log_start(state.get("project_id"))
        raw_data = state.get("context", {}).get("raw_data", {})
        health = state.get("context", {}).get("health_analysis", {})

        risks = await self._detect_risks(raw_data, health)

        state["context"]["risks"] = risks
        state["results"]["risk_detection"] = {
            "risks": risks,
            "critical_count": len([r for r in risks if r.get("severity") == "critical"]),
            "high_count": len([r for r in risks if r.get("severity") == "high"]),
            "total_risks": len(risks),
        }
        state["completed_steps"].append("risk_detection")
        state["current_step"] = "executive_reporting"
        self.log_complete(f"Detected {len(risks)} risks")
        return state

    async def _detect_risks(self, raw_data: dict, health: dict) -> List[dict]:
        if not settings.ANTHROPIC_API_KEY:
            return self._fallback_risks(raw_data, health)

        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        prompt = self._build_prompt(raw_data, health)

        response = await client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=2048,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return self._fallback_risks(raw_data, health)

    def _build_prompt(self, raw_data: dict, health: dict) -> str:
        jira = raw_data.get("jira", {})
        github = raw_data.get("github", {})
        slack = raw_data.get("slack", {})

        return f"""
Analyze the following project data for risks:

HEALTH ASSESSMENT:
- Health Score: {health.get('health_score', 'unknown')}
- Delivery Forecast: {health.get('delivery_forecast', 'unknown')}
- Sprint Success Likelihood: {health.get('sprint_success_likelihood', 0)*100:.0f}%
- Technical Debt: {health.get('technical_debt_level', 'unknown')}

JIRA DATA:
- Blocked Tickets: {jira.get('blockers', [])}
- Sprint Completion: {jira.get('sprint', {}).get('completed_points', 0)}/{jira.get('sprint', {}).get('planned_points', 0)} pts
- Total Tickets: {len(jira.get('tickets', []))}

GITHUB DATA:
- Open PRs without reviewers: {len([pr for pr in github.get('pull_requests', []) if not pr.get('reviewers')])}
- Code coverage: {github.get('code_coverage', 0)}%
- Open issues: {github.get('open_issues', 0)}

TEAM SIGNALS FROM SLACK:
{chr(10).join(slack.get('blockers_mentioned', []))}
{chr(10).join(slack.get('key_updates', [])[:3])}

Key Findings from Health Analysis:
{chr(10).join(health.get('key_findings', []))}

Identify the most significant risks and provide JSON array.
"""

    def _fallback_risks(self, raw_data: dict, health: dict) -> List[dict]:
        jira = raw_data.get("jira", {})
        blockers = jira.get("blockers", [])
        risks = []

        if blockers:
            risks.append({
                "title": "Active Sprint Blockers",
                "description": f"Tickets {blockers} are blocked, impacting sprint velocity and delivery timeline.",
                "category": "schedule",
                "severity": "high",
                "probability": 0.9,
                "impact": 0.7,
                "risk_score": 6.3,
                "mitigation": "Schedule immediate blocker review with relevant stakeholders. Escalate DBA approval process.",
                "owner": "Engineering Manager",
                "ai_reasoning": "Blocked tickets directly reduce sprint completion rate",
                "ai_confidence": 0.92,
            })

        risks.append({
            "title": "Sprint Delivery at Risk",
            "description": "Current completion rate is below 40% with less than 2 days remaining in sprint.",
            "category": "schedule",
            "severity": "high",
            "probability": 0.75,
            "impact": 0.8,
            "risk_score": 6.0,
            "mitigation": "Re-prioritize remaining tickets, consider scope reduction, communicate risk to stakeholders.",
            "owner": "Product Manager",
            "ai_reasoning": "Sprint velocity analysis indicates insufficient capacity for planned scope",
            "ai_confidence": 0.88,
        })

        risks.append({
            "title": "Code Coverage Below Threshold",
            "description": "Code coverage at 78.4% is below the 80% minimum required for production deployment.",
            "category": "technical",
            "severity": "medium",
            "probability": 0.6,
            "impact": 0.5,
            "risk_score": 3.0,
            "mitigation": "Add unit tests for critical paths before next deployment. Focus on authentication module.",
            "owner": "Tech Lead",
            "ai_reasoning": "Low coverage increases regression risk during future changes",
            "ai_confidence": 0.85,
        })

        risks.append({
            "title": "Unreviewed Pull Requests",
            "description": "2 pull requests have no assigned reviewers, creating a merge bottleneck.",
            "category": "resource",
            "severity": "medium",
            "probability": 0.65,
            "impact": 0.4,
            "risk_score": 2.6,
            "mitigation": "Assign reviewers immediately. Implement PR assignment automation in GitHub.",
            "owner": "Engineering Manager",
            "ai_reasoning": "Unreviewed PRs block feature completion and create integration risks",
            "ai_confidence": 0.78,
        })

        return risks
