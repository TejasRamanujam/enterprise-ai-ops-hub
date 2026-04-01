from typing import Optional
from datetime import datetime, timezone
import asyncio
import structlog

from app.agents.base import BaseAgent, AgentState
from app.core.config import settings

logger = structlog.get_logger()


class DataAggregationAgent(BaseAgent):
    name = "data_aggregation"
    description = "Gathers and normalizes data from all integrated enterprise systems"

    async def run(self, state: AgentState) -> AgentState:
        self.log_start(state.get("project_id"))
        project_id = state.get("project_id")
        context = state.get("context", {})
        errors = state.get("errors", [])

        aggregated = {}

        # Gather from each integration source concurrently
        tasks = [
            self._fetch_jira_data(project_id, context),
            self._fetch_github_data(project_id, context),
            self._fetch_confluence_data(project_id, context),
            self._fetch_slack_data(project_id, context),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        sources = ["jira", "github", "confluence", "slack"]

        for source, result in zip(sources, results):
            if isinstance(result, Exception):
                errors.append(f"{source}: {str(result)}")
                aggregated[source] = {}
            else:
                aggregated[source] = result

        aggregated["aggregated_at"] = datetime.now(timezone.utc).isoformat()
        aggregated["project_id"] = project_id

        state["context"]["raw_data"] = aggregated
        state["results"]["data_aggregation"] = {
            "status": "completed",
            "sources_collected": [s for s in sources if aggregated.get(s)],
            "total_tickets": len(aggregated.get("jira", {}).get("tickets", [])),
            "total_prs": len(aggregated.get("github", {}).get("pull_requests", [])),
        }
        state["completed_steps"].append("data_aggregation")
        state["current_step"] = "project_health"
        self.log_complete(f"Aggregated from {len(sources)} sources")
        return state

    async def _fetch_jira_data(self, project_id: Optional[str], context: dict) -> dict:
        if not settings.JIRA_URL:
            return self._generate_demo_jira(project_id)
        from app.integrations.jira.connector import JiraConnector
        connector = JiraConnector()
        return await connector.fetch_project_data(
            project_key=context.get("jira_project_key", project_id)
        )

    async def _fetch_github_data(self, project_id: Optional[str], context: dict) -> dict:
        if not settings.GITHUB_TOKEN:
            return self._generate_demo_github(project_id)
        from app.integrations.github.connector import GitHubConnector
        connector = GitHubConnector()
        return await connector.fetch_repo_data(repo=context.get("github_repo"))

    async def _fetch_confluence_data(self, project_id: Optional[str], context: dict) -> dict:
        if not settings.CONFLUENCE_URL:
            return self._generate_demo_confluence(project_id)
        from app.integrations.confluence.connector import ConfluenceConnector
        connector = ConfluenceConnector()
        return await connector.fetch_space_data(space=context.get("confluence_space"))

    async def _fetch_slack_data(self, project_id: Optional[str], context: dict) -> dict:
        if not settings.SLACK_BOT_TOKEN:
            return self._generate_demo_slack(project_id)
        from app.integrations.slack.connector import SlackConnector
        connector = SlackConnector()
        return await connector.fetch_channel_data(channel=context.get("slack_channel"))

    def _generate_demo_jira(self, project_id: Optional[str]) -> dict:
        return {
            "project_key": project_id or "DEMO",
            "tickets": [
                {"id": "DEMO-101", "title": "Implement OAuth2 authentication", "status": "In Progress",
                 "type": "Story", "points": 8, "assignee": "alice@company.com", "is_blocker": False},
                {"id": "DEMO-102", "title": "Database migration script failing", "status": "Blocked",
                 "type": "Bug", "points": 5, "assignee": "bob@company.com", "is_blocker": True},
                {"id": "DEMO-103", "title": "API rate limiting implementation", "status": "To Do",
                 "type": "Story", "points": 5, "assignee": None, "is_blocker": False},
                {"id": "DEMO-104", "title": "Performance testing suite", "status": "In Progress",
                 "type": "Task", "points": 3, "assignee": "carol@company.com", "is_blocker": False},
                {"id": "DEMO-105", "title": "Security audit findings remediation", "status": "To Do",
                 "type": "Epic", "points": 13, "assignee": "alice@company.com", "is_blocker": False},
            ],
            "sprint": {
                "name": "Sprint 14", "number": 14, "status": "active",
                "planned_points": 34, "completed_points": 11,
                "start_date": "2026-06-02", "end_date": "2026-06-13",
            },
            "blockers": ["DEMO-102"],
            "velocity_history": [28, 31, 24, 29, 33, 27, 30, 34],
        }

    def _generate_demo_github(self, project_id: Optional[str]) -> dict:
        return {
            "repo": f"company/{project_id or 'demo-service'}",
            "pull_requests": [
                {"number": 234, "title": "feat: Add JWT refresh token rotation", "status": "open",
                 "author": "alice", "reviewers": ["bob", "carol"], "created_at": "2026-06-10"},
                {"number": 233, "title": "fix: Memory leak in connection pool", "status": "merged",
                 "author": "bob", "reviewers": ["alice"], "created_at": "2026-06-09"},
                {"number": 232, "title": "chore: Upgrade dependencies to latest", "status": "open",
                 "author": "carol", "reviewers": [], "created_at": "2026-06-08"},
            ],
            "commits_last_30d": 47,
            "deployments": [
                {"env": "staging", "status": "success", "date": "2026-06-11"},
                {"env": "production", "status": "success", "date": "2026-06-08"},
            ],
            "code_coverage": 78.4,
            "open_issues": 12,
        }

    def _generate_demo_confluence(self, project_id: Optional[str]) -> dict:
        return {
            "space": project_id or "DEMO",
            "pages": [
                {"id": "conf-001", "title": "Architecture Decision Records", "updated": "2026-06-10",
                 "author": "alice@company.com"},
                {"id": "conf-002", "title": "Sprint 14 Planning Notes", "updated": "2026-06-02",
                 "author": "pm@company.com"},
                {"id": "conf-003", "title": "Technical Debt Register", "updated": "2026-06-05",
                 "author": "bob@company.com"},
            ],
            "recent_decisions": [
                "Adopted PostgreSQL over MongoDB for ACID compliance",
                "Deferred mobile app development to Q3",
                "Mandated API versioning for all external endpoints",
            ],
        }

    def _generate_demo_slack(self, project_id: Optional[str]) -> dict:
        return {
            "channel": f"#{project_id or 'project-demo'}",
            "messages_last_7d": 156,
            "key_updates": [
                "Database migration blocked by DBA approval process",
                "New security requirements from compliance team added",
                "Team agreed to extend sprint by 2 days",
                "Staging deployment successful after 3 retry attempts",
            ],
            "blockers_mentioned": ["DBA approval", "security requirements"],
            "sentiment": "neutral",
        }
