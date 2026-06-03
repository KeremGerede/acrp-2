from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from app.db.database import Base


class EnvironmentPromotionLog(Base):
    __tablename__ = "environment_promotion_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    integration_id = Column(Integer, ForeignKey("project_integrations.id"), nullable=False)
    merge_review_run_id = Column(Integer, ForeignKey("merge_review_runs.id"))
    functional_test_run_id = Column(Integer, ForeignKey("functional_test_runs.id"))
    from_stage = Column(String(100))
    to_stage = Column(String(100))
    status = Column(String(100), default="ready_for_test_environment")
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
