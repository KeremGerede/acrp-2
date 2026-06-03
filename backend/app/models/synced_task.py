from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.database import Base


class SyncedTask(Base):
    __tablename__ = "synced_tasks"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    integration_id = Column(Integer, ForeignKey("project_integrations.id"), nullable=False)
    sprint_id = Column(Integer, ForeignKey("synced_sprints.id"))
    external_id = Column(String(255))
    task_key = Column(String(100), nullable=False, index=True)
    title = Column(String(500))
    assignee_username = Column(String(255))
    assignee_email = Column(String(255))
    status = Column(String(50), default="open")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
