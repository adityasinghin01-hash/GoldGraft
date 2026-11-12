"""PR6 synthetic recorder with durable capture retrieval through the shared Runner port.

This implementation generates exchanges in-process. It does not provision
isolation, execute shop scenarios or contact PayPal. Production GU04 remains held.
"""

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from goldgraft_contracts.offline_payments import OfflinePayments, PaymentAccessDenied
from goldgraft_contracts.registry import validate
from goldgraft_contracts.runner import JobResult, JobSpec, RawCapture
from goldgraft_foundation.blobs import BlobStore, LocalBlobStore

log = logging.getLogger("goldgraft.sandbox_recorder")


class SandboxRecorder:
    """Records PR6 synthetic exchanges; does not execute or isolate a shop."""

    evidence_class = "scripted"

    def __init__(
        self,
        broker: OfflinePayments,
        blob_store: BlobStore | None = None,
        repo_root: Path | None = None,
    ):
        if broker.evidence_class not in ("scripted", "real_sandbox", "qualified"):
            raise ValueError("UNQUALIFIED recorder accepts synthetic brokers only")
        self.broker = broker
        self.blob_store = blob_store or LocalBlobStore()
        current_dir = Path(__file__).resolve()
        self.repo_root = repo_root or current_dir.parent.parent.parent
        self._captures_store: dict[str, dict[str, Any]] = {}

    def run_job(self, spec: JobSpec) -> JobResult:
        """Shared Runner interface; successful output remains synthetic evidence."""
        return self.run_isolated_job(spec)

    def run_isolated_job(self, spec: JobSpec) -> JobResult:
        """Compatibility entry point for synthetic scenario/variant exchange generation."""
        now = datetime.now(UTC).isoformat()

        # Enforce valid secret resolution before beginning work
        try:
            self.broker.resolve_and_verify(spec.secrets_ref)
        except PaymentAccessDenied as err:
            return JobResult.model_validate(
                {
                    "job_id": spec.job_id,
                    "status": "BLOCKED",
                    "started": now,
                    "finished": now,
                    "error": str(err),
                    "raw_capture_refs": [],
                    "artifacts": [],
                    "rate_limit_pauses": 0,
                    "logs_ref": f"blob://logs/{spec.job_id}",
                    "runner_identity": {
                        "workflow": "offline-simulated-recorder",
                        "sha": "UNQUALIFIED-SYNTHETIC",
                        "run_id": spec.job_id,
                    },
                }
            )

        # Handle timeout scenarios
        if any(s.endswith("__timeout") for s in spec.scenario_ids):
            return JobResult.model_validate(
                {
                    "job_id": spec.job_id,
                    "status": "TIMEOUT",
                    "started": now,
                    "finished": now,
                    "error": "Execution exceeded timeout limits",
                    "raw_capture_refs": [],
                    "artifacts": [],
                    "rate_limit_pauses": 0,
                    "logs_ref": f"blob://logs/{spec.job_id}",
                    "runner_identity": {
                        "workflow": "offline-simulated-recorder",
                        "sha": "UNQUALIFIED-SYNTHETIC",
                        "run_id": spec.job_id,
                    },
                }
            )

        raw_capture_refs: list[str] = []

        for scenario in spec.scenario_ids:
            for variant in spec.variants:
                capture_data = self._record_scenario_exchange(spec, scenario, variant)
                # Store in blob store
                capture_bytes = json.dumps(capture_data, sort_keys=True).encode("utf-8")
                capture_ref = self.blob_store.put(capture_bytes)
                self._captures_store[capture_ref] = capture_data
                raw_capture_refs.append(capture_ref)

        return JobResult.model_validate(
            {
                "job_id": spec.job_id,
                "status": "OK",
                "started": now,
                "finished": now,
                "error": None,
                "raw_capture_refs": raw_capture_refs,
                "artifacts": [],
                "rate_limit_pauses": 0,
                "logs_ref": f"blob://logs/{spec.job_id}",
                "runner_identity": {
                    "workflow": "offline-simulated-recorder",
                    "sha": "UNQUALIFIED-SYNTHETIC",
                    "run_id": spec.job_id,
                },
            }
        )

    def _record_scenario_exchange(
        self, spec: JobSpec, scenario_id: str, variant: str
    ) -> dict[str, Any]:
        """Simulates and records the HTTP exchanges for a given scenario variant."""
        datetime.now(UTC)

        # Execute broker call depending on variant
        if variant in ("OLD", "OLD_TWIN"):
            broker_resp = self.broker.execute_nvp(
                "SetExpressCheckout",
                {"AMT": "10.00", "CURRENCYCODE": "USD"},
                secret_ref=spec.secrets_ref,
                graft_id=spec.graft_id,
            )
            req_url = "https://api-3t.sandbox.paypal.com/nvp"
        else:
            broker_resp = self.broker.execute_orders_v2(
                "create",
                {
                    "intent": "CAPTURE",
                    "purchase_units": [{"amount": {"currency_code": "USD", "value": "10.00"}}],
                },
                secret_ref=spec.secrets_ref,
                graft_id=spec.graft_id,
            )
            req_url = "https://api-m.sandbox.paypal.com/v2/checkout/orders"

        sanitized_headers = {
            "content-type": "application/json",
            "authorization": "[REDACTED]",
            "x-paypal-client-metadata-id": hashlib.sha256(scenario_id.encode()).hexdigest()[:16],
        }

        exchanges = [
            {
                "seq": 1,
                "t_ms": 12,
                "direction": "SHOP_TO_PAYPAL",
                "method": "POST",
                "url": req_url,
                "headers": sanitized_headers,
                "body_json": broker_resp.data,
                "status": broker_resp.status_code,
            }
        ]

        return {
            "graft_id": spec.graft_id,
            "run_id": spec.job_id,
            "variant": variant,
            "scenario_id": scenario_id,
            "exchanges": exchanges,
        }

    def fetch_capture(self, ref: str) -> RawCapture:
        """Fetches and validates a recorded capture."""
        if ref.startswith("blob://"):
            return validate("RawCapture/1", json.loads(self.blob_store.get(ref)))
        if ref not in self._captures_store:
            # Fall back to fixture capture if available
            prefix = "fixtures://proof/legacy-php-shop/raw/"
            if ref.startswith(prefix):
                name = ref.removeprefix(prefix)
                if "/" in name or "\\" in name or not name.endswith(".json"):
                    raise LookupError("Invalid fixture capture reference")
                path = self.repo_root / "fixtures" / "proof" / "legacy-php-shop" / "raw" / name
                if path.is_file():
                    data = json.loads(path.read_text(encoding="utf-8"))
                    return validate("RawCapture/1", data)
            raise LookupError(f"Capture reference not found: {ref!r}")

        return validate("RawCapture/1", self._captures_store[ref])
