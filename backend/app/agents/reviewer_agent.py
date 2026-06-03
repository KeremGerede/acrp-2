import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from app.services.llm_service import llm_service
from app.tools.review_rule_loader_tool import load_rules, format_rules_for_prompt
from app.tools.changed_files_fetcher_tool import format_diff_for_prompt
from app.tools.review_report_normalizer_tool import normalize_report
from app.tools.review_decision_policy_tool import apply_policy
from app.services.agent_step_service import log_step

logger = logging.getLogger(__name__)


REVIEWER_PROMPT = """You are a senior corporate code reviewer. Your task is a thorough code review.

## Configured Review Rules
{rules}

## Changed Files / Diff
{diff}

## Instructions
- Analyze ONLY the changed code shown above
- Apply each enabled review rule strictly
- Consider: security, maintainability, architecture, code quality, performance, testing, and style
- Do NOT invent file names or issues not present in the diff
- Return STRICTLY valid JSON with NO markdown, NO explanation outside the JSON object
- result must be "success" or "failed"
- risk_level must be "low", "medium", "high", or "critical"
- Every finding must include: file_path, severity, category, issue, explanation, suggestion

Return this EXACT JSON structure:
{{
  "result": "success",
  "summary": "Brief overall summary of the code changes and review.",
  "risk_level": "low",
  "decision_reason": "Explanation of why this result was chosen.",
  "findings": [
    {{
      "file_path": "path/to/file.py",
      "line_number": 42,
      "rule_title": "SQL Injection Prevention",
      "category": "security",
      "severity": "critical",
      "issue": "Short description of the problem",
      "explanation": "Why this is a problem",
      "suggestion": "How to fix it",
      "code_snippet": "the problematic line(s)"
    }}
  ]
}}"""


def run_review(
    db: Session,
    tenant_id: int,
    integration_id: int,
    merge_review_run_id: int,
    event_log_id: int,
    changed_files: List[dict],
    actor_username: str = "",
) -> dict:
    # Load rules
    log_step(db, tenant_id, "ReviewerAgent", "review_rule_loader_tool", "load_rules", "completed",
             integration_id=integration_id, merge_review_run_id=merge_review_run_id,
             input_summary=f"tenant_id={tenant_id}", output_summary="Rules loaded")

    rules = load_rules(db, tenant_id, integration_id)
    rules_text = format_rules_for_prompt(rules)
    diff_text = format_diff_for_prompt(changed_files)

    prompt = REVIEWER_PROMPT.format(rules=rules_text, diff=diff_text)

    # Call LLM
    log_step(db, tenant_id, "ReviewerAgent", "llm_service", "call_llm", "running",
             integration_id=integration_id, merge_review_run_id=merge_review_run_id,
             input_summary=f"{len(changed_files)} files, {len(rules)} rules")

    try:
        raw = llm_service.generate_json(prompt)
        if not raw or not isinstance(raw, dict):
            raise ValueError("LLM returned invalid JSON")

        log_step(db, tenant_id, "ReviewerAgent", "llm_service", "call_llm", "completed",
                 integration_id=integration_id, merge_review_run_id=merge_review_run_id,
                 output_summary=f"result={raw.get('result')}, findings={len(raw.get('findings', []))}")
    except Exception as e:
        logger.error(f"ReviewerAgent LLM call failed: {e}")
        log_step(db, tenant_id, "ReviewerAgent", "llm_service", "call_llm", "failed",
                 integration_id=integration_id, merge_review_run_id=merge_review_run_id,
                 error_message=str(e))
        return {
            "result": "failed",
            "summary": f"Review failed due to LLM error: {e}",
            "risk_level": "high",
            "decision_reason": "System error during review.",
            "findings": [],
            "blocking_findings_count": 0,
        }

    normalized = normalize_report(raw)
    final = apply_policy(normalized)

    log_step(db, tenant_id, "ReviewerAgent", "review_decision_policy_tool", "apply_policy", "completed",
             integration_id=integration_id, merge_review_run_id=merge_review_run_id,
             output_summary=f"final_result={final['result']}, blocking={final.get('blocking_findings_count', 0)}")

    return final
