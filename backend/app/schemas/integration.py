from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_validator
import json


class IntegrationCreate(BaseModel):
    tenant_id: int
    provider: str
    name: str
    repository_owner: Optional[str] = None
    repository_name: Optional[str] = None
    repository_full_name: Optional[str] = None
    repository_url: Optional[str] = None
    default_branch: str = "main"
    sprint_branch_pattern: str = "sprint/*"
    task_branch_pattern: str = "task/*"
    development_branch: str = "development"
    test_branch: str = "test"
    webhook_secret: Optional[str] = None
    notification_recipients: Optional[List[str]] = []
    manager_email: Optional[str] = None
    is_active: bool = True


class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    repository_owner: Optional[str] = None
    repository_name: Optional[str] = None
    repository_full_name: Optional[str] = None
    repository_url: Optional[str] = None
    default_branch: Optional[str] = None
    sprint_branch_pattern: Optional[str] = None
    task_branch_pattern: Optional[str] = None
    development_branch: Optional[str] = None
    test_branch: Optional[str] = None
    webhook_secret: Optional[str] = None
    notification_recipients: Optional[List[str]] = None
    manager_email: Optional[str] = None
    is_active: Optional[bool] = None


class IntegrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    provider: str
    name: str
    repository_owner: Optional[str] = None
    repository_name: Optional[str] = None
    repository_full_name: Optional[str] = None
    repository_url: Optional[str] = None
    default_branch: Optional[str] = None
    sprint_branch_pattern: Optional[str] = None
    task_branch_pattern: Optional[str] = None
    development_branch: Optional[str] = None
    test_branch: Optional[str] = None
    webhook_secret: Optional[str] = None
    notification_recipients: Optional[List[str]] = []
    manager_email: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @field_validator("notification_recipients", mode="before")
    @classmethod
    def parse_recipients(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [v] if v else []
        return v or []
