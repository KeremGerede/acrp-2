from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_validator
import json


class NotificationLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    integration_id: int
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    notification_type: Optional[str] = None
    recipients: Optional[List[str]] = []
    subject: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime

    @field_validator("recipients", mode="before")
    @classmethod
    def parse_recipients(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [v] if v else []
        return v or []
