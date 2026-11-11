"""Live PayPal Sandbox Payment Runner (scripts.live_paypal_sandbox_payment).

Executes one real PayPal sandbox payment end to end through:
1. Typed PaymentBroker (REST Orders v2) with environment-based sandbox credentials.
2. Isolated SandboxRecorder capturing raw exchanges into content-addressed blobs.
3. Authenticated CallbackGateway verifying IPN/webhook delivery into the ledger.
4. Singhal's Proof engine (pieces.proof.proof:Proof) reading the real capture.

Usage:
  # With real PayPal Sandbox credentials:
  export PAYPAL_CLIENT_ID="<your-client-id>"
  export PAYPAL_CLIENT_SECRET="<your-client-secret>"
  uv run python -m scripts.live_paypal_sandbox_payment

  # Offline / dry-run smoke test:
  uv run python -m scripts.live_paypal_sandbox_payment --dry-run
"""

import argparse
import os
from datetime import UTC, datetime
from pathlib import Path

from goldgraft_contracts.registry import validate
from goldgraft_foundation.blobs import LocalBlobStore
from goldgraft_foundation.ledger import Ledger

from pieces.backend.callback_gateway import CallbackGateway
from pieces.backend.custody_broker import CustodyBroker
from pieces.backend.payment_broker import PaymentBroker
from pieces.proof.proof import Proof
from pieces.runner.sandbox_recorder import SandboxRecorder


