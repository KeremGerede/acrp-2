from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserActivityStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    integration_id: int
    username: str
    email: Optional[str] = None
    successful_review_count: int
    failed_review_count: int
    successful_test_count: int
    failed_test_count: int
    successful_promotion_count: int
    failed_promotion_count: int
    created_at: datetime
    updated_at: datetime
