from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.functional_test import FunctionalTestRun
from app.schemas.functional_test import FunctionalTestRunResponse

router = APIRouter(prefix="/api/functional-tests", tags=["functional-tests"])


@router.get("", response_model=List[FunctionalTestRunResponse])
def list_test_runs(
    tenant_id: Optional[int] = None,
    integration_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(FunctionalTestRun)
    if tenant_id:
        q = q.filter_by(tenant_id=tenant_id)
    if integration_id:
        q = q.filter_by(integration_id=integration_id)
    return q.order_by(FunctionalTestRun.id.desc()).limit(limit).all()


@router.get("/{test_run_id}", response_model=FunctionalTestRunResponse)
def get_test_run(test_run_id: int, db: Session = Depends(get_db)):
    run = db.query(FunctionalTestRun).filter_by(id=test_run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    return run
