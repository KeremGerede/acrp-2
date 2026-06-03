from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.database import Base


class UserActivityStats(Base):
    __tablename__ = "user_activity_stats"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    integration_id = Column(Integer, ForeignKey("project_integrations.id"), nullable=False)
    username = Column(String(255), nullable=False)
    email = Column(String(255))
    successful_review_count = Column(Integer, default=0)
    failed_review_count = Column(Integer, default=0)
    successful_test_count = Column(Integer, default=0)
    failed_test_count = Column(Integer, default=0)
    successful_promotion_count = Column(Integer, default=0)
    failed_promotion_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
