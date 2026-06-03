from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user_stats import UserActivityStats
from app.schemas.user_stats import UserActivityStatsResponse

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/users", response_model=List[UserActivityStatsResponse])
def user_stats(
    tenant_id: Optional[int] = None,
    integration_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(UserActivityStats)
    if tenant_id:
        q = q.filter_by(tenant_id=tenant_id)
    if integration_id:
        q = q.filter_by(integration_id=integration_id)
    return q.order_by(UserActivityStats.successful_review_count.desc()).all()
