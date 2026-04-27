from typing import Optional, List
import httpx
import structlog

from app.integrations.base.connector import BaseConnector
from app.core.config import settings

logger = structlog.get_logger()

GITHUB_API = "https://api.github.com"


class GitHubConnector(BaseConnector):
    name = "github"
    integration_type = "github"

    def __init__(self):
        super().__init__()
        self.token = settings.GITHUB_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
        } if self.token else {}

    async def test_connection(self) -> bool:
        if not self.token:
            return False
        async with httpx.AsyncClient(headers=self.headers, timeout=10) as client:
            resp = await client.get(f"{GITHUB_API}/user")
            return resp.status_code == 200

    async def fetch_data(self, **kwargs) -> dict:
        repo = kwargs.get("repo")
        return await self.fetch_repo_data(repo)

    async def fetch_repo_data(self, repo: Optional[str]) -> dict:
        if not self.token or not repo:
            return {}

        async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
            # PRs
            prs_resp = await client.get(
                f"{GITHUB_API}/repos/{repo}/pulls",
                params={"state": "all", "per_page": 50, "sort": "updated"},
            )
            # Commits
            commits_resp = await client.get(
                f"{GITHUB_API}/repos/{repo}/commits",
                params={"per_page": 100},
            )
            # Issues
            issues_resp = await client.get(
                f"{GITHUB_API}/repos/{repo}/issues",
                params={"state": "open", "per_page": 50},
            )
            # Deployments
            deploy_resp = await client.get(
                f"{GITHUB_API}/repos/{repo}/deployments",
                params={"per_page": 10},
            )

        prs = []
        if prs_resp.status_code == 200:
            for pr in prs_resp.json():
                prs.append({
                    "number": pr["number"],
                    "title": pr["title"],
                    "status": "merged" if pr.get("merged_at") else pr["state"],
                    "author": pr["user"]["login"],
                    "reviewers": [r["login"] for r in pr.get("requested_reviewers", [])],
                    "created_at": pr["created_at"],
                    "merged_at": pr.get("merged_at"),
                    "draft": pr.get("draft", False),
                })

        deployments = []
        if deploy_resp.status_code == 200:
            for d in deploy_resp.json()[:5]:
                deployments.append({
                    "env": d.get("environment", "unknown"),
                    "status": d.get("task", "deploy"),
                    "date": d.get("created_at"),
                })

        return {
            "repo": repo,
            "pull_requests": prs,
            "commits_last_30d": len(commits_resp.json()) if commits_resp.status_code == 200 else 0,
            "open_issues": len(issues_resp.json()) if issues_resp.status_code == 200 else 0,
            "deployments": deployments,
            "code_coverage": None,
        }
