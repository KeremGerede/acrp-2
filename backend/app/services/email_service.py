import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:

    def send(self, subject: str, body_html: str, recipients: List[str]) -> bool:
        if not recipients:
            return True
        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            logger.warning("SMTP credentials not configured — skipping email send")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
        msg["To"] = ", ".join(recipients)
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(msg["From"], recipients, msg.as_string())
            logger.info(f"Email sent: {subject} -> {recipients}")
            return True
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False

    def build_review_body(self, review_run, findings: list) -> str:
        result_color = "#22c55e" if review_run.result == "success" else "#ef4444"
        findings_html = ""
        for f in findings[:20]:
            sev_color = {"critical": "#ef4444", "high": "#f97316", "warning": "#eab308", "info": "#3b82f6"}.get(
                f.severity or "info", "#6b7280"
            )
            findings_html += f"""
            <tr>
              <td style="padding:6px 8px;border-bottom:1px solid #e5e7eb">{f.file_path or ""}</td>
              <td style="padding:6px 8px;border-bottom:1px solid #e5e7eb;color:{sev_color}">{f.severity or ""}</td>
              <td style="padding:6px 8px;border-bottom:1px solid #e5e7eb">{f.issue or ""}</td>
            </tr>"""

        return f"""
        <html><body style="font-family:sans-serif;max-width:800px;margin:0 auto;padding:20px">
          <h2 style="color:{result_color}">Code Review: {review_run.result.upper() if review_run.result else "N/A"}</h2>
          <table style="border-collapse:collapse;width:100%">
            <tr><td style="padding:4px 0"><strong>Task:</strong></td><td>{review_run.task_key or "N/A"}</td></tr>
            <tr><td style="padding:4px 0"><strong>Sprint:</strong></td><td>{review_run.sprint_name or "N/A"}</td></tr>
            <tr><td style="padding:4px 0"><strong>Branch:</strong></td><td>{review_run.source_branch or "N/A"} → {review_run.target_branch or "N/A"}</td></tr>
            <tr><td style="padding:4px 0"><strong>Actor:</strong></td><td>{review_run.actor_username or "N/A"}</td></tr>
            <tr><td style="padding:4px 0"><strong>Risk Level:</strong></td><td>{review_run.risk_level or "N/A"}</td></tr>
            <tr><td style="padding:4px 0"><strong>Files Analyzed:</strong></td><td>{review_run.total_files_analyzed}</td></tr>
            <tr><td style="padding:4px 0"><strong>Total Findings:</strong></td><td>{review_run.total_findings}</td></tr>
            <tr><td style="padding:4px 0"><strong>Blocking Findings:</strong></td><td>{review_run.blocking_findings_count}</td></tr>
          </table>
          <h3>Summary</h3>
          <p>{review_run.report_summary or "No summary available."}</p>
          <h3>Decision Reason</h3>
          <p>{review_run.decision_reason or ""}</p>
          {"<h3>Findings</h3><table style='border-collapse:collapse;width:100%;font-size:13px'><thead><tr><th style='text-align:left;padding:6px 8px;background:#f3f4f6'>File</th><th style='text-align:left;padding:6px 8px;background:#f3f4f6'>Severity</th><th style='text-align:left;padding:6px 8px;background:#f3f4f6'>Issue</th></tr></thead><tbody>" + findings_html + "</tbody></table>" if findings else ""}
        </body></html>"""

    def build_test_body(self, test_run) -> str:
        result_color = "#22c55e" if test_run.result == "success" else "#ef4444"
        return f"""
        <html><body style="font-family:sans-serif;max-width:800px;margin:0 auto;padding:20px">
          <h2 style="color:{result_color}">Functional Tests: {test_run.result.upper() if test_run.result else "N/A"}</h2>
          <table style="border-collapse:collapse;width:100%">
            <tr><td style="padding:4px 0"><strong>Task:</strong></td><td>{test_run.task_key or "N/A"}</td></tr>
            <tr><td style="padding:4px 0"><strong>Sprint:</strong></td><td>{test_run.sprint_name or "N/A"}</td></tr>
            <tr><td style="padding:4px 0"><strong>Total Tests:</strong></td><td>{test_run.total_tests}</td></tr>
            <tr><td style="padding:4px 0"><strong>Passed:</strong></td><td style="color:#22c55e">{test_run.passed_tests}</td></tr>
            <tr><td style="padding:4px 0"><strong>Failed:</strong></td><td style="color:#ef4444">{test_run.failed_tests}</td></tr>
          </table>
          <h3>Summary</h3>
          <p>{test_run.report_summary or "No summary available."}</p>
        </body></html>"""


email_service = EmailService()
