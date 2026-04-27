from typing import Optional
import httpx

from app.integrations.base.connector import BaseConnector
from app.core.config import settings


class ConfluenceConnector(BaseConnector):
    name = "confluence"
    integration_type = "confluence"

    def __init__(self):
        super().__init__()
        self.base_url = settings.CONFLUENCE_URL
        self.auth = (settings.CONFLUENCE_EMAIL, settings.CONFLUENCE_API_TOKEN) if settings.CONFLUENCE_EMAIL else None

    async def test_connection(self) -> bool:
        if not self.base_url or not self.auth:
            return False
        async with httpx.AsyncClient(auth=self.auth, timeout=10) as client:
            resp = await client.get(f"{self.base_url}/rest/api/user/current")
            return resp.status_code == 200

    async def fetch_data(self, **kwargs) -> dict:
        space = kwargs.get("space")
        return await self.fetch_space_data(space)

    async def fetch_space_data(self, space: Optional[str]) -> dict:
        if not self.base_url or not self.auth or not space:
            return {}

        async with httpx.AsyncClient(auth=self.auth, timeout=30) as client:
            pages_resp = await client.get(
                f"{self.base_url}/rest/api/content",
                params={
                    "spaceKey": space,
                    "type": "page",
                    "limit": 50,
                    "expand": "history,metadata.labels",
                    "orderby": "history.lastUpdated.when desc",
                },
            )

        pages = []
        if pages_resp.status_code == 200:
            for page in pages_resp.json().get("results", []):
                pages.append({
                    "id": page["id"],
                    "title": page["title"],
                    "updated": page.get("history", {}).get("lastUpdated", {}).get("when"),
                    "author": page.get("history", {}).get("createdBy", {}).get("displayName"),
                    "url": f"{self.base_url}/wiki{page.get('_links', {}).get('webui', '')}",
                    "labels": [l["name"] for l in page.get("metadata", {}).get("labels", {}).get("results", [])],
                })

        return {
            "space": space,
            "pages": pages,
            "recent_decisions": [],
        }

    async def get_page_content(self, page_id: str) -> Optional[str]:
        if not self.base_url or not self.auth:
            return None
        async with httpx.AsyncClient(auth=self.auth, timeout=15) as client:
            resp = await client.get(
                f"{self.base_url}/rest/api/content/{page_id}",
                params={"expand": "body.storage"},
            )
            if resp.status_code == 200:
                body = resp.json().get("body", {}).get("storage", {}).get("value", "")
                import re
                return re.sub(r'<[^>]+>', ' ', body).strip()
        return None
