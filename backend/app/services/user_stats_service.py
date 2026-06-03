from sqlalchemy.orm import Session
from app.models.user_stats import UserActivityStats


def get_or_create_stats(db: Session, tenant_id: int, integration_id: int, username: str, email: str = None) -> UserActivityStats:
    stats = db.query(UserActivityStats).filter_by(
        tenant_id=tenant_id, integration_id=integration_id, username=username
    ).first()
    if not stats:
        stats = UserActivityStats(
            tenant_id=tenant_id,
            integration_id=integration_id,
            username=username,
            email=email,
        )
        db.add(stats)
        db.commit()
        db.refresh(stats)
    return stats


def increment(db: Session, tenant_id: int, integration_id: int, username: str, email: str, field: str):
    stats = get_or_create_stats(db, tenant_id, integration_id, username, email)
    current = getattr(stats, field, 0) or 0
    setattr(stats, field, current + 1)
    db.commit()
