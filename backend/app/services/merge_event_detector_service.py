from fnmatch import fnmatch
from app.providers.normalized_events import NormalizedSCMEvent, EventType


def detect_event_type(event: NormalizedSCMEvent, integration) -> EventType:
    source = event.source_branch or ""
    target = event.target_branch or event.branch or ""

    task_pattern = integration.task_branch_pattern or "task/*"
    sprint_pattern = integration.sprint_branch_pattern or "sprint/*"
    dev_branch = integration.development_branch or "development"
    test_branch = integration.test_branch or "test"

    if source and target:
        if fnmatch(source, task_pattern) and fnmatch(target, sprint_pattern):
            return EventType.task_to_sprint_merge
        if fnmatch(source, sprint_pattern) and target == dev_branch:
            return EventType.sprint_to_development_event
        if source == dev_branch and target == test_branch:
            return EventType.development_test_event

    # Push-only event: just check the branch
    if fnmatch(target, task_pattern) or fnmatch(source, task_pattern):
        return EventType.push

    return EventType.push
