from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from app.db.database import Base


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    integration_id = Column(Integer, ForeignKey("project_integrations.id"), nullable=False)
    related_entity_type = Column(String(100))  # merge_review, functional_test
    related_entity_id = Column(Integer)
    notification_type = Column(String(100))
    recipients = Column(Text)   # JSON array
    subject = Column(String(500))
    status = Column(String(50), default="pending")  # pending, sent, failed
    error_message = Column(Text)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
