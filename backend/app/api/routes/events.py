from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.scm_event import SCMEventLog
from app.schemas.scm_event import SCMEventLogResponse

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=List[SCMEventLogResponse])
def list_events(
    tenant_id: Optional[int] = None,
    integration_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(SCMEventLog)
    if tenant_id:
        q = q.filter_by(tenant_id=tenant_id)
    if integration_id:
        q = q.filter_by(integration_id=integration_id)
    return q.order_by(SCMEventLog.id.desc()).limit(limit).all()


@router.get("/{event_id}", response_model=SCMEventLogResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(SCMEventLog).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
