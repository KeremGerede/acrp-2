from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from app.db.database import Base


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    merge_review_run_id = Column(Integer, ForeignKey("merge_review_runs.id"), nullable=False, index=True)
    file_path = Column(String(500))
    line_number = Column(Integer)
    rule_title = Column(String(255))
    category = Column(String(100))
    severity = Column(String(50))   # info, warning, high, critical
    issue = Column(Text)
    explanation = Column(Text)
    suggestion = Column(Text)
    code_snippet = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
