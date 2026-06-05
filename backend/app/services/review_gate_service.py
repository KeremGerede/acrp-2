import logging
from sqlalchemy.orm import Session
from app.models.merge_review import MergeReviewRun

logger = logging.getLogger(__name__)


class ReviewGateService:
    def evaluate(self, review_result: str) -> dict:
        if review_result == "success":
            return {
                "gate_status": "passed",
                "allow_functional_tests": True,
                "allow_promotion": True,
                "revert_required": False,
                "reason": "Review approved.",
            }
        return {
            "gate_status": "blocked",
            "allow_functional_tests": False,
            "allow_promotion": False,
            "revert_required": True,
            "reason": "Review failed due to high/critical findings.",
        }

    def apply_to_run(self, db: Session, review_run: MergeReviewRun, gate_result: dict) -> None:
        review_run.gate_status = gate_result["gate_status"]
        review_run.gate_reason = gate_result["reason"]
        review_run.revert_status = "required" if gate_result["revert_required"] else "not_required"
        db.commit()
        logger.info(
            f"[ReviewGate] gate_status={gate_result['gate_status']} "
            f"review_run_id={review_run.id} task={review_run.task_key}"
        )


review_gate_service = ReviewGateService()
