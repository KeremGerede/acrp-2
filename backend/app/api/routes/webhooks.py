import json
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db, SessionLocal
from app.models.integration import ProjectIntegration
from app.models.scm_event import SCMEventLog
from app.models.merge_review import MergeReviewRun
from app.models.finding import Finding
from app.providers.registry import get_adapter
from app.providers.normalized_events import EventType, NormalizedSCMEvent
from app.services.branch_parser_service import parse_sprint_and_task
from app.services.merge_event_detector_service import detect_event_type
from app.services.lifecycle_status_service import update_review_status
from app.services.notification_log_service import create_notification_log, mark_sent, mark_failed
from app.services.user_stats_service import increment
from app.services.email_service import email_service
from app.services.functional_test_runner_service import run_tests_for_review
from app.services.pdf_report_service import generate_review_pdf
from app.tools.changed_files_fetcher_tool import fetch_changed_files
from app.agents.reviewer_agent import run_review

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


def _collect_recipients(integration, actor_email: Optional[str]) -> List[str]:
    recipients = []
    if actor_email:
        recipients.append(actor_email)
    if integration.manager_email:
        recipients.append(integration.manager_email)
    if integration.notification_recipients:
        try:
            extras = json.loads(integration.notification_recipients)
            recipients.extend(extras)
        except Exception:
            pass
    return list(dict.fromkeys(r for r in recipients if r))


def _get_token(db: Session, integration_id: int) -> Optional[str]:
    from app.models.integration import PlatformCredential
    cred = db.query(PlatformCredential).filter_by(integration_id=integration_id).first()
    return (cred.token_encrypted_or_placeholder if cred else None) or None


def _process_task_merge(event_log_id: int, integration_id: int) -> None:
    """Background task: fetch diff → run review → email → optionally run functional tests."""
    db = SessionLocal()
    try:
        event_log = db.query(SCMEventLog).filter_by(id=event_log_id).first()
        if not event_log:
            return

        integration = db.query(ProjectIntegration).filter_by(id=integration_id).first()
        if not integration:
            return

        tenant_id   = event_log.tenant_id
        sprint_name = event_log.detected_sprint or ""
        task_key    = event_log.detected_task_key or ""
        actor_username = event_log.actor_username or ""
        actor_email    = event_log.actor_email
        repo_full_name = integration.repository_full_name or ""

        # Decode commit messages
        try:
            commit_messages: List[str] = json.loads(event_log.commit_messages or "[]")
        except Exception:
            commit_messages = []

        # ── Fetch changed files ──────────────────────────────────────────────
        changed_files: List[dict] = []
        try:
            token = _get_token(db, integration_id)
            changed_files = fetch_changed_files(
                provider=event_log.provider,
                repo_full_name=repo_full_name,
                before_sha=event_log.before_sha,
                after_sha=event_log.after_sha,
                token=token,
                commit_sha=event_log.commit_sha,
            )
            logger.info(f"Fetched {len(changed_files)} changed file(s) for review run")
        except Exception as exc:
            logger.warning(f"Could not fetch changed files: {exc}")

        # ── Create MergeReviewRun ────────────────────────────────────────────
        review_start = datetime.utcnow()
        review_run = MergeReviewRun(
            tenant_id=tenant_id,
            integration_id=integration_id,
            event_log_id=event_log_id,
            repository_full_name=repo_full_name,
            sprint_name=sprint_name,
            task_key=task_key,
            source_branch=event_log.source_branch,
            target_branch=event_log.target_branch,
            commit_sha=event_log.commit_sha,
            actor_username=actor_username,
            status="running",
            started_at=review_start,
            total_files_analyzed=len(changed_files),
        )
        db.add(review_run)
        db.commit()
        db.refresh(review_run)

        # ── Run ReviewerAgent ────────────────────────────────────────────────
        try:
            report = run_review(
                db=db,
                tenant_id=tenant_id,
                integration_id=integration_id,
                merge_review_run_id=review_run.id,
                event_log_id=event_log_id,
                changed_files=changed_files,
                actor_username=actor_username,
                commit_messages=commit_messages,
                sprint_name=sprint_name,
                task_key=task_key,
                source_branch=event_log.source_branch or "",
                target_branch=event_log.target_branch or "",
                repository_full_name=repo_full_name,
            )
        except Exception as exc:
            logger.error(f"ReviewerAgent failed: {exc}")
            update_review_status(
                db, review_run.id, "failed", "failed",
                decision_reason=f"System error: {exc}",
                report_summary="Review could not be completed due to a system error.",
            )
            return

        # ── Save findings ────────────────────────────────────────────────────
        findings_objs: List[Finding] = []
        for f in report.get("findings", []):
            finding = Finding(
                merge_review_run_id=review_run.id,
                rule_id=f.get("rule_id"),
                file_path=f.get("file_path"),
                line_number=f.get("line_number"),
                rule_title=f.get("rule_title"),
                category=f.get("category"),
                severity=f.get("severity"),
                issue=f.get("issue"),
                explanation=f.get("explanation"),
                suggestion=f.get("suggestion"),
                code_snippet=f.get("code_snippet"),
            )
            db.add(finding)
            findings_objs.append(finding)
        db.commit()

        improvements = report.get("improvements", [])
        passed_checks = report.get("passed_checks", [])
        failed_checks = report.get("failed_checks", [])
        file_assessments = report.get("file_assessments", [])
        blocking = report.get("blocking_findings_count", 0)

        # Serialize full agent response for audit trail
        raw_json = json.dumps({
            "result": report.get("result"),
            "summary": report.get("summary"),
            "risk_level": report.get("risk_level"),
            "decision_reason": report.get("decision_reason"),
            "findings": report.get("findings", []),
            "improvements": improvements,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "file_assessments": file_assessments,
        }, ensure_ascii=False)

        update_review_status(
            db, review_run.id,
            status="completed",
            result=report["result"],
            decision_reason=report.get("decision_reason", ""),
            risk_level=report.get("risk_level", "medium"),
            total_findings=len(report.get("findings", [])),
            blocking_findings_count=blocking,
            report_summary=report.get("summary", ""),
            raw_agent_response_json=raw_json,
        )

        # ── Update user stats ────────────────────────────────────────────────
        stat_field = "successful_review_count" if report["result"] == "success" else "failed_review_count"
        increment(db, tenant_id, integration_id, actor_username, actor_email or "", stat_field)

        # ── Send email ───────────────────────────────────────────────────────
        recipients = _collect_recipients(integration, actor_email)
        passed = report["result"] == "success"

        if passed:
            subject = f"[REVIEW SUCCESS] {task_key or 'N/A'} - {sprint_name or 'N/A'}"
            notification_type = "review_success"
        else:
            subject = f"[REVIEW FAILED] {task_key or 'N/A'} - {sprint_name or 'N/A'}"
            notification_type = "review_failed"

        notif = create_notification_log(
            db, tenant_id, integration_id, notification_type, subject, recipients,
            related_entity_type="merge_review", related_entity_id=review_run.id,
        )

        review_run_refreshed = db.query(MergeReviewRun).filter_by(id=review_run.id).first()
        body = email_service.build_review_body(
            review_run_refreshed, findings_objs, improvements=improvements,
            passed_checks=passed_checks, failed_checks=failed_checks,
            file_assessments=file_assessments,
        )

        pdf_bytes = None
        try:
            pdf_bytes = generate_review_pdf(
                review_run_refreshed, findings_objs,
                passed_checks=passed_checks, failed_checks=failed_checks,
                file_assessments=file_assessments,
            )
        except Exception as exc:
            logger.warning(f"PDF generation failed, sending email without attachment: {exc}")

        safe_task   = (task_key or "report").replace("/", "-").replace(" ", "_")
        safe_sprint = (sprint_name or "").replace("/", "-").replace(" ", "_")
        pdf_filename = f"review_{safe_task}_{safe_sprint}.pdf".strip("_")

        ok = email_service.send(
            subject, body, recipients,
            pdf_bytes=pdf_bytes, pdf_filename=pdf_filename,
        )
        if ok:
            mark_sent(db, notif.id)
        else:
            mark_failed(db, notif.id, "SMTP send failed")

        # ── Functional tests (only if approved) ─────────────────────────────
        if passed:
            run_tests_for_review(
                db=db,
                tenant_id=tenant_id,
                integration_id=integration_id,
                merge_review_run_id=review_run.id,
                event_log_id=event_log_id,
                sprint_name=sprint_name,
                task_key=task_key,
                commit_sha=event_log.commit_sha,
                actor_username=actor_username,
                actor_email=actor_email,
                integration=integration,
            )
        else:
            logger.info(
                f"Functional tests SKIPPED — review rejected for {task_key} / {sprint_name}"
            )

    except Exception as exc:
        logger.exception(f"Background pipeline error: {exc}")
    finally:
        db.close()


