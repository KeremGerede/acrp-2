from typing import Optional


_VALID_RESULTS = {"success", "failed"}
_VALID_RISK = {"low", "medium", "high", "critical"}
_VALID_SEVERITY = {"info", "warning", "high", "critical"}
_VALID_CATEGORY = {
    "security", "code_quality", "architecture", "testing",
    "performance", "maintainability", "style", "other",
}


def normalize_report(raw: dict) -> dict:
    result = raw.get("result", "failed")
    if result not in _VALID_RESULTS:
        result = "failed"

    risk_level = raw.get("risk_level", "medium")
    if risk_level not in _VALID_RISK:
        risk_level = "medium"

    findings = []
    for f in raw.get("findings", []):
        sev = str(f.get("severity", "warning")).lower()
        cat = str(f.get("category", "other")).lower()
        findings.append({
            "file_path": str(f.get("file_path", "")),
            "line_number": f.get("line_number") if isinstance(f.get("line_number"), int) else None,
            "rule_id": f.get("rule_id"),          # populated by reviewer_agent after rule mapping
            "rule_title": str(f.get("rule_title", "")),
            "category": cat if cat in _VALID_CATEGORY else "other",
            "severity": sev if sev in _VALID_SEVERITY else "warning",
            "issue": str(f.get("issue", "")),
            "explanation": str(f.get("explanation", "")),
            "suggestion": str(f.get("suggestion", "")),
            "code_snippet": str(f.get("code_snippet", "")) if f.get("code_snippet") else None,
        })

    improvements = []
    for imp in raw.get("improvements", []):
        if not isinstance(imp, dict):
            continue
        improvements.append({
            "file_path": str(imp.get("file_path", "")),
            "title": str(imp.get("title", "")),
            "description": str(imp.get("description", "")),
            "suggestion": str(imp.get("suggestion", "")),
        })

    passed_checks = []
    for pc in raw.get("passed_checks", []):
        if not isinstance(pc, dict):
            continue
        passed_checks.append({
            "file_path": str(pc.get("file_path", "")),
            "check_title": str(pc.get("check_title", "")),
            "evidence": str(pc.get("evidence", "")),
            "reason": str(pc.get("reason", "")),
        })

    failed_checks = []
    for fc in raw.get("failed_checks", []):
        if not isinstance(fc, dict):
            continue
        sev = str(fc.get("severity", "warning")).lower()
        fi = fc.get("related_finding_index")
        failed_checks.append({
            "file_path": str(fc.get("file_path", "")),
            "check_title": str(fc.get("check_title", "")),
            "severity": sev if sev in _VALID_SEVERITY else "warning",
            "reason": str(fc.get("reason", "")),
            "related_finding_index": fi if isinstance(fi, int) else None,
        })

    _VALID_FA_STATUS = {"passed", "passed_with_warnings", "failed"}
    file_assessments = []
    for fa in raw.get("file_assessments", []):
        if not isinstance(fa, dict):
            continue
        status = str(fa.get("status", "passed")).lower()
        passed_pts = fa.get("passed_points", [])
        remaining_pts = fa.get("remaining_points", [])
        file_assessments.append({
            "file_path": str(fa.get("file_path", "")),
            "status": status if status in _VALID_FA_STATUS else "passed",
            "passed_points": [str(p) for p in passed_pts] if isinstance(passed_pts, list) else [],
            "remaining_points": [str(p) for p in remaining_pts] if isinstance(remaining_pts, list) else [],
        })

    return {
        "result": result,
        "summary": str(raw.get("summary", "")),
        "risk_level": risk_level,
        "decision_reason": str(raw.get("decision_reason", "")),
        "findings": findings,
        "improvements": improvements,
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "file_assessments": file_assessments,
    }
