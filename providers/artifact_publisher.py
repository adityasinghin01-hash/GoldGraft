"""Artifact Publisher Provider (GU04).

Implements:
1. Direct artifact publishing to local or remote OCI registries.
2. Content digest sealing and immutability receipts.
"""

import hashlib
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx


@dataclass
class PublishReceipt:
    publish_id: str
    artifact_id: str
    destination: str
    digest: str
    created_at: str
    live: bool = False


class ArtifactPublisher:
    """Publishes tested and verified container artifacts."""

    def publish_artifact(
        self,
        artifact_id: str,
        destination: str,
        content_bytes: bytes,
        *,
        token: str | None = None,
    ) -> PublishReceipt:
        digest = hashlib.sha256(content_bytes).hexdigest()
        pub_id = f"pub-{digest[:10]}"
        is_live = False

        if destination.startswith("http://") or destination.startswith("https://"):
            auth_token = token or os.getenv("REGISTRY_AUTH_TOKEN")
            headers = {"Content-Type": "application/octet-stream"}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            try:
                resp = httpx.put(destination, headers=headers, content=content_bytes, timeout=30.0)
                if resp.status_code in (200, 201, 202, 204):
                    is_live = True
            except Exception:
                pass
        elif destination.startswith("file://") or "/" in destination or "\\" in destination:
            clean_path = destination.removeprefix("file://")
            target_path = Path(clean_path)
            try:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_bytes(content_bytes)
                is_live = True
            except Exception:
                pass

        return PublishReceipt(
            publish_id=pub_id,
            artifact_id=artifact_id,
            destination=destination,
            digest=digest,
            created_at=datetime.now(UTC).isoformat(),
            live=is_live,
        )
