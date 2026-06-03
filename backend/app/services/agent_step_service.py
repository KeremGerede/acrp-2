from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models.agent_step import AgentStep


def log_step(
    db: Session,
    tenant_id: int,
    agent_name: str,
    tool_name: str,
    step_name: str,
    status: str,
    integration_id: Optional[int] = None,
    event_log_id: Optional[int] = None,
    merge_review_run_id: Optional[int] = None,
    functional_test_run_id: Optional[int] = None,
    input_summary: Optional[str] = None,
    output_summary: Optional[str] = None,
    error_message: Optional[str] = None,
) -> AgentStep:
    step = AgentStep(
        tenant_id=tenant_id,
        integration_id=integration_id,
        event_log_id=event_log_id,
        merge_review_run_id=merge_review_run_id,
        functional_test_run_id=functional_test_run_id,
        agent_name=agent_name,
        tool_name=tool_name,
        step_name=step_name,
        status=status,
        input_summary=input_summary,
        output_summary=output_summary,
        error_message=error_message,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow() if status in ("completed", "failed") else None,
    )
    db.add(step)
    db.commit()
    db.refresh(step)
    return step
