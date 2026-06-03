from dataclasses import dataclass, field
from typing import Optional, List, Any
from enum import Enum


class EventType(str, Enum):
    push = "push"
    task_to_sprint_merge = "task_to_sprint_merge"
    sprint_to_development_event = "sprint_to_development_event"
    development_test_event = "development_test_event"
    unknown = "unknown"


@dataclass
class NormalizedSCMEvent:
    provider: str
    tenant_id: int
    integration_id: int
    repository_full_name: str
    event_type: EventType = EventType.unknown
    actor_username: str = ""
    actor_email: Optional[str] = None
    source_branch: Optional[str] = None
    target_branch: Optional[str] = None
    branch: Optional[str] = None
    before_sha: Optional[str] = None
    after_sha: Optional[str] = None
    commit_sha: Optional[str] = None
    commit_messages: List[str] = field(default_factory=list)
    is_merge_event: bool = False
    raw_payload: Any = None
