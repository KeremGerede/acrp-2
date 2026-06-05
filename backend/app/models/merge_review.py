from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from app.db.database import Base


class MergeReviewRun(Base):
    __tablename__ = "merge_review_runs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    integration_id = Column(Integer, ForeignKey("project_integrations.id"), nullable=False)
    event_log_id = Column(Integer, ForeignKey("scm_event_logs.id"), nullable=False)
    repository_id = Column(Integer, ForeignKey("repositories.id"))
    repository_full_name = Column(String(500))
    sprint_name = Column(String(255))
    task_key = Column(String(100))
    source_branch = Column(String(500))
    target_branch = Column(String(500))
    commit_sha = Column(String(100))
    pull_request_number = Column(Integer)
    pull_request_url = Column(String(1000))
    actor_username = Column(String(255))
    status = Column(String(50), default="pending")   # pending, running, completed, failed, skipped
    result = Column(String(50))                       # success, failed
    decision_reason = Column(Text)
    risk_level = Column(String(50))
    total_files_analyzed = Column(Integer, default=0)
    total_findings = Column(Integer, default=0)
    blocking_findings_count = Column(Integer, default=0)
    report_summary = Column(Text)
    raw_agent_response_json = Column(Text)
    gate_status = Column(String(50), default="pending")    # pending, passed, blocked
    gate_reason = Column(Text)
    revert_status = Column(String(50), default="not_required")  # not_required, required, revert_pr_created, reverted, revert_failed
    revert_pr_url = Column(String(1000))
    revert_branch_name = Column(String(500))
    revert_error_message = Column(Text)
    revert_merge_commit_sha = Column(String(100))
    reverted_at = Column(DateTime)
    started_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
