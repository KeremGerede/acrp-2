from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    merge_review_run_id: int
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    rule_title: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    issue: Optional[str] = None
    explanation: Optional[str] = None
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None
    created_at: datetime