@router.post("/{provider}/{integration_id}")
async def handle_webhook(
    provider: str,
    integration_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    integration = db.query(ProjectIntegration).filter_by(
        id=integration_id, provider=provider, is_active=True
    ).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    body = await request.body()
    headers = dict(request.headers)

    try:
        adapter = get_adapter(provider)
        if not adapter.verify_webhook_signature(body, integration.webhook_secret or "", headers):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
    except NotImplementedError:
        pass
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(f"Signature verification error: {exc}")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    try:
        normalized: Optional[NormalizedSCMEvent] = adapter.parse_webhook_event(
            payload, integration.tenant_id, integration_id
        )
    except NotImplementedError:
        return {"status": "ignored", "reason": "Provider not yet implemented"}
    except Exception as exc:
        logger.warning(f"Webhook parse error: {exc}")
        return {"status": "ignored", "reason": str(exc)}

    if not normalized:
        return {"status": "ignored", "reason": "Event not actionable"}

    event_type = detect_event_type(normalized, integration)
    normalized.event_type = event_type

    sprint_name, task_key = parse_sprint_and_task(
        normalized.source_branch or "",
        normalized.target_branch or normalized.branch or "",
    )

    event_log = SCMEventLog(
        tenant_id=integration.tenant_id,
        integration_id=integration_id,
        provider=provider,
        event_type=event_type.value,
        actor_username=normalized.actor_username,
        actor_email=normalized.actor_email,
        source_branch=normalized.source_branch,
        target_branch=normalized.target_branch,
        branch=normalized.branch,
        before_sha=normalized.before_sha,
        after_sha=normalized.after_sha,
        commit_sha=normalized.commit_sha,
        commit_messages=json.dumps(normalized.commit_messages),
        detected_sprint=sprint_name,
        detected_task_key=task_key,
        is_merge_event=normalized.is_merge_event,
        raw_payload_json=json.dumps(payload)[:50000],
    )
    db.add(event_log)
    db.commit()
    db.refresh(event_log)

    if event_type == EventType.task_to_sprint_merge:
        background_tasks.add_task(_process_task_merge, event_log.id, integration_id)
        return {"status": "accepted", "event_id": event_log.id, "event_type": event_type.value}

    return {"status": "logged", "event_id": event_log.id, "event_type": event_type.value}
