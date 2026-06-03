from typing import Optional, List, Dict, Any
from app.providers.base import ProviderAdapter
from app.providers.normalized_events import NormalizedSCMEvent


class GitLabAdapter(ProviderAdapter):

    def verify_webhook_signature(self, payload: bytes, secret: str, headers: Dict[str, str]) -> bool:
        raise NotImplementedError("GitLab adapter not yet implemented")

    def parse_webhook_event(
        self, payload: Dict[str, Any], tenant_id: int, integration_id: int
    ) -> Optional[NormalizedSCMEvent]:
        raise NotImplementedError("GitLab adapter not yet implemented")

    def fetch_changed_files(
        self, repo_full_name: str, before_sha: str, after_sha: str, token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError("GitLab adapter not yet implemented")
