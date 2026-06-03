from typing import Optional


def normalize_report(raw: dict) -> dict:
    """Ensure the LLM response conforms to the expected structure."""
    result = raw.get("result", "failed")
    if result not in ("success", "failed"):
        result = "failed"

    risk_level = raw.get("risk_level", "medium")
    if risk_level not in ("low", "medium", "high", "critical"):
        risk_level = "medium"

    findings = []
    for f in raw.get("findings", []):
        findings.append({
            "file_path": str(f.get("file_path", "")),
            "line_number": f.get("line_number"),
            "rule_title": str(f.get("rule_title", "")),
            "category": str(f.get("category", "other")),
            "severity": str(f.get("severity", "warning")),
            "issue": str(f.get("issue", "")),
            "explanation": str(f.get("explanation", "")),
            "suggestion": str(f.get("suggestion", "")),
            "code_snippet": str(f.get("code_snippet", "")) if f.get("code_snippet") else None,
        })

    return {
        "result": result,
        "summary": str(raw.get("summary", "")),
        "risk_level": risk_level,
        "decision_reason": str(raw.get("decision_reason", "")),
        "findings": findings,
    }
