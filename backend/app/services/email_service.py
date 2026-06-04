import smtplib
import logging
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

_SEV_COLOR = {
    "critical": "#ef4444",
    "high":     "#f97316",
    "warning":  "#eab308",
    "info":     "#3b82f6",
}

_BASE_STYLE = """
  body  { font-family: Arial, sans-serif; background:#f8fafc; margin:0; padding:0; }
  .wrap { max-width:700px; margin:24px auto; background:#fff;
          border-radius:8px; overflow:hidden;
          box-shadow:0 1px 6px rgba(0,0,0,.12); }
  .hdr  { padding:20px 28px; }
  .body { padding:20px 28px; }
  h2   { margin:0 0 4px; font-size:20px; }
  h3   { font-size:14px; color:#374151; margin:18px 0 6px; border-bottom:1px solid #e5e7eb; padding-bottom:4px; }
  p    { margin:6px 0; font-size:14px; color:#374151; line-height:1.6; }
  table.meta { width:100%; border-collapse:collapse; font-size:13px; }
  table.meta td { padding:5px 0; vertical-align:top; }
  table.meta td:first-child { color:#6b7280; width:160px; white-space:nowrap; }
  table.findings { width:100%; border-collapse:collapse; font-size:13px; margin-top:6px; }
  table.findings th { text-align:left; padding:7px 10px; background:#f1f5f9; color:#374151; border-bottom:2px solid #e2e8f0; }
  table.findings td { padding:7px 10px; border-bottom:1px solid #f1f5f9; vertical-align:top; }
  .badge { display:inline-block; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:600; }
  .tag-success { background:#dcfce7; color:#166534; }
  .tag-failed  { background:#fee2e2; color:#991b1b; }
  .tag-low     { background:#f0fdf4; color:#166534; }
  .tag-medium  { background:#fefce8; color:#854d0e; }
  .tag-high    { background:#fff7ed; color:#9a3412; }
  .tag-critical{ background:#fef2f2; color:#7f1d1d; }
  .tag-warning { background:#fefce8; color:#854d0e; }
  .tag-info    { background:#eff6ff; color:#1e40af; }
  pre { background:#f8fafc; border:1px solid #e2e8f0; border-radius:4px;
        padding:8px 10px; font-size:12px; overflow-x:auto; white-space:pre-wrap; }
"""


def _badge(value: str, extra: str = "") -> str:
    cls = f"tag-{(value or '').lower()}"
    return f'<span class="badge {cls} {extra}">{value or "—"}</span>'


