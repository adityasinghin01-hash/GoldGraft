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


def test_payment_broker_refetch_and_live_transport(tmp_path):
    custody = CustodyBroker()
    ref = custody.store_credentials(
        "shop-test",
        {"paypal_client_id": "CID", "paypal_client_secret": "SEC"},
    )
    broker = PaymentBroker(custody_broker=custody)

    cap_resp = broker.refetch_capture("CAP-12345", secret_ref=ref.to_uri())
    assert cap_resp.status_code == 200
    assert cap_resp.data["id"] == "CAP-12345"
    assert cap_resp.data["status"] == "COMPLETED"

    ref_resp = broker.refetch_refund("REF-99999", secret_ref=ref.to_uri())
    assert ref_resp.status_code == 200
    assert ref_resp.data["id"] == "REF-99999"
    assert ref_resp.data["status"] == "COMPLETED"

    ord_resp = broker.refetch_order("ORD-55555", secret_ref=ref.to_uri())
    assert ord_resp.status_code == 200
    assert ord_resp.data["id"] == "ORD-55555"

    class MockSandboxTransport:
        def post(self, url, headers=None, json=None, data=None, content=None, timeout=None):
            class Response:
                def __init__(self, status_code, json_data):
                    self.status_code = status_code
                    self._data = json_data

                def json(self):
                    return self._data

            if "oauth2/token" in url:
                return Response(200, {"access_token": "ACCESS-TOKEN-XYZ"})
            if "/v2/checkout/orders" in url and url.endswith("/orders"):
                return Response(201, {"id": "ORD-LIVE-001", "status": "CREATED"})
            if url.endswith("/capture"):
                return Response(
                    200,
                    {
                        "id": "ORD-LIVE-001",
                        "status": "COMPLETED",
                        "purchase_units": [
                            {
                                "payments": {
                                    "captures": [
                                        {"id": "CAP-LIVE-001", "status": "COMPLETED"}
                                    ]
                                }
                            }
                        ],
                    },
                )
            if url.endswith("/refund"):
                return Response(200, {"id": "REF-LIVE-001", "status": "COMPLETED"})
            raise ValueError(f"Unexpected POST url: {url}")

        def get(self, url, headers=None, timeout=None):
            class Response:
                def __init__(self, status_code, json_data):
                    self.status_code = status_code
                    self._data = json_data

                def json(self):
                    return self._data

            if "/captures/CAP-LIVE-001" in url:
                return Response(200, {"id": "CAP-LIVE-001", "status": "COMPLETED"})
            if "/refunds/REF-LIVE-001" in url:
                return Response(200, {"id": "REF-LIVE-001", "status": "COMPLETED"})
            raise ValueError(f"Unexpected GET url: {url}")

    db_file = tmp_path / "sandbox_test.sqlite"
    live_broker = PaymentBroker(
        custody_broker=custody,
        live=True,
        mode="sandbox",
        transport=MockSandboxTransport(),
        database=str(db_file),
        authorize=lambda *_: True,
    )
    try:
        c_res = live_broker.execute_orders_v2(
            "create",
            {
                "intent": "CAPTURE",
                "purchase_units": [{"amount": {"currency_code": "USD", "value": "10.00"}}],
            },
            secret_ref=ref.to_uri(),
            idempotency_key="live-create-1",
        )
        assert c_res.evidence_class == "real_sandbox"
        assert c_res.data["id"] == "ORD-LIVE-001"

        cap_res = live_broker.execute_orders_v2(
            "capture",
            {"order_id": "ORD-LIVE-001"},
            secret_ref=ref.to_uri(),
            idempotency_key="live-cap-1",
        )
        assert cap_res.evidence_class == "real_sandbox"

        ref_cap_res = live_broker.refetch_capture("CAP-LIVE-001", secret_ref=ref.to_uri())
        assert ref_cap_res.evidence_class == "real_sandbox"
        assert ref_cap_res.data["id"] == "CAP-LIVE-001"
        assert ref_cap_res.data["status"] == "COMPLETED"

        ref_res = live_broker.execute_orders_v2(
            "refund",
            {"capture_id": "CAP-LIVE-001", "amount": {"currency_code": "USD", "value": "10.00"}},
            secret_ref=ref.to_uri(),
            idempotency_key="live-ref-1",
        )
        assert ref_res.evidence_class == "real_sandbox"
        assert ref_res.data["id"] == "REF-LIVE-001"

        ref_refund_res = live_broker.refetch_refund("REF-LIVE-001", secret_ref=ref.to_uri())
        assert ref_refund_res.evidence_class == "real_sandbox"
        assert ref_refund_res.data["id"] == "REF-LIVE-001"
        assert ref_refund_res.data["status"] == "COMPLETED"
    finally:
        live_broker.close()

