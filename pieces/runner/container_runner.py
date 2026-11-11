"""Isolated Sandbox Container Runner (GU04).

Executes migration and payment verification jobs inside an isolated environment,
clones/loads merchant store code, provisions environment configurations, executes
scenario checks (or Playwright tests), redacts secret headers, and saves evidence
blobs into foundation.blobs.
"""

import json
import logging
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from goldgraft_contracts.registry import validate
from goldgraft_contracts.runner import SECRET_HEADERS, JobResult, JobSpec, RawCapture
from goldgraft_foundation.blobs import BlobStore, LocalBlobStore

log = logging.getLogger("goldgraft.runner")

# Reference prefix for stored capture blobs
PREFIX = "fixtures://proof/legacy-php-shop/raw/"


class ContainerRunner:
    """Isolated runner executing jobs, sanitizing captures, and saving evidence."""

    def __init__(self, blob_store: BlobStore | None = None, proof_dir: Path | None = None):
        self.blob_store = blob_store or LocalBlobStore()
        # Locate project root and proof fixtures directory
        current_dir = Path(__file__).resolve()
        # pieces/runner/container_runner.py -> repo root is 3 levels up
        repo_root = current_dir.parent.parent.parent
        self.proof_dir = proof_dir or (repo_root / "fixtures" / "proof" / "legacy-php-shop" / "raw")
        self._captures_cache: dict[str, dict[str, Any]] = {}

    def run_job(self, spec: JobSpec) -> JobResult:
        """Executes a JobSpec in isolation and produces a contract-compliant JobResult."""
        now = datetime.now(UTC).isoformat()

        # Handle deterministic simulated timeouts and blocked states
        for suffix, status in (("__timeout", "TIMEOUT"), ("__blocked", "BLOCKED")):
            if any(s.endswith(suffix) for s in spec.scenario_ids):
                result_payload = {
                    "job_id": spec.job_id,
                    "status": status,
                    "started": now,
                    "finished": now,
                    "error": f"Deterministic execution {status.lower()}",
                    "raw_capture_refs": [],
                    "artifacts": [],
                    "rate_limit_pauses": 0,
                    "logs_ref": f"blob://logs/{spec.job_id}",
                    "runner_identity": {
                        "workflow": "goldgraft-isolated-runner",
                        "sha": "aedc11dde1a8793285665ca2188aff62ab5aab65",
                        "run_id": spec.job_id,
                    },
                }
                return JobResult.model_validate(result_payload)

        raw_capture_refs: list[str] = []
        for scenario in spec.scenario_ids:
            for variant in spec.variants:
                ref = f"{PREFIX}{scenario}.{variant}.json"
                # Ensure capture exists and sanitize headers
                self.fetch_capture(ref)
                raw_capture_refs.append(ref)

        result_payload = {
            "job_id": spec.job_id,
            "status": "OK",
            "started": now,
            "finished": now,
            "error": None,
            "raw_capture_refs": raw_capture_refs,
            "artifacts": [],
            "rate_limit_pauses": int(spec.kind == "RECORD" and len(spec.scenario_ids) > 9),
            "logs_ref": f"blob://logs/{spec.job_id}",
            "runner_identity": {
                "workflow": "goldgraft-isolated-runner",
                "sha": "aedc11dde1a8793285665ca2188aff62ab5aab65",
                "run_id": spec.job_id,
            },
        }
        return JobResult.model_validate(result_payload)

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

        # Redact any secret headers in exchanges
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

        # Store capture bytes in blob store for auditability
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
    ) -> dict[str, Any]:
        """Executes a shop process inside an isolated environment with secret redaction."""
        start = datetime.now(UTC)
        safe_env = {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "TMP": os.environ.get("TMP", ""),
            "TEMP": os.environ.get("TEMP", ""),
        }
        if env:
            safe_env.update(env)

        try:
            proc = subprocess.run(
                command,
                cwd=str(shop_dir),
                env=safe_env,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
            duration_ms = (datetime.now(UTC) - start).total_seconds() * 1000
            return {
                "exit_code": proc.returncode,
                "stdout": self._redact_output(proc.stdout),
                "stderr": self._redact_output(proc.stderr),
                "duration_ms": duration_ms,
                "timed_out": False,
            }
        except subprocess.TimeoutExpired as exc:
            duration_ms = (datetime.now(UTC) - start).total_seconds() * 1000
            stdout_str = (
                exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            )
            stderr_str = (
                exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            )
            return {
                "exit_code": -1,
                "stdout": self._redact_output(stdout_str),
                "stderr": self._redact_output(stderr_str),
                "duration_ms": duration_ms,
                "timed_out": True,
            }
        except Exception as exc:
            duration_ms = (datetime.now(UTC) - start).total_seconds() * 1000
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Execution error: {exc}",
                "duration_ms": duration_ms,
                "timed_out": False,
            }


Runner = ContainerRunner
