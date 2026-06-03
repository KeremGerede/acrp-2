from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from app.db.database import Base


class AgentStep(Base):
    __tablename__ = "agent_steps"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    integration_id = Column(Integer, ForeignKey("project_integrations.id"))
    event_log_id = Column(Integer, ForeignKey("scm_event_logs.id"))
    merge_review_run_id = Column(Integer, ForeignKey("merge_review_runs.id"))
    functional_test_run_id = Column(Integer, ForeignKey("functional_test_runs.id"))
    agent_name = Column(String(100))
    tool_name = Column(String(100))
    step_name = Column(String(255))
    status = Column(String(50), default="pending")
    input_summary = Column(Text)
    output_summary = Column(Text)
    error_message = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
