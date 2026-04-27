from typing import Optional
import httpx
import structlog

from app.integrations.base.connector import BaseConnector
from app.core.config import settings

logger = structlog.get_logger()


class JiraConnector(BaseConnector):
    name = "jira"
    integration_type = "jira"

    def __init__(self):
        super().__init__()
        self.base_url = settings.JIRA_URL
        self.auth = (settings.JIRA_EMAIL, settings.JIRA_API_TOKEN) if settings.JIRA_EMAIL else None

    async def test_connection(self) -> bool:
        if not self.base_url or not self.auth:
            return False
        async with httpx.AsyncClient(auth=self.auth, timeout=10) as client:
            resp = await client.get(f"{self.base_url}/rest/api/3/myself")
            return resp.status_code == 200

    async def fetch_data(self, **kwargs) -> dict:
        project_key = kwargs.get("project_key")
        return await self.fetch_project_data(project_key)

    async def fetch_project_data(self, project_key: Optional[str]) -> dict:
        if not self.base_url or not self.auth:
            return {}

        async with httpx.AsyncClient(auth=self.auth, timeout=30) as client:
            # Fetch project info
            proj_resp = await client.get(
                f"{self.base_url}/rest/api/3/project/{project_key}"
            )

            # Fetch active sprint
            sprint_resp = await client.get(
                f"{self.base_url}/rest/agile/1.0/board",
                params={"projectKeyOrId": project_key, "type": "scrum"},
            )

            # Fetch issues in current sprint
            jql = f"project = {project_key} AND sprint in openSprints()"
            issues_resp = await client.get(
                f"{self.base_url}/rest/api/3/search",
                params={"jql": jql, "maxResults": 100, "fields": "summary,status,priority,assignee,story_points,issuetype,labels,created,updated,resolutiondate"},
            )

        tickets = []
        if issues_resp.status_code == 200:
            issues_data = issues_resp.json()
            for issue in issues_data.get("issues", []):
                fields = issue.get("fields", {})
                tickets.append({
                    "id": issue["key"],
                    "title": fields.get("summary", ""),
                    "status": fields.get("status", {}).get("name", ""),
                    "type": fields.get("issuetype", {}).get("name", ""),
                    "priority": fields.get("priority", {}).get("name", "Medium"),
                    "points": fields.get("story_points") or fields.get("customfield_10016"),
                    "assignee": (fields.get("assignee") or {}).get("emailAddress"),
                    "is_blocker": fields.get("priority", {}).get("name", "").lower() == "blocker",
                    "labels": fields.get("labels", []),
                    "created_date": fields.get("created"),
                    "updated_date": fields.get("updated"),
                })

        blockers = [t["id"] for t in tickets if t["is_blocker"] or t["status"] == "Blocked"]

        return {
            "project_key": project_key,
            "tickets": tickets,
            "blockers": blockers,
            "sprint": {},
            "velocity_history": [],
        }

    async def create_ticket(self, project_key: str, title: str, description: str, ticket_type: str = "Task") -> Optional[str]:
        if not self.base_url or not self.auth:
            return None
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": title,
                "description": {"type": "doc", "version": 1, "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": description}]}
                ]},
                "issuetype": {"name": ticket_type},
            }
        }
        async with httpx.AsyncClient(auth=self.auth, timeout=15) as client:
            resp = await client.post(f"{self.base_url}/rest/api/3/issue", json=payload)
            if resp.status_code == 201:
                return resp.json().get("key")
        return None
