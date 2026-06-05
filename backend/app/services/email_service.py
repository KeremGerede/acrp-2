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
  .wrap { max-width:720px; margin:24px auto; background:#fff;
          border-radius:8px; overflow:hidden;
          box-shadow:0 1px 6px rgba(0,0,0,.12); }
  .hdr  { padding:20px 28px; }
  .body { padding:20px 28px; }
  h2   { margin:0 0 4px; font-size:20px; }
  h3   { font-size:14px; color:#374151; margin:22px 0 8px;
         border-bottom:2px solid #e5e7eb; padding-bottom:5px; }
  p    { margin:6px 0; font-size:14px; color:#374151; line-height:1.6; }
  table.meta { width:100%; border-collapse:collapse; font-size:13px; }
  table.meta td { padding:5px 0; vertical-align:top; }
  table.meta td:first-child { color:#6b7280; width:200px; white-space:nowrap; }
  .badge { display:inline-block; padding:2px 8px; border-radius:12px;
           font-size:11px; font-weight:600; }
  .tag-success  { background:#dcfce7; color:#166534; }
  .tag-failed   { background:#fee2e2; color:#991b1b; }
  .tag-low      { background:#f0fdf4; color:#166534; }
  .tag-medium   { background:#fefce8; color:#854d0e; }
  .tag-high     { background:#fff7ed; color:#9a3412; }
  .tag-critical { background:#fef2f2; color:#7f1d1d; }
  .tag-warning  { background:#fefce8; color:#854d0e; }
  .tag-info     { background:#eff6ff; color:#1e40af; }
  .finding-card {
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    margin-bottom: 16px;
    overflow: hidden;
  }
  .finding-header {
    background: #f8fafc;
    padding: 9px 14px;
    border-bottom: 1px solid #e5e7eb;
    font-size: 12px;
    color: #374151;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .finding-body { padding: 12px 14px; }
  .finding-label {
    font-size: 12px;
    font-weight: 600;
    color: #6b7280;
    margin: 10px 0 3px;
    text-transform: uppercase;
    letter-spacing: .4px;
  }
  .finding-label:first-child { margin-top: 0; }
  .finding-value { font-size: 13px; color: #111827; line-height: 1.6; margin: 0; }
  .finding-file  { font-family: monospace; font-size: 11px; color: #6b7280; margin: 0 0 8px; }
  pre { background:#f8fafc; border:1px solid #e2e8f0; border-radius:4px;
        padding:8px 10px; font-size:11px; overflow-x:auto; white-space:pre-wrap;
        margin: 6px 0 0; }
  .imp-card {
    border-left: 3px solid #6366f1;
    background: #f5f3ff;
    border-radius: 4px;
    padding: 10px 14px;
    margin-bottom: 10px;
  }
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
    def build_review_body(
        self,
        review_run,
        findings: list,
        improvements: list = None,
        passed_checks: list = None,
        failed_checks: list = None,
        file_assessments: list = None,
    ) -> str:
        improvements = improvements or []
        passed_checks = passed_checks or []
        failed_checks = failed_checks or []
        file_assessments = file_assessments or []
        result  = review_run.result or "unknown"
        passed  = result == "success"
        hdr_color   = "#16a34a" if passed else "#dc2626"
        result_text = "✅ ONAYLANDI" if passed else "❌ REDDEDİLDİ"

        # ── Meta tablosu ─────────────────────────────────────────────────────
        meta = "\n".join(f"""
          <tr>
            <td>{label}</td>
            <td style="color:#111827;font-weight:500">{value}</td>
          </tr>""" for label, value in [
            ("Task",                      review_run.task_key        or "—"),
            ("Sprint",                    review_run.sprint_name     or "—"),
            ("Source Branch",             review_run.source_branch   or "—"),
            ("Target Branch",             review_run.target_branch   or "—"),
            ("İşlemi Yapan",              review_run.actor_username  or "—"),
            ("Commit SHA",                (review_run.commit_sha or "—")[:12]),
            ("Risk Seviyesi",             _badge(review_run.risk_level or "—")),
            ("Analiz Edilen Dosya Sayısı",str(review_run.total_files_analyzed)),
            ("Toplam Bulgu",              str(review_run.total_findings)),
            ("Engelleyici Bulgu",         str(review_run.blocking_findings_count)),
        ])

        # ── Dosya Bazli Inceleme Sonucu ──────────────────────────────────────
        _FA_STATUS_CLS = {
            "passed": "tag-success",
            "passed_with_warnings": "tag-warning",
            "failed": "tag-failed",
        }
        _FA_STATUS_LBL = {
            "passed": "Geçti",
            "passed_with_warnings": "Uyarı ile geçti",
            "failed": "Başarısız",
        }
        file_assess_section = ""
        if file_assessments:
            rows = ""
            for fa in file_assessments:
                status = fa.get("status", "passed")
                s_cls = _FA_STATUS_CLS.get(status, "tag-info")
                s_lbl = _FA_STATUS_LBL.get(status, status)
                passed_pts = fa.get("passed_points", [])
                remaining_pts = fa.get("remaining_points", [])
                p_html = "".join(
                    f"<li style='font-size:12px;color:#374151;line-height:1.6'>{pt}</li>"
                    for pt in passed_pts
                ) if passed_pts else ""
                r_html = "".join(
                    f"<li style='font-size:12px;color:#374151;line-height:1.6'>{pt}</li>"
                    for pt in remaining_pts
                ) if remaining_pts else ""
                rows += f"""
                <div style="border:1px solid #e5e7eb;border-radius:6px;padding:10px 14px;margin-bottom:8px">
                  <div style="font-family:monospace;font-size:12px;color:#111827;font-weight:600">{fa.get('file_path', '-')}</div>
                  <div style="margin-top:4px"><span class="badge {s_cls}">{s_lbl}</span></div>
                  {"<p style='font-size:12px;color:#6b7280;margin:8px 0 2px;font-weight:600'>Geçen noktalar:</p><ul style='margin:2px 0;padding-left:18px'>" + p_html + "</ul>" if p_html else ""}
                  {"<p style='font-size:12px;color:#6b7280;margin:8px 0 2px;font-weight:600'>Kalan noktalar:</p><ul style='margin:2px 0;padding-left:18px'>" + r_html + "</ul>" if r_html else ""}
                </div>"""
            file_assess_section = f"<h3>Dosya Bazlı İnceleme Sonucu</h3>{rows}"

        # ── Basariyla Gecen Kontroller ────────────────────────────────────────
        passed_checks_section = ""
        if passed_checks:
            cards = ""
            for idx, pc in enumerate(passed_checks, 1):
                evidence_row = (
                    f"<p style='margin:4px 0 0;font-size:12px;color:#374151'>"
                    f"<strong>Kanıt:</strong> {pc.get('evidence', '')}</p>"
                ) if pc.get("evidence") else ""
                reason_row = (
                    f"<p style='margin:4px 0 0;font-size:12px;color:#374151'>{pc.get('reason', '')}</p>"
                ) if pc.get("reason") else ""
                cards += f"""
                <div style="border-left:3px solid #16a34a;background:#f0fdf4;border-radius:4px;padding:10px 14px;margin-bottom:10px">
                  <p style="margin:0;font-size:12px;font-weight:600;color:#166534">Kontrol {idx}: {pc.get('check_title', '-')}</p>
                  <p style="margin:2px 0 0;font-size:11px;font-family:monospace;color:#6b7280">{pc.get('file_path', '')}</p>
                  {evidence_row}
                  {reason_row}
                </div>"""
            passed_checks_section = f"<h3>Başarıyla Geçen Kontroller ({len(passed_checks)})</h3>{cards}"

        # ── Kalan / Duzeltilmesi Gereken Kisimlar ────────────────────────────
        if findings:
            kalan_items = ""
            for idx, f in enumerate(findings, 1):
                sev = (f.severity or "info").lower()
                file_line = f.file_path or "—"
                if f.line_number:
                    file_line += f":{f.line_number}"
                issue_row = (
                    f"<p class='finding-label'>Sorun</p>"
                    f"<p class='finding-value'>{f.issue}</p>"
                ) if f.issue else ""
                beklenen_row = (
                    f"<p class='finding-label'>Beklenen</p>"
                    f"<p class='finding-value'>{f.suggestion}</p>"
                ) if f.suggestion else ""
                etki_row = (
                    f"<p class='finding-label'>Etki</p>"
                    f"<p class='finding-value'>{f.explanation}</p>"
                ) if f.explanation else ""
                kalan_items += f"""
                <div style="border:1px solid #e5e7eb;border-radius:6px;padding:10px 14px;margin-bottom:8px">
                  <div style="font-family:monospace;font-size:11px;color:#6b7280;margin-bottom:6px">
                    {idx}. {file_line} &nbsp;{_badge(sev.upper())}
                  </div>
                  {issue_row}
                  {beklenen_row}
                  {etki_row}
                </div>"""
            kalan_section = f"<h3>Kalan / Düzeltilmesi Gereken Kısımlar</h3>{kalan_items}"
        else:
            kalan_section = (
                "<h3>Kalan / Düzeltilmesi Gereken Kısımlar</h3>"
                "<p style='color:#16a34a;font-size:13px'>"
                "Engelleyici veya düzeltme gerektiren bir bulgu tespit edilmedi.</p>"
            )

        # ── Bulgular (kart formatı) ───────────────────────────────────────────
        if findings:
            cards = ""
            for idx, f in enumerate(findings, 1):
                sev = (f.severity or "info").lower()
                cat = (f.category or "other")

                file_line = f.file_path or "—"
                if f.line_number:
                    file_line += f" &nbsp;·&nbsp; Satır: {f.line_number}"

                rule_row = ""
                if f.rule_title:
                    rule_row = f"""
                    <p class="finding-label">Kural</p>
                    <p class="finding-value">{f.rule_title}</p>"""

                snippet_row = ""
                if f.code_snippet:
                    snippet_row = f"""
                    <p class="finding-label">Kod</p>
                    <pre>{f.code_snippet}</pre>"""

                exp_row = ""
                if f.explanation:
                    exp_row = f"""
                    <p class="finding-label">Açıklama</p>
                    <p class="finding-value">{f.explanation}</p>"""

                cards += f"""
                <div class="finding-card">
                  <div class="finding-header">
                    <strong>Bulgu {idx}</strong>
                    {_badge(sev.upper())}
                    {_badge(cat)}
                  </div>
                  <div class="finding-body">
                    <p class="finding-file">{file_line}</p>

                    <p class="finding-label">Sorun</p>
                    <p class="finding-value">{f.issue or "—"}</p>

                    {exp_row}

                    <p class="finding-label">Öneri</p>
                    <p class="finding-value">{f.suggestion or "—"}</p>

                    {snippet_row}
                    {rule_row}
                  </div>
                </div>"""
            findings_section = f"<h3>Bulgular ({len(findings)})</h3>{cards}"
        else:
            findings_section = (
                "<h3>Bulgular</h3>"
                "<p style='color:#6b7280;font-style:italic'>Herhangi bir bulgu tespit edilmedi.</p>"
            )

        # ── İyileştirme önerileri ─────────────────────────────────────────────
        improvements_section = ""
        if improvements:
            imp_cards = ""
            for imp in improvements[:15]:
                imp_file = imp.get("file_path") or ""
                imp_title = imp.get("title") or "—"
                imp_desc  = imp.get("description") or ""
                imp_sug   = imp.get("suggestion") or "—"
                file_row  = f'<p style="font-family:monospace;font-size:11px;color:#6b7280;margin:0 0 6px">{imp_file}</p>' if imp_file else ""
                desc_row  = f'<p style="font-size:13px;color:#374151;margin:4px 0">{imp_desc}</p>' if imp_desc else ""
                imp_cards += f"""
                <div class="imp-card">
                  {file_row}
                  <p style="font-weight:600;font-size:13px;color:#4338ca;margin:0 0 4px">{imp_title}</p>
                  {desc_row}
                  <p style="font-size:13px;color:#374151;margin:4px 0"><strong>Öneri:</strong> {imp_sug}</p>
                </div>"""
            improvements_section = f"<h3>İyileştirme Önerileri ({len(improvements)})</h3>{imp_cards}"

        # ── Sonraki adım mesajı ───────────────────────────────────────────────
        if passed:
            next_step = """
              <div style="margin-top:20px;padding:12px 16px;background:#f0fdf4;
                          border-left:4px solid #16a34a;border-radius:4px">
                <p style="margin:0;font-size:13px;color:#166534">
                  ✅ İnceleme <strong>onaylandı</strong>.
                  Gate Durumu: <strong>PASSED</strong>.
                  Test yapılandırması mevcutsa fonksiyonel test aşaması otomatik olarak başlayacaktır.
                </p>
              </div>"""
        else:
            revert_status_val   = getattr(review_run, "revert_status", "required")
            revert_pr_url       = getattr(review_run, "revert_pr_url", None)
            revert_error_msg    = getattr(review_run, "revert_error_message", None)
            reverted_at         = getattr(review_run, "reverted_at", None)

            _REVERT_LABELS = {
                "not_required":             ("GEREKLİ DEĞİL",                           "#16a34a"),
                "required":                 ("⚠ GEREKLİ — Pull request event gerekli",  "#f97316"),
                "started":                  ("⏳ BAŞLADI",                               "#6366f1"),
                "revert_pr_created":        ("🔀 REVERT PR OLUŞTURULDU",                 "#6366f1"),
                "revert_auto_merge_started":("⏳ OTOMATİK MERGE BAŞLADI",                "#6366f1"),
                "reverted":                 ("✅ OTOMATİK GERİ ALINDI",                  "#16a34a"),
                "revert_conflict":          ("⚠ ÇAKIŞMA — MANUEL MÜDAHALE GEREKLİ",    "#dc2626"),
                "revert_failed":            ("❌ BAŞARISIZ — MANUEL MÜDAHALE GEREKLİ",  "#dc2626"),
            }
            rs_label, rs_color = _REVERT_LABELS.get(revert_status_val, ("⚠ GEREKLİ", "#f97316"))

            revert_pr_row = (
                f'<tr><td style="color:#6b7280;padding:3px 0">Revert PR:</td>'
                f'<td><a href="{revert_pr_url}" style="color:#1d4ed8;text-decoration:underline">'
                f'{revert_pr_url}</a></td></tr>'
            ) if revert_pr_url else ""

            revert_error_row = (
                f'<tr><td style="color:#6b7280;padding:3px 0;vertical-align:top">Revert Hatası:</td>'
                f'<td style="color:#dc2626;font-size:12px">{revert_error_msg}</td></tr>'
            ) if revert_error_msg else ""

            reverted_at_row = (
                f'<tr><td style="color:#6b7280;padding:3px 0">Geri Alınma Zamanı:</td>'
                f'<td style="color:#16a34a;font-weight:600">{reverted_at}</td></tr>'
            ) if reverted_at else ""

            # Trailing sentence depends on whether revert succeeded
            if revert_status_val == "reverted":
                revert_notice = (
                    "RevertAgent revert PR'ı oluşturdu ve <strong>otomatik olarak merge etti</strong>. "
                    "Başarısız merge <strong>geri alındı</strong>. "
                    "Revert PR yukarıdaki URL üzerinden incelenebilir."
                )
            elif revert_status_val == "revert_pr_created":
                revert_notice = (
                    "RevertAgent bir <strong>revert PR oluşturdu</strong>. "
                    "PR'ı merge ederek değişiklikleri geri alabilirsiniz. "
                    "<strong>AUTO_REVERT_MODE=create_revert_pr</strong> olduğu için otomatik merge yapılmadı."
                )
            elif revert_status_val == "required":
                revert_notice = (
                    "RevertAgent pull request bilgisini çözümleyemedi. "
                    "Otomatik revert için GitHub webhook ayarlarında "
                    "<strong>Pull requests</strong> event'i de aktif edilmelidir "
                    "(Settings → Webhooks → Edit → Pull requests). "
                    "Başarısız merge hâlâ sprint branch'inde mevcut olabilir — "
                    "lütfen manuel olarak revert edin."
                )
            elif revert_status_val in ("revert_failed", "revert_conflict"):
                sebep = revert_error_msg or "Bilinmeyen hata"
                revert_notice = (
                    "Revert PR oluşturuldu ancak <strong>otomatik merge edilemedi</strong>. "
                    f"<strong>Sebep:</strong> {sebep} "
                    "Lütfen branch'ı manuel olarak revert edin veya "
                    "GitHub token yetkilerini kontrol edin "
                    "(gerekli: Contents Read/Write, Pull Requests Read/Write, Metadata Read). "
                    "Başarısız merge hâlâ hedef branch'te mevcut olabilir."
                )
            else:
                revert_notice = (
                    "RevertAgent tetiklendi. Revert işlemi için lütfen ekibinizle iletişime geçin."
                )

            next_step = f"""
              <div style="margin-top:20px;padding:14px 16px;background:#fef2f2;
                          border-left:4px solid #dc2626;border-radius:4px">
                <p style="margin:0 0 10px;font-size:13px;font-weight:700;color:#7f1d1d">
                  🚫 MERGE BLOCKED — İnceleme reddedildi, pipeline durduruldu.
                </p>
                <table style="font-size:12px;width:100%;border-collapse:collapse">
                  <tr><td style="color:#6b7280;width:200px;padding:3px 0">Karar:</td><td style="color:#991b1b;font-weight:600">❌ REDDEDİLDİ</td></tr>
                  <tr><td style="color:#6b7280;padding:3px 0">Gate Durumu:</td><td style="color:#dc2626;font-weight:600">🚫 ENGELLENDİ</td></tr>
                  <tr><td style="color:#6b7280;padding:3px 0">Fonksiyonel Test:</td><td style="color:#dc2626;font-weight:600">⏭ ATLANILDI</td></tr>
                  <tr><td style="color:#6b7280;padding:3px 0">Promosyon:</td><td style="color:#dc2626;font-weight:600">🚫 ENGELLENDİ</td></tr>
                  <tr><td style="color:#6b7280;padding:3px 0">Revert Durumu:</td>
                      <td style="color:{rs_color};font-weight:600">{rs_label}</td></tr>
                  {revert_pr_row}
                  {reverted_at_row}
                  {revert_error_row}
                </table>
                <p style="margin:12px 0 0;font-size:13px;color:#991b1b">
                  Bu merge CodeReviewAgent tarafından reddedildiği için pipeline durduruldu.
                  Functional test aşaması çalıştırılmadı ve DEV/TEST promotion süreci engellendi.
                  {revert_notice}
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
    <h3>Detaylar</h3>
    <table class="meta">{meta}</table>

    <h3>Özet</h3>
    <p>{review_run.report_summary or "Özet bilgisi mevcut değil."}</p>

    <h3>Karar Gerekçesi</h3>
    <p>{review_run.decision_reason or "—"}</p>

    {file_assess_section}
    {passed_checks_section}
    {kalan_section}

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
        result_text = "✅ BAŞARILI" if result == "success" else "❌ BAŞARISIZ"

        meta = "\n".join(f"""
          <tr>
            <td>{label}</td>
            <td style="color:#111827;font-weight:500">{value}</td>
          </tr>""" for label, value in [
            ("Task",               test_run.task_key    or "—"),
            ("Sprint",             test_run.sprint_name or "—"),
            ("Toplam Test",        str(test_run.total_tests)),
            ("Başarılı",           f'<span style="color:#16a34a;font-weight:700">{test_run.passed_tests}</span>'),
            ("Başarısız",          f'<span style="color:#dc2626;font-weight:700">{test_run.failed_tests}</span>'),
        ])

        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>{_BASE_STYLE}</style></head>
<body>
<div class="wrap">
  <div class="hdr" style="background:{hdr_color}">
    <h2 style="color:#fff">Fonksiyonel Testler — {result_text}</h2>
    <p style="color:rgba(255,255,255,.85);margin:0;font-size:13px">
      {test_run.task_key or "N/A"} &middot; {test_run.sprint_name or "N/A"}
    </p>
  </div>
  <div class="body">
    <h3>Detaylar</h3>
    <table class="meta">{meta}</table>

    <h3>Özet</h3>
    <p>{test_run.report_summary or "Özet bilgisi mevcut değil."}</p>
  </div>
</div>
</body></html>"""


email_service = EmailService()
