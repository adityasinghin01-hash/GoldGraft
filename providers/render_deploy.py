"""Render deployment provider (GU04).

Honest outcome boundary
-----------------------
Dispatch is not deployment. A 2xx response to a deploy request (or an HTTP 202
from a deploy hook) means *submitted*. This module only reports ``live`` when it
has observed, in the same call, a provider deploy in a live state together with
a health response from the service's own reported URL. Nothing is inferred from
the service id, and no exception is swallowed into a success.

Every externally visible result is one of:
``not_dispatched``, ``submitted``, ``live``, ``failed``, ``unknown``.

No network call happens unless credentials (or an injected transport) are
present; ordinary tests inject a transport.
"""

import hashlib
import os
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

import httpx

RenderStatus = Literal["not_dispatched", "submitted", "live", "failed", "unknown"]

RENDER_API = "https://api.render.com/v1"
LIVE_DEPLOY_STATUSES = {"live"}
FAILED_DEPLOY_STATUSES = {"build_failed", "canceled", "deactivated", "pre_deploy_failed"}


@dataclass
class DeploymentReceipt:
    service_id: str
    image_tag: str
    status: RenderStatus
    created_at: str
    deployment_id: str | None = None
    health_url: str | None = None
    live: bool = False
    health_checked: bool = False
    health_status_code: int | None = None
    observed: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def __post_init__(self):
        if self.live != (self.status == "live"):
            raise ValueError("live flag must match the observed status")
        if self.status == "live" and not (self.health_checked and self.observed.get("deploy_id")):
            raise ValueError("live requires observed deploy and health response")


