import datetime
from typing import List

from fpdf import FPDF

_SEV_COLORS = {
    "critical": (220, 38, 38),
    "high":     (234, 88, 12),
    "warning":  (161, 98, 7),
    "info":     (37, 99, 235),
}

_SEV_BG = {
    "critical": (254, 242, 242),
    "high":     (255, 247, 237),
    "warning":  (254, 252, 232),
    "info":     (239, 246, 255),
}

# FPDF uses latin-1; convert Turkish chars to ASCII equivalents
_TR = str.maketrans(
    "çÇğĞıİöÖşŞüÜ",
    "cCgGiIoOsSuU",
)


def _s(text) -> str:
    """Safe string for FPDF: convert to str and transliterate non-latin-1 chars."""
    t = str(text or "").translate(_TR)
    # Replace remaining non-latin-1 characters with '?'
    return t.encode("latin-1", errors="replace").decode("latin-1")


def generate_review_pdf(review_run, findings: List) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    result = review_run.result or "unknown"
    passed = result == "success"

    # ── Header ────────────────────────────────────────────────────────────────
    pdf.set_fill_color(*(22, 163, 74) if passed else (220, 38, 38))
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    verdict = "ONAYLANDI" if passed else "REDDEDILDI"
    pdf.cell(0, 13, f"Code Review Raporu - {verdict}",
             fill=True, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_fill_color(*(16, 120, 56) if passed else (185, 28, 28))
    subtitle = _s(f"{review_run.task_key or 'N/A'}  |  {review_run.sprint_name or 'N/A'}")
    pdf.cell(0, 8, subtitle, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)

    # ── Detaylar ─────────────────────────────────────────────────────────────
    _section_title(pdf, "Detaylar")

    meta_rows = [
        ("Task",                      review_run.task_key or "-"),
        ("Sprint",                    review_run.sprint_name or "-"),
        ("Source Branch",             review_run.source_branch or "-"),
        ("Target Branch",             review_run.target_branch or "-"),
        ("Islemi Yapan",              review_run.actor_username or "-"),
        ("Commit SHA",                (review_run.commit_sha or "-")[:12]),
        ("Risk Seviyesi",             (review_run.risk_level or "-").upper()),
        ("Analiz Edilen Dosya",       str(review_run.total_files_analyzed or 0)),
        ("Toplam Bulgu",              str(review_run.total_findings or 0)),
        ("Engelleyici Bulgu",         str(review_run.blocking_findings_count or 0)),
    ]
    pdf.set_font("Helvetica", "", 10)
    for label, value in meta_rows:
        pdf.set_text_color(107, 114, 128)
        pdf.cell(52, 6, _s(label) + ":", new_x="RIGHT", new_y="TOP")
        pdf.set_text_color(17, 24, 39)
        pdf.cell(0, 6, _s(value), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)

    # ── Ozet ─────────────────────────────────────────────────────────────────
    _section_title(pdf, "Ozet")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(55, 65, 81)
    pdf.multi_cell(0, 6, _s(review_run.report_summary or "Ozet bilgisi mevcut degil."))
    pdf.ln(4)

    # ── Karar Gerekcesi ───────────────────────────────────────────────────────
    if review_run.decision_reason:
        _section_title(pdf, "Karar Gerekcesi")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(55, 65, 81)
        pdf.multi_cell(0, 6, _s(review_run.decision_reason))
        pdf.ln(4)

    # ── Bulgular (blok format) ────────────────────────────────────────────────
    _section_title(pdf, f"Bulgular ({len(findings)})")

    if not findings:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(107, 114, 128)
        pdf.cell(0, 8, "Herhangi bir bulgu tespit edilmedi.", new_x="LMARGIN", new_y="NEXT")
    else:
        for idx, f in enumerate(findings, 1):
            sev = (f.severity or "info").lower()
            cat = (f.category or "other")
            fg_r, fg_g, fg_b = _SEV_COLORS.get(sev, (107, 114, 128))
            bg_r, bg_g, bg_b = _SEV_BG.get(sev, (248, 250, 252))

            # Bulgu başlık bandı
            pdf.set_fill_color(bg_r, bg_g, bg_b)
            pdf.set_text_color(fg_r, fg_g, fg_b)
            pdf.set_font("Helvetica", "B", 10)
            header_text = _s(f"Bulgu {idx}  |  {sev.upper()}  |  {cat}")
            pdf.cell(0, 8, header_text, fill=True, new_x="LMARGIN", new_y="NEXT")

            # Dosya / satır
            file_str = _s(f.file_path or "-")
            if f.line_number:
                file_str += f"  :  Satir {f.line_number}"
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(107, 114, 128)
            pdf.cell(0, 5, file_str, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

            # Sorun
            _field_label(pdf, "Sorun")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(17, 24, 39)
            pdf.multi_cell(0, 6, _s(f.issue or "-"))
            pdf.ln(1)

            # Aciklama
            if f.explanation:
                _field_label(pdf, "Aciklama")
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(55, 65, 81)
                pdf.multi_cell(0, 6, _s(f.explanation))
                pdf.ln(1)

            # Oneri
            if f.suggestion:
                _field_label(pdf, "Oneri")
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(55, 65, 81)
                pdf.multi_cell(0, 6, _s(f.suggestion))
                pdf.ln(1)

            # Kod
            if f.code_snippet:
                _field_label(pdf, "Kod")
                pdf.set_font("Courier", "", 8)
                pdf.set_text_color(55, 65, 81)
                pdf.set_fill_color(248, 250, 252)
                snippet = _s(f.code_snippet)
                # Limit snippet to avoid huge blocks
                if len(snippet) > 400:
                    snippet = snippet[:397] + "..."
                pdf.multi_cell(0, 5, snippet, fill=True)
                pdf.ln(1)

            # Kural
            if f.rule_title:
                pdf.set_font("Helvetica", "I", 9)
                pdf.set_text_color(107, 114, 128)
                pdf.cell(0, 5, _s(f"Kural: {f.rule_title}"), new_x="LMARGIN", new_y="NEXT")

            pdf.ln(5)
            # Ince ayirici
            pdf.set_draw_color(229, 231, 235)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(5)

    # ── Footer ────────────────────────────────────────────────────────────────
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(156, 163, 175)
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    pdf.cell(0, 6, f"ACRP tarafindan olusturuldu  |  {ts}",
             align="C", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())


# ── Yardimci fonksiyonlar ─────────────────────────────────────────────────────

def _section_title(pdf: FPDF, title: str) -> None:
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(17, 24, 39)
    pdf.cell(0, 8, _s(title), new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(209, 213, 219)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)


def _field_label(pdf: FPDF, label: str) -> None:
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(0, 5, label + ":", new_x="LMARGIN", new_y="NEXT")
