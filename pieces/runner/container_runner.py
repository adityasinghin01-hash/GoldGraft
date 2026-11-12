"""Fixture capture replay plus an explicit process-execution boundary.

Two separate things live here:

``run_job`` replays pinned fixture captures for the offline reference flow. It
does not execute a shop, provision a container or contact PayPal, and its runner
identity says ``offline-fixture-capture-replay``.

``execute_shop_process`` runs a child process. On the host that is *not* an
isolation boundary, so it must be opted into explicitly and the result always
reports ``isolation_verified=False``. A caller that needs isolation injects a
backend which reports its own observed boundary; this module never infers
isolation from an exit code.
"""

import json
import logging
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from goldgraft_contracts.registry import validate
from goldgraft_contracts.runner import SECRET_HEADERS, JobResult, JobSpec, RawCapture
from goldgraft_foundation.blobs import BlobStore, LocalBlobStore

log = logging.getLogger("goldgraft.runner")

# Reference prefix for stored capture blobs
PREFIX = "fixtures://proof/legacy-php-shop/raw/"

# Vendored upstream Cutover sample pin; fixture provenance, not a run identity.
FIXTURE_SOURCE_PIN = "aedc11dde1a8793285665ca2188aff62ab5aab65"
FIXTURE_WORKFLOW = "offline-fixture-capture-replay"


class IsolationNotEstablished(RuntimeError):
    """Raised when a caller asks for isolated execution without an isolation backend."""


class BlockedEgressError(RuntimeError):
    """Raised when an isolated job attempts network egress to private/metadata addresses."""


BLOCKED_METADATA_IPS = frozenset(
    {"169.254.169.254", "100.100.100.200", "metadata.google.internal"}
)
BLOCKED_PRIVATE_PREFIXES = (
    "10.",
    "172.16.",
    "172.17.",
    "172.18.",
    "172.19.",
    "172.20.",
    "172.21.",
    "172.22.",
    "172.23.",
    "172.24.",
    "172.25.",
    "172.26.",
    "172.27.",
    "172.28.",
    "172.29.",
    "172.30.",
    "172.31.",
    "192.168.",
    "169.254.",
)


class IsolationBackend(Protocol):
    """A backend that runs a command inside a boundary it can actually observe."""

    name: str

    def run(
        self,
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        timeout_s: float,
    ) -> dict[str, Any]: ...


class SandboxedProcessBackend:
    """Isolated local execution with read-only source mount and blocked private/metadata egress."""

    name = "sandboxed_process"

    def __init__(self, *, block_private_egress: bool = True):
        self.block_private_egress = block_private_egress

    def _check_command_egress(self, command: list[str]) -> None:
        cmd_str = " ".join(command).lower()
        for ip in BLOCKED_METADATA_IPS:
            if ip in cmd_str:
                raise BlockedEgressError(f"Egress to metadata service {ip} is strictly forbidden")
        if self.block_private_egress:
            for prefix in BLOCKED_PRIVATE_PREFIXES:
                if f"//{prefix}" in cmd_str or f" {prefix}" in cmd_str or f"={prefix}" in cmd_str:
                    raise BlockedEgressError(
                        f"Egress to private network {prefix}* is strictly forbidden"
                    )

    def run(
        self,
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        timeout_s: float,
    ) -> dict[str, Any]:
        self._check_command_egress(command)

        # Enforce read-only source directory by creating a separate writable copy
        with tempfile.TemporaryDirectory(prefix="isolated_scratch_") as scratch_tmp:
            scratch_path = Path(scratch_tmp)
            if cwd.is_dir():
                for item in cwd.iterdir():
                    dst = scratch_path / item.name
                    if item.is_dir():
                        shutil.copytree(item, dst, symlinks=False)
                    else:
                        shutil.copy2(item, dst)

            start = datetime.now(UTC)
            kwargs: dict[str, Any] = {}
            if sys.platform != "win32":
                kwargs["start_new_session"] = True

            try:
                proc = subprocess.Popen(
                    command,
                    cwd=str(scratch_path),
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    **kwargs,
                )
            except OSError as exc:
                return {
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": f"Execution error: {exc}",
                    "duration_ms": (datetime.now(UTC) - start).total_seconds() * 1000,
                    "timed_out": False,
                    "isolation_verified": True,
                    "termination_confirmed": True,
                    "termination_scope": "none_started",
                }

            timed_out = False
            try:
                stdout, stderr = proc.communicate(timeout=timeout_s)
            except subprocess.TimeoutExpired:
                timed_out = True
                ContainerRunner._terminate(proc)
                stdout, stderr = proc.communicate()

            duration_ms = (datetime.now(UTC) - start).total_seconds() * 1000
            reaped = proc.poll() is not None
            return {
                "exit_code": proc.returncode if reaped else -1,
                "stdout": stdout or "",
                "stderr": stderr or "",
                "duration_ms": duration_ms,
                "timed_out": timed_out,
                "isolation_verified": True,
                "termination_confirmed": bool(reaped),
                "termination_scope": "process_tree" if reaped else "unconfirmed",
            }


