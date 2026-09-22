import requests
from typing import Dict, Any, List, Optional
import logging

from app.services.token_refresh_service import token_refresh_service

logger = logging.getLogger(__name__)


class GitHubExecutor:
    """
    User-scoped GitHub API executor for developer capabilities:
    - Repository listing & metadata retrieval
    - GitHub Issues listing, retrieval & creation
    - GitHub Pull Requests listing & retrieval
    """

    BASE_URL = "https://api.github.com"

    def _get_headers(self, user_id: str) -> Dict[str, str]:
        """
        Retrieve valid access token for authenticated user and construct API headers.
        """
        try:
            access_token = token_refresh_service.get_valid_access_token(user_id, "github")
        except Exception as exc:
            raise ValueError(f"No active GitHub connection found for user '{user_id}'.") from exc

        if not access_token:
            raise ValueError(f"No active GitHub connection found for user '{user_id}'.")

        return {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "MITRA-Assistant",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def list_repositories(
        self,
        user_id: str,
        visibility: str = "all",
        sort: str = "updated",
        max_results: int = 30,
    ) -> Dict[str, Any]:
        """List repositories accessible to the connected GitHub account."""
        try:
            headers = self._get_headers(user_id)
            params = {
                "visibility": visibility,
                "sort": sort,
                "per_page": min(max_results, 100),
            }
            res = requests.get(
                f"{self.BASE_URL}/user/repos",
                headers=headers,
                params=params,
                timeout=10,
            )
            if res.status_code != 200:
                return {
                    "status": "failed",
                    "error": f"GitHub API error (HTTP {res.status_code}): {res.text[:200]}",
                    "user_connected_account": True,
                }

            raw_repos = res.json()
            repos = [
                {
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "full_name": r.get("full_name"),
                    "private": r.get("private"),
                    "html_url": r.get("html_url"),
                    "description": r.get("description"),
                    "stargazers_count": r.get("stargazers_count"),
                    "forks_count": r.get("forks_count"),
                    "language": r.get("language"),
                    "updated_at": r.get("updated_at"),
                }
                for r in raw_repos
                if isinstance(r, dict)
            ]
            return {
                "status": "success",
                "user_connected_account": True,
                "repositories": repos,
                "count": len(repos),
                "method": "github_api",
            }
        except Exception as e:
            logger.error(f"Failed to list GitHub repositories for user '{user_id}': {e}")
            return {
                "status": "failed",
                "error": str(e),
                "user_connected_account": False,
            }

    def get_repository(self, user_id: str, owner: str, repo: str) -> Dict[str, Any]:
        """Get detailed metadata for a specific repository."""
        try:
            headers = self._get_headers(user_id)
            res = requests.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}",
                headers=headers,
                timeout=10,
            )
            if res.status_code != 200:
                return {
                    "status": "failed",
                    "error": f"GitHub API error (HTTP {res.status_code}): {res.text[:200]}",
                }

            return {
                "status": "success",
                "repository": res.json(),
                "method": "github_api",
                "user_connected_account": True,
            }
        except Exception as e:
            logger.error(
                f"Failed to fetch GitHub repository '{owner}/{repo}' for user '{user_id}': {e}"
            )
            return {"status": "failed", "error": str(e)}

    def list_issues(
        self,
        user_id: str,
        owner: str,
        repo: str,
        state: str = "open",
        max_results: int = 30,
    ) -> Dict[str, Any]:
        """List issues for a repository."""
        try:
            headers = self._get_headers(user_id)
            params = {"state": state, "per_page": min(max_results, 100)}
            res = requests.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/issues",
                headers=headers,
                params=params,
                timeout=10,
            )
            if res.status_code != 200:
                return {
                    "status": "failed",
                    "error": f"GitHub API error (HTTP {res.status_code}): {res.text[:200]}",
                }

            raw_issues = res.json()
            issues = [
                {
                    "number": i.get("number"),
                    "title": i.get("title"),
                    "state": i.get("state"),
                    "user": i.get("user", {}).get("login"),
                    "created_at": i.get("created_at"),
                    "updated_at": i.get("updated_at"),
                    "comments": i.get("comments"),
                    "html_url": i.get("html_url"),
                    "is_pull_request": "pull_request" in i,
                }
                for i in raw_issues
                if isinstance(i, dict)
            ]
            return {
                "status": "success",
                "issues": issues,
                "count": len(issues),
                "method": "github_api",
                "user_connected_account": True,
            }
        except Exception as e:
            logger.error(
                f"Failed to list GitHub issues for '{owner}/{repo}', user '{user_id}': {e}"
            )
            return {"status": "failed", "error": str(e)}

    def get_issue(
        self, user_id: str, owner: str, repo: str, issue_number: int
    ) -> Dict[str, Any]:
        """Retrieve details of a specific issue."""
        try:
            headers = self._get_headers(user_id)
            res = requests.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/issues/{issue_number}",
                headers=headers,
                timeout=10,
            )
            if res.status_code != 200:
                return {
                    "status": "failed",
                    "error": f"GitHub API error (HTTP {res.status_code}): {res.text[:200]}",
                }

            return {
                "status": "success",
                "issue": res.json(),
                "method": "github_api",
                "user_connected_account": True,
            }
        except Exception as e:
            logger.error(
                f"Failed to fetch GitHub issue #{issue_number} in '{owner}/{repo}' for user '{user_id}': {e}"
            )
            return {"status": "failed", "error": str(e)}

    def create_issue(
        self,
        user_id: str,
        owner: str,
        repo: str,
        title: str,
        body: str = "",
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a new issue in a repository."""
        try:
            headers = self._get_headers(user_id)
            payload = {"title": title, "body": body}
            if labels:
                payload["labels"] = labels

            res = requests.post(
                f"{self.BASE_URL}/repos/{owner}/{repo}/issues",
                headers=headers,
                json=payload,
                timeout=10,
            )
            if res.status_code not in (200, 201):
                return {
                    "status": "failed",
                    "error": f"GitHub API error (HTTP {res.status_code}): {res.text[:200]}",
                }

            data = res.json()
            return {
                "status": "success",
                "issue_number": data.get("number"),
                "html_url": data.get("html_url"),
                "issue": data,
                "method": "github_api",
                "user_connected_account": True,
            }
        except Exception as e:
            logger.error(
                f"Failed to create GitHub issue in '{owner}/{repo}' for user '{user_id}': {e}"
            )
            return {"status": "failed", "error": str(e)}

    def list_pull_requests(
        self,
        user_id: str,
        owner: str,
        repo: str,
        state: str = "open",
        max_results: int = 30,
    ) -> Dict[str, Any]:
        """List pull requests for a repository."""
        try:
            headers = self._get_headers(user_id)
            params = {"state": state, "per_page": min(max_results, 100)}
            res = requests.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/pulls",
                headers=headers,
                params=params,
                timeout=10,
            )
            if res.status_code != 200:
                return {
                    "status": "failed",
                    "error": f"GitHub API error (HTTP {res.status_code}): {res.text[:200]}",
                }

            raw_prs = res.json()
            prs = [
                {
                    "number": pr.get("number"),
                    "title": pr.get("title"),
                    "state": pr.get("state"),
                    "user": pr.get("user", {}).get("login"),
                    "head": pr.get("head", {}).get("ref"),
                    "base": pr.get("base", {}).get("ref"),
                    "created_at": pr.get("created_at"),
                    "updated_at": pr.get("updated_at"),
                    "html_url": pr.get("html_url"),
                }
                for pr in raw_prs
                if isinstance(pr, dict)
            ]
            return {
                "status": "success",
                "pull_requests": prs,
                "count": len(prs),
                "method": "github_api",
                "user_connected_account": True,
            }
        except Exception as e:
            logger.error(
                f"Failed to list GitHub PRs for '{owner}/{repo}', user '{user_id}': {e}"
            )
            return {"status": "failed", "error": str(e)}

    def get_pull_request(
        self, user_id: str, owner: str, repo: str, pull_number: int
    ) -> Dict[str, Any]:
        """Retrieve details of a specific pull request."""
        try:
            headers = self._get_headers(user_id)
            res = requests.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/pulls/{pull_number}",
                headers=headers,
                timeout=10,
            )
            if res.status_code != 200:
                return {
                    "status": "failed",
                    "error": f"GitHub API error (HTTP {res.status_code}): {res.text[:200]}",
                }

            return {
                "status": "success",
                "pull_request": res.json(),
                "method": "github_api",
                "user_connected_account": True,
            }
        except Exception as e:
            logger.error(
                f"Failed to fetch GitHub PR #{pull_number} in '{owner}/{repo}' for user '{user_id}': {e}"
            )
            return {"status": "failed", "error": str(e)}
