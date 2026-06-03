from datetime import datetime
from sqlalchemy.orm import Session
from app.models.merge_review import MergeReviewRun
from app.models.functional_test import FunctionalTestRun


def update_review_status(db: Session, run_id: int, status: str, result: str = None, **kwargs):
    run = db.query(MergeReviewRun).filter_by(id=run_id).first()
    if not run:
        return
    run.status = status
    if result:
        run.result = result
    if status in ("completed", "failed"):
        run.completed_at = datetime.utcnow()
    for k, v in kwargs.items():
        setattr(run, k, v)
    db.commit()


def update_test_status(db: Session, run_id: int, status: str, result: str = None, **kwargs):
    run = db.query(FunctionalTestRun).filter_by(id=run_id).first()
    if not run:
        return
    run.status = status
    if result:
        run.result = result
    if status in ("completed", "failed"):
        run.completed_at = datetime.utcnow()
    for k, v in kwargs.items():
        setattr(run, k, v)
    db.commit()
