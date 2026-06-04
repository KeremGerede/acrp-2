import json
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.services.llm_service import llm_service
from app.tools.review_rule_loader_tool import load_rules, format_rules_for_prompt
from app.tools.changed_files_fetcher_tool import format_diff_for_prompt
from app.tools.review_report_normalizer_tool import normalize_report
from app.tools.review_decision_policy_tool import apply_policy
from app.services.agent_step_service import log_step

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

REVIEWER_PROMPT = """\
You are a senior software engineer performing a thorough, professional code review \
for a production codebase. Your goal is to find real issues that matter, not \
nitpicks.

## Merge Event Context
- Repository  : {repo_full_name}
- Sprint      : {sprint_name}
- Task        : {task_key}
- Source branch (merged FROM): {source_branch}
- Target branch (merged INTO): {target_branch}
- Developer   : {actor_username}

## Active Review Rules  (YOU MUST CHECK EACH ONE)
{rules}

## Changed Files / Diff
{diff}

## Review Checklist
Analyze ONLY the code visible in the diff above. Do not invent issues.

For every changed file, check:
1. BUGS           — logic errors, wrong conditions, off-by-one, null/undefined access,
                    unreachable code, wrong variable used
2. SECURITY       — SQL injection, XSS, command injection, hardcoded secrets / API keys /
                    passwords, improper authentication or authorization, insecure data
                    handling, path traversal, SSRF, missing input sanitization
3. MISSING LOGIC  — TODO / FIXME / pass / NotImplemented left in production code,
                    incomplete error handling, missing edge case handling, missing
                    validation of external inputs
4. CODE QUALITY   — duplicated code, dead code, overly complex functions (>50 lines),
                    misleading variable names, magic numbers
5. ARCHITECTURE   — violation of separation of concerns, business logic in wrong layer,
                    tight coupling, missing abstraction where clearly needed
6. PERFORMANCE    — obvious N+1 query patterns, missing index on frequently filtered
                    column, large data loaded into memory unnecessarily
7. TESTING        — critical path with no test coverage (if test files are in the diff)
8. MAINTAINABILITY — undocumented non-obvious logic, deeply nested conditions that
                    could be simplified

For each finding, check whether it violates one of the configured Review Rules above
and reference that rule title exactly.

## Output Requirements
Return ONLY valid JSON — no markdown fences, no explanation outside the JSON.

{{
  "result": "success",
  "summary": "2-4 sentence summary of what changed and overall quality assessment.",
  "risk_level": "low",
  "decision_reason": "Concise explanation of the final decision.",
  "findings": [
    {{
      "file_path": "path/to/file.py",
      "line_number": 42,
      "rule_title": "Exact title of violated Review Rule, or empty string if none",
      "category": "security|code_quality|architecture|testing|performance|maintainability|style|other",
      "severity": "info|warning|high|critical",
      "issue": "One sentence describing the problem.",
      "explanation": "Why this is a problem and what its impact is.",
      "suggestion": "Concrete, actionable fix.",
      "code_snippet": "The exact problematic line(s) from the diff."
    }}
  ],
  "improvements": [
    {{
      "file_path": "path/to/file.py",
      "title": "Short improvement title",
      "description": "What could be improved and why it would help.",
      "suggestion": "How to implement it."
    }}
  ]
}}

## Decision Rules (apply these yourself before setting result)
- result = "failed"  if ANY finding has severity "critical" or "high"
- result = "failed"  if ANY active Review Rule with severity "critical" or "high" is violated
- result = "success" if all findings are "warning" or "info" only
- result = "success" if there are no findings
- risk_level = "critical" if any critical finding exists
- risk_level = "high"     if any high finding exists (and no critical)
- risk_level = "medium"   if only warning findings exist
- risk_level = "low"      if only info findings or no findings

## Language Requirement  (IMPORTANT)
Write ALL explanatory text in Turkish.
This includes: summary, decision_reason, issue, explanation, suggestion, description, title fields.
Keep technical software terms in English as-is:
  API, endpoint, controller, service, repository, DTO, webhook, commit, branch, merge,
  pull request, dependency injection, SQL injection, XSS, SSRF, JWT, token, HTTP, REST,
  null, undefined, try/catch, async/await, middleware, decorator, interface, class, method.
Example good output:
  issue: "AddCar endpoint'i basarili kayit sonrasinda HTTP 200 donmektedir."
  explanation: "REST API tasariminda yeni kaynak olusturuldugunda HTTP 201 Created donulmesi daha dogrudur."
  suggestion: "Ok(...) yerine CreatedAtAction(...) veya StatusCode(201) kullanilabilir."
"""


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_review(
    db: Session,
    tenant_id: int,
    integration_id: int,
    merge_review_run_id: int,
    event_log_id: int,
    changed_files: List[dict],
    actor_username: str = "",
    commit_messages: Optional[List[str]] = None,
    sprint_name: str = "",
    task_key: str = "",
    source_branch: str = "",
    target_branch: str = "",
    repository_full_name: str = "",
) -> dict:
    commit_messages = commit_messages or []

    # ── Step 1: Load review rules ────────────────────────────────────────────
    log_step(
        db, tenant_id, "ReviewerAgent", "review_rule_loader_tool",
        "review_rules_loaded", "running",
        integration_id=integration_id,
        merge_review_run_id=merge_review_run_id,
        input_summary=f"tenant_id={tenant_id} integration_id={integration_id}",
    )

    rules = load_rules(db, tenant_id, integration_id)
    rules_by_title = {r.title.lower(): r.id for r in rules}
    rules_text = format_rules_for_prompt(rules)

    log_step(
        db, tenant_id, "ReviewerAgent", "review_rule_loader_tool",
        "review_rules_loaded", "completed",
        integration_id=integration_id,
        merge_review_run_id=merge_review_run_id,
        output_summary=f"{len(rules)} active rule(s) loaded",
    )

    # ── Step 2: Build diff text ──────────────────────────────────────────────
    diff_text = format_diff_for_prompt(changed_files, commit_messages=commit_messages)

    log_step(
        db, tenant_id, "ReviewerAgent", "changed_files_fetcher_tool",
        "review_context_created", "completed",
        integration_id=integration_id,
        merge_review_run_id=merge_review_run_id,
        input_summary=f"{len(changed_files)} file(s)",
        output_summary=f"diff_chars={len(diff_text)}",
    )

    # ── Step 3: Build and call LLM ───────────────────────────────────────────
    prompt = REVIEWER_PROMPT.format(
        repo_full_name=repository_full_name or "N/A",
        sprint_name=sprint_name or "N/A",
        task_key=task_key or "N/A",
        source_branch=source_branch or "N/A",
        target_branch=target_branch or "N/A",
        actor_username=actor_username or "N/A",
        rules=rules_text,
        diff=diff_text,
    )

    log_step(
        db, tenant_id, "ReviewerAgent", "llm_service",
        "llm_review_started", "running",
        integration_id=integration_id,
        merge_review_run_id=merge_review_run_id,
        input_summary=f"{len(changed_files)} files, {len(rules)} rules, prompt_chars={len(prompt)}",
    )

    try:
        raw = llm_service.generate_json(prompt)
        if not raw or not isinstance(raw, dict):
            raise ValueError("LLM returned invalid or empty JSON")
    except Exception as exc:
        logger.error(f"ReviewerAgent LLM call failed: {exc}")
        log_step(
            db, tenant_id, "ReviewerAgent", "llm_service",
            "llm_review_completed", "failed",
            integration_id=integration_id,
            merge_review_run_id=merge_review_run_id,
            error_message=str(exc),
        )
        return _error_result(str(exc))

    log_step(
        db, tenant_id, "ReviewerAgent", "llm_service",
        "llm_review_completed", "completed",
        integration_id=integration_id,
        merge_review_run_id=merge_review_run_id,
        output_summary=(
            f"result={raw.get('result')}, "
            f"findings={len(raw.get('findings', []))}, "
            f"improvements={len(raw.get('improvements', []))}"
        ),
    )

    # ── Step 4: Normalize + policy ───────────────────────────────────────────
    normalized = normalize_report(raw)

    # Map rule titles back to rule IDs (deterministic, no LLM trust needed)
    for finding in normalized["findings"]:
        title_key = finding.get("rule_title", "").lower()
        finding["rule_id"] = rules_by_title.get(title_key)

    final = apply_policy(normalized, rules)

    log_step(
        db, tenant_id, "ReviewerAgent", "review_decision_policy_tool",
        "decision_policy_applied", "completed",
        integration_id=integration_id,
        merge_review_run_id=merge_review_run_id,
        output_summary=(
            f"final_result={final['result']}, "
            f"blocking={final.get('blocking_findings_count', 0)}, "
            f"risk={final.get('risk_level')}"
        ),
    )

    return final


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _error_result(reason: str) -> dict:
    return {
        "result": "failed",
        "summary": f"Review could not be completed due to a system error: {reason}",
        "risk_level": "high",
        "decision_reason": "System error during LLM review call.",
        "findings": [],
        "improvements": [],
        "blocking_findings_count": 0,
    }
