import logging
from sqlalchemy.orm import Session
from app.models.merge_review import MergeReviewRun

logger = logging.getLogger(__name__)


class RevertService:
    def mark_revert_required(self, db: Session, review_run: MergeReviewRun, reason: str) -> None:
        review_run.revert_status = "required"
        if not review_run.gate_reason:
            review_run.gate_reason = reason
        db.commit()
        logger.warning(
            f"[RevertService] revert_required marked — review_run_id={review_run.id} "
            f"branch={review_run.source_branch} → {review_run.target_branch} reason={reason}"
        )

    def create_revert_pr_if_supported(self, db: Session, review_run: MergeReviewRun, integration) -> None:
        # MVP: automatic revert PR creation is not implemented.
        # Operator must manually revert the merged branch.
        # When GitHub API support is sufficient, implement:
        #   1. Create revert branch from target_branch HEAD
        #   2. Open a PR to undo the merge commit
        #   3. Set review_run.revert_status = "revert_pr_created"
        #   4. Set review_run.revert_pr_url = pr.html_url
        #   5. db.commit()
        logger.info(
            f"[RevertService] Revert PR creation skipped (not implemented in MVP) — "
            f"review_run_id={review_run.id} source_branch={review_run.source_branch}"
        )


revert_service = RevertService()
