"""Immutable local artifact export; remote OCI publication requires qualification.

A generic HTTP PUT is not an OCI registry push or proof of private pull rights.
This local adapter never returns live provider evidence.
"""

import hashlib
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class PublishReceipt:
    publish_id: str
    artifact_id: str
    destination: str
    digest: str
    created_at: str
    live: bool = False


class ArtifactPublisher:
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
