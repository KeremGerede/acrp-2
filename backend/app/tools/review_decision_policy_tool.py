from typing import List

BLOCKING_SEVERITIES = {"critical", "high"}


def apply_policy(normalized_report: dict, rules: List = None) -> dict:
    """
    Deterministic policy override:
    1. Any finding with severity critical/high  → result = failed
    2. Any *violated* Review Rule with severity critical/high → result = failed
    3. No findings → result = success
    4. Only warning/info findings → keep LLM result (usually success)
    """
    findings = normalized_report.get("findings", [])
    blocking = [f for f in findings if f.get("severity", "").lower() in BLOCKING_SEVERITIES]

    # Check rule-based override: if a high/critical rule was referenced in a finding
    rule_override = False
    if rules:
        blocking_rule_severities = {r.title.lower() for r in (rules or [])
                                    if r.severity.lower() in BLOCKING_SEVERITIES}
        for f in findings:
            rt = f.get("rule_title", "").lower()
            if rt and rt in blocking_rule_severities:
                rule_override = True
                break

    if blocking or rule_override:
        normalized_report["result"] = "failed"
        if not normalized_report.get("decision_reason"):
            parts = []
            if blocking:
                parts.append(f"{len(blocking)} blocking finding(s) with critical/high severity")
            if rule_override:
                parts.append("high/critical Review Rule violation detected")
            normalized_report["decision_reason"] = "Policy override: " + "; ".join(parts) + "."
    elif not findings:
        normalized_report["result"] = "success"
        if not normalized_report.get("decision_reason"):
            normalized_report["decision_reason"] = "No findings detected. Code looks good."

    normalized_report["blocking_findings_count"] = len(blocking)
    return normalized_report
