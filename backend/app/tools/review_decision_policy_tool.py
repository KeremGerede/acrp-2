from typing import List


BLOCKING_SEVERITIES = {"critical", "high"}


def apply_policy(normalized_report: dict) -> dict:
    """
    Override LLM result with deterministic policy:
    - Any critical or high finding => result = failed
    - Otherwise keep LLM result, but default to success if no findings
    """
    findings = normalized_report.get("findings", [])
    blocking = [f for f in findings if f.get("severity", "").lower() in BLOCKING_SEVERITIES]

    if blocking:
        normalized_report["result"] = "failed"
        if not normalized_report.get("decision_reason"):
            normalized_report["decision_reason"] = (
                f"Policy override: {len(blocking)} blocking finding(s) with critical/high severity."
            )
    elif not findings:
        normalized_report["result"] = "success"

    normalized_report["blocking_findings_count"] = len(blocking)
    return normalized_report