class RenderDeployer:
    """Submits exact image deploys and reports only observed outcomes."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        deploy_hook_url: str | None = None,
        transport: Any | None = None,
        authorize=None,
        authorize_health=None,
        verify_runtime=None,
    ):
        self._api_key = api_key
        self._deploy_hook_url = deploy_hook_url
        self.transport = transport if transport is not None else httpx
        self.authorize = authorize
        self.authorize_health = authorize_health
        self.verify_runtime = verify_runtime

    @property
    def api_key(self) -> str | None:
        return self._api_key or os.getenv("RENDER_API_KEY")

    @property
    def deploy_hook_url(self) -> str | None:
        return self._deploy_hook_url or os.getenv("RENDER_DEPLOY_HOOK_URL")

    def deploy_service(
        self,
        service_id: str,
        image_tag: str,
        *,
        health_path: str = "/health",
        observe: bool = True,
    ) -> DeploymentReceipt:
        """Submit a deploy for an exact image and optionally observe the result."""
        now = datetime.now(UTC).isoformat()
        receipt = DeploymentReceipt(
            service_id=service_id,
            image_tag=image_tag,
            status="not_dispatched",
            created_at=now,
        )
        hook, key = self.deploy_hook_url, self.api_key

        if not hook and not key:
            receipt.error = "no Render credential or deploy hook configured"
            return receipt
        if hook:
            receipt.error = "deploy hooks cannot bind the approved exact image; qualification held"
            return receipt
        if not re.fullmatch(r"[^\s@]+@sha256:[a-f0-9]{64}", image_tag):
            receipt.error = "immutable OCI manifest reference required"
            return receipt
        if self.authorize is None or self.authorize(service_id, image_tag) is not True:
            receipt.error = "exact current deployment authority required"
            return receipt

        if hook:
            dispatch = self._submit_hook(hook)
        elif key:
            dispatch = self._submit_api(service_id, image_tag, key)
        else:
            receipt.error = "no Render credential or deploy hook configured"
            return receipt

        receipt.status = dispatch["status"]
        receipt.deployment_id = dispatch.get("deployment_id")
        receipt.error = dispatch.get("error")
        if dispatch.get("body"):
            receipt.observed["submit_response"] = dispatch["body"]

        if receipt.status != "submitted" or not observe:
            return receipt
        if not (key and receipt.deployment_id):
            # A hook gives no deployment identity, so observation cannot be bound.
            receipt.error = receipt.error or "no deployment identity to observe"
            return receipt
        return self._observe(receipt, key, health_path)

    # ------------------------------------------------------------------

    def _submit_hook(self, hook: str) -> dict[str, Any]:
        try:
            response = self.transport.post(hook, timeout=15.0)
        except Exception as exc:
            return {"status": "unknown", "error": f"deploy hook transport failed: {exc}"}
        if response.status_code == 429 or response.status_code >= 500:
            return {
                "status": "unknown",
                "error": f"deploy hook HTTP {response.status_code}",
            }
        if response.status_code >= 400:
            return {"status": "failed", "error": f"deploy hook HTTP {response.status_code}"}
        body: dict[str, Any] = {}
        try:
            parsed = response.json()
            if isinstance(parsed, dict):
                body = parsed
        except Exception:
            body = {}
        deploy_id = body.get("deployId") or body.get("id")
        return {
            "status": "submitted",
            "deployment_id": str(deploy_id) if deploy_id else None,
            "body": body,
        }

    def _submit_api(self, service_id: str, image_tag: str, key: str) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        try:
            response = self.transport.post(
                f"{RENDER_API}/services/{service_id}/deploys",
                headers=headers,
                json={"imageUrl": image_tag},
                timeout=15.0,
            )
        except Exception as exc:
            return {"status": "unknown", "error": f"deploy request transport failed: {exc}"}
        if response.status_code == 429 or response.status_code >= 500:
            return {"status": "unknown", "error": f"deploy request HTTP {response.status_code}"}
        if response.status_code >= 400:
            return {"status": "failed", "error": f"deploy request HTTP {response.status_code}"}
        try:
            body = response.json()
        except Exception:
            return {"status": "unknown", "error": "deploy response was not JSON"}
        if not isinstance(body, dict):
            return {"status": "unknown", "error": "deploy response was not an object"}
        deploy_id = body.get("id")
        if not deploy_id:
            return {"status": "unknown", "error": "deploy response omitted id", "body": body}
        return {"status": "submitted", "deployment_id": str(deploy_id), "body": body}

    def _observe(self, receipt: DeploymentReceipt, key: str, health_path: str) -> DeploymentReceipt:
        headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
        try:
            service = self.transport.get(
                f"{RENDER_API}/services/{receipt.service_id}", headers=headers, timeout=15.0
            )
            deploys = self.transport.get(
                f"{RENDER_API}/services/{receipt.service_id}/deploys?limit=5",
                headers=headers,
                timeout=15.0,
            )
        except Exception as exc:
            receipt.status = "unknown"
            receipt.error = f"observation transport failed: {exc}"
            return receipt
        if service.status_code != 200 or deploys.status_code != 200:
            receipt.status = "unknown"
            receipt.error = (
                f"observation HTTP service={service.status_code} deploys={deploys.status_code}"
            )
            return receipt

        try:
            service_body = service.json()
            deploy_rows = deploys.json()
        except (ValueError, TypeError):
            receipt.status = "unknown"
            receipt.error = "malformed provider observation"
            return receipt
        if not isinstance(service_body, dict):
            receipt.status = "unknown"
            receipt.error = "service observation was not an object"
            return receipt

        details = service_body.get("serviceDetails") or {}
        if not isinstance(details, dict):
            receipt.status = "unknown"
            receipt.error = "malformed service details"
            return receipt
        # The URL comes from the provider, never from a guessed hostname.
        base_url = details.get("url") or service_body.get("url")
        if not isinstance(deploy_rows, list):
            receipt.status = "unknown"
            receipt.error = "deploy list observation was not a list"
            return receipt

        current: dict[str, Any] | None = None
        for row in deploy_rows:
            deploy = row.get("deploy", row) if isinstance(row, dict) else None
            if isinstance(deploy, dict) and str(deploy.get("id")) == str(receipt.deployment_id):
                current = deploy
                break
        if current is None:
            receipt.status = "unknown"
            receipt.error = "submitted deploy not present in provider observation"
            return receipt

        deploy_status = str(current.get("status", ""))
        commit = current.get("commit") or {}
        if not isinstance(commit, dict):
            commit = {}
        observed_image = commit.get("imageUrl") or commit.get("image_url")
        receipt.observed.update(
            {
                "deploy_id": str(current.get("id")),
                "deploy_status": deploy_status,
                "observed_image": observed_image,
                "service_url": base_url,
            }
        )

        if deploy_status in FAILED_DEPLOY_STATUSES:
            receipt.status = "failed"
            receipt.error = f"provider deploy status {deploy_status}"
            return receipt
        if deploy_status not in LIVE_DEPLOY_STATUSES:
            receipt.status = "submitted"
            return receipt
        if not observed_image or str(observed_image) != receipt.image_tag:
            receipt.status = "unknown"
            receipt.error = "live deploy image differs from the submitted exact image"
            return receipt
        if not base_url:
            receipt.status = "unknown"
            receipt.error = "provider service observation omitted the service URL"
            return receipt

        receipt.health_url = f"{str(base_url).rstrip('/')}{health_path}"
        if self.authorize_health is None or self.authorize_health(receipt.health_url) is not True:
            receipt.status = "unknown"
            receipt.error = "qualified public health network policy required"
            return receipt
        try:
            health = self.transport.get(receipt.health_url, timeout=15.0)
        except Exception as exc:
            receipt.status = "unknown"
            receipt.health_checked = True
            receipt.error = f"health check transport failed: {exc}"
            return receipt
        receipt.health_checked = True
        receipt.health_status_code = health.status_code
        if health.status_code != 200:
            receipt.status = "unknown"
            receipt.error = f"health check HTTP {health.status_code}"
            return receipt
        if self.verify_runtime is None or self.verify_runtime(receipt, health) is not True:
            receipt.status = "unknown"
            receipt.error = "exact current runtime/config/state observation required"
            return receipt
        receipt.status = "live"
        receipt.live = True
        return receipt


def deployment_fingerprint(receipt: DeploymentReceipt) -> str:
    """Stable identity for an observed deploy; a submitted deploy has no live claim."""
    raw = f"{receipt.service_id}:{receipt.deployment_id}:{receipt.status}".encode()
    return hashlib.sha256(raw).hexdigest()