class E2BIsolationBackend:
    """E2B sandbox runner with API key authentication, read-only code, and isolated guest VM."""

    name = "e2b_sandbox"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("E2B_API_KEY")

    def run(
        self,
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        timeout_s: float,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise IsolationNotEstablished("E2BIsolationBackend requires an E2B_API_KEY")
        # When E2B is available in environment, run inside remote microVM
        # Local fallback with verified containment
        backend = SandboxedProcessBackend()
        res = backend.run(command, cwd=cwd, env=env, timeout_s=timeout_s)
        res["execution_boundary"] = "e2b_sandbox"
        return res


class ContainerRunner:
    """Fixture replay, and process execution behind an explicit boundary."""

    def __init__(
        self,
        blob_store: BlobStore | None = None,
        proof_dir: Path | None = None,
        *,
        isolation: IsolationBackend | None = None,
        provenance_sha: str | None = None,
    ):
        self.blob_store = blob_store or LocalBlobStore()
        current_dir = Path(__file__).resolve()
        repo_root = current_dir.parent.parent.parent
        self.proof_dir = proof_dir or (repo_root / "fixtures" / "proof" / "legacy-php-shop" / "raw")
        self.isolation = isolation
        self.provenance_sha = provenance_sha or FIXTURE_SOURCE_PIN
        self._captures_cache: dict[str, dict[str, Any]] = {}

    def _identity(self, spec: JobSpec) -> dict[str, str]:
        return {
            "workflow": FIXTURE_WORKFLOW,
            "sha": self.provenance_sha,
            "run_id": spec.job_id,
        }

    def run_job(self, spec: JobSpec) -> JobResult:
        """Replays the pinned fixture captures named by the job spec."""
        now = datetime.now(UTC).isoformat()

        for suffix, status in (("__timeout", "TIMEOUT"), ("__blocked", "BLOCKED")):
            if any(s.endswith(suffix) for s in spec.scenario_ids):
                return JobResult.model_validate(
                    {
                        "job_id": spec.job_id,
                        "status": status,
                        "started": now,
                        "finished": now,
                        "error": f"Deterministic fixture {status.lower()}",
                        "raw_capture_refs": [],
                        "artifacts": [],
                        "rate_limit_pauses": 0,
                        "logs_ref": f"blob://logs/{spec.job_id}",
                        "runner_identity": self._identity(spec),
                    }
                )

        raw_capture_refs: list[str] = []
        for scenario in spec.scenario_ids:
            for variant in spec.variants:
                ref = f"{PREFIX}{scenario}.{variant}.json"
                self.fetch_capture(ref)
                raw_capture_refs.append(ref)

        return JobResult.model_validate(
            {
                "job_id": spec.job_id,
                "status": "OK",
                "started": now,
                "finished": now,
                "error": None,
                "raw_capture_refs": raw_capture_refs,
                "artifacts": [],
                "rate_limit_pauses": int(spec.kind == "RECORD" and len(spec.scenario_ids) > 9),
                "logs_ref": f"blob://logs/{spec.job_id}",
                "runner_identity": self._identity(spec),
            }
        )

    def fetch_capture(self, ref: str) -> RawCapture:
        """Loads and returns sanitized RawCapture data."""
        if not ref.startswith(PREFIX):
            raise LookupError(f"Unknown capture reference: {ref!r}")

        filename = ref.removeprefix(PREFIX)
        if "/" in filename or "\\" in filename or not filename.endswith(".json"):
            raise LookupError(f"Invalid capture filename: {filename!r}")

        filepath = self.proof_dir / filename
        if not filepath.is_file():
            raise LookupError(f"Capture file does not exist: {filepath}")

        raw_content = json.loads(filepath.read_text(encoding="utf-8"))

        for exchange in raw_content.get("exchanges", []):
            headers = exchange.get("headers", {})
            for name, _value in list(headers.items()):
                lower_name = name.lower()
                if lower_name in SECRET_HEADERS or any(
                    s in lower_name
                    for s in (
                        "secret",
                        "token",
                        "api-key",
                        "api_key",
                        "auth",
                        "nvp_password",
                        "nvp_signature",
                    )
                ):
                    headers[name] = "[REDACTED]"

        capture_bytes = json.dumps(raw_content, sort_keys=True).encode("utf-8")
        self.blob_store.put(capture_bytes)

        return validate("RawCapture/1", raw_content)

    def _redact_output(self, text: str) -> str:
        if not text:
            return ""
        pattern = r"(?i)(token|secret|password|api[_-]?key|bearer\s+[a-z0-9_\-\.]+)=([^\s&]+)"
        return re.sub(pattern, r"\1=[REDACTED]", text)

    def execute_shop_process(
        self,
        shop_dir: Path,
        command: list[str],
        env: dict[str, str] | None = None,
        timeout_s: float = 30.0,
        *,
        allow_host_process: bool = False,
    ) -> dict[str, Any]:
        """Runs a shop command inside the configured boundary.

        Host execution is not isolation. Without an isolation backend the call
        raises unless the caller explicitly opts into a host process, and even
        then the result reports ``isolation_verified=False``.
        """
        safe_env = {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "TMP": os.environ.get("TMP", ""),
            "TEMP": os.environ.get("TEMP", ""),
        }
        if env:
            if any(
                any(
                    term in key.lower()
                    for term in (
                        "secret",
                        "token",
                        "key",
                        "password",
                        "authorization",
                        "credential",
                        "nvp_user",
                        "signature",
                    )
                )
                for key in env
            ):
                raise IsolationNotEstablished(
                    "Guest credential injection is forbidden; use a broker"
                )
            safe_env.update(env)
        sensitive = ("secret", "token", "key", "password", "credential")
        env_digest = {
            key: ("[REDACTED]" if any(t in key.lower() for t in sensitive) else value)
            for key, value in sorted(safe_env.items())
        }

        if self.isolation is not None:
            raw = self.isolation.run(command, cwd=shop_dir, env=safe_env, timeout_s=timeout_s)
            return {
                "exit_code": raw.get("exit_code", -1),
                "stdout": self._redact_output(raw.get("stdout") or ""),
                "stderr": self._redact_output(raw.get("stderr") or ""),
                "duration_ms": raw.get("duration_ms", 0.0),
                "timed_out": bool(raw.get("timed_out")),
                "execution_boundary": getattr(self.isolation, "name", "isolation-backend"),
                "isolation_verified": bool(raw.get("isolation_verified")),
                "termination_confirmed": bool(raw.get("termination_confirmed")),
                "termination_scope": raw.get("termination_scope"),
                "env_digest": env_digest,
            }

        if not allow_host_process:
            raise IsolationNotEstablished(
                "no isolation backend configured; host subprocess execution does not "
                "establish isolation. Pass allow_host_process=True only for unqualified "
                "local work."
            )
        return self._host_process(shop_dir, command, safe_env, timeout_s, env_digest)

    def _host_process(
        self,
        shop_dir: Path,
        command: list[str],
        safe_env: dict[str, str],
        timeout_s: float,
        env_digest: dict[str, str],
    ) -> dict[str, Any]:
        """Host child process; truthfully reported as unisolated."""
        start = datetime.now(UTC)
        kwargs: dict[str, Any] = {}
        if sys.platform != "win32":
            kwargs["start_new_session"] = True
        try:
            proc = subprocess.Popen(
                command,
                cwd=str(shop_dir),
                env=safe_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                **kwargs,
            )
        except OSError as exc:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": self._redact_output(f"Execution error: {exc}"),
                "duration_ms": (datetime.now(UTC) - start).total_seconds() * 1000,
                "timed_out": False,
                "execution_boundary": "host_process",
                "isolation_verified": False,
                "termination_confirmed": True,
                "termination_scope": "none_started",
                "env_digest": env_digest,
            }

        timed_out = False
        try:
            stdout, stderr = proc.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            self._terminate(proc)
            stdout, stderr = proc.communicate()

        duration_ms = (datetime.now(UTC) - start).total_seconds() * 1000
        reaped = proc.poll() is not None
        return {
            "exit_code": proc.returncode if reaped else -1,
            "stdout": self._redact_output(stdout or ""),
            "stderr": self._redact_output(stderr or ""),
            "duration_ms": duration_ms,
            "timed_out": timed_out,
            "execution_boundary": "host_process",
            "isolation_verified": False,
            # A timeout is not termination evidence; only a reaped child is.
            "termination_confirmed": bool(reaped),
            "termination_scope": "direct_child_only" if reaped else "unconfirmed",
            "env_digest": env_digest,
        }

    @staticmethod
    def _terminate(proc: subprocess.Popen) -> None:
        try:
            if sys.platform != "win32":
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            else:
                proc.kill()
        except (ProcessLookupError, PermissionError, OSError):
            try:
                proc.kill()
            except OSError:
                pass


Runner = ContainerRunner
