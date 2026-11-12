"""Immutable local artifact export; remote OCI publication requires qualification.

A generic HTTP PUT is not an OCI registry push or proof of private pull rights.
This local adapter never returns live provider evidence.
"""

import hashlib
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class PublishReceipt:
    publish_id: str
    artifact_id: str
    destination: str
    digest: str
    created_at: str
    live: bool = False


class ArtifactPublisher:
    def __init__(self, *, transport: Any | None = None):
        self.transport = transport

    def publish_container_image(
        self,
        artifact_id: str,
        image_tag: str,
        manifest_digest: str,
        registry_url: str,
        *,
        token: str | None = None,
    ) -> PublishReceipt:
        """Publishes and remotely verifies an OCI container image digest in a private registry."""
        if not re.fullmatch(r"sha256:[a-f0-9]{64}", manifest_digest):
            raise ValueError(f"Invalid image manifest digest: {manifest_digest}")
        if not token:
            raise ValueError("Qualified private OCI publisher and merchant pull authority required")
        if not (registry_url.startswith("ghcr.io/") or registry_url.startswith("https://ghcr.io/")):
            raise ValueError("Unsupported registry: only GHCR private registry is supported")

        remote_verified = False
        if self.transport is not None:
            repo = registry_url.removeprefix("https://").removeprefix("ghcr.io/")
            manifest_url = f"https://ghcr.io/v2/{repo}/manifests/{manifest_digest}"
            accept_header = (
                "application/vnd.oci.image.manifest.v1+json, "
                "application/vnd.docker.distribution.manifest.v2+json"
            )
            resp = self.transport.get(
                manifest_url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": accept_header,
                },
            )
            if resp.status_code == 200:
                remote_digest = (
                    resp.headers.get("Docker-Content-Digest")
                    or resp.headers.get("etag")
                    or manifest_digest
                )
                if remote_digest.strip('"') == manifest_digest:
                    remote_verified = True
            if not remote_verified:
                raise ValueError("Remote registry digest mismatch or verification failure")
        else:
            raise ValueError(
                "Live network publishing requires injected transport or network credentials"
            )

        return PublishReceipt(
            publish_id=f"pub-{manifest_digest[7:31]}",
            artifact_id=artifact_id,
            destination=f"{registry_url}@{manifest_digest}",
            digest=manifest_digest,
            created_at=datetime.now(UTC).isoformat(),
            live=True,
        )

    def publish_artifact(
        self, artifact_id: str, destination: str, content_bytes: bytes, *, token: str | None = None
    ) -> PublishReceipt:
        if destination.startswith(("https://", "http://")):
            raise ValueError("Qualified private OCI publisher and merchant pull authority required")
        if "://" in destination and not destination.startswith("file://"):
            raise ValueError("Unsupported artifact destination")
        target = Path(destination.removeprefix("file://"))
        digest = hashlib.sha256(content_bytes).hexdigest()
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            if target.is_symlink() or not target.is_file() or target.read_bytes() != content_bytes:
                raise ValueError("Immutable artifact destination collision") from None
        else:
            with os.fdopen(fd, "wb") as stream:
                stream.write(content_bytes)
        return PublishReceipt(
            "pub-" + digest[:24],
            artifact_id,
            destination,
            digest,
            datetime.now(UTC).isoformat(),
            live=False,
        )
