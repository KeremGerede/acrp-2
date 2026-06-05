import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.merge_review import MergeReviewRun
from app.models.finding import Finding
from app.models.agent_step import AgentStep
from app.schemas.merge_review import MergeReviewRunResponse
from app.schemas.finding import FindingResponse
from app.schemas.agent_step import AgentStepResponse
from app.services.pdf_report_service import generate_review_pdf

router = APIRouter(prefix="/api/merge-reviews", tags=["merge-reviews"])


@router.get("", response_model=List[MergeReviewRunResponse])
def list_reviews(
    tenant_id: Optional[int] = None,
    integration_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(MergeReviewRun)
    if tenant_id:
        q = q.filter_by(tenant_id=tenant_id)
    if integration_id:
        q = q.filter_by(integration_id=integration_id)
    return q.order_by(MergeReviewRun.id.desc()).limit(limit).all()


@router.get("/{review_id}", response_model=MergeReviewRunResponse)
def get_review(review_id: int, db: Session = Depends(get_db)):
    review = db.query(MergeReviewRun).filter_by(id=review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@router.get("/{review_id}/findings", response_model=List[FindingResponse])
def get_findings(review_id: int, db: Session = Depends(get_db)):
    return db.query(Finding).filter_by(merge_review_run_id=review_id).all()


@router.get("/{review_id}/steps", response_model=List[AgentStepResponse])
def get_steps(review_id: int, db: Session = Depends(get_db)):
    return db.query(AgentStep).filter_by(merge_review_run_id=review_id).all()


@router.get("/{review_id}/report-data")
def get_report_data(review_id: int, db: Session = Depends(get_db)):
    review = db.query(MergeReviewRun).filter_by(id=review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    data = {"passed_checks": [], "failed_checks": [], "file_assessments": [], "improvements": []}
    if review.raw_agent_response_json:
        try:
            raw = json.loads(review.raw_agent_response_json)
            data["passed_checks"] = raw.get("passed_checks", [])
            data["failed_checks"] = raw.get("failed_checks", [])
            data["file_assessments"] = raw.get("file_assessments", [])
            data["improvements"] = raw.get("improvements", [])
        except Exception:
            pass
    return data


@router.get("/{review_id}/pdf")
def download_pdf(review_id: int, db: Session = Depends(get_db)):
    review = db.query(MergeReviewRun).filter_by(id=review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    findings = db.query(Finding).filter_by(merge_review_run_id=review_id).all()
    passed_checks, failed_checks, file_assessments = [], [], []
    if review.raw_agent_response_json:
        try:
            raw = json.loads(review.raw_agent_response_json)
            passed_checks = raw.get("passed_checks", [])
            failed_checks = raw.get("failed_checks", [])
            file_assessments = raw.get("file_assessments", [])
        except Exception:
            pass
    pdf_bytes = generate_review_pdf(
        review, findings,
        passed_checks=passed_checks,
        failed_checks=failed_checks,
        file_assessments=file_assessments,
    )
    safe_task = (review.task_key or "report").replace("/", "-").replace(" ", "_")
    safe_sprint = (review.sprint_name or "").replace("/", "-").replace(" ", "_")
    filename = f"review_{safe_task}_{safe_sprint}.pdf".strip("_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
