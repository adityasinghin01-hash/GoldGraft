"""Artifact build descriptors with honest provenance.

A hash over build *inputs* is a metadata digest. It is not an OCI image
manifest digest, an image config digest or an export-tar digest, and this module
never presents one as another. ``image_digest`` is populated only from an image
id the builder actually observed (Docker's ``--iidfile``); otherwise the build
is reported as ``not_built`` or ``built_unverified`` and cannot be deployed as
an exact artifact.

Building on the host is not an isolated builder. Callers that need the reviewed
isolated builder must supply a backend whose result this module records rather
than infers.
"""

import hashlib
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

BuildOutcome = Literal["built_observed", "built_unverified", "not_built", "failed"]


@dataclass
class ArtifactDescriptor:
    artifact_id: str
    image_tag: str
    metadata_digest: str
    source_digest: str
    created_at: str
    outcome: BuildOutcome = "not_built"
    image_digest: str | None = None
    reproducible: bool = False
    build_output: str | None = None

    def __post_init__(self):
        if self.image_digest is not None and not self.image_digest.startswith("sha256:"):
            raise ValueError("an image digest must be an observed sha256 reference")
        if self.outcome == "built_observed" and self.image_digest is None:
            raise ValueError("an observed build requires the observed image digest")


class ArtifactBuilder:
    """Builds container artifacts and binds source provenance honestly."""

    def calculate_source_digest(self, root_dir: Path) -> str:
        """Calculates a deterministic digest across source files in a directory."""
        hasher = hashlib.sha256()
        for path in sorted(root_dir.rglob("*")):
            if path.is_file() and not path.name.startswith("."):
                relative = path.relative_to(root_dir).as_posix()
                hasher.update(relative.encode())
                hasher.update(path.read_bytes())
        return hasher.hexdigest()

    def create_artifact_build(
        self,
        graft_id: str,
        image_name: str,
        version: str,
        source_digest: str,
    ) -> ArtifactDescriptor:
        """Describes the intended build; it does not claim an image exists."""
        raw = f"{graft_id}:{image_name}:{version}:{source_digest}".encode()
        metadata_digest = hashlib.sha256(raw).hexdigest()
        return ArtifactDescriptor(
            artifact_id=f"art-{metadata_digest[:12]}",
            image_tag=f"{image_name}:{version}",
            metadata_digest=metadata_digest,
            source_digest=source_digest,
            created_at=datetime.now(UTC).isoformat(),
            outcome="not_built",
            image_digest=None,
            reproducible=False,
        )

    def build_image(
        self,
        root_dir: Path,
        image_name: str,
        tag: str,
        dockerfile: Path | None = None,
        timeout_s: float = 120.0,
    ) -> ArtifactDescriptor:
        """Builds an image and records the image id the builder reported."""
        source_digest = self.calculate_source_digest(root_dir)
        raw = f"{image_name}:{tag}:{source_digest}".encode()
        metadata_digest = hashlib.sha256(raw).hexdigest()
        descriptor = ArtifactDescriptor(
            artifact_id=f"art-{metadata_digest[:12]}",
            image_tag=f"{image_name}:{tag}",
            metadata_digest=metadata_digest,
            source_digest=source_digest,
            created_at=datetime.now(UTC).isoformat(),
        )

        docker_bin = shutil.which("docker")
        dockerfile_path = root_dir / (dockerfile.name if dockerfile else "Dockerfile")
        if not docker_bin:
            descriptor.outcome = "not_built"
            descriptor.build_output = "docker CLI not available; no image was built"
            return descriptor
        if not dockerfile_path.exists():
            descriptor.outcome = "not_built"
            descriptor.build_output = f"missing build definition: {dockerfile_path}"
            return descriptor

        iidfile = root_dir / f".goldgraft-iid-{metadata_digest[:8]}"
        command = [docker_bin, "build", "-t", f"{image_name}:{tag}", "--iidfile", str(iidfile), "."]
        if dockerfile:
            command.extend(["-f", str(dockerfile)])
        try:
            proc = subprocess.run(
                command,
                cwd=str(root_dir),
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired:
            descriptor.outcome = "failed"
            descriptor.build_output = "docker build exceeded its timeout"
            return descriptor
        except OSError as exc:
            descriptor.outcome = "failed"
            descriptor.build_output = f"docker build could not start: {exc}"
            return descriptor

        log = proc.stdout + ("\nSTDERR:\n" + proc.stderr if proc.stderr else "")
        descriptor.build_output = log
        if proc.returncode != 0:
            descriptor.outcome = "failed"
            return descriptor

        observed: str | None = None
        try:
            if iidfile.is_file():
                observed = iidfile.read_text(encoding="utf-8").strip() or None
        finally:
            iidfile.unlink(missing_ok=True)

        if observed and observed.startswith("sha256:"):
            descriptor.image_digest = observed
            descriptor.outcome = "built_observed"
            descriptor.reproducible = False
        else:
            descriptor.outcome = "built_unverified"
            descriptor.build_output += (
                "\nNo image id was reported by the builder; this build has no exact artifact."
            )
        return descriptor