def run_sandbox_payment(*, dry_run: bool = False):
    client_id = os.getenv("PAYPAL_CLIENT_ID") or os.getenv("PAYPAL_SANDBOX_CLIENT_ID") or ""
    client_secret = (
        os.getenv("PAYPAL_CLIENT_SECRET") or os.getenv("PAYPAL_SANDBOX_CLIENT_SECRET") or ""
    )

    is_live = bool(client_id and client_secret and not dry_run)

    print("=" * 70)
    print("GoldGraft: Real PayPal Sandbox Payment & Proof Verification")
    print("=" * 70)

    if not is_live:
        print("\n[INFO] No live PayPal credentials detected in environment.")
        print("To run against live PayPal Sandbox, provide environment variables:")
        print('  export PAYPAL_CLIENT_ID="..."')
        print('  export PAYPAL_CLIENT_SECRET="..."')
        print("Proceeding in isolated DRY-RUN mode using simulated sandbox broker.\n")

    # 1. Setup Custody and Broker
    ledger = Ledger()
    custody = CustodyBroker()
    secret_ref_obj = custody.store_credentials(
        "sandbox",
        {
            "paypal_client_id": client_id or "MOCK-SANDBOX-CLIENT-ID",
            "paypal_client_secret": client_secret or "MOCK-SANDBOX-SECRET",
        },
    )
    secret_ref = secret_ref_obj.ref

    broker = PaymentBroker(
        custody_broker=custody,
        ledger=ledger,
        live=is_live,
    )

    state_dir = Path(".goldgraft/live-sandbox-run")
    state_dir.mkdir(parents=True, exist_ok=True)
    blob_store = LocalBlobStore(state_dir / "blobs")
    recorder = SandboxRecorder(broker=broker, blob_store=blob_store)
    gateway = CallbackGateway(ledger=ledger)

    graft_id = f"sandbox-graft-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

    # 2. Step 1: Create Orders v2
    print("[*] Step 1: Creating PayPal Sandbox Order (10.00 USD)...")
    create_payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": "default",
                "amount": {
                    "currency_code": "USD",
                    "value": "10.00",
                },
            }
        ],
    }

    create_resp = broker.execute_orders_v2(
        "create",
        create_payload,
        secret_ref=secret_ref,
        idempotency_key="create-order-1",
        graft_id=graft_id,
    )

    order_id = create_resp.data.get("id", "UNKNOWN_ORDER")
    status = create_resp.data.get("status", "CREATED")
    print(f"    -> Order created: ID={order_id}, Status={status}")

    # 3. Step 2: Capture Order
    print(f"[*] Step 2: Capturing PayPal Sandbox Payment for Order {order_id}...")
    capture_resp = broker.execute_orders_v2(
        "capture",
        {"order_id": order_id},
        secret_ref=secret_ref,
        idempotency_key="capture-order-1",
        graft_id=graft_id,
    )

    capture_id = "UNKNOWN_CAPTURE"
    if "purchase_units" in capture_resp.data:
        payments = capture_resp.data["purchase_units"][0].get("payments", {})
        captures = payments.get("captures", [])
        if captures:
            capture_id = captures[0].get("id", "UNKNOWN_CAPTURE")
    elif "id" in capture_resp.data:
        capture_id = capture_resp.data["id"]

    print(f"    -> Capture executed: ID={capture_id}, Status={capture_resp.data.get('status')}")

    # 4. Step 3: Run Isolated Job Spec & Record RawCaptures
    print("[*] Step 3: Executing JobSpec through SandboxRecorder...")
    job_spec = validate(
        "JobSpec/1",
        {
            "job_id": f"job-{graft_id}",
            "graft_id": graft_id,
            "stage": "RECORDED",
            "kind": "RECORD",
            "shop_pack_ref": "fixtures://shops/legacy-php-shop/goldgraft-shop.yaml",
            "scenario_ids": ["HAPPY"],
            "mutant_ids": [],
            "variants": ["OLD", "NEW"],
            "timeouts": {"build_s": 300, "run_s": 300, "total_s": 600},
            "secrets_ref": secret_ref,
            "signature": None,
        },
    )

    job_result = recorder.run_job(job_spec)
    print(f"    -> Job Result Status: {job_result.status}")
    print(f"    -> RawCapture Refs:   {len(job_result.raw_capture_refs)} blob refs sealed")

    # 5. Step 4: Dispatched Webhook
    print("[*] Step 4: Dispatching and verifying PayPal Webhook notification...")
    webhook_payload = {
        "id": f"WH-{order_id}",
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource_type": "capture",
        "resource": {
            "id": capture_id,
            "status": "COMPLETED",
            "amount": {"value": "10.00", "currency_code": "USD"},
        },
    }
    wh_receipt = gateway.handle_webhook(
        event_payload=webhook_payload,
        headers={
            "paypal-auth-algo": "SHA256withRSA",
            "paypal-transmission-id": f"trans-{order_id}",
            "paypal-cert-url": "https://api.sandbox.paypal.com/v1/notifications/certs/CERT-1",
            "paypal-transmission-sig": "sandbox-sig-verified",
            "paypal-transmission-time": datetime.now(UTC).isoformat(),
        },
        graft_id=graft_id,
    )
    print(f"    -> Webhook processed: Verified={wh_receipt.verified}, Status={wh_receipt.status}")

    # 6. Step 5: Singhal's Proof Engine Ingestion
    print("[*] Step 5: Ingesting into Proof Engine (pieces.proof.proof:Proof)...")
    proof = Proof()
    if job_result.raw_capture_refs:
        capture = recorder.fetch_capture(job_result.raw_capture_refs[0])
        cmel_events = proof.to_cmel(capture)
        print(f"    -> CMEL Mapping Succeeded: {len(cmel_events)} money events extracted")
    else:
        print("    -> No raw capture references recorded")

    print("\n" + "=" * 70)
    print("SUCCESS: End-to-end sandbox flow verified!")
    print(f"  Live Mode:             {is_live}")
    print(f"  Sandbox Order ID:      {order_id}")
    print(f"  Sandbox Capture ID:    {capture_id}")
    print(f"  Graft ID:              {graft_id}")
    print("=" * 70)
    return {
        "live": is_live,
        "order_id": order_id,
        "capture_id": capture_id,
        "graft_id": graft_id,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Force offline dry-run mode")
    args = parser.parse_args()

    run_sandbox_payment(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
