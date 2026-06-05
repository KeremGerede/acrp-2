import json
import logging
import requests
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.models.merge_review import MergeReviewRun
from app.core.config import settings

logger = logging.getLogger(__name__)

_GITHUB_API = "https://api.github.com"
_GITHUB_GQL = "https://api.github.com/graphql"

_REVERT_PR_MUTATION = """
mutation RevertPullRequest($pullRequestId: ID!, $title: String, $body: String) {
  revertPullRequest(input: {
    pullRequestId: $pullRequestId
    title: $title
    body: $body
  }) {
    revertPullRequest {
      number
      url
      headRefName
    }
  }
}
"""


class RevertService:

    def _auth_headers(self, token: Optional[str]) -> dict:
        use_token = token or settings.GITHUB_TOKEN
        h = {"Accept": "application/vnd.github+json"}
        if use_token:
            h["Authorization"] = f"Bearer {use_token}"
        else:
            logger.warning("[RevertService] No GitHub token — API calls may fail on private repos")
        return h

    # ── PR info extraction ─────────────────────────────────────────────────────

    def extract_pr_info_from_event(self, event_log) -> Tuple[Optional[str], Optional[int]]:
        """
        Extract (pr_node_id, pr_number) from the stored raw webhook payload.
        Works for GitHub pull_request merge events.
        Returns (None, None) if the event is a push (no pull_request key) or payload is missing.
        """
        try:
            raw = json.loads(event_log.raw_payload_json or "{}")
            pr = raw.get("pull_request", {})
            node_id = pr.get("node_id") or None
            number = pr.get("number") or None
            return node_id, number
        except Exception as exc:
            logger.warning(f"[RevertService] Could not parse raw payload: {exc}")
            return None, None

    def find_pr_by_commit(
        self,
        repo_full_name: str,
        commit_sha: str,
        token: Optional[str],
    ) -> Tuple[Optional[str], Optional[int]]:
        """
        Fallback: find the PR associated with a merge commit via REST API.
        Uses GET /repos/{owner}/{repo}/commits/{sha}/pulls.
        Returns (pr_node_id, pr_number) or (None, None).
        """
        headers = {
            **self._auth_headers(token),
            # groot-preview header required for commits-to-pulls association
            "Accept": "application/vnd.github.groot-preview+json",
        }
        url = f"{_GITHUB_API}/repos/{repo_full_name}/commits/{commit_sha}/pulls"
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.ok:
                prs = resp.json()
                if prs:
                    return prs[0].get("node_id"), prs[0].get("number")
                logger.info(f"[RevertService] No PRs found for commit {commit_sha}")
            else:
                logger.warning(f"[RevertService] commit→pulls lookup returned {resp.status_code}")
        except Exception as exc:
            logger.warning(f"[RevertService] PR lookup by commit failed: {exc}")
        return None, None

    # ── Revert PR creation ─────────────────────────────────────────────────────

    def create_revert_pr_graphql(
        self,
        pr_node_id: str,
        task_key: str,
        token: Optional[str],
    ) -> dict:
        """
        Create a revert PR via GitHub GraphQL revertPullRequest mutation.

        Returns:
          {"ok": True, "pr_number": int, "pr_url": str, "branch_name": str}
          {"ok": False, "error": str}
        """
        headers = {
            **self._auth_headers(token),
            "Content-Type": "application/json",
        }
        title = f"Revert: {task_key} — failed code review"
        body = (
            f"This PR was automatically created by RevertAgent because the code review "
            f"for task **{task_key}** was rejected by CodeReviewAgent.\n\n"
            "Please merge this PR to undo the failed merge, or close it "
            "after fixing the review findings and re-merging the task branch."
        )
        gql_payload = {
            "query": _REVERT_PR_MUTATION,
            "variables": {
                "pullRequestId": pr_node_id,
                "title": title,
                "body": body,
            },
        }
        try:
            resp = requests.post(_GITHUB_GQL, json=gql_payload, headers=headers, timeout=30)
            data = resp.json()
            if "errors" in data:
                return {"ok": False, "error": str(data["errors"])}
            revert_pr = (
                data.get("data", {})
                    .get("revertPullRequest", {})
                    .get("revertPullRequest", {})
            )
            if not revert_pr:
                return {"ok": False, "error": "Empty revertPullRequest response from GraphQL"}
            return {
                "ok": True,
                "pr_number": revert_pr.get("number"),
                "pr_url": revert_pr.get("url"),
                "branch_name": revert_pr.get("headRefName"),
                "error": None,
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # ── PR merge ───────────────────────────────────────────────────────────────

    def merge_pr_rest(
        self,
        repo_full_name: str,
        pr_number: int,
        token: Optional[str],
        commit_title: str = "",
    ) -> dict:
        """
        Attempt to merge a PR via GitHub REST API.
        PUT /repos/{owner}/{repo}/pulls/{number}/merge

        Returns:
          {"ok": True}
          {"ok": False, "conflict": bool, "error": str}
        """
        headers = self._auth_headers(token)
        url = f"{_GITHUB_API}/repos/{repo_full_name}/pulls/{pr_number}/merge"
        payload = {
            "merge_method": "merge",
            "commit_title": commit_title or f"Revert PR #{pr_number} — auto-merged by RevertAgent",
        }
        try:
            resp = requests.put(url, json=payload, headers=headers, timeout=20)
            if resp.status_code in (200, 201):
                return {"ok": True, "conflict": False, "error": None}
            data = resp.json() if resp.content else {}
            msg = data.get("message", f"HTTP {resp.status_code}")
            conflict = resp.status_code in (405, 409)
            return {"ok": False, "conflict": conflict, "error": msg}
        except Exception as exc:
            return {"ok": False, "conflict": False, "error": str(exc)}

    # ── Safe fallback ──────────────────────────────────────────────────────────

    def mark_revert_required(self, db: Session, review_run: MergeReviewRun, reason: str) -> None:
        """Fallback: mark revert as required without any GitHub API call."""
        review_run.revert_status = "required"
        if not review_run.gate_reason:
            review_run.gate_reason = reason
        db.commit()
        logger.info(
            f"[RevertService] revert_required — review_run_id={review_run.id} "
            f"branch={review_run.source_branch} → {review_run.target_branch}"
        )


revert_service = RevertService()
