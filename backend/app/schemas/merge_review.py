from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class MergeReviewRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    integration_id: int
    event_log_id: int
    repository_id: Optional[int] = None
    sprint_name: Optional[str] = None
    task_key: Optional[str] = None
    source_branch: Optional[str] = None
    target_branch: Optional[str] = None
    commit_sha: Optional[str] = None
    actor_username: Optional[str] = None
    status: str
    result: Optional[str] = None
    decision_reason: Optional[str] = None
    risk_level: Optional[str] = None
    total_files_analyzed: int
    total_findings: int
    blocking_findings_count: int
    report_summary: Optional[str] = None
    gate_status: Optional[str] = None
    gate_reason: Optional[str] = None
    revert_status: Optional[str] = None
    revert_pr_url: Optional[str] = None
    revert_branch_name: Optional[str] = None
    revert_error_message: Optional[str] = None
    reverted_at: Optional[datetime] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
