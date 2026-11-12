"""GitHub publication provider (GU04).

Honest outcome boundary
-----------------------
A failed or uncertain API call never returns a made-up pull-request identifier.
``pr_id`` and ``pr_url`` are populated only from a provider response, and
``state`` says what actually happened: ``not_attempted``, ``created``,
``failed`` or ``unknown``.

A commit that does not look like a real object id is rejected instead of being
digested into a plausible-looking receipt.

No network call happens without a token or an injected transport.
"""

import hashlib
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal
from urllib.parse import urlparse

import httpx

PublishState = Literal["not_attempted", "created", "failed", "unknown"]
COMMIT_SHA = re.compile(r"^[0-9a-f]{7,40}$")


@dataclass
class PullRequestReceipt:
    repo_url: str
    branch_name: str
    target_branch: str
    title: str
    commit_sha: str
    state: PublishState
    created_at: str
    receipt_digest: str
    pr_id: str | None = None
    pr_url: str | None = None
    live: bool = False
    error: str | None = None

    def __post_init__(self):
        if self.pr_id is not None and self.state != "created":
            raise ValueError("a pull-request identity only exists after a provider response")
        if self.live != (self.state == "created"):
            raise ValueError("live flag must match provider creation")


class GitHubPublisher:
    """Creates merchant pull requests and reports only observed results."""

    def __init__(self, *, transport: Any | None = None, authorize=None):
        self.transport = transport if transport is not None else httpx
        self.authorize = authorize

    def publish_pull_request(
        self,
        repo_url: str,
        branch_name: str,
        *,
        target_branch: str = "main",
        title: str,
        commit_sha: str,
        body: str | None = None,
        token: str | None = None,
    ) -> PullRequestReceipt:
        if target_branch == branch_name:
            raise ValueError("Target branch cannot be identical to source branch")
        if not COMMIT_SHA.match(commit_sha or ""):
            raise ValueError(
                "Publication requires a real provider commit id, not a fabricated digest"
            )

        receipt_digest = hashlib.sha256(
            f"{repo_url}:{branch_name}:{commit_sha}".encode()
        ).hexdigest()
        created_at = datetime.now(UTC).isoformat()
        base = {
            "repo_url": repo_url,
            "branch_name": branch_name,
            "target_branch": target_branch,
            "title": title,
            "commit_sha": commit_sha,
            "created_at": created_at,
            "receipt_digest": receipt_digest,
        }

        auth_token = token or os.getenv("GITHUB_TOKEN")
        parsed = urlparse(repo_url)
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]
        if parsed.hostname not in {"github.com", "www.github.com"} or len(path_parts) < 2:
            raise ValueError(f"Not a GitHub repository URL: {repo_url!r}")
        if not auth_token:
            return PullRequestReceipt(
                **base, state="not_attempted", error="no GitHub token configured"
            )

        if (
            self.authorize is None
            or self.authorize(repo_url, branch_name, target_branch, commit_sha) is not True
        ):
            return PullRequestReceipt(
                **base, state="not_attempted", error="exact current publication authority required"
            )

        owner, name = path_parts[-2], path_parts[-1].removesuffix(".git")
        try:
            response = self.transport.post(
                f"https://api.github.com/repos/{owner}/{name}/pulls",
                headers={
                    "Authorization": f"Bearer {auth_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                json={
                    "title": title,
                    "head": branch_name,
                    "base": target_branch,
                    "body": body or f"GoldGraft verified migration commit {commit_sha}",
                },
                timeout=15.0,
            )
        except Exception:
            return PullRequestReceipt(
                **base,
                state="unknown",
                error="publication transport failed; reconcile before retry",
            )

        if response.status_code == 429 or response.status_code >= 500:
            return PullRequestReceipt(
                **base, state="unknown", error=f"publication HTTP {response.status_code}"
            )
        if response.status_code >= 400:
            return PullRequestReceipt(
                **base, state="failed", error=f"publication HTTP {response.status_code}"
            )
        try:
            data = response.json()
        except Exception:
            return PullRequestReceipt(
                **base, state="unknown", error="publication response was not JSON"
            )
        if not isinstance(data, dict) or "number" not in data:
            return PullRequestReceipt(
                **base, state="unknown", error="publication response omitted the PR number"
            )
        head_sha = str((data.get("head") or {}).get("sha") or "")
        if not head_sha or head_sha != commit_sha:
            return PullRequestReceipt(
                **base,
                state="failed",
                error="provider head sha differs from the approved commit",
            )
        return PullRequestReceipt(
            **base,
            state="created",
            pr_id=str(data["number"]),
            pr_url=data.get("html_url"),
            live=True,
        )
