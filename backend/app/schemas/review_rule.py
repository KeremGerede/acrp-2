from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ReviewRuleCreate(BaseModel):
    tenant_id: int
    integration_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    category: str = "other"
    severity: str = "warning"
    is_enabled: bool = True


class ReviewRuleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    is_enabled: Optional[bool] = None


class ReviewRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    integration_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    category: str
    severity: str
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
