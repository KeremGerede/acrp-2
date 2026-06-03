from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class PromotionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    integration_id: int
    merge_review_run_id: Optional[int] = None
    functional_test_run_id: Optional[int] = None
    from_stage: Optional[str] = None
    to_stage: Optional[str] = None
    status: str
    message: Optional[str] = None
    created_at: datetime
