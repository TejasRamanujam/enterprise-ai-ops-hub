from typing import Optional, List
import httpx

from app.integrations.base.connector import BaseConnector
from app.core.config import settings


class SlackConnector(BaseConnector):
    name = "slack"
    integration_type = "slack"

    SLACK_API = "https://slack.com/api"

    def __init__(self):
        super().__init__()
        self.token = settings.SLACK_BOT_TOKEN

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    async def test_connection(self) -> bool:
        if not self.token:
            return False
        async with httpx.AsyncClient(headers=self.headers, timeout=10) as client:
            resp = await client.post(f"{self.SLACK_API}/auth.test")
            return resp.json().get("ok", False)

    async def fetch_data(self, **kwargs) -> dict:
        channel = kwargs.get("channel")
        return await self.fetch_channel_data(channel)

    async def fetch_channel_data(self, channel: Optional[str]) -> dict:
        if not self.token or not channel:
            return {}

        async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
            channels_resp = await client.get(
                f"{self.SLACK_API}/conversations.list",
                params={"exclude_archived": True, "limit": 200},
            )

            channel_id = None
            if channels_resp.json().get("ok"):
                for c in channels_resp.json().get("channels", []):
                    if c["name"] == channel.lstrip("#"):
                        channel_id = c["id"]
                        break

            if not channel_id:
                return {"channel": channel, "messages_last_7d": 0, "key_updates": []}

            history_resp = await client.get(
                f"{self.SLACK_API}/conversations.history",
                params={"channel": channel_id, "limit": 200},
            )

        messages = []
        if history_resp.json().get("ok"):
            for msg in history_resp.json().get("messages", []):
                if msg.get("type") == "message" and not msg.get("bot_id"):
                    messages.append(msg.get("text", ""))

        return {
            "channel": channel,
            "messages_last_7d": len(messages),
            "key_updates": messages[:10],
            "blockers_mentioned": [m for m in messages if "block" in m.lower() or "blocked" in m.lower()],
            "sentiment": "neutral",
        }

    async def post_message(self, channel: str, text: str, blocks: Optional[list] = None) -> bool:
        if not self.token:
            return False
        payload = {"channel": channel, "text": text}
        if blocks:
            payload["blocks"] = blocks
        async with httpx.AsyncClient(headers=self.headers, timeout=10) as client:
            resp = await client.post(f"{self.SLACK_API}/chat.postMessage", json=payload)
            return resp.json().get("ok", False)
