import json
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.notification import NotificationLog


def create_notification_log(
    db: Session,
    tenant_id: int,
    integration_id: int,
    notification_type: str,
    subject: str,
    recipients: List[str],
    related_entity_type: Optional[str] = None,
    related_entity_id: Optional[int] = None,
) -> NotificationLog:
    log = NotificationLog(
        tenant_id=tenant_id,
        integration_id=integration_id,
        notification_type=notification_type,
        subject=subject,
        recipients=json.dumps(recipients),
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        status="pending",
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def mark_sent(db: Session, log_id: int):
    log = db.query(NotificationLog).filter_by(id=log_id).first()
    if log:
        log.status = "sent"
        log.sent_at = datetime.utcnow()
        db.commit()


def mark_failed(db: Session, log_id: int, error: str):
    log = db.query(NotificationLog).filter_by(id=log_id).first()
    if log:
        log.status = "failed"
        log.error_message = error
        db.commit()
