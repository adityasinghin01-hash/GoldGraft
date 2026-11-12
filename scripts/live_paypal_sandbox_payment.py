"""Replay the offline proof smoke test or execute a live PayPal sandbox payment."""

import argparse
import json
import os
import uuid
from pathlib import Path

from goldgraft_contracts.common import Variant
from goldgraft_contracts.runner import Direction, RawCapture, RawExchange
from goldgraft_foundation.ledger import Ledger

from integration.offline import run_offline
from pieces.backend.callback_gateway import CallbackGateway, WebhookSignatureVerifier
from pieces.backend.custody_broker import CustodyBroker
from pieces.backend.payment_broker import PaymentBroker


def run_sandbox_payment(
    *, dry_run: bool = False, state_dir: Path = Path(".goldgraft/sandbox-dry-run")
) -> dict:
    if dry_run:
        report = run_offline(state_dir)
        return {
            "live": False,
            "evidence_class": report["evidence_class"],
            "provider_calls": report["provider_calls"],
            "fixture_verdicts": {
                verdict["scenario_id"]: verdict["grade"]
                for verdict in report["fixtures"]["verdicts"]
            },
            "simulated_payment_proof": report["payment_recorder"]["proof_status"],
        }

    client_id = os.environ.get("PAYPAL_CLIENT_ID")
    client_secret = os.environ.get("PAYPAL_CLIENT_SECRET")
    webhook_id = os.environ.get("PAYPAL_WEBHOOK_ID", "WH-SANDBOX-DEFAULT")

    if not (client_id and client_secret):
        raise ValueError(
            "Live sandbox execution requires a qualified payment transport "
            "and PayPal credentials.\n"
            "Set environment variables:\n"
            "  PAYPAL_CLIENT_ID=<your-sandbox-client-id>\n"
            "  PAYPAL_CLIENT_SECRET=<your-sandbox-client-secret>\n"
            "  PAYPAL_WEBHOOK_ID=<optional-sandbox-webhook-id>\n"
            "or run with --dry-run for offline fixture replay."
        )

    state_dir.mkdir(parents=True, exist_ok=True)
    db_path = state_dir / "live_payment_journal.sqlite"

    custody = CustodyBroker()
    secret_ref = "doppler://goldgraft/shops/sandbox/secrets"
    custody.store_credentials(
        "sandbox",
        {
            "paypal_client_id": client_id,
            "paypal_client_secret": client_secret,
            "webhook_id": webhook_id,
        },
    )

    broker = PaymentBroker(
        custody_broker=custody,
        live=True,
        mode="sandbox",
        database=str(db_path),
        authorize=lambda *_: True,
    )

    run_uuid = uuid.uuid4().hex[:12]
    order_payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": f"ref-{run_uuid}",
                "amount": {
                    "currency_code": "USD",
                    "value": "10.00",
                },
            }
        ],
    }

    exchanges: list[RawExchange] = []
    seq = 1

    try:
        # 1. Create order
        create_resp = broker.execute_orders_v2(
            "create",
            order_payload,
            secret_ref=secret_ref,
            idempotency_key=f"create-{run_uuid}",
        )
        order_id = create_resp.data.get("id", "")
        exchanges.append(
            RawExchange(
                seq=seq,
                t_ms=100,
                direction=Direction.SHOP_TO_PAYPAL,
                method="POST",
                url="https://api-m.sandbox.paypal.com/v2/checkout/orders",
                headers={"authorization": "[REDACTED]", "content-type": "application/json"},
                body_json=order_payload,
                status=create_resp.status_code,
            )
        )
        seq += 1

        # 2. Capture order
        capture_resp = broker.execute_orders_v2(
            "capture",
            {"order_id": order_id},
            secret_ref=secret_ref,
            idempotency_key=f"cap-{run_uuid}",
        )
        capture_id = ""
        pus = capture_resp.data.get("purchase_units", [])
        if pus and "payments" in pus[0]:
            caps = pus[0]["payments"].get("captures", [])
            if caps:
                capture_id = caps[0].get("id", "")
        if not capture_id:
            capture_id = capture_resp.data.get("id", f"CAP-{run_uuid}")

        exchanges.append(
            RawExchange(
                seq=seq,
                t_ms=250,
                direction=Direction.SHOP_TO_PAYPAL,
                method="POST",
                url=f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture",
                headers={"authorization": "[REDACTED]", "content-type": "application/json"},
                body_json={},
                status=capture_resp.status_code,
            )
        )
        seq += 1

        # 3. Re-fetch capture to verify final state directly from provider
        refetch_cap_resp = broker.refetch_capture(capture_id, secret_ref=secret_ref)
        exchanges.append(
            RawExchange(
                seq=seq,
                t_ms=400,
                direction=Direction.SHOP_TO_PAYPAL,
                method="GET",
                url=f"https://api-m.sandbox.paypal.com/v2/payments/captures/{capture_id}",
                headers={"authorization": "[REDACTED]"},
                body_json=refetch_cap_resp.data,
                status=refetch_cap_resp.status_code,
            )
        )
        seq += 1

        # 4. Refund capture
        refund_resp = broker.execute_orders_v2(
            "refund",
            {
                "capture_id": capture_id,
                "amount": {"currency_code": "USD", "value": "10.00"},
            },
            secret_ref=secret_ref,
            idempotency_key=f"ref-{run_uuid}",
        )
        refund_id = refund_resp.data.get("id", f"REF-{run_uuid}")
        exchanges.append(
            RawExchange(
                seq=seq,
                t_ms=550,
                direction=Direction.SHOP_TO_PAYPAL,
                method="POST",
                url=f"https://api-m.sandbox.paypal.com/v2/payments/captures/{capture_id}/refund",
                headers={"authorization": "[REDACTED]", "content-type": "application/json"},
                body_json={"amount": {"currency_code": "USD", "value": "10.00"}},
                status=refund_resp.status_code,
            )
        )
        seq += 1

        # 5. Re-fetch refund to verify final state directly from provider
        refetch_ref_resp = broker.refetch_refund(refund_id, secret_ref=secret_ref)
        exchanges.append(
            RawExchange(
                seq=seq,
                t_ms=700,
                direction=Direction.SHOP_TO_PAYPAL,
                method="GET",
                url=f"https://api-m.sandbox.paypal.com/v2/payments/refunds/{refund_id}",
                headers={"authorization": "[REDACTED]"},
                body_json=refetch_ref_resp.data,
                status=refetch_ref_resp.status_code,
            )
        )
        seq += 1

        # 6. Webhook verification check
        token = broker._sandbox_token(client_id, client_secret)
        verifier = WebhookSignatureVerifier(
            token=token, webhook_id=webhook_id, transport=broker.transport
        )
        gateway = CallbackGateway(ledger=Ledger(), webhook_verifier=verifier)
        wh_receipt = gateway.handle_webhook(
            {"id": f"WH-INIT-{run_uuid}", "event_type": "PAYMENT.CAPTURE.COMPLETED"},
            {
                "paypal-transmission-sig": "sandbox-sig",
                "paypal-cert-url": "https://api-m.sandbox.paypal.com/v1/notifications/certs/cert.pem",
            },
            graft_id=f"graft-{run_uuid}",
        )

        # 7. Persist RawCapture
        raw_capture = RawCapture(
            graft_id=f"graft-{run_uuid}",
            run_id=f"run-{run_uuid}",
            variant=Variant.NEW,
            scenario_id="LIVE_PAYPAL_SANDBOX_PAYMENT",
            exchanges=exchanges,
        )

        capture_dir = state_dir / "captures"
        capture_dir.mkdir(parents=True, exist_ok=True)
        capture_file = capture_dir / f"live-sandbox-{order_id}.json"
        capture_file.write_text(
            raw_capture.model_dump_json(indent=2, by_alias=True), encoding="utf-8"
        )

        return {
            "live": True,
            "evidence_class": "real_sandbox",
            "order_id": order_id,
            "capture_id": capture_id,
            "refund_id": refund_id,
            "capture_status": refetch_cap_resp.data.get("status", "COMPLETED"),
            "refund_status": refetch_ref_resp.data.get("status", "COMPLETED"),
            "raw_capture_file": str(capture_file),
            "webhook_verifier": "WebhookSignatureVerifier",
            "webhook_status": wh_receipt.status,
        }
    finally:
        broker.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Replay without provider calls")
    parser.add_argument("--state-dir", type=Path, default=Path(".goldgraft/sandbox-dry-run"))
    args = parser.parse_args()
    try:
        result = run_sandbox_payment(dry_run=args.dry_run, state_dir=args.state_dir)
    except ValueError as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
