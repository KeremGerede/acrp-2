from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from app.db.database import Base


class FunctionalTestConfig(Base):
    __tablename__ = "functional_test_configs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    integration_id = Column(Integer, ForeignKey("project_integrations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    test_command = Column(Text, nullable=False)
    working_directory = Column(String(500))
    target_branch_pattern = Column(String(100))
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FunctionalTestRun(Base):
    __tablename__ = "functional_test_runs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    integration_id = Column(Integer, ForeignKey("project_integrations.id"), nullable=False)
    merge_review_run_id = Column(Integer, ForeignKey("merge_review_runs.id"))
    event_log_id = Column(Integer, ForeignKey("scm_event_logs.id"))
    repository_id = Column(Integer, ForeignKey("repositories.id"))
    sprint_name = Column(String(255))
    task_key = Column(String(100))
    commit_sha = Column(String(100))
    status = Column(String(50), default="pending")
    result = Column(String(50))
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    report_summary = Column(Text)
    raw_output = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
