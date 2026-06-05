"""
RevertAgent — automatically reverts a failed merge after CodeReviewAgent rejects it.

Modes (AUTO_REVERT_MODE env var):
  create_revert_pr              → create a revert PR, leave merging to a human
  create_and_merge_revert_pr    → create revert PR and auto-merge it (default)
  disabled                      → mark revert_status=required, do nothing

PR node_id resolution priority:
  1. event_log.pull_request_node_id  (stored directly from pull_request webhook event)
  2. event_log.pull_request_number   → fetch node_id via GET /pulls/{number}
  3. raw payload JSON                → parse pull_request.node_id (legacy fallback)
  4. review_run.commit_sha           → GET /commits/{sha}/pulls
  If all fail → revert_status=required with explanation.
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

_MISSING_PR_MSG = (
    "Could not resolve the merged pull request. "
    "Automatic revert requires the GitHub Pull request webhook event to be enabled. "
    "Go to your GitHub repo → Settings → Webhooks → Edit → "
    "select 'Pull requests' in addition to 'Pushes'. "
    "The failed merge may still be present in the sprint branch."
)


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


def _mark_failed(
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
    Entry point for RevertAgent.
    Updates review_run fields in-place; returns a result dict:
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

    # ── Disabled / misconfigured ───────────────────────────────────────────────
    if mode == "disabled" or not repo:
        reason = "AUTO_REVERT_MODE is disabled or repository not configured."
        revert_service.mark_revert_required(db, review_run, reason)
        _step(db, tenant_id, integration_id, event_log_id, review_run.id,
              "revert_required_due_to_missing_pr", "completed", output_summary=reason)
        return {"status": "required", "revert_pr_url": None, "error": reason}

    # Mark that revert is actively being attempted
    review_run.revert_status = "started"
    db.commit()

    token = _get_token(db, integration_id)
    event_log = db.query(SCMEventLog).filter_by(id=event_log_id).first()

    # ── Step 1-4: resolve PR node_id ──────────────────────────────────────────
    pr_node_id: Optional[str] = None
    pr_number: Optional[int] = None

    # 1. Dedicated column (set when event came from a pull_request webhook event)
    if event_log:
        pr_node_id = getattr(event_log, "pull_request_node_id", None) or None
        pr_number  = getattr(event_log, "pull_request_number", None) or None
        if pr_node_id:
            logger.info(f"[RevertAgent] PR node_id from event log column: #{pr_number}")
            _step(db, tenant_id, integration_id, event_log_id, review_run.id,
                  "pr_node_id_resolved", "completed",
                  output_summary=f"source=event_log_column pr_number={pr_number}")

    # 2. Have number but not node_id → fetch via REST (reliable, single PR lookup)
    if not pr_node_id and pr_number and repo:
        logger.info(f"[RevertAgent] Fetching node_id for PR #{pr_number} via REST")
        pr_node_id = revert_service.find_pr_node_id_by_number(repo, pr_number, token)
        if pr_node_id:
            _step(db, tenant_id, integration_id, event_log_id, review_run.id,
                  "pr_node_id_resolved", "completed",
                  output_summary=f"source=rest_by_number pr_number={pr_number}")

    # 3. Legacy: parse raw payload JSON (events logged before dedicated columns)
    if not pr_node_id and event_log:
        raw_node_id, raw_number = revert_service.extract_pr_info_from_event(event_log)
        if raw_node_id:
            pr_node_id = raw_node_id
            pr_number  = pr_number or raw_number
            logger.info(f"[RevertAgent] PR node_id from raw payload JSON: #{pr_number}")
            _step(db, tenant_id, integration_id, event_log_id, review_run.id,
                  "pr_node_id_resolved", "completed",
                  output_summary=f"source=raw_payload_json pr_number={pr_number}")

    # 4. Last resort: commit-SHA → PR lookup (may fail for push-only events)
    if not pr_node_id and merge_sha and repo:
        logger.info(f"[RevertAgent] Attempting commit→PR lookup for {merge_sha}")
        pr_node_id, pr_number = revert_service.find_pr_by_commit(repo, merge_sha, token)
        if pr_node_id:
            logger.info(f"[RevertAgent] PR found via commit lookup: #{pr_number}")
            _step(db, tenant_id, integration_id, event_log_id, review_run.id,
                  "pr_node_id_resolved", "completed",
                  output_summary=f"source=commit_lookup pr_number={pr_number}")

    # All resolution attempts failed
    if not pr_node_id:
        logger.warning(f"[RevertAgent] Could not resolve PR node_id for repo={repo}")
        _mark_failed(db, review_run, "required", _MISSING_PR_MSG)
        _step(db, tenant_id, integration_id, event_log_id, review_run.id,
              "pr_lookup_failed", "failed", output_summary=_MISSING_PR_MSG)
        return {"status": "required", "revert_pr_url": None, "error": _MISSING_PR_MSG}

    # ── Create revert PR ───────────────────────────────────────────────────────
    _step(db, tenant_id, integration_id, event_log_id, review_run.id,
          "revert_pr_creation_started", "running",
          input_summary=f"pr_node_id={pr_node_id} pr_number={pr_number}")

    pr_result = revert_service.create_revert_pr_graphql(pr_node_id, task_key, token)

    if not pr_result["ok"]:
        error_msg = pr_result.get("error", "GraphQL revertPullRequest mutation failed")
        perm_err  = pr_result.get("permission_error", False)
        logger.error(f"[RevertAgent] Revert PR creation failed (permission={perm_err}): {error_msg}")
        _mark_failed(db, review_run, "revert_failed", error_msg)
        step_name = "revert_permission_error" if perm_err else "revert_failed"
        _step(db, tenant_id, integration_id, event_log_id, review_run.id,
              step_name, "failed", output_summary=error_msg)
        return {"status": "revert_failed", "revert_pr_url": None, "error": error_msg}

    revert_pr_number = pr_result["pr_number"]
    revert_pr_url    = pr_result["pr_url"]
    revert_branch    = pr_result["branch_name"]

    review_run.revert_status      = "revert_pr_created"
    review_run.revert_pr_url      = revert_pr_url
    review_run.revert_branch_name = revert_branch
    db.commit()

    _step(db, tenant_id, integration_id, event_log_id, review_run.id,
          "revert_pr_created", "completed",
          output_summary=f"revert_pr_url={revert_pr_url} branch={revert_branch}")
    logger.info(f"[RevertAgent] Revert PR created: {revert_pr_url}")

    # ── Validate revert PR base branch ────────────────────────────────────────
    expected_base = review_run.target_branch or ""
    actual_base = revert_service.get_revert_pr_base_branch(repo, revert_pr_number, token)
    if actual_base is not None and actual_base != expected_base:
        error_msg = (
            f"Revert PR #{revert_pr_number} targets '{actual_base}' "
            f"but the original merge targeted '{expected_base}'. "
            "Auto-merge aborted to prevent merging into the wrong branch."
        )
        logger.error(f"[RevertAgent] Base branch mismatch: {error_msg}")
        _mark_failed(db, review_run, "revert_failed", error_msg)
        _step(db, tenant_id, integration_id, event_log_id, review_run.id,
              "revert_pr_base_branch_validated", "failed", output_summary=error_msg)
        return {"status": "revert_failed", "revert_pr_url": revert_pr_url, "error": error_msg}

    _step(db, tenant_id, integration_id, event_log_id, review_run.id,
          "revert_pr_base_branch_validated", "completed",
          output_summary=f"base={actual_base or 'unknown'} expected={expected_base}")

    # ── Stop if mode is create_revert_pr only ─────────────────────────────────
    if mode != "create_and_merge_revert_pr":
        return {"status": "revert_pr_created", "revert_pr_url": revert_pr_url, "error": None}

    # ── Auto-merge revert PR ───────────────────────────────────────────────────
    review_run.revert_status = "revert_auto_merge_started"
    db.commit()

    _step(db, tenant_id, integration_id, event_log_id, review_run.id,
          "revert_auto_merge_started", "running",
          input_summary=f"revert_pr_number={revert_pr_number}")

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
        _step(db, tenant_id, integration_id, event_log_id, review_run.id,
              "revert_auto_merge_completed", "completed",
              output_summary=f"Revert PR #{revert_pr_number} auto-merged successfully.")
        logger.info(f"[RevertAgent] Revert PR #{revert_pr_number} auto-merged. ✓")
        return {"status": "reverted", "revert_pr_url": revert_pr_url, "error": None}

    # Auto-merge failed
    perm_err      = merge_result.get("permission_error", False)
    conflict      = merge_result.get("conflict", False)
    error_msg     = merge_result.get("error") or "Unknown error during auto-merge"
    final_status  = "revert_conflict" if conflict else "revert_failed"

    review_run.revert_status        = final_status
    review_run.revert_error_message = error_msg
    db.commit()

    if perm_err:
        step_name = "revert_permission_error"
    elif conflict:
        step_name = "revert_conflict_detected"
    else:
        step_name = "revert_failed"

    _step(db, tenant_id, integration_id, event_log_id, review_run.id,
          step_name, "failed", output_summary=error_msg)
    _step(db, tenant_id, integration_id, event_log_id, review_run.id,
          "revert_auto_merge_failed", "failed",
          output_summary=f"final_status={final_status} error={error_msg}")
    logger.warning(f"[RevertAgent] Auto-merge failed ({final_status}): {error_msg}")
    return {"status": final_status, "revert_pr_url": revert_pr_url, "error": error_msg}
