import json
import logging
import requests
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.models.merge_review import MergeReviewRun
from app.core.config import settings
from app.providers.github_adapter import normalize_repository_full_name

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
      baseRefName
    }
  }
}
"""

# Substrings that indicate a GitHub token permission / scope error
_PERMISSION_ERROR_FRAGMENTS = (
    "Resource not accessible by personal access token",
    "Although you appear to have the correct authorization credentials",
    "Must have admin rights",
    "INSUFFICIENT_SCOPES",
    "Resource protected by organization SAML enforcement",
    "Your token has not been granted",
)

_PERMISSION_ERROR_DETAIL = (
    "GitHub token lacks the required permissions to create a revert PR. "
    "Required scopes / fine-grained permissions: "
    "Contents (Read & Write), Pull Requests (Read & Write), Metadata (Read). "
    "Update your token in the integration settings and retry."
)


def _is_permission_error(msg: str) -> bool:
    return any(fragment in msg for fragment in _PERMISSION_ERROR_FRAGMENTS)


class RevertService:

    def _auth_headers(self, token: Optional[str]) -> dict:
        use_token = token or settings.GITHUB_TOKEN
        h = {"Accept": "application/vnd.github+json"}
        if use_token:
            h["Authorization"] = f"Bearer {use_token}"
        else:
            logger.warning("[RevertService] No GitHub token — API calls may fail on private repos")
        return h

    # ── PR info extraction from stored event ──────────────────────────────────

    def extract_pr_info_from_event(self, event_log) -> Tuple[Optional[str], Optional[int]]:
        """
        Legacy: parse (pr_node_id, pr_number) from raw webhook JSON.
        Used when the event was logged before dedicated columns were added.
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

    # ── REST: resolve PR node_id from PR number ───────────────────────────────

    def find_pr_node_id_by_number(
        self,
        repo_full_name: str,
        pr_number: int,
        token: Optional[str],
    ) -> Optional[str]:
        """
        Fetch the GraphQL node_id for a known PR number via REST API.
        GET /repos/{owner}/{repo}/pulls/{number}
        Returns node_id string or None.
        """
        headers = self._auth_headers(token)
        repo = normalize_repository_full_name(repo_full_name)
        url = f"{_GITHUB_API}/repos/{repo}/pulls/{pr_number}"
        logger.info(f"[GitHubAdapter] GET /repos/{repo}/pulls/{pr_number}")
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.ok:
                data = resp.json()
                node_id = data.get("node_id")
                if node_id:
                    logger.info(f"[RevertService] Resolved node_id for PR #{pr_number}: {node_id}")
                    return node_id
                logger.warning(f"[RevertService] PR #{pr_number} found but node_id missing in response")
            else:
                logger.warning(
                    f"[GitHubAdapter] GET /repos/{repo}/pulls/{pr_number} "
                    f"response status={resp.status_code} body={resp.text[:300]}"
                )
        except Exception as exc:
            logger.warning(f"[RevertService] find_pr_node_id_by_number failed: {exc}")
        return None

    # ── REST: find PR by merge commit SHA ─────────────────────────────────────

    def find_pr_by_commit(
        self,
        repo_full_name: str,
        commit_sha: str,
        token: Optional[str],
    ) -> Tuple[Optional[str], Optional[int]]:
        """
        Fallback: find PR associated with a merge commit SHA.
        GET /repos/{owner}/{repo}/commits/{sha}/pulls  (GA endpoint, no preview header needed)
        Returns (pr_node_id, pr_number) or (None, None).
        """
        headers = self._auth_headers(token)
        repo = normalize_repository_full_name(repo_full_name)
        url = f"{_GITHUB_API}/repos/{repo}/commits/{commit_sha}/pulls"
        logger.info(f"[GitHubAdapter] GET /repos/{repo}/commits/{commit_sha}/pulls")
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.ok:
                prs = resp.json()
                if prs:
                    pr = prs[0]
                    logger.info(
                        f"[RevertService] Found PR #{pr.get('number')} for commit {commit_sha}"
                    )
                    return pr.get("node_id"), pr.get("number")
                logger.info(f"[RevertService] No PRs associated with commit {commit_sha}")
            else:
                logger.warning(
                    f"[GitHubAdapter] GET /repos/{repo}/commits/{commit_sha}/pulls "
                    f"response status={resp.status_code} body={resp.text[:300]}"
                )
        except Exception as exc:
            logger.warning(f"[RevertService] find_pr_by_commit failed: {exc}")
        return None, None

    # ── REST: fetch revert PR base branch ────────────────────────────────────

    def get_revert_pr_base_branch(
        self,
        repo_full_name: str,
        pr_number: int,
        token: Optional[str],
    ) -> Optional[str]:
        """
        Fetch the base (target) branch of a PR via REST API.
        GET /repos/{owner}/{repo}/pulls/{number}
        Returns the base branch ref string, or None on failure.
        """
        headers = self._auth_headers(token)
        repo = normalize_repository_full_name(repo_full_name)
        url = f"{_GITHUB_API}/repos/{repo}/pulls/{pr_number}"
        logger.info(f"[GitHubAdapter] GET /repos/{repo}/pulls/{pr_number} (base branch)")
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.ok:
                return resp.json().get("base", {}).get("ref")
            logger.warning(
                f"[GitHubAdapter] GET /repos/{repo}/pulls/{pr_number} (base branch) "
                f"response status={resp.status_code} body={resp.text[:300]}"
            )
        except Exception as exc:
            logger.warning(f"[RevertService] get_revert_pr_base_branch failed: {exc}")
        return None

    # ── GraphQL: create revert PR ─────────────────────────────────────────────

    def create_revert_pr_graphql(
        self,
        pr_node_id: str,
        task_key: str,
        token: Optional[str],
    ) -> dict:
        """
        Create a revert PR via GitHub GraphQL revertPullRequest mutation.

        Returns:
          {"ok": True,  "pr_number": int, "pr_url": str, "branch_name": str}
          {"ok": False, "permission_error": bool, "error": str}
        """
        headers = {
            **self._auth_headers(token),
            "Content-Type": "application/json",
        }
        title = f"Revert: {task_key} — failed code review"
        body = (
            f"This revert PR was automatically created by the Agentic DevOps platform "
            f"(RevertAgent) because the code review for task **{task_key}** was rejected "
            f"by CodeReviewAgent.\n\n"
            "When `AUTO_REVERT_MODE=create_and_merge_revert_pr` is active, the system will "
            "automatically attempt to merge this revert PR to undo the failed merge — "
            "no manual action is required in that mode.\n\n"
            "If automatic merge is disabled or fails, this PR documents the revert that "
            "should be applied. Review the original code review findings before re-merging "
            "the task branch."
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
                raw_error = str(data["errors"])
                perm = _is_permission_error(raw_error)
                error_msg = _PERMISSION_ERROR_DETAIL if perm else raw_error
                logger.error(f"[RevertService] GraphQL error (permission={perm}): {raw_error[:300]}")
                return {"ok": False, "permission_error": perm, "error": error_msg}

            revert_pr = (
                data.get("data", {})
                    .get("revertPullRequest", {})
                    .get("revertPullRequest", {})
            )
            if not revert_pr:
                return {
                    "ok": False,
                    "permission_error": False,
                    "error": "Empty revertPullRequest response from GraphQL",
                }
            return {
                "ok": True,
                "pr_number": revert_pr.get("number"),
                "pr_url": revert_pr.get("url"),
                "branch_name": revert_pr.get("headRefName"),
                "base_branch": revert_pr.get("baseRefName"),
                "error": None,
            }
        except Exception as exc:
            return {"ok": False, "permission_error": False, "error": str(exc)}

    # ── REST: merge a PR ──────────────────────────────────────────────────────

    def merge_pr_rest(
        self,
        repo_full_name: str,
        pr_number: int,
        token: Optional[str],
        commit_title: str = "",
        commit_message: str = "",
    ) -> dict:
        """
        Attempt to merge a PR via GitHub REST API.
        PUT /repos/{owner}/{repo}/pulls/{number}/merge

        Returns:
          {"ok": True,  "merge_commit_sha": Optional[str], ...}
          {"ok": False, "conflict": bool, "permission_error": bool, "error": str, "merge_commit_sha": None}

        Status mapping on failure:
          403 → permission / branch protection problem
          404 → wrong repo, wrong PR number, or inaccessible repo
          405 → PR is not mergeable or merge method not allowed
          409 → merge conflict
        """
        headers = self._auth_headers(token)
        repo = normalize_repository_full_name(repo_full_name)
        url = f"{_GITHUB_API}/repos/{repo}/pulls/{pr_number}/merge"
        payload = {"merge_method": "merge"}
        if commit_title:
            payload["commit_title"] = commit_title
        if commit_message:
            payload["commit_message"] = commit_message

        logger.info(f"[GitHubAdapter] PUT /repos/{repo}/pulls/{pr_number}/merge")
        try:
            resp = requests.put(url, json=payload, headers=headers, timeout=30)
            body = resp.text[:500] if resp.content else ""
            logger.info(
                f"[GitHubAdapter] merge PR #{pr_number} response status={resp.status_code} body={body}"
            )
            data = resp.json() if resp.content else {}

            # GitHub returns 200 with {"merged": true, "sha": "..."} on success.
            if resp.status_code in (200, 201) and data.get("merged") is True:
                return {
                    "ok": True,
                    "conflict": False,
                    "permission_error": False,
                    "error": None,
                    "merge_commit_sha": data.get("sha"),
                }

            code = resp.status_code
            gh_msg = data.get("message", "") or body
            conflict = code == 409
            perm = code == 403 or _is_permission_error(gh_msg)

            if code == 403:
                reason = "permission / branch protection problem"
            elif code == 404:
                reason = "wrong repo, wrong PR number, or inaccessible repo"
            elif code == 405:
                reason = "PR is not mergeable or merge method not allowed"
            elif code == 409:
                reason = "merge conflict"
            else:
                reason = "merge failed"

            if perm:
                error = f"{_PERMISSION_ERROR_DETAIL} (status={code}, {reason}): {gh_msg}"
            else:
                error = f"GitHub merge failed (status={code}, {reason}): {gh_msg}"

            return {
                "ok": False,
                "conflict": conflict,
                "permission_error": perm,
                "error": error,
                "merge_commit_sha": None,
            }
        except Exception as exc:
            return {
                "ok": False,
                "conflict": False,
                "permission_error": False,
                "error": str(exc),
                "merge_commit_sha": None,
            }

    # ── Safe fallback ─────────────────────────────────────────────────────────

    def mark_revert_required(self, db: Session, review_run: MergeReviewRun, reason: str) -> None:
        """Mark revert as required without any GitHub API call."""
        review_run.revert_status = "required"
        review_run.revert_error_message = reason
        if not review_run.gate_reason:
            review_run.gate_reason = reason
        db.commit()
        logger.info(
            f"[RevertService] revert_required — review_run_id={review_run.id} "
            f"branch={review_run.source_branch} → {review_run.target_branch}"
        )


revert_service = RevertService()
