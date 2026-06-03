from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class FunctionalTestConfigCreate(BaseModel):
    tenant_id: int
    integration_id: int
    name: str
    test_command: str
    working_directory: Optional[str] = None
    target_branch_pattern: Optional[str] = None
    is_enabled: bool = True


class FunctionalTestConfigUpdate(BaseModel):
    name: Optional[str] = None
    test_command: Optional[str] = None
    working_directory: Optional[str] = None
    target_branch_pattern: Optional[str] = None
    is_enabled: Optional[bool] = None


class FunctionalTestConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    integration_id: int
    name: str
    test_command: str
    working_directory: Optional[str] = None
    target_branch_pattern: Optional[str] = None
    is_enabled: bool
    created_at: datetime
    updated_at: datetime


class FunctionalTestRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    integration_id: int
    merge_review_run_id: Optional[int] = None
    event_log_id: Optional[int] = None
    repository_id: Optional[int] = None
    sprint_name: Optional[str] = None
    task_key: Optional[str] = None
    commit_sha: Optional[str] = None
    status: str
    result: Optional[str] = None
    total_tests: int
    passed_tests: int
    failed_tests: int
    report_summary: Optional[str] = None
    raw_output: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
