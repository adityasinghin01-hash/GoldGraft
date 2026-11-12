"""Read-provider adapters for GitHub, Render and WorkOS (GU01).

An observation is evidence only when it came from the provider in this call.
The offline/deterministic branch used to report ``verified=True`` with
``live=False``; that conflated "we can describe a shape" with "we observed the
resource". Now ``verified`` is true only for a successful live read, and every
result says which evidence class it belongs to.

No credentials means no live read, and no verification.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Literal
from urllib.parse import urlparse

import httpx

EvidenceClass = Literal["live", "offline", "unknown"]


@dataclass
class ProviderObservation:
    provider: str
    resource_id: str
    verified: bool
    read_only: bool
    evidence_class: EvidenceClass
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def __post_init__(self):
        if self.verified and self.evidence_class != "live":
            raise ValueError("an offline observation cannot be verified")
        if self.verified and self.error is not None:
            raise ValueError("a failed observation cannot be verified")


def _offline(provider: str, resource_id: str, metadata: dict[str, Any], error: str):
    return ProviderObservation(
        provider=provider,
        resource_id=resource_id,
        verified=False,
        read_only=True,
        evidence_class="offline",
        metadata=metadata,
        error=error,
    )


class ProviderAdapter:
    """Discovers and verifies external platform identities and resources."""

    def __init__(self, *, transport: Any | None = None, qualify_reader=None):
        self.transport = transport if transport is not None else httpx
        self.qualify_reader = qualify_reader

    def observe_github_repo(
        self,
        repo_url: str,
        *,
        token: str | None = None,
    ) -> ProviderObservation:
        """Reads GitHub repository metadata. Never widens beyond read scope."""
        auth_token = token or os.getenv("GITHUB_TOKEN")
        parsed = urlparse(repo_url)
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]
        if parsed.hostname not in {"github.com", "www.github.com"} or len(path_parts) < 2:
            return _offline("github", repo_url, {}, "not a GitHub repository URL")
        owner, name = path_parts[-2], path_parts[-1].removesuffix(".git")
        if not auth_token:
            return _offline(
                "github", repo_url, {"repo_name": name}, "no GitHub token; resource not observed"
            )
        try:
            response = self.transport.get(
                f"https://api.github.com/repos/{owner}/{name}",
                headers={
                    "Authorization": f"Bearer {auth_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                timeout=10.0,
            )
        except Exception:
            return ProviderObservation(
                provider="github",
                resource_id=repo_url,
                verified=False,
                read_only=True,
                evidence_class="unknown",
                metadata={"repo_name": name},
                error="github read transport failed",
            )
        if response.status_code != 200:
            return ProviderObservation(
                provider="github",
                resource_id=repo_url,
                verified=False,
                read_only=True,
                evidence_class="unknown",
                metadata={"repo_name": name},
                error=f"github read HTTP {response.status_code}",
            )
        try:
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("provider object required")
        except (ValueError, TypeError):
            return ProviderObservation(
                provider="github",
                resource_id=repo_url,
                verified=False,
                read_only=False,
                evidence_class="unknown",
                error="malformed provider response",
            )
        permissions = data.get("permissions") or {}
        # Read-only is established by the provider denying push, not by assuming it.
        if not isinstance(permissions, dict):
            permissions = {}
        read_only = (
            permissions.get("push") is False
            and self.qualify_reader is not None
            and self.qualify_reader("github", repo_url, data) is True
        )
        return ProviderObservation(
            provider="github",
            resource_id=repo_url,
            verified=True,
            read_only=read_only,
            evidence_class="live",
            metadata={
                "repo_name": data.get("name", name),
                "default_branch": data.get("default_branch"),
                "private": data.get("private"),
                "permissions": permissions,
            },
        )

    def observe_render_service(
        self, service_id: str, *, api_key: str | None = None
    ) -> ProviderObservation:
        """Reads Render service metadata without performing any deployment."""
        key = api_key or os.getenv("RENDER_API_KEY")
        if not key:
            return _offline(
                "render", service_id, {"service_id": service_id}, "no Render key; not observed"
            )
        try:
            response = self.transport.get(
                f"https://api.render.com/v1/services/{service_id}",
                headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
                timeout=10.0,
            )
        except Exception:
            return ProviderObservation(
                provider="render",
                resource_id=service_id,
                verified=False,
                read_only=True,
                evidence_class="unknown",
                metadata={"service_id": service_id},
                error="render read transport failed",
            )
        if response.status_code != 200:
            return ProviderObservation(
                provider="render",
                resource_id=service_id,
                verified=False,
                read_only=True,
                evidence_class="unknown",
                metadata={"service_id": service_id},
                error=f"render read HTTP {response.status_code}",
            )
        try:
            data = response.json()
            details = data.get("serviceDetails") or {}
            if not isinstance(data, dict) or not isinstance(details, dict):
                raise ValueError("provider object required")
        except (ValueError, TypeError, AttributeError):
            return ProviderObservation(
                provider="render",
                resource_id=service_id,
                verified=False,
                read_only=False,
                evidence_class="unknown",
                error="malformed provider response",
            )
        return ProviderObservation(
            provider="render",
            resource_id=service_id,
            verified=True,
            read_only=(
                self.qualify_reader is not None
                and self.qualify_reader("render", service_id, data) is True
            ),
            evidence_class="live",
            metadata={
                "service_type": data.get("type"),
                "region": details.get("region"),
                "plan": details.get("plan"),
                "url": details.get("url") or data.get("url"),
                "suspended": data.get("suspended"),
            },
        )

    def observe_workos_user(
        self, user_id: str, organization_id: str, *, api_key: str | None = None
    ) -> ProviderObservation:
        """Verifies directory identity and organisational boundary."""
        key = api_key or os.getenv("WORKOS_API_KEY")
        if not key:
            return _offline(
                "workos",
                user_id,
                {"org_id": organization_id},
                "no WorkOS key; identity not observed",
            )
        try:
            response = self.transport.get(
                f"https://api.workos.com/user_management/users/{user_id}",
                headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
                timeout=10.0,
            )
        except Exception:
            return ProviderObservation(
                provider="workos",
                resource_id=user_id,
                verified=False,
                read_only=True,
                evidence_class="unknown",
                metadata={"org_id": organization_id},
                error="workos read transport failed",
            )
        if response.status_code != 200:
            return ProviderObservation(
                provider="workos",
                resource_id=user_id,
                verified=False,
                read_only=True,
                evidence_class="unknown",
                metadata={"org_id": organization_id},
                error=f"workos read HTTP {response.status_code}",
            )
        try:
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("provider object required")
        except (ValueError, TypeError):
            return ProviderObservation(
                provider="workos",
                resource_id=user_id,
                verified=False,
                read_only=False,
                evidence_class="unknown",
                error="malformed provider response",
            )
        organization = data.get("organization")
        observed_org = data.get("organization_id") or (
            organization.get("id") if isinstance(organization, dict) else None
        )
        if observed_org != organization_id or data.get("id") != user_id:
            return ProviderObservation(
                provider="workos",
                resource_id=user_id,
                verified=False,
                read_only=True,
                evidence_class="live",
                metadata={"org_id": organization_id, "observed_org_id": observed_org},
                error="directory membership does not belong to the claimed organisation",
            )
        return ProviderObservation(
            provider="workos",
            resource_id=user_id,
            verified=True,
            read_only=True,
            evidence_class="live",
            metadata={"org_id": organization_id, "email": data.get("email")},
        )
