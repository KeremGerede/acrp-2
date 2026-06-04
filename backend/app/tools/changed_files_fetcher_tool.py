import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from app.providers.registry import get_adapter
from app.utils.file_filters import filter_files

log = logging.getLogger(__name__)

_NULL_SHA = "0" * 40


def _normalize_repo_name(repo_full_name: str) -> str:
    """
    GitHub API expects 'owner/repo' but the DB may store a full URL
    like 'https://github.com/owner/repo'. Extract just the path part.
    """
    if not repo_full_name:
        return ""
    if "://" in repo_full_name:
        path = urlparse(repo_full_name).path.strip("/")
        if path.endswith(".git"):
            path = path[:-4]
        log.debug(f"Normalized repo name: {repo_full_name!r} → {path!r}")
        return path
    return repo_full_name


def fetch_changed_files(
    provider: str,
    repo_full_name: str,
    before_sha: Optional[str],
    after_sha: Optional[str],
    token: Optional[str] = None,
    commit_sha: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch changed files using a multi-fallback strategy:
      1. Compare before_sha...after_sha  (most accurate, requires both SHAs)
      2. Fetch merge commit_sha directly (reliable for all merge events)
      3. Fetch after_sha as a commit     (last resort if commit_sha unavailable)
    Each strategy is tried in order; the first non-empty result wins.
    """
    adapter = get_adapter(provider)
    repo_full_name = _normalize_repo_name(repo_full_name)

    def _filter_and_log(files: List[dict], strategy: str) -> List[dict]:
        filtered = filter_files(files)
        log.info(
            f"[{strategy}] {repo_full_name}: "
            f"{len(files)} file(s) from API, {len(filtered)} after filter"
        )
        return filtered

    # ── Strategy 1: compare before...after ──────────────────────────────────
    if (
        before_sha
        and after_sha
        and before_sha != _NULL_SHA
        and after_sha != _NULL_SHA
    ):
        log.info(
            f"Strategy 1 — compare: {before_sha[:8]}...{after_sha[:8]} "
            f"on {repo_full_name}"
        )
        try:
            files = adapter.fetch_changed_files(
                repo_full_name, before_sha, after_sha, token=token
            )
            if files:
                return _filter_and_log(files, "compare")
            log.warning("Strategy 1 returned 0 files — falling back to commit fetch")
        except Exception as exc:
            log.warning(f"Strategy 1 failed: {exc}")
    else:
        log.warning(
            f"Strategy 1 skipped — before_sha={before_sha!r} after_sha={after_sha!r}"
        )

    # ── Strategy 2: fetch merge commit directly ──────────────────────────────
    target_commit = commit_sha or after_sha
    if target_commit and target_commit != _NULL_SHA and hasattr(adapter, "fetch_commit_files"):
        log.info(
            f"Strategy 2 — commit fetch: {target_commit[:8]} on {repo_full_name}"
        )
        try:
            files = adapter.fetch_commit_files(repo_full_name, target_commit, token=token)
            if files:
                return _filter_and_log(files, "commit")
            log.warning("Strategy 2 returned 0 files — no more fallbacks")
        except Exception as exc:
            log.warning(f"Strategy 2 failed: {exc}")

    # ── Strategy 3: after_sha as commit (if different from commit_sha) ───────
    if (
        after_sha
        and after_sha != _NULL_SHA
        and after_sha != target_commit
        and hasattr(adapter, "fetch_commit_files")
    ):
        log.info(
            f"Strategy 3 — after_sha commit fetch: {after_sha[:8]} on {repo_full_name}"
        )
        try:
            files = adapter.fetch_commit_files(repo_full_name, after_sha, token=token)
            if files:
                return _filter_and_log(files, "after_sha_commit")
        except Exception as exc:
            log.warning(f"Strategy 3 failed: {exc}")

    log.warning(
        f"All fetch strategies returned 0 files for {repo_full_name}. "
        f"Check token, repo visibility, and SHA values."
    )
    return []


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
