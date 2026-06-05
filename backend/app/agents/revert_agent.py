"""
RevertAgent — automatically reverts a failed merge after CodeReviewAgent rejects it.

Modes (AUTO_REVERT_MODE env var):
  create_revert_pr              → create a revert PR, leave merging to a human
  create_and_merge_revert_pr    → create revert PR and auto-merge it (default)
  disabled                      → mark revert_status=required, do nothing

Flow:
  1. Extract PR node_id from the stored webhook payload (pull_request event).
  2. Fallback: look up the PR by merge_commit_sha via REST API.
  3. Create revert PR via GitHub GraphQL revertPullRequest mutation.
  4. If mode == create_and_merge_revert_pr: merge the revert PR via REST API.
  5. Update review_run fields and log AgentStep entries throughout.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.merge_review import MergeReviewRun
from app.models.scm_event import SCMEventLog
from app.services.revert_service import revert_service
from app.services.agent_step_service import log_step
from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_token(db: Session, integration_id: int) -> Optional[str]:
    from app.models.integration import PlatformCredential
    cred = db.query(PlatformCredential).filter_by(integration_id=integration_id).first()
    return (cred.token_encrypted_or_placeholder if cred else None) or None


def _step(
    db: Session,
    tenant_id: int,
    integration_id: int,
    event_log_id: int,
    review_run_id: int,
    step_name: str,
    status: str,
    input_summary: str = None,
    output_summary: str = None,
) -> None:
    log_step(
        db,
        tenant_id=tenant_id,
        agent_name="RevertAgent",
        tool_name="revert_agent",
        step_name=step_name,
        status=status,
        integration_id=integration_id,
        event_log_id=event_log_id,
        merge_review_run_id=review_run_id,
        input_summary=input_summary,
        output_summary=output_summary,
    )


def _fail(
    db: Session,
    review_run: MergeReviewRun,
    status: str,
    error: str,
) -> None:
    review_run.revert_status = status
    review_run.revert_error_message = error
    db.commit()


def run_revert(
    db: Session,
    tenant_id: int,
    integration_id: int,
    review_run: MergeReviewRun,
    event_log_id: int,
    integration,
) -> dict:
    """
    Entry point for RevertAgent.  Updates review_run in-place and returns
    a result dict:
      {"status": str, "revert_pr_url": Optional[str], "error": Optional[str]}
    """
    mode = settings.AUTO_REVERT_MODE
    repo = review_run.repository_full_name or ""
    task_key = review_run.task_key or "N/A"
    merge_sha = review_run.commit_sha

    _step(
        db, tenant_id, integration_id, event_log_id, review_run.id,
        "revert_agent_started", "running",
        input_summary=f"mode={mode} repo={repo} commit={merge_sha}",
    )

    # ── Disabled mode ──────────────────────────────────────────────────────────
    if mode == "disabled" or not repo:
        reason = "AUTO_REVERT_MODE is disabled or repository not set."
        revert_service.mark_revert_required(db, review_run, reason)
        _step(
            db, tenant_id, integration_id, event_log_id, review_run.id,
            "revert_failed", "completed",
            output_summary=reason,
        )
        return {"status": "required", "revert_pr_url": None, "error": reason}

    token = _get_token(db, integration_id)

    # ── Resolve PR node_id ─────────────────────────────────────────────────────
    event_log = db.query(SCMEventLog).filter_by(id=event_log_id).first()
    pr_node_id, pr_number = None, None

    if event_log:
        pr_node_id, pr_number = revert_service.extract_pr_info_from_event(event_log)
        if pr_node_id:
            logger.info(f"[RevertAgent] PR node_id found in webhook payload: #{pr_number}")

    if not pr_node_id and merge_sha and repo:
        logger.info(f"[RevertAgent] node_id missing — looking up PR by commit {merge_sha}")
        pr_node_id, pr_number = revert_service.find_pr_by_commit(repo, merge_sha, token)
        if pr_node_id:
            logger.info(f"[RevertAgent] PR found via commit lookup: #{pr_number}")

    if not pr_node_id:
        msg = (
            "Could not resolve PR node_id from webhook payload or commit lookup. "
            "Manual revert is required."
        )
        logger.warning(f"[RevertAgent] {msg}")
        _fail(db, review_run, "required", msg)
        _step(
            db, tenant_id, integration_id, event_log_id, review_run.id,
            "revert_failed", "failed",
            output_summary=msg,
        )
        return {"status": "required", "revert_pr_url": None, "error": msg}

    # ── Create revert PR ───────────────────────────────────────────────────────
    _step(
        db, tenant_id, integration_id, event_log_id, review_run.id,
        "revert_pr_creation_started", "running",
        input_summary=f"pr_node_id={pr_node_id} pr_number={pr_number}",
    )

    pr_result = revert_service.create_revert_pr_graphql(pr_node_id, task_key, token)

    if not pr_result["ok"]:
        msg = pr_result.get("error", "GraphQL revertPullRequest mutation failed")
        logger.error(f"[RevertAgent] Revert PR creation failed: {msg}")
        _fail(db, review_run, "revert_failed", msg)
        _step(
            db, tenant_id, integration_id, event_log_id, review_run.id,
            "revert_failed", "failed",
            output_summary=msg,
        )
        return {"status": "revert_failed", "revert_pr_url": None, "error": msg}

    revert_pr_number = pr_result["pr_number"]
    revert_pr_url    = pr_result["pr_url"]
    revert_branch    = pr_result["branch_name"]

    review_run.revert_status     = "revert_pr_created"
    review_run.revert_pr_url     = revert_pr_url
    review_run.revert_branch_name = revert_branch
    db.commit()

    _step(
        db, tenant_id, integration_id, event_log_id, review_run.id,
        "revert_pr_created", "completed",
        output_summary=f"revert_pr_url={revert_pr_url} branch={revert_branch}",
    )
    logger.info(f"[RevertAgent] Revert PR created: {revert_pr_url}")

    # ── Stop here if mode is create_revert_pr only ─────────────────────────────
    if mode != "create_and_merge_revert_pr":
        return {"status": "revert_pr_created", "revert_pr_url": revert_pr_url, "error": None}

    # ── Auto-merge the revert PR ───────────────────────────────────────────────
    review_run.revert_status = "revert_auto_merge_started"
    db.commit()

    _step(
        db, tenant_id, integration_id, event_log_id, review_run.id,
        "revert_auto_merge_started", "running",
        input_summary=f"revert_pr_number={revert_pr_number}",
    )

    merge_result = revert_service.merge_pr_rest(
        repo,
        revert_pr_number,
        token,
        commit_title=f"Revert: {task_key} — auto-merged by RevertAgent",
    )

    if merge_result["ok"]:
        review_run.revert_status = "reverted"
        review_run.reverted_at   = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        _step(
            db, tenant_id, integration_id, event_log_id, review_run.id,
            "revert_completed", "completed",
            output_summary=f"Revert PR #{revert_pr_number} auto-merged successfully.",
        )
        logger.info(f"[RevertAgent] Revert PR #{revert_pr_number} auto-merged. ✓")
        return {"status": "reverted", "revert_pr_url": revert_pr_url, "error": None}

    # Auto-merge failed
    conflict = merge_result.get("conflict", False)
    final_status = "revert_conflict" if conflict else "revert_failed"
    error_msg    = merge_result.get("error") or "Unknown error during auto-merge"

    review_run.revert_status        = final_status
    review_run.revert_error_message = error_msg
    db.commit()

    step_name = "revert_conflict_detected" if conflict else "revert_failed"
    _step(
        db, tenant_id, integration_id, event_log_id, review_run.id,
        step_name, "failed",
        output_summary=error_msg,
    )
    logger.warning(f"[RevertAgent] Auto-merge failed ({final_status}): {error_msg}")
    return {
        "status": final_status,
        "revert_pr_url": revert_pr_url,
        "error": error_msg,
    }
