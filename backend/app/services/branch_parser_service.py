import re
from typing import Optional, Tuple


def parse_sprint_and_task(source_branch: str, target_branch: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract sprint_name and task_key from branch names.

    Examples:
      source=task/sprint-3/TASK-128-login-validation, target=sprint/sprint-3
        => sprint_name="sprint-3", task_key="TASK-128"

      source=sprint/sprint-3, target=development
        => sprint_name="sprint-3", task_key=None
    """
    sprint_name: Optional[str] = None
    task_key: Optional[str] = None

    # Try to extract task_key from source branch: task/{sprint}/{TASK-123}-description
    task_match = re.match(r"task/([^/]+)/([A-Z]+-\d+)(?:[-_].*)?$", source_branch or "")
    if task_match:
        sprint_name = task_match.group(1)
        task_key = task_match.group(2)
        return sprint_name, task_key

    # Try source as sprint branch
    sprint_match = re.match(r"sprint/(.+)", source_branch or "")
    if sprint_match:
        sprint_name = sprint_match.group(1)
        return sprint_name, None

    # Try to extract sprint from target branch
    sprint_match = re.match(r"sprint/(.+)", target_branch or "")
    if sprint_match:
        sprint_name = sprint_match.group(1)
        return sprint_name, None

    return None, None


def extract_sprint_from_branch(branch: str) -> Optional[str]:
    m = re.match(r"sprint/(.+)", branch or "")
    return m.group(1) if m else None
