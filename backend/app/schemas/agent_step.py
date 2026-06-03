from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AgentStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    integration_id: Optional[int] = None
    event_log_id: Optional[int] = None
    merge_review_run_id: Optional[int] = None
    functional_test_run_id: Optional[int] = None
    agent_name: Optional[str] = None
    tool_name: Optional[str] = None
    step_name: Optional[str] = None
    status: str
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
