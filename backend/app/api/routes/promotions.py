from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.promotion import EnvironmentPromotionLog
from app.schemas.promotion import PromotionLogResponse

router = APIRouter(prefix="/api/promotions", tags=["promotions"])


@router.get("", response_model=List[PromotionLogResponse])
def list_promotions(
    tenant_id: Optional[int] = None,
    integration_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(EnvironmentPromotionLog)
    if tenant_id:
        q = q.filter_by(tenant_id=tenant_id)
    if integration_id:
        q = q.filter_by(integration_id=integration_id)
    return q.order_by(EnvironmentPromotionLog.id.desc()).limit(limit).all()


@router.get("/{promotion_id}", response_model=PromotionLogResponse)
def get_promotion(promotion_id: int, db: Session = Depends(get_db)):
    p = db.query(EnvironmentPromotionLog).filter_by(id=promotion_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Promotion log not found")
    return p
