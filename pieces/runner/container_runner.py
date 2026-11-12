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
import signal
import subprocess
import sys
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
