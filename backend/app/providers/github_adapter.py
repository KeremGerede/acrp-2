import re
from typing import Optional, List, Dict, Any
import requests
from app.providers.base import ProviderAdapter
from app.providers.normalized_events import NormalizedSCMEvent, EventType
from app.core.security import verify_hmac_sha256
from app.core.config import settings


class GitHubAdapter(ProviderAdapter):

    BASE_URL = "https://api.github.com"

    def verify_webhook_signature(self, payload: bytes, secret: str, headers: Dict[str, str]) -> bool:
        signature = headers.get("x-hub-signature-256") or headers.get("X-Hub-Signature-256", "")
        return verify_hmac_sha256(payload, secret, signature)

    def parse_webhook_event(
        self, payload: Dict[str, Any], tenant_id: int, integration_id: int
    ) -> Optional[NormalizedSCMEvent]:
        repo = payload.get("repository", {})
        repo_full_name = repo.get("full_name", "")

        # Handle pull_request closed+merged event
        if "pull_request" in payload:
            pr = payload["pull_request"]
            action = payload.get("action", "")
            if action != "closed" or not pr.get("merged"):
                return None

            source_branch = pr.get("head", {}).get("ref")
            target_branch = pr.get("base", {}).get("ref")
            actor = pr.get("merged_by") or pr.get("user") or {}
            commit_sha = pr.get("merge_commit_sha")

            return NormalizedSCMEvent(
                provider="github",
                tenant_id=tenant_id,
                integration_id=integration_id,
                repository_full_name=repo_full_name,
                event_type=EventType.unknown,
                actor_username=actor.get("login", ""),
                actor_email=None,
                source_branch=source_branch,
                target_branch=target_branch,
                branch=target_branch,
                before_sha=None,
                after_sha=commit_sha,
                commit_sha=commit_sha,
                commit_messages=[pr.get("title", "")],
                is_merge_event=True,
                raw_payload=payload,
            )

        # Handle push event
        if "ref" in payload:
            ref = payload.get("ref", "")
            branch = ref.replace("refs/heads/", "")
            before_sha = payload.get("before")
            after_sha = payload.get("after")
            pusher = payload.get("pusher", {})
            commits = payload.get("commits", [])
            head_commit = payload.get("head_commit") or {}

            commit_messages = [c.get("message", "") for c in commits]
            commit_sha = after_sha

            # Try to detect merge from commit message
            is_merge = False
            source_branch = None
            for msg in commit_messages:
                merge_match = re.match(r"Merge (?:branch |pull request .+ from )'?([^']+)'?", msg)
                if merge_match:
                    is_merge = True
                    source_branch = merge_match.group(1).strip()
                    break

            actor_email = pusher.get("email") or (head_commit.get("author") or {}).get("email")

            return NormalizedSCMEvent(
                provider="github",
                tenant_id=tenant_id,
                integration_id=integration_id,
                repository_full_name=repo_full_name,
                event_type=EventType.unknown,
                actor_username=pusher.get("name", ""),
                actor_email=actor_email,
                source_branch=source_branch,
                target_branch=branch,
                branch=branch,
                before_sha=before_sha,
                after_sha=after_sha,
                commit_sha=commit_sha,
                commit_messages=commit_messages,
                is_merge_event=is_merge,
                raw_payload=payload,
            )

        return None

    def fetch_changed_files(
        self, repo_full_name: str, before_sha: str, after_sha: str, token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        use_token = token or settings.GITHUB_TOKEN
        headers = {"Accept": "application/vnd.github+json"}
        if use_token:
            headers["Authorization"] = f"Bearer {use_token}"

        url = f"{self.BASE_URL}/repos/{repo_full_name}/compare/{before_sha}...{after_sha}"
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("files", [])
        except Exception as e:
            return []

    def sync_repositories(self, token: Optional[str] = None) -> List[Dict[str, Any]]:
        use_token = token or settings.GITHUB_TOKEN
        if not use_token:
            return []
        headers = {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {use_token}"}
        try:
            response = requests.get(f"{self.BASE_URL}/user/repos?per_page=100", headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception:
            return []
