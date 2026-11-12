"""Offline broker/callback/recorder checks, despite the historical filename.

Injected verifiers test adapter plumbing only. SandboxRecorder produces scripted
exchanges and never executes or isolates a shop or authenticates to PayPal.
"""

import pytest
from goldgraft_contracts.registry import validate
from goldgraft_foundation.ledger import Ledger

from pieces.backend.callback_gateway import CallbackGateway
from pieces.backend.custody_broker import CustodyBroker
from pieces.backend.payment_broker import PaymentBroker, SecretDeniedError
from pieces.runner.sandbox_recorder import SandboxRecorder


def test_payment_broker_secret_enforcement():
    custody = CustodyBroker()
    broker = PaymentBroker(custody_broker=custody)

    # Storing credentials returns Doppler URI
    ref = custody.store_credentials(
        "shop-sandbox",
        {
            "paypal_client_id": "CLIENT-ID-99",
            "paypal_client_secret": "CLIENT-SECRET-88",
        },
    )
    assert ref.to_uri().startswith("doppler://")

    # Valid execution
    resp = broker.execute_nvp("SetExpressCheckout", {"AMT": "25.00"}, secret_ref=ref.to_uri())
    assert resp.status_code == 200
    assert resp.data["ACK"] == "Success"
    assert "TOKEN" in resp.data

    # Unresolvable secret MUST deny
    with pytest.raises(SecretDeniedError):
        broker.execute_nvp(
            "SetExpressCheckout", {}, secret_ref="doppler://goldgraft/shops/nonexistent/secrets"
        )


def test_callback_gateway_ipn_and_webhook():
    ledger = Ledger()

    # Default gateway without verifiers: honest unverified receipt
    unverified_gw = CallbackGateway(ledger)
    ipn_body = "cmd=_notify-validate&payment_status=Completed&txn_id=TXN12345&mc_gross=15.00"
    unverified_receipt = unverified_gw.handle_ipn(
        ipn_body, {"paypal-delivery-id": "deliv-unverified"}, graft_id="graft-cb-unv"
    )
    assert unverified_receipt.verified is False
    assert unverified_receipt.status == "UNVERIFIED"
    assert "no IPN postback verifier configured" in unverified_receipt.holds

    # Qualified gateway with injected verifiers
    class MockVerifier:
        def verify(self, *args, **kwargs):
            return "verified"

    gateway = CallbackGateway(ledger, ipn_verifier=MockVerifier(), webhook_verifier=MockVerifier())

    # 1. IPN postback receipt
    receipt = gateway.handle_ipn(
        ipn_body, {"paypal-delivery-id": "deliv-001"}, graft_id="graft-cb-1"
    )
    assert receipt.verified is True
    assert receipt.status == "VERIFIED"
    assert receipt.ledger_seq > 0

    # Deduplication test
    dup = gateway.handle_ipn(ipn_body, {"paypal-delivery-id": "deliv-001"}, graft_id="graft-cb-1")
    assert dup.status == "DUPLICATE"

    # 2. Webhook verification
    wh_payload = {"id": "WH-999", "event_type": "PAYMENT.CAPTURE.COMPLETED"}
    wh_receipt = gateway.handle_webhook(
        wh_payload,
        {
            "paypal-transmission-sig": "valid-sig-token",
            "paypal-cert-url": "https://api.sandbox.paypal.com/cert",
        },
        graft_id="graft-cb-1",
    )
    assert wh_receipt.verified is True
    assert wh_receipt.status == "VERIFIED"


def test_sandbox_recorder_live_execution():
    custody = CustodyBroker()
    ref = custody.store_credentials(
        "shop-run-1",
        {
            "paypal_client_id": "CID",
            "paypal_client_secret": "SEC",
        },
    )
    broker = PaymentBroker(custody_broker=custody)
    recorder = SandboxRecorder(broker=broker)

    job_spec = validate(
        "JobSpec/1",
        {
            "job_id": "job-sandbox-01",
            "graft_id": "graft-run-01",
            "stage": "RECORDED",
            "kind": "RECORD",
            "shop_pack_ref": "fixtures://shops/legacy-php-shop/goldgraft-shop.yaml",
            "scenario_ids": ["HAPPY", "REFUND"],
            "mutant_ids": [],
            "variants": ["OLD", "NEW"],
            "timeouts": {"build_s": 300, "run_s": 300, "total_s": 600},
            "secrets_ref": ref.to_uri(),
            "signature": None,
        },
    )

    result = recorder.run_isolated_job(job_spec)
    assert result.status == "OK"
    assert len(result.raw_capture_refs) == 4  # 2 scenarios x 2 variants

    # Fetch recorded capture
    capture = recorder.fetch_capture(result.raw_capture_refs[0])
    assert capture.scenario_id in ("HAPPY", "REFUND")
    assert len(capture.exchanges) > 0
    assert capture.exchanges[0].headers["authorization"] == "[REDACTED]"
