from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from app.db.database import Base


class ProjectIntegration(Base):
    __tablename__ = "project_integrations"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    repository_owner = Column(String(255))
    repository_name = Column(String(255))
    repository_full_name = Column(String(255))
    repository_url = Column(String(500))
    default_branch = Column(String(100), default="main")
    sprint_branch_pattern = Column(String(100), default="sprint/*")
    task_branch_pattern = Column(String(100), default="task/*")
    development_branch = Column(String(100), default="development")
    test_branch = Column(String(100), default="test")
    webhook_secret = Column(String(255))
    notification_recipients = Column(Text)  # JSON array stored as text
    manager_email = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PlatformCredential(Base):
    __tablename__ = "platform_credentials"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    integration_id = Column(Integer, ForeignKey("project_integrations.id"), nullable=False)
    provider = Column(String(50), nullable=False)
    token_encrypted_or_placeholder = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
