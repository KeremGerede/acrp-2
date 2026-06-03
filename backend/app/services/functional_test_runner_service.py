import json
import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.functional_test import FunctionalTestConfig, FunctionalTestRun
from app.models.promotion import EnvironmentPromotionLog
from app.agents.functional_test_agent import run_functional_tests
from app.services.lifecycle_status_service import update_test_status
from app.services.notification_log_service import create_notification_log, mark_sent, mark_failed
from app.services.user_stats_service import increment
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


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


def run_tests_for_review(
    db: Session,
    tenant_id: int,
    integration_id: int,
    merge_review_run_id: int,
    event_log_id: Optional[int],
    sprint_name: Optional[str],
    task_key: Optional[str],
    commit_sha: Optional[str],
    actor_username: str,
    actor_email: Optional[str],
    integration,
):
    configs = db.query(FunctionalTestConfig).filter_by(
        tenant_id=tenant_id, integration_id=integration_id, is_enabled=True
    ).all()

    if not configs:
        logger.info(f"No functional test configs for integration {integration_id}")
        return

    for config in configs:
        test_run = FunctionalTestRun(
            tenant_id=tenant_id,
            integration_id=integration_id,
            merge_review_run_id=merge_review_run_id,
            event_log_id=event_log_id,
            sprint_name=sprint_name,
            task_key=task_key,
            commit_sha=commit_sha,
            status="running",
        )
        db.add(test_run)
        db.commit()
        db.refresh(test_run)

        report = run_functional_tests(
            db=db,
            tenant_id=tenant_id,
            integration_id=integration_id,
            functional_test_run_id=test_run.id,
            test_command=config.test_command,
            working_directory=config.working_directory,
        )

        update_test_status(
            db, test_run.id,
            status="completed",
            result=report["result"],
            total_tests=report.get("total_tests", 0),
            passed_tests=report.get("passed_tests", 0),
            failed_tests=report.get("failed_tests", 0),
            report_summary=report.get("summary", ""),
            raw_output=report.get("raw_output", ""),
        )

        # Update user stats
        stat_field = "successful_test_count" if report["result"] == "success" else "failed_test_count"
        increment(db, tenant_id, integration_id, actor_username, actor_email or "", stat_field)

        # Build email
        test_run_refreshed = db.query(FunctionalTestRun).filter_by(id=test_run.id).first()
        recipients = _collect_recipients(integration, actor_email)

        if report["result"] == "success":
            subject = f"[TEST SUCCESS] {task_key or 'N/A'} Ready for Test Environment - {sprint_name or 'N/A'}"
            notification_type = "test_success"
        else:
            subject = f"[TEST FAILED] {task_key or 'N/A'} Functional Tests Failed - {sprint_name or 'N/A'}"
            notification_type = "test_failed"

        notif = create_notification_log(
            db, tenant_id, integration_id, notification_type, subject, recipients,
            related_entity_type="functional_test", related_entity_id=test_run.id,
        )
        body = email_service.build_test_body(test_run_refreshed)
        ok = email_service.send(subject, body, recipients)
        if ok:
            mark_sent(db, notif.id)
        else:
            mark_failed(db, notif.id, "SMTP send failed")

        # Environment promotion if tests passed
        if report["result"] == "success":
            promotion = EnvironmentPromotionLog(
                tenant_id=tenant_id,
                integration_id=integration_id,
                merge_review_run_id=merge_review_run_id,
                functional_test_run_id=test_run.id,
                from_stage="sprint",
                to_stage="test",
                status="ready_for_test_environment",
                message=f"Task {task_key} passed review and functional tests. Ready for TEST environment.",
            )
            db.add(promotion)
            db.commit()

            increment(db, tenant_id, integration_id, actor_username, actor_email or "", "successful_promotion_count")

            prom_subject = f"[PROMOTION READY] {task_key or 'N/A'} is ready for TEST environment"
            prom_notif = create_notification_log(
                db, tenant_id, integration_id, "promotion_success", prom_subject, recipients,
                related_entity_type="promotion", related_entity_id=promotion.id,
            )
            prom_body = f"""<html><body style="font-family:sans-serif;padding:20px">
            <h2 style="color:#22c55e">Promotion Ready</h2>
            <p>Task <strong>{task_key or 'N/A'}</strong> ({sprint_name or 'N/A'}) has passed code review and functional tests.</p>
            <p>It is ready to be promoted to the <strong>TEST</strong> environment.</p>
            </body></html>"""
            ok2 = email_service.send(prom_subject, prom_body, recipients)
            if ok2:
                mark_sent(db, prom_notif.id)
            else:
                mark_failed(db, prom_notif.id, "SMTP send failed")
