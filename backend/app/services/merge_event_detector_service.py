"""
Event type detection from normalized SCM event + integration config.

Detection order:
1. Configured fnmatch patterns (explicit — highest priority)
2. Smart fallback: if is_merge_event=True and target is not a known
   terminal branch (dev/test/main/master), treat as task_to_sprint_merge
"""

from fnmatch import fnmatch
from app.providers.normalized_events import NormalizedSCMEvent, EventType

# Branches that are NEVER the target of a task→sprint merge
_TERMINAL_BRANCHES = {"main", "master", "development", "develop", "dev", "test", "staging", "production", "prod"}


def detect_event_type(event: NormalizedSCMEvent, integration) -> EventType:
    source = event.source_branch or ""
    target = event.target_branch or event.branch or ""

    task_pattern = integration.task_branch_pattern or "task/*"
    sprint_pattern = integration.sprint_branch_pattern or "sprint/*"
    dev_branch = (integration.development_branch or "development").lower()
    test_branch = (integration.test_branch or "test").lower()
    target_lower = target.lower()

    if source and target:
        # --- Explicit pattern matching ---
        if fnmatch(source, task_pattern) and fnmatch(target, sprint_pattern):
            return EventType.task_to_sprint_merge

        if fnmatch(source, sprint_pattern) and target_lower == dev_branch:
            return EventType.sprint_to_development_event

        if source.lower() == dev_branch and target_lower == test_branch:
            return EventType.development_test_event

        # --- Smart fallback ---
        # If this is a confirmed merge event (PR merge or merge commit) and the
        # target is not a well-known terminal branch, assume task→sprint.
        terminal = _TERMINAL_BRANCHES | {dev_branch, test_branch}
        if event.is_merge_event and target_lower not in terminal:
            return EventType.task_to_sprint_merge

    return EventType.push
