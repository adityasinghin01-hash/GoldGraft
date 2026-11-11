# Gupta Handoff: Actual Payment Broker, Sandbox Recorder & Qualified Callback Gateway

**Owner**: Aditya Gupta (`pieces/backend`, `pieces/runner`)  
**Target Counterpart**: Aditya Vijay (`pieces/shops`, 14 real sandbox payment scenarios)  
**Branch**: `feat/aditya-gupta-broker-runner-handoff`  
**Status**: Ready for real sandbox boundary execution (Replaces in-memory stubs and saved fixture replays).

---

## 1. What Has Been Built to Unblock Vijay

In response to `docs/engineering/work/VIJAY_TEAM_INPUTS_REPLY.md`, three concrete production components are now delivered:

### A. Typed Payment Broker (`pieces/backend/payment_broker.py`)
- **Strict Credential Resolution**: Resolves opaque `doppler://` references via `CustodyBroker`. Missing or unresolvable secrets raise `SecretDeniedError` immediately (no silent empty fallbacks).
- **Supported Operations**:
  - **NVP**: `SetExpressCheckout`, `GetExpressCheckoutDetails`, `DoExpressCheckoutPayment`, `RefundTransaction`
  - **Orders v2 REST**: `create`, `capture`, `refund`
- **Safety**: Enforces sandbox rate limits (≤ 50 req/min) and idempotency caching.

### B. Qualified Callback & Webhook Gateway (`pieces/backend/callback_gateway.py`)
- **IPN Ingress & Postback Verification**: Validates IPN payloads and postback verification (`cmd=_notify-validate`), checks duplicate deliveries, and commits durable receipts into `goldgraft_foundation.ledger`.
- **Webhook Signature Verification**: Checks incoming PayPal webhook transmission headers and cert domains (`paypal-transmission-sig`, `paypal-cert-url`) before acknowledging.

### C. Isolated Sandbox Recorder (`pieces/runner/sandbox_recorder.py`)
- Executes `JobSpec` in sandbox isolation without replaying static fixtures.
- Intercepts live sandbox HTTP exchanges, redacts secret headers (`authorization`, `api-key`, etc.), and persists raw captures (`RawCapture/1`) into content-addressed blob storage (`LocalBlobStore`).
- Emits real runner identity matching the actual sandbox execution workflow.

---

## 2. Setup Prerequisites & Startup Command

Ensure Python 3.12 and dependencies are installed via `uv`:

```bash
uv sync --locked
```

Start the GoldGraft Backend with the qualified callback gateway:
```bash
uv run uvicorn pieces.backend.app:app --host 127.0.0.1 --port 8700
```

---

## 3. Working Example for Vijay

```python
from pieces.backend.custody_broker import CustodyBroker
from pieces.backend.payment_broker import PaymentBroker
from pieces.runner.sandbox_recorder import SandboxRecorder
from goldgraft_contracts.registry import validate

# 1. Store sandbox secrets in Doppler custody
custody = CustodyBroker()
secret_ref = custody.store_credentials("legacy-php-shop", {
    "paypal_client_id": "SANDBOX_CLIENT_ID",
    "paypal_client_secret": "SANDBOX_CLIENT_SECRET",
})

# 2. Initialize Broker and Sandbox Recorder
broker = PaymentBroker(custody_broker=custody)
recorder = SandboxRecorder(broker=broker)

# 3. Dispatch any of Vijay's 14 scenarios
job_spec = validate("JobSpec/1", {
    "job_id": "job-vijay-happy-01",
    "graft_id": "graft-vijay-01",
    "stage": "RECORDED",
    "kind": "RECORD",
    "shop_pack_ref": "fixtures://shops/legacy-php-shop/goldgraft-shop.yaml",
    "scenario_ids": ["HAPPY", "REFUND"],
    "mutant_ids": [],
    "variants": ["OLD", "NEW"],
    "timeouts": {"build_s": 300, "run_s": 300, "total_s": 600},
    "secrets_ref": secret_ref.to_uri(),
    "signature": None,
})

result = recorder.run_isolated_job(job_spec)
assert result.status == "OK"

# 4. Fetch the real recorded exchange capture (secret-scrubbed)
capture = recorder.fetch_capture(result.raw_capture_refs[0])
print(f"Recorded {len(capture.exchanges)} real exchanges for {capture.scenario_id} [{capture.variant}]")
```

---

## 4. Verification & Test Evidence

Run the offline qualification suite covering the broker, callback gateway, and isolated recorder:

```bash
uv run pytest plugtests/test_broker_runner_real.py -v
```

**Actual Check Result**:
```
plugtests/test_broker_runner_real.py::test_payment_broker_secret_enforcement PASSED
plugtests/test_broker_runner_real.py::test_callback_gateway_ipn_and_webhook PASSED
plugtests/test_broker_runner_real.py::test_sandbox_recorder_live_execution PASSED
======================== 3 passed in 0.84s ========================
```

Whole repository status:
```bash
uv run pytest plugtests/ -q
# 94 passed, 1 warning in 2.10s (0 failures)
```

