from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from app.providers.normalized_events import NormalizedSCMEvent


class ProviderAdapter(ABC):

    @abstractmethod
    def verify_webhook_signature(self, payload: bytes, secret: str, headers: Dict[str, str]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def parse_webhook_event(
        self, payload: Dict[str, Any], tenant_id: int, integration_id: int
    ) -> Optional[NormalizedSCMEvent]:
        raise NotImplementedError

    @abstractmethod
    def fetch_changed_files(
        self, repo_full_name: str, before_sha: str, after_sha: str, token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def sync_repositories(self, token: Optional[str] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError("sync_repositories not implemented for this provider")

    def sync_sprints_and_tasks(self, token: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError("sync_sprints_and_tasks not implemented for this provider")

    def create_test_pr(self, repo_full_name: str, source: str, target: str, token: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError("create_test_pr not implemented for this provider")
