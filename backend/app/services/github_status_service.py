import logging

logger = logging.getLogger(__name__)


class GitHubStatusService:
    """
    Extension point for publishing GitHub commit statuses/checks.
    When implemented, this will mark commits as pending/success/failure
    based on the review gate result, enabling branch protection rules.
    """

    def publish_status(
        self,
        state: str,
        description: str,
        context: str = "code-review/gate",
        commit_sha: str = None,
        repo_full_name: str = None,
        token: str = None,
    ) -> None:
        # TODO: call GitHub Commit Status API:
        #   POST /repos/{owner}/{repo}/statuses/{sha}
        #   body: {"state": state, "description": description, "context": context}
        logger.info(
            f"[GitHubStatusService] state={state} repo={repo_full_name} "
            f"sha={commit_sha} description={description}"
        )


github_status_service = GitHubStatusService()
