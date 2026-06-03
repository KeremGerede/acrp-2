from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TenantCreate(BaseModel):
    name: str
    contact_email: str


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    contact_email: Optional[str] = None


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    contact_email: str
    created_at: datetime
    updated_at: datetime
