from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_validator
import json


class SCMEventLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    integration_id: int
    repository_id: Optional[int] = None
    provider: str
    event_type: str
    actor_username: Optional[str] = None
    actor_email: Optional[str] = None
    source_branch: Optional[str] = None
    target_branch: Optional[str] = None
    branch: Optional[str] = None
    before_sha: Optional[str] = None
    after_sha: Optional[str] = None
    commit_sha: Optional[str] = None
    commit_messages: Optional[List[str]] = []
    detected_sprint: Optional[str] = None
    detected_task_key: Optional[str] = None
    is_merge_event: bool
    created_at: datetime

    @field_validator("commit_messages", mode="before")
    @classmethod
    def parse_messages(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [v] if v else []
        return v or []
