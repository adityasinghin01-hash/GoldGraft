"""Offline checks of the live sandbox flow and read-only re-fetch (mock transport, no network)."""

import pytest

from pieces.backend.custody_broker import CustodyBroker
from pieces.backend.payment_broker import PaymentBroker
from scripts.live_paypal_sandbox_payment import run_sandbox_payment

CREDS = {"PAYPAL_CLIENT_ID": "test-client", "PAYPAL_CLIENT_SECRET": "test-secret"}


class Response:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data


class SandboxTransport:
    """Answers like PayPal's sandbox; records every request it receives."""

    def __init__(self, *, capture_statuses=("COMPLETED",), capture_id="CAP-1"):
        self.calls = []
        self.order_polls = 0
        self.capture_statuses = list(capture_statuses)
        self.capture_id = capture_id

    def post(self, url, headers=None, json=None, data=None, content=None, timeout=None):
        self.calls.append(("POST", url, dict(headers or {}), json))
        if url.endswith("/v1/oauth2/token"):
            return Response(200, {"access_token": "TOKEN"})
        if url.endswith("/v2/checkout/orders"):
            return Response(
                201,
                {
                    "id": "ORD-1",
                    "status": "PAYER_ACTION_REQUIRED",
                    "links": [{"rel": "payer-action", "href": "https://sandbox.example/approve"}],
                },
            )
        if url.endswith("/capture"):
            capture = {"status": "COMPLETED"}
            if self.capture_id:
                capture["id"] = self.capture_id
            return Response(
                201,
                {
                    "id": "ORD-1",
                    "status": "COMPLETED",
                    "purchase_units": [{"payments": {"captures": [capture]}}],
                },
            )
        if url.endswith("/refund"):
            return Response(201, {"id": "REF-1", "status": "COMPLETED"})
        raise AssertionError(url)

    def get(self, url, headers=None, timeout=None):
        self.calls.append(("GET", url, dict(headers or {}), None))
        amount = {"currency_code": "USD", "value": "10.00"}
        if "/v2/checkout/orders/" in url:
            self.order_polls += 1
            status = "APPROVED" if self.order_polls >= 2 else "PAYER_ACTION_REQUIRED"
            return Response(200, {"id": "ORD-1", "status": status})
        if "/v2/payments/captures/" in url:
            status = self.capture_statuses.pop(0) if self.capture_statuses else "COMPLETED"
            return Response(200, {"id": "CAP-1", "status": status, "amount": amount})
        if "/v2/payments/refunds/" in url:
            return Response(200, {"id": "REF-1", "status": "COMPLETED", "amount": amount})
        raise AssertionError(url)


def test_live_flow_refuses_without_explicit_authorisation(tmp_path):
    with pytest.raises(ValueError, match="authorize-sandbox-payment"):
        run_sandbox_payment(state_dir=tmp_path / "live", credentials=CREDS)
    with pytest.raises(ValueError, match="qualified payment transport"):
        run_sandbox_payment(state_dir=tmp_path / "live", authorize_payment=True)
    assert not (tmp_path / "live").exists()


def test_live_flow_records_only_provider_answers(tmp_path):
    transport = SandboxTransport()
    shown = []
    report = run_sandbox_payment(
        state_dir=tmp_path,
        authorize_payment=True,
        credentials=CREDS,
        show_approval=shown.append,
        poll_s=0,
        transport=transport,
    )
    assert shown == ["https://sandbox.example/approve"]
    assert report["order_id"] == "ORD-1" and report["approval_polls"] == 2
    assert report["capture_id"] == "CAP-1" and report["capture_status_refetched"] == "COMPLETED"
    assert report["refund_id"] == "REF-1" and report["refund_status_refetched"] == "COMPLETED"
    # No capture before approval, and the refund body carries no path id.
    methods = [(m, u.rsplit("/", 1)[-1]) for m, u, _, _ in transport.calls if "oauth2" not in u]
    assert methods.index(("POST", "capture")) > methods.index(("GET", "ORD-1"))
    refund = next(body for m, u, _, body in transport.calls if u.endswith("/refund"))
    assert refund == {"amount": {"currency_code": "USD", "value": "10.00"}}
    # Reads never carry a payment request id.
    assert all("PayPal-Request-Id" not in h for m, _, h, _ in transport.calls if m == "GET")
    assert report["exchanges"] == 12


def test_live_flow_stops_instead_of_inventing_a_capture_id(tmp_path):
    with pytest.raises(RuntimeError, match="no capture id"):
        run_sandbox_payment(
            state_dir=tmp_path,
            authorize_payment=True,
            credentials=CREDS,
            show_approval=lambda _url: None,
            poll_s=0,
            transport=SandboxTransport(capture_id=None),
        )


def test_out_of_scope_amount_is_refused(tmp_path):
    from pieces.backend.payment_broker import BrokerRefused
    from scripts.live_paypal_sandbox_payment import _scoped_authority

    custody = CustodyBroker()
    ref = custody.store_credentials(
        "s", {"paypal_client_id": "a", "paypal_client_secret": "b"}
    ).to_uri()
    broker = PaymentBroker(
        custody_broker=custody,
        mode="sandbox",
        database=str(tmp_path / "j.sqlite"),
        authorize=_scoped_authority("g", "10.00", "USD"),
        transport=SandboxTransport(),
    )
    order = {
        "intent": "CAPTURE",
        "purchase_units": [{"amount": {"currency_code": "USD", "value": "99.00"}}],
    }
    with pytest.raises(BrokerRefused, match="authority"):
        broker.execute_orders_v2("create", order, secret_ref=ref, idempotency_key="k", graft_id="g")
    with pytest.raises(BrokerRefused, match="authority"):
        broker.execute_orders_v2(
            "create", order, secret_ref=ref, idempotency_key="k2", graft_id="other"
        )
    broker.close()


def test_refetch_is_read_only_and_sees_current_state(tmp_path):
    custody = CustodyBroker()
    ref = custody.store_credentials(
        "s", {"paypal_client_id": "a", "paypal_client_secret": "b"}
    ).to_uri()
    transport = SandboxTransport(capture_statuses=("PENDING", "COMPLETED"))
    broker = PaymentBroker(
        custody_broker=custody,
        mode="sandbox",
        database=str(tmp_path / "j.sqlite"),
        authorize=lambda *_: True,
        transport=transport,
    )
    assert broker.refetch_capture("CAP-1", secret_ref=ref).data["status"] == "PENDING"
    assert broker.refetch_capture("CAP-1", secret_ref=ref).data["status"] == "COMPLETED"
    rows = broker._journal.execute("SELECT COUNT(*) FROM payment_requests").fetchone()[0]
    assert rows == 0
    broker.close()
