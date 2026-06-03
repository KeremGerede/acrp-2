from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.review_rule import ReviewRule
from app.schemas.review_rule import ReviewRuleCreate, ReviewRuleUpdate, ReviewRuleResponse

router = APIRouter(prefix="/api/review-rules", tags=["review-rules"])


@router.get("", response_model=List[ReviewRuleResponse])
def list_rules(tenant_id: Optional[int] = None, integration_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(ReviewRule)
    if tenant_id:
        q = q.filter_by(tenant_id=tenant_id)
    if integration_id:
        q = q.filter_by(integration_id=integration_id)
    return q.order_by(ReviewRule.id.desc()).all()


@router.post("", response_model=ReviewRuleResponse, status_code=201)
def create_rule(data: ReviewRuleCreate, db: Session = Depends(get_db)):
    rule = ReviewRule(**data.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/{rule_id}", response_model=ReviewRuleResponse)
def update_rule(rule_id: int, data: ReviewRuleUpdate, db: Session = Depends(get_db)):
    rule = db.query(ReviewRule).filter_by(id=rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(rule, k, v)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=204)
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(ReviewRule).filter_by(id=rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()


@router.patch("/{rule_id}/toggle", response_model=ReviewRuleResponse)
def toggle_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(ReviewRule).filter_by(id=rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.is_enabled = not rule.is_enabled
    db.commit()
    db.refresh(rule)
    return rule
