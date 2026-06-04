import logging
from typing import List, Dict, Any, Optional
from app.providers.registry import get_adapter
from app.utils.file_filters import filter_files

log = logging.getLogger(__name__)

_NULL_SHA = "0" * 40   # GitHub sends this for new-branch pushes


def fetch_changed_files(
    provider: str,
    repo_full_name: str,
    before_sha: Optional[str],
    after_sha: Optional[str],
    token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if not before_sha or not after_sha:
        log.warning(f"fetch_changed_files: missing SHA — before={before_sha!r} after={after_sha!r}")
        return []

    if before_sha == _NULL_SHA:
        log.warning(
            "fetch_changed_files: before_sha is all-zeros (new-branch push). "
            "Cannot diff — add 'Pull requests' to your GitHub webhook events so "
            "PR base/head SHAs are used instead."
        )
        return []

    log.info(f"Fetching diff: {repo_full_name}  {before_sha[:8]}...{after_sha[:8]}")
    adapter = get_adapter(provider)
    files = adapter.fetch_changed_files(repo_full_name, before_sha, after_sha, token=token)

    filtered = filter_files(files)
    log.info(f"Diff result: {len(files)} total file(s), {len(filtered)} after filter")
    return filtered


def format_diff_for_prompt(
    files: List[Dict[str, Any]],
    commit_messages: Optional[List[str]] = None,
    max_chars: int = 40_000,
) -> str:
    parts = []
    total = 0

    if commit_messages:
        msgs = "\n".join(f"  - {m}" for m in commit_messages if m)
        header = f"## Commit Messages\n{msgs}\n\n## Changed Files ({len(files)} file(s))\n"
        parts.append(header)
        total += len(header)

    for f in files:
        filename  = f.get("filename", "unknown")
        status    = f.get("status", "modified")
        patch     = f.get("patch", "") or ""
        additions = f.get("additions", 0)
        deletions = f.get("deletions", 0)

        file_header = (
            f"### {filename}  [{status}]  "
            f"+{additions} -{deletions} lines\n"
        )
        block = f"{file_header}```diff\n{patch}\n```\n\n"

        if total + len(block) > max_chars:
            truncated = f"### {filename}  [{status}] — diff truncated (too large)\n\n"
            parts.append(truncated)
            total += len(truncated)
            break

        parts.append(block)
        total += len(block)

    return "".join(parts) if parts else "No diff available."
