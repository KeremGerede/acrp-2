"""
Branch-based automatic sprint and task detection.

Works with any naming convention — no rigid format required.

Examples that all work:
  task/sprint-3/TASK-128-login  →  sprint/sprint-3
  sprint1/task-7                →  sprint1/task-6
  feature/FEAT-42-payment       →  sprint-2
  fix/BUG-7                     →  sprint/1
"""

import re
from typing import Optional, Tuple

# Sprint identifiers: sprint-1 / sprint1 / sp-1 / sp1
_SPRINT_RE = re.compile(r'(?:sprint|sp)[-_]?(\d+)', re.IGNORECASE)

# JIRA-style uppercase task key: TASK-1, FEAT-123, BUG-42, STORY-5
_JIRA_KEY_RE = re.compile(r'\b([A-Z]{2,10}-\d+)\b')

# Lowercase fallback: task-7, task_7, fix-12, feature-3
_WORD_NUM_RE = re.compile(
    r'\b(task|feat|feature|bug|fix|story|issue|ticket|hotfix|chore)[-_](\d+)\b',
    re.IGNORECASE,
)


def extract_sprint_name(branch: str) -> Optional[str]:
    """Find a sprint identifier anywhere in the branch name."""
    m = _SPRINT_RE.search(branch)
    if m:
        return f"sprint-{m.group(1)}"
    return None


def extract_task_key(branch: str) -> Optional[str]:
    """
    Find a task key anywhere in the branch name.
    Prefers uppercase JIRA-style (TASK-1), falls back to word-number (task-7).
    """
    m = _JIRA_KEY_RE.search(branch)
    if m:
        return m.group(1)

    m = _WORD_NUM_RE.search(branch)
    if m:
        prefix = m.group(1).upper()
        num = m.group(2)
        return f"{prefix}-{num}"

    return None


def parse_sprint_and_task(
    source_branch: str,
    target_branch: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract (sprint_name, task_key) from a pair of branch names.

    Strategy:
    - sprint_name  → target branch first (it is the stable base), fall back to source
    - task_key     → source branch (it is the feature/task branch)
    """
    sprint_name = extract_sprint_name(target_branch) or extract_sprint_name(source_branch)
    task_key = extract_task_key(source_branch)
    return sprint_name, task_key
