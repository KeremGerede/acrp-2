from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from app.db.database import Base


class SCMEventLog(Base):
    __tablename__ = "scm_event_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    integration_id = Column(Integer, ForeignKey("project_integrations.id"), nullable=False)
    repository_id = Column(Integer, ForeignKey("repositories.id"))
    provider = Column(String(50), nullable=False)
    event_type = Column(String(100), default="unknown")
    actor_username = Column(String(255))
    actor_email = Column(String(255))
    source_branch = Column(String(500))
    target_branch = Column(String(500))
    branch = Column(String(500))
    before_sha = Column(String(100))
    after_sha = Column(String(100))
    commit_sha = Column(String(100))
    commit_messages = Column(Text)   # JSON array
    detected_sprint = Column(String(255))
    detected_task_key = Column(String(100))
    is_merge_event = Column(Boolean, default=False)
    raw_payload_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
