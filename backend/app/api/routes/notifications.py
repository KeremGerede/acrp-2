from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.notification import NotificationLog
from app.schemas.notification import NotificationLogResponse

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=List[NotificationLogResponse])
def list_notifications(
    tenant_id: Optional[int] = None,
    integration_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(NotificationLog)
    if tenant_id:
        q = q.filter_by(tenant_id=tenant_id)
    if integration_id:
        q = q.filter_by(integration_id=integration_id)
    return q.order_by(NotificationLog.id.desc()).limit(limit).all()


@router.get("/merge-reviews/{review_id}", response_model=List[NotificationLogResponse])
def notifications_for_review(review_id: int, db: Session = Depends(get_db)):
    return db.query(NotificationLog).filter_by(
        related_entity_type="merge_review", related_entity_id=review_id
    ).all()


@router.get("/functional-tests/{test_run_id}", response_model=List[NotificationLogResponse])
def notifications_for_test(test_run_id: int, db: Session = Depends(get_db)):
    return db.query(NotificationLog).filter_by(
        related_entity_type="functional_test", related_entity_id=test_run_id
    ).all()