class EmailService:

    def send(
        self,
        subject: str,
        body_html: str,
        recipients: List[str],
        pdf_bytes: Optional[bytes] = None,
        pdf_filename: str = "report.pdf",
    ) -> bool:
        if not recipients:
            return True
        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            logger.warning("SMTP credentials not configured — skipping email send")
            return False

        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
        msg["To"] = ", ".join(recipients)

        html_part = MIMEMultipart("alternative")
        html_part.attach(MIMEText(body_html, "html", "utf-8"))
        msg.attach(html_part)

        if pdf_bytes:
            part = MIMEBase("application", "pdf")
            part.set_payload(pdf_bytes)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{pdf_filename}"')
            msg.attach(part)

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(msg["From"], recipients, msg.as_string())
            logger.info(f"Email sent: {subject} → {recipients}")
            return True
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False

    # ── Code Review ───────────────────────────────────────────────────────────
    def build_review_body(self, review_run, findings: list, improvements: list = None) -> str:
        improvements = improvements or []
        result      = review_run.result or "unknown"
        passed      = result == "success"
        hdr_color   = "#16a34a" if passed else "#dc2626"
        result_text = "✅ APPROVED" if passed else "❌ REJECTED"

        # Meta table
        meta = "\n".join(f"""
          <tr>
            <td>{label}</td>
            <td style="color:#111827;font-weight:500">{value}</td>
          </tr>""" for label, value in [
            ("Task",             review_run.task_key        or "—"),
            ("Sprint",           review_run.sprint_name     or "—"),
            ("Source Branch",    review_run.source_branch   or "—"),
            ("Target Branch",    review_run.target_branch   or "—"),
            ("Actor",            review_run.actor_username  or "—"),
            ("Commit",           (review_run.commit_sha or "—")[:12]),
            ("Risk Level",       _badge(review_run.risk_level or "—")),
            ("Files Analyzed",   str(review_run.total_files_analyzed)),
            ("Total Findings",   str(review_run.total_findings)),
            ("Blocking",         str(review_run.blocking_findings_count)),
        ])

        # Findings table
        findings_section = ""
        if findings:
            rows = ""
            for f in findings[:30]:
                sev = (f.severity or "info").lower()
                cat = (f.category or "other")
                rule_label = f'<br><span style="font-size:10px;color:#9ca3af">{f.rule_title}</span>' if f.rule_title else ""
                rows += f"""
                <tr>
                  <td style="font-family:monospace;font-size:11px;color:#6b7280">
                    {f.file_path or "—"}{f" :{f.line_number}" if f.line_number else ""}
                  </td>
                  <td>{_badge(sev)}</td>
                  <td>{_badge(cat)}</td>
                  <td style="font-weight:500">{f.issue or "—"}{rule_label}</td>
                  <td style="color:#374151">{f.suggestion or "—"}</td>
                </tr>"""
            findings_section = f"""
              <h3>Findings ({len(findings)})</h3>
              <table class="findings">
                <thead>
                  <tr>
                    <th>File</th><th>Severity</th><th>Category</th>
                    <th>Issue</th><th>Suggestion</th>
                  </tr>
                </thead>
                <tbody>{rows}</tbody>
              </table>"""
        else:
            findings_section = "<p style='color:#6b7280;font-style:italic'>No findings detected.</p>"

        # Improvements section
        improvements_section = ""
        if improvements:
            imp_rows = ""
            for imp in improvements[:10]:
                imp_rows += f"""
                <tr>
                  <td style="font-family:monospace;font-size:11px;color:#6b7280">{imp.get('file_path') or '—'}</td>
                  <td style="font-weight:500;color:#374151">{imp.get('title') or '—'}</td>
                  <td style="color:#374151">{imp.get('suggestion') or '—'}</td>
                </tr>"""
            improvements_section = f"""
              <h3>Suggested Improvements ({len(improvements)})</h3>
              <table class="findings">
                <thead>
                  <tr><th>File</th><th>Improvement</th><th>Suggestion</th></tr>
                </thead>
                <tbody>{imp_rows}</tbody>
              </table>"""

        # Next-step message
        if passed:
            next_step = """
              <div style="margin-top:16px;padding:12px 16px;background:#f0fdf4;border-left:4px solid #16a34a;border-radius:4px">
                <p style="margin:0;font-size:13px;color:#166534">
                  ✅ Review <strong>approved</strong>. Functional test phase will start automatically if tests are configured.
                </p>
              </div>"""
        else:
            next_step = """
              <div style="margin-top:16px;padding:12px 16px;background:#fef2f2;border-left:4px solid #dc2626;border-radius:4px">
                <p style="margin:0;font-size:13px;color:#991b1b">
                  ❌ Review <strong>rejected</strong>. Functional tests will <strong>not</strong> run until blocking issues are resolved.
                </p>
              </div>"""

        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>{_BASE_STYLE}</style></head>
<body>
<div class="wrap">
  <div class="hdr" style="background:{hdr_color}">
    <h2 style="color:#fff">Code Review — {result_text}</h2>
    <p style="color:rgba(255,255,255,.85);margin:0;font-size:13px">
      {review_run.task_key or "N/A"} &middot; {review_run.sprint_name or "N/A"}
    </p>
  </div>
  <div class="body">
    <table class="meta">{meta}</table>

    <h3>Summary</h3>
    <p>{review_run.report_summary or "No summary available."}</p>

    <h3>Decision Reason</h3>
    <p>{review_run.decision_reason or "—"}</p>

    {findings_section}
    {improvements_section}
    {next_step}
  </div>
</div>
</body></html>"""

    # ── Functional Tests ──────────────────────────────────────────────────────
    def build_test_body(self, test_run) -> str:
        result      = test_run.result or "unknown"
        hdr_color   = "#16a34a" if result == "success" else "#dc2626"
        result_text = "✅ PASSED" if result == "success" else "❌ FAILED"

        meta = "\n".join(f"""
          <tr>
            <td>{label}</td>
            <td style="color:#111827;font-weight:500">{value}</td>
          </tr>""" for label, value in [
            ("Task",         test_run.task_key   or "—"),
            ("Sprint",       test_run.sprint_name or "—"),
            ("Total Tests",  str(test_run.total_tests)),
            ("Passed",       f'<span style="color:#16a34a;font-weight:700">{test_run.passed_tests}</span>'),
            ("Failed",       f'<span style="color:#dc2626;font-weight:700">{test_run.failed_tests}</span>'),
        ])

        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>{_BASE_STYLE}</style></head>
<body>
<div class="wrap">
  <div class="hdr" style="background:{hdr_color}">
    <h2 style="color:#fff">Functional Tests — {result_text}</h2>
    <p style="color:rgba(255,255,255,.85);margin:0;font-size:13px">
      {test_run.task_key or "N/A"} · {test_run.sprint_name or "N/A"}
    </p>
  </div>
  <div class="body">
    <table class="meta">{meta}</table>

    <h3>Summary</h3>
    <p>{test_run.report_summary or "No summary available."}</p>
  </div>
</div>
</body></html>"""


email_service = EmailService()
