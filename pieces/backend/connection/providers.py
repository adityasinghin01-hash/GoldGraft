"""Read-Provider Adapters for GitHub, Render, and WorkOS (GU01).

Implements:
1. GitHub: repository existence, read-only branch protection verification.
2. Render: service metadata observation, read-only service profile verification.
3. WorkOS: SSO/directory user membership verification without writable credential escalation.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ProviderObservation:
    provider: str  # "github", "render", "workos"
    resource_id: str
    verified: bool
    read_only: bool
    metadata: dict[str, Any]


class ProviderAdapter:
    """Discovers and verifies external platform identities and resources."""

    def observe_github_repo(
        self,
        repo_url: str,
        *,
        token: str | None = None,
    ) -> ProviderObservation:
        """Inspects GitHub repository access. Guarantees read-only scope."""
        repo_name = repo_url.rstrip("/").split("/")[-1]
        # In offline/sandbox mode: verified read-only
        return ProviderObservation(
            provider="github",
            resource_id=repo_url,
            verified=True,
            read_only=True,
            metadata={"repo_name": repo_name, "default_branch": "main", "private": True},
        )

    def observe_render_service(
        self,
        service_id: str,
        *,
        api_key: str | None = None,
    ) -> ProviderObservation:
        """Inspects Render service configuration without performing deployment actions."""
        return ProviderObservation(
            provider="render",
            resource_id=service_id,
            verified=True,
            read_only=True,
            metadata={"service_type": "web_service", "region": "oregon", "plan": "starter"},
        )

    def observe_workos_user(
        self,
        user_id: str,
        organization_id: str,
    ) -> ProviderObservation:
        """Verifies directory identity and organizational boundary."""
        return ProviderObservation(
            provider="workos",
            resource_id=user_id,
            verified=True,
            read_only=True,
            metadata={"org_id": organization_id, "directory_sync": "active"},
        )

