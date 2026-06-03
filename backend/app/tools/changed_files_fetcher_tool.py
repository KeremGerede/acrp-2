from typing import List, Dict, Any, Optional
from app.providers.registry import get_adapter
from app.utils.file_filters import filter_files


def fetch_changed_files(
    provider: str,
    repo_full_name: str,
    before_sha: Optional[str],
    after_sha: Optional[str],
    token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if not before_sha or not after_sha:
        return []
    adapter = get_adapter(provider)
    files = adapter.fetch_changed_files(repo_full_name, before_sha, after_sha, token=token)
    return filter_files(files)


def format_diff_for_prompt(files: List[Dict[str, Any]], max_chars: int = 40000) -> str:
    parts = []
    total = 0
    for f in files:
        filename = f.get("filename", "unknown")
        status = f.get("status", "modified")
        patch = f.get("patch", "")
        entry = f"### {filename} ({status})\n```\n{patch}\n```\n"
        if total + len(entry) > max_chars:
            parts.append(f"### {filename} — truncated (diff too large)\n")
            break
        parts.append(entry)
        total += len(entry)
    return "\n".join(parts) if parts else "No diff available."
