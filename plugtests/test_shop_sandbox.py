"""Sandbox shop safeguards, with injected HTTP responses; no external network.

PayPal wire fixtures follow https://developer.paypal.com/api/orders/v2/ and
https://developer.paypal.com/api/payments/v2/ . Negative testing header:
https://developer.paypal.com/negative-testing/request-headers/ .
"""

import importlib
import json

import httpx
import pytest

from integration.local_shop import Recorder

CREDS = {"PAYPAL_CLIENT_ID": "private-client", "PAYPAL_CLIENT_SECRET": "private-secret"}
AMOUNT = {"currency_code": "USD", "value": "25.00"}


def sandbox_module():
    return importlib.import_module("integration.shop_sandbox")


class Upstream:
    def __init__(self, *, approved=True, capture_status="COMPLETED", missing_id=False):
        self.calls = []
        self.approved = approved
        self.capture_status = capture_status
        self.missing_id = missing_id
        self.polls = 0

    def __call__(self, req):
        self.calls.append(req)
        path = req.url.path
        if path == "/v1/oauth2/token":
            return httpx.Response(
                200, json={"access_token": "private-token", "token_type": "Bearer"}
            )
        if path == "/v2/checkout/orders":
            return httpx.Response(
                201,
                json={
                    "id": "ORDER-1",
                    "status": "CREATED",
                    "links": [{"rel": "approve", "href": "https://www.sandbox.paypal.com/approve"}],
                },
            )
        if path == "/v2/checkout/orders/ORDER-1":
            self.polls += 1
            return httpx.Response(
                200,
                json={
                    "id": "ORDER-1",
                    "status": "APPROVED" if self.approved else "CREATED",
                },
            )
        if path.endswith("/capture"):
            if req.headers.get("PayPal-Mock-Response"):
                return httpx.Response(422, json={"details": [{"issue": "INSTRUMENT_DECLINED"}]})
            cap = {"status": self.capture_status, "amount": AMOUNT}
            if not self.missing_id:
                cap["id"] = "CAP-1"
            return httpx.Response(
                201,
                json={
                    "id": "ORDER-1",
                    "status": "COMPLETED",
                    "purchase_units": [{"payments": {"captures": [cap]}}],
                },
            )
        if path.endswith("/refund"):
            return httpx.Response(
                201, json={"id": "REF-1", "status": "COMPLETED", "amount": AMOUNT}
            )
        if path.endswith("/CAP-1"):
            return httpx.Response(
                200, json={"id": "CAP-1", "status": self.capture_status, "amount": AMOUNT}
            )
        if path.endswith("/REF-1"):
            return httpx.Response(
                200, json={"id": "REF-1", "status": "COMPLETED", "amount": AMOUNT}
            )
        raise AssertionError(path)


def make_proxy(upstream=None, **kwargs):
    return sandbox_module().SandboxProxy(
        "HAPPY",
        credentials=CREDS,
        authorize_payment=True,
        transport=httpx.MockTransport(upstream or Upstream()),
        show_approval=lambda _: None,
        poll_s=0,
        **kwargs,
    )


def create(proxy):
    proxy.exchange(
        "POST",
        "/v1/oauth2/token",
        {"Authorization": "Basic placeholder"},
        b"grant_type=client_credentials",
    )
    return proxy.exchange(
        "POST",
        "/v2/checkout/orders",
        {},
        json.dumps(
            {
                "intent": "CAPTURE",
                "purchase_units": [{"amount": AMOUNT}],
            }
        ).encode(),
    )


def test_proxy_requires_authority_before_starting():
    with pytest.raises(ValueError, match="authorize-sandbox-payment"):
        sandbox_module().SandboxProxy("HAPPY", credentials=CREDS)


def test_http_handler_latches_unknown_capture_before_php_retry():
    from io import BytesIO

    upstream = Upstream()
    dispatches = []

    def uncertain_capture(request):
        if request.url.path.endswith("/capture"):
            dispatches.append(request)
            raise httpx.ReadTimeout("unknown capture outcome", request=request)
        return upstream(request)

    proxy = make_proxy(uncertain_capture)
    try:
        create(proxy)
        proxy.approve("ORDER-1")

        def php_capture():
            handler = proxy.handler_class.__new__(proxy.handler_class)
            handler.command = "POST"
            handler.path = "/v2/checkout/orders/ORDER-1/capture"
            handler.headers = {"Content-Length": "2"}
            handler.rfile = BytesIO(b"{}")
            handler.wfile = BytesIO()
            replies = []
            handler.send_response = replies.append
            handler.send_header = lambda *_: None
            handler.end_headers = lambda: None
            handler._handle()
            return replies

        assert php_capture() == [502]
        assert php_capture() == [502]
        assert len(dispatches) == 1
        assert proxy.error is not None
        # Reconciliation reads remain possible after an unknown write outcome.
        assert proxy.exchange("GET", "/v2/checkout/orders/ORDER-1", {})[0] == 200
    finally:
        proxy.close()


def test_approval_poll_recovers_from_one_read_timeout_without_retrying_payment():
    upstream = Upstream()
    attempts = []

    def intermittent_read(request):
        if request.method == "GET" and request.url.path == "/v2/checkout/orders/ORDER-1":
            attempts.append(request)
            if len(attempts) == 1:
                raise httpx.ReadTimeout("transient read failure", request=request)
        return upstream(request)

    proxy = make_proxy(intermittent_read)
    try:
        create(proxy)
        proxy.approve("ORDER-1")
        proxy.exchange("POST", "/v2/checkout/orders/ORDER-1/capture", {}, b"{}")
        assert len(attempts) == 2
        assert sum(r.url.path.endswith("/capture") for r in upstream.calls) == 1
    finally:
        proxy.close()


def test_approval_poll_stops_after_three_failed_reads_without_capture():
    upstream = Upstream()
    attempts = []

    def unavailable_read(request):
        if request.method == "GET":
            attempts.append(request)
            raise httpx.ReadTimeout("read unavailable", request=request)
        return upstream(request)

    proxy = make_proxy(unavailable_read)
    try:
        create(proxy)
        with pytest.raises(sandbox_module().SandboxHeld, match="three"):
            proxy.approve("ORDER-1")
        assert len(attempts) == 3
        assert not any(r.url.path.endswith("/capture") for r in upstream.calls)
    finally:
        proxy.close()


def test_proxy_records_real_wire_but_never_credentials():
    upstream = Upstream()
    proxy = make_proxy(upstream)
    proxy.recorder = Recorder("SHOP-HAPPY")
    try:
        create(proxy)
        proxy.approve("ORDER-1")
        proxy.exchange("POST", "/v2/checkout/orders/ORDER-1/capture", {}, b"{}")
        saved = json.dumps(proxy.recorder.exchanges)
        assert all(secret not in saved for secret in (*CREDS.values(), "private-token"))
        assert "[REDACTED]" in saved and "CAP-1" in saved
        assert all(
            str(req.url).startswith("https://api-m.sandbox.paypal.com/") for req in upstream.calls
        )
        assert upstream.calls[0].headers["authorization"].startswith("Basic ")
        assert upstream.calls[-1].headers["authorization"] == "Bearer private-token"
        times = [ex["t_ms"] for ex in proxy.recorder.exchanges]
        assert times == sorted(times)
    finally:
        proxy.close()


def test_unapproved_capture_never_reaches_upstream():
    upstream = Upstream(approved=False)
    proxy = make_proxy(upstream, approval_timeout_s=0)
    try:
        create(proxy)
        with pytest.raises(TimeoutError, match="not approved"):
            proxy.approve("ORDER-1")
        with pytest.raises(RuntimeError, match="approval"):
            proxy.exchange("POST", "/v2/checkout/orders/ORDER-1/capture", {}, b"{}")
        assert not any(req.url.path.endswith("/capture") for req in upstream.calls)
    finally:
        proxy.close()


@pytest.mark.parametrize(
    "kwargs,match",
    [({"missing_id": True}, "capture id"), ({"capture_status": "PENDING"}, "status")],
)
def test_unexpected_capture_stops_without_invented_success(kwargs, match):
    proxy = make_proxy(Upstream(**kwargs))
    try:
        create(proxy)
        proxy.approve("ORDER-1")
        with pytest.raises(RuntimeError, match=match):
            proxy.exchange("POST", "/v2/checkout/orders/ORDER-1/capture", {}, b"{}")
    finally:
        proxy.close()


@pytest.mark.parametrize(
    "path",
    [
        "https://evil.example/v2/checkout/orders",
        "//evil.example/",
        "/v1/notifications/verify-webhook-signature",
        "/nvp",
    ],
)
def test_proxy_rejects_unknown_endpoints(path):
    upstream = Upstream()
    proxy = make_proxy(upstream)
    try:
        with pytest.raises(ValueError, match="path"):
            proxy.exchange("POST", path, {}, b"{}")
        assert not upstream.calls
    finally:
        proxy.close()


def test_decline_injects_only_documented_negative_capture_header():
    upstream = Upstream()
    proxy = sandbox_module().SandboxProxy(
        "DECLINE",
        credentials=CREDS,
        authorize_payment=True,
        transport=httpx.MockTransport(upstream),
        show_approval=lambda _: None,
        poll_s=0,
    )
    proxy.recorder = Recorder("SHOP-DECLINE")
    try:
        create(proxy)
        proxy.approve("ORDER-1")
        status, _, body = proxy.exchange("POST", "/v2/checkout/orders/ORDER-1/capture", {}, b"{}")
        assert status == 422 and b"INSTRUMENT_DECLINED" in body
        assert all("PayPal-Mock-Response" not in req.headers for req in upstream.calls[:-1])
        assert json.loads(upstream.calls[-1].headers["PayPal-Mock-Response"]) == {
            "mock_application_codes": "INSTRUMENT_DECLINED",
        }
        assert "PayPal-Mock-Response" in json.dumps(proxy.recorder.exchanges)
    finally:
        proxy.close()


def test_real_provider_refused_for_old_or_standin_only_scenario(monkeypatch):
    from integration import local_shop

    class Provider:
        real_sandbox = True

    for scenario, variant in [("HAPPY", "OLD"), ("PENDING", "NEW")]:
        with pytest.raises(ValueError, match="NEW.*scenario"):
            local_shop.run_scenario(
                scenario, variant, {}, graft_id="g", run_id="r", paypal=Provider()
            )


def test_cli_refuses_before_credentials_or_output(tmp_path, monkeypatch):
    module = importlib.import_module("scripts.live_shop_sandbox")

    def unauthorized(*_a, **_kw):
        raise AssertionError("unauthorized credential read or execution")

    monkeypatch.setattr(module, "load_credentials", unauthorized)
    monkeypatch.setattr(module, "run_shop_sandbox", unauthorized)
    with pytest.raises(SystemExit):
        module.main(["--run-dir", str(tmp_path / "absent"), "--output", str(tmp_path / "out")])
    assert not (tmp_path / "out").exists()


def test_refetch_calls_broker_for_every_unique_recorded_resource(tmp_path):
    module = sandbox_module()
    proxy = make_proxy()
    try:
        create(proxy)
        proxy.approve("ORDER-1")
        proxy.exchange("POST", "/v2/checkout/orders/ORDER-1/capture", {}, b"{}")
        proxy.exchange(
            "POST",
            "/v2/payments/captures/CAP-1/refund",
            {},
            json.dumps({"amount": AMOUNT}).encode(),
        )
        from pieces.backend.custody_broker import CustodyBroker
        from pieces.backend.payment_broker import PaymentBroker

        custody = CustodyBroker()
        ref = custody.store_credentials(
            "s", {"paypal_client_id": "a", "paypal_client_secret": "b"}
        ).to_uri()
        transport = httpx.Client(transport=httpx.MockTransport(Upstream()))
        broker = PaymentBroker(
            custody_broker=custody,
            mode="sandbox",
            transport=transport,
            database=str(tmp_path / "reads.sqlite"),
            authorize=lambda _g, op, *_: op.startswith("get_"),
        )
        try:
            rows = module.refetch_resources(
                {"exchanges": proxy.recorder.exchanges}, broker, secret_ref=ref, graft_id="g"
            )
            assert {(r["kind"], r["id"]) for r in rows} == {
                ("capture", "CAP-1"),
                ("refund", "REF-1"),
            }
            assert all(r["body"]["status"] == "COMPLETED" for r in rows)
            assert all(r["evidence_class"] == "real_sandbox" and not r["simulated"] for r in rows)
        finally:
            broker.close()
            transport.close()
    finally:
        proxy.close()


def write_bundle(tmp_path, *, scenario="HAPPY"):
    import hashlib

    agents, evidence = tmp_path / "agents", tmp_path / "sandbox"
    agents.mkdir()
    evidence.mkdir()
    for name in ("CHANGES.json", "OUTPUTS.json"):
        (agents / name).write_text("{}")
    proxy = make_proxy()
    try:
        proxy.recorder.add(
            "BROWSER_TO_SHOP",
            "POST",
            "http://127.0.0.1/api/create-payment.php",
            body_json={"tee": 1},
        )
        create(proxy)
        proxy.approve("ORDER-1")
        proxy.recorder.add(
            "BROWSER_TO_SHOP",
            "POST",
            "http://127.0.0.1/api/execute-payment.php",
            body_json={"token": "ORDER-1"},
        )
        proxy.exchange("POST", "/v2/checkout/orders/ORDER-1/capture", {}, b"{}")
        raw = {
            "graft_id": "agents",
            "run_id": "agents-shop-sandbox-test",
            "variant": "NEW",
            "scenario_id": scenario,
            "exchanges": proxy.recorder.exchanges,
        }
    finally:
        proxy.close()
    (evidence / f"{scenario}.NEW.json").write_text(json.dumps(raw))
    reads = {
        scenario: [
            {
                "kind": "capture",
                "id": "CAP-1",
                "status_code": 200,
                "evidence_class": "real_sandbox",
                "simulated": False,
                "correlation_id": "CAP-1",
                "t_ms": 1,
                "body": {"id": "CAP-1", "status": "COMPLETED", "amount": AMOUNT},
            }
        ]
    }
    (evidence / "REFETCH.json").write_text(json.dumps(reads))

    def sha(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()

    report = {
        "graft_id": "agents",
        "run_id": raw["run_id"],
        "evidence_class": "real_provider",
        "provider": "paypal_sandbox",
        "real_money": False,
        "status": "RECORDED",
        "changes_sha256": sha(agents / "CHANGES.json"),
        "outputs_sha256": sha(agents / "OUTPUTS.json"),
        "requested_scenarios": [scenario],
        "scenarios": [
            {
                "scenario": scenario,
                "status": "RECORDED",
                "variants": {
                    "NEW": "real_provider",
                    "OLD": "simulated_paypal",
                    "OLD_TWIN": "simulated_paypal",
                },
            }
        ],
        "capture_sha256": {f"{scenario}.NEW.json": sha(evidence / f"{scenario}.NEW.json")},
        "refetch_sha256": sha(evidence / "REFETCH.json"),
    }
    (evidence / "REPORT.json").write_text(json.dumps(report))
    return agents, evidence


def update_bundle(evidence, name, transform):
    import hashlib

    path = evidence / name
    data = json.loads(path.read_text())
    transform(data)
    path.write_text(json.dumps(data))
    if name != "REPORT.json":
        report = json.loads((evidence / "REPORT.json").read_text())
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if name == "REFETCH.json":
            report["refetch_sha256"] = digest
        else:
            report["capture_sha256"][name] = digest
        (evidence / "REPORT.json").write_text(json.dumps(report))


def test_bundle_verified_only_from_recorded_new_checkout_and_exact_refetch(tmp_path):
    agents, evidence = write_bundle(tmp_path)
    result = importlib.import_module("integration.shop_sandbox_evidence").shop_sandbox_evidence(
        evidence, agents
    )
    assert result["state"] == "verified" and result["evidence_refs"]


@pytest.mark.parametrize(
    "problem",
    [
        "pending",
        "amount",
        "currency",
        "missing_read",
        "fake_read",
        "wrong_id",
        "old",
        "standin",
        "no_approval",
        "empty",
        "candidate_drift",
        "bytes_drift",
        "failed_run",
    ],
)
def test_bundle_never_promotes_incomplete_or_wrong_evidence(tmp_path, problem):
    agents, evidence = write_bundle(tmp_path)
    if problem in {"pending", "amount", "currency", "wrong_id", "fake_read", "missing_read"}:

        def damage(data):
            row = data["HAPPY"][0]
            if problem == "pending":
                row["body"]["status"] = "PENDING"
            elif problem == "amount":
                row["body"]["amount"] = {"currency_code": "USD", "value": "0.01"}
            elif problem == "currency":
                row["body"]["amount"] = {"currency_code": "EUR", "value": "25.00"}
            elif problem == "wrong_id":
                row["body"]["id"] = "OTHER"
            elif problem == "fake_read":
                row["simulated"] = True
            else:
                data["HAPPY"] = []

        update_bundle(evidence, "REFETCH.json", damage)
    elif problem == "candidate_drift":
        (agents / "CHANGES.json").write_text('{"drift":true}')
    elif problem == "bytes_drift":
        with (evidence / "HAPPY.NEW.json").open("a") as f:
            f.write(" ")
    elif problem == "failed_run":
        update_bundle(evidence, "REPORT.json", lambda d: d.update(status="HELD"))
    else:

        def damage(raw):
            if problem == "old":
                raw["variant"] = "OLD"
            elif problem == "empty":
                raw["exchanges"] = []
            elif problem == "standin":
                for ex in raw["exchanges"]:
                    if ex["direction"] in {"SHOP_TO_PAYPAL", "PAYPAL_TO_SHOP"}:
                        ex["url"] = ex["url"].replace(
                            "https://api-m.sandbox.paypal.com", "http://127.0.0.1:1234"
                        )
            else:
                for ex in raw["exchanges"]:
                    if ex.get("body_json", {}).get("status") == "APPROVED":
                        ex["body_json"]["status"] = "CREATED"

        update_bundle(evidence, "HAPPY.NEW.json", damage)
    result = importlib.import_module("integration.shop_sandbox_evidence").shop_sandbox_evidence(
        evidence, agents
    )
    assert result["state"] != "verified"


@pytest.mark.parametrize("scenario", ["PENDING", "NOTIFY_DUP", "NOTIFY_FORGED", "PARITY_EXTRA"])
def test_nonreal_scenarios_cannot_construct_real_proxy(scenario):
    with pytest.raises(ValueError, match="stand-in"):
        sandbox_module().SandboxProxy(scenario, credentials=CREDS, authorize_payment=True)


def test_http_handler_forwards_and_returns_body_without_logging_auth():
    from io import BytesIO

    proxy = make_proxy()
    try:
        handler = proxy.handler_class.__new__(proxy.handler_class)
        handler.command = "POST"
        handler.path = "/v1/oauth2/token"
        handler.headers = {"Content-Length": "29", "Authorization": "Basic private-php-auth"}
        handler.rfile = BytesIO(b"grant_type=client_credentials")
        handler.wfile = BytesIO()
        replies = []
        handler.send_response = replies.append
        handler.send_header = lambda *_: None
        handler.end_headers = lambda: None
        handler._handle()
        assert replies == [200]
        assert json.loads(handler.wfile.getvalue())["access_token"] == "private-token"
        assert "private-php-auth" not in json.dumps(proxy.recorder.exchanges)
        assert "private-token" not in json.dumps(proxy.recorder.exchanges)
    finally:
        proxy.close()


def test_malformed_provider_response_is_still_recorded():
    def upstream(_req):
        return httpx.Response(502, text="provider unavailable")

    proxy = make_proxy(upstream)
    try:
        with pytest.raises(RuntimeError, match="non-JSON"):
            create(proxy)
        replies = [e for e in proxy.recorder.exchanges if e["direction"] == "PAYPAL_TO_SHOP"]
        assert len(replies) == 1 and replies[0]["status"] == 502
    finally:
        proxy.close()


def test_capture_rejects_mismatched_order_id():
    upstream = Upstream()

    def damaged(req):
        response = upstream(req)
        if req.url.path.endswith("/capture"):
            body = response.json()
            body["id"] = "OTHER"
            return httpx.Response(201, json=body)
        return response

    proxy = make_proxy(damaged)
    try:
        create(proxy)
        proxy.approve("ORDER-1")
        with pytest.raises(RuntimeError, match="order.*mismatch"):
            proxy.exchange("POST", "/v2/checkout/orders/ORDER-1/capture", {}, b"{}")
    finally:
        proxy.close()


@pytest.mark.parametrize(
    "scenario", ["HAPPY", "REFUND", "REFUND_TWICE", "DOUBLE", "DECLINE", "PENDING"]
)
def test_cli_routes_only_new_to_real_and_saves_broker_reads(tmp_path, monkeypatch, scenario):
    module = importlib.import_module("scripts.live_shop_sandbox")
    agents = tmp_path / "agents"
    agents.mkdir()
    for name in ("CHANGES.json", "OUTPUTS.json"):
        (agents / name).write_text("{}")
    monkeypatch.setattr(module, "load_candidate", lambda _: ({}, {}))
    monkeypatch.setattr(module, "resolve_php", lambda _: "/unused/php")
    calls = []

    def execute(s, variant, _files, *, graft_id, run_id, php, paypal=None):
        calls.append((s, variant, paypal is not None))
        if paypal is None:
            return {
                "graft_id": graft_id,
                "run_id": run_id,
                "variant": variant,
                "scenario_id": s,
                "exchanges": [],
            }
        paypal.recorder.add(
            "BROWSER_TO_SHOP",
            "POST",
            "http://127.0.0.1/api/create-payment.php",
            body_json={"tee": 1},
        )
        create(paypal)
        paypal.approve("ORDER-1")
        paypal.recorder.add(
            "BROWSER_TO_SHOP",
            "POST",
            "http://127.0.0.1/api/execute-payment.php",
            body_json={"token": "ORDER-1"},
        )
        paypal.exchange("POST", "/v2/checkout/orders/ORDER-1/capture", {}, b"{}")
        if s == "DOUBLE":
            paypal.exchange("POST", "/v2/checkout/orders/ORDER-1/capture", {}, b"{}")
        if s in {"REFUND", "REFUND_TWICE"}:
            paypal.exchange(
                "POST",
                "/v2/payments/captures/CAP-1/refund",
                {},
                json.dumps({"amount": AMOUNT}).encode(),
            )
            if s == "REFUND_TWICE":
                paypal.exchange(
                    "POST",
                    "/v2/payments/captures/CAP-1/refund",
                    {},
                    json.dumps({"amount": AMOUNT}).encode(),
                )
        return {
            "graft_id": graft_id,
            "run_id": run_id,
            "variant": variant,
            "scenario_id": s,
            "exchanges": paypal.recorder.exchanges,
        }

    monkeypatch.setattr(module, "run_scenario", execute)
    transport = httpx.Client(transport=httpx.MockTransport(Upstream()))
    try:
        output = tmp_path / "out"
        report = module.run_shop_sandbox(
            agents,
            output,
            authorize_payment=True,
            credentials=CREDS,
            scenarios=[scenario],
            show_approval=lambda _: None,
            poll_s=0,
            transport=httpx.MockTransport(Upstream()),
            broker_transport=transport,
        )
        assert calls == [
            (scenario, "OLD", False),
            (scenario, "OLD_TWIN", False),
            (scenario, "NEW", scenario != "PENDING"),
        ]
        assert report["status"] == "RECORDED"
        reads = json.loads((output / "REFETCH.json").read_text())
        if scenario in {"DECLINE", "PENDING"}:
            assert not reads.get(scenario)
        else:
            assert any(r["kind"] == "capture" for r in reads[scenario])
        saved = "".join(p.read_text() for p in output.glob("*.json"))
        assert all(secret not in saved for secret in (*CREDS.values(), "private-token"))
    finally:
        transport.close()


def test_failed_checkout_preserves_partial_capture_and_refetches_known_capture(
    tmp_path, monkeypatch
):
    module = importlib.import_module("scripts.live_shop_sandbox")
    agents = tmp_path / "agents"
    agents.mkdir()
    for name in ("CHANGES.json", "OUTPUTS.json"):
        (agents / name).write_text("{}")
    monkeypatch.setattr(module, "load_candidate", lambda _: ({}, {}))
    monkeypatch.setattr(module, "resolve_php", lambda _: "/unused/php")

    def execute(s, variant, _files, *, graft_id, run_id, php, paypal=None):
        if paypal is None:
            return {
                "graft_id": graft_id,
                "run_id": run_id,
                "variant": variant,
                "scenario_id": s,
                "exchanges": [],
            }
        create(paypal)
        paypal.approve("ORDER-1")
        paypal.exchange("POST", "/v2/checkout/orders/ORDER-1/capture", {}, b"{}")
        raise RuntimeError("checkout fault after payment")

    monkeypatch.setattr(module, "run_scenario", execute)
    transport = httpx.Client(transport=httpx.MockTransport(Upstream()))
    try:
        output = tmp_path / "out"
        report = module.run_shop_sandbox(
            agents,
            output,
            authorize_payment=True,
            credentials=CREDS,
            scenarios=["HAPPY", "DOUBLE"],
            show_approval=lambda _: None,
            transport=httpx.MockTransport(Upstream()),
            broker_transport=transport,
        )
        assert report["status"] == "HELD"
        assert len(report["scenarios"]) == 1
        assert (output / "HAPPY.NEW.json").exists()
        reads = json.loads((output / "REFETCH.json").read_text())
        assert reads["HAPPY"][0]["id"] == "CAP-1"
        assert reads["HAPPY"][0]["body"]["status"] == "COMPLETED"
    finally:
        transport.close()


def test_proxy_requests_full_provider_resource_representation():
    upstream = Upstream()
    proxy = make_proxy(upstream)
    try:
        create(proxy)
        proxy.approve("ORDER-1")
        proxy.exchange("POST", "/v2/checkout/orders/ORDER-1/capture", {}, b"{}")
        assert upstream.calls[-1].headers["Prefer"] == "return=representation"
    finally:
        proxy.close()


def test_duplicate_payment_never_swallows_unknown_provider_error():
    upstream = Upstream()
    captures = 0

    def failing(req):
        nonlocal captures
        if req.url.path.endswith("/capture"):
            captures += 1
            if captures > 1:
                return httpx.Response(500, json={"name": "INTERNAL_SERVER_ERROR"})
        return upstream(req)

    proxy = sandbox_module().SandboxProxy(
        "DOUBLE",
        credentials=CREDS,
        authorize_payment=True,
        transport=httpx.MockTransport(failing),
        show_approval=lambda _: None,
        poll_s=0,
    )
    try:
        create(proxy)
        proxy.approve("ORDER-1")
        proxy.exchange("POST", "/v2/checkout/orders/ORDER-1/capture", {}, b"{}")
        with pytest.raises(RuntimeError, match="HTTP 500"):
            proxy.exchange("POST", "/v2/checkout/orders/ORDER-1/capture", {}, b"{}")
    finally:
        proxy.close()


@pytest.mark.parametrize("scenario", ["HAPPY", "REFUND", "REFUND_TWICE", "DOUBLE", "DECLINE"])
def test_scenario_driver_approves_before_execute_and_never_forges_webhooks(monkeypatch, scenario):
    from pathlib import Path
    from types import SimpleNamespace
    from urllib.parse import urlsplit

    from integration import local_shop

    upstream = Upstream()
    proxy = sandbox_module().SandboxProxy(
        scenario,
        credentials=CREDS,
        authorize_payment=True,
        transport=httpx.MockTransport(upstream),
        show_approval=lambda _: None,
        poll_s=0,
    )
    # Exercise the real Python scenario driver with an in-process shop boundary.
    # Socket/PHP transport remains the live check; proxy and broker tests use HTTP fakes.
    monkeypatch.setattr(proxy, "start", lambda: None)
    monkeypatch.setattr(local_shop, "resolve_php", lambda _: Path("/unused/php"))
    shop = SimpleNamespace(base="http://shop.local", state={}, close=lambda: None)
    shop.orders = lambda: shop.state
    monkeypatch.setattr(local_shop, "Shop", lambda *_a, **_kw: shop)

    class Reply:
        def __init__(self, body):
            self.body = body

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def read(self):
            return json.dumps(self.body).encode()

    def call(request, **_kwargs):
        path = urlsplit(request.full_url).path
        if path == "/api/create-payment.php":
            create(proxy)
            shop.state["ORDER-1"] = {"amount": "25.00", "status": "CREATED"}
            return Reply({"token": "ORDER-1"})
        if path == "/api/execute-payment.php":
            if shop.state["ORDER-1"]["status"] != "PAID":
                status, _, _ = proxy.exchange(
                    "POST", "/v2/checkout/orders/ORDER-1/capture", {}, b"{}"
                )
                if status == 201:
                    shop.state["ORDER-1"]["status"] = "PAID"
            return Reply({"ok": True})
        if path == "/api/refund.php":
            if shop.state["ORDER-1"]["status"] != "REFUNDED":
                proxy.exchange(
                    "POST",
                    "/v2/payments/captures/CAP-1/refund",
                    {},
                    json.dumps({"amount": AMOUNT}).encode(),
                )
                shop.state["ORDER-1"]["status"] = "REFUNDED"
            return Reply({"ok": True})
        raise AssertionError("unexpected notification or shop endpoint")

    monkeypatch.setattr(local_shop, "urlopen", call)
    raw = local_shop.run_scenario(scenario, "NEW", {}, graft_id="g", run_id="r", paypal=proxy)
    assert not any(e["direction"] == "PAYPAL_NOTIFY_TO_SHOP" for e in raw["exchanges"])
    paths = [r.url.path for r in upstream.calls]
    assert paths.index("/v2/checkout/orders/ORDER-1") < paths.index(
        "/v2/checkout/orders/ORDER-1/capture"
    )
    assert paths.count("/v2/checkout/orders/ORDER-1/capture") == 1
    assert all("FAKEPAYER" not in json.dumps(ex) for ex in raw["exchanges"])
    assert any(e["direction"] == "SHOP_DB_WRITE" for e in raw["exchanges"])


def test_programmatic_runner_refuses_authority_before_candidate_or_output(tmp_path):
    module = importlib.import_module("scripts.live_shop_sandbox")
    with pytest.raises(ValueError, match="authorize-sandbox-payment"):
        module.run_shop_sandbox(tmp_path / "absent", tmp_path / "out", credentials=CREDS)
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("damage", ["missing_id", "unknown_status", "unexpected_http"])
def test_ledger_read_stops_on_incomplete_or_unexpected_provider_result(damage):
    upstream = Upstream()

    def damaged(req):
        response = upstream(req)
        if req.url.path == "/v2/payments/captures/CAP-1":
            body = response.json()
            if damage == "missing_id":
                body.pop("id")
            elif damage == "unknown_status":
                body["status"] = "MYSTERY"
            return httpx.Response(202 if damage == "unexpected_http" else 200, json=body)
        return response

    proxy = make_proxy(damaged)
    try:
        create(proxy)
        proxy.approve("ORDER-1")
        proxy.exchange("POST", "/v2/checkout/orders/ORDER-1/capture", {}, b"{}")
        with pytest.raises(RuntimeError, match="id|status|HTTP"):
            proxy.exchange("GET", "/v2/payments/captures/CAP-1", {})
    finally:
        proxy.close()


def test_bad_independent_refetch_stops_subsequent_scenarios(tmp_path, monkeypatch):
    module = importlib.import_module("scripts.live_shop_sandbox")
    agents = tmp_path / "agents"
    agents.mkdir()
    for name in ("CHANGES.json", "OUTPUTS.json"):
        (agents / name).write_text("{}")
    monkeypatch.setattr(module, "load_candidate", lambda _: ({}, {}))
    monkeypatch.setattr(module, "resolve_php", lambda _: "/unused/php")

    def execute(s, variant, _files, *, graft_id, run_id, php, paypal=None):
        if paypal is not None:
            create(paypal)
            paypal.approve("ORDER-1")
            paypal.exchange("POST", "/v2/checkout/orders/ORDER-1/capture", {}, b"{}")
        return {
            "graft_id": graft_id,
            "run_id": run_id,
            "variant": variant,
            "scenario_id": s,
            "exchanges": paypal.recorder.exchanges if paypal else [],
        }

    monkeypatch.setattr(module, "run_scenario", execute)
    transport = httpx.Client(transport=httpx.MockTransport(Upstream(capture_status="PENDING")))
    try:
        report = module.run_shop_sandbox(
            agents,
            tmp_path / "out",
            authorize_payment=True,
            credentials=CREDS,
            scenarios=["HAPPY", "DOUBLE"],
            show_approval=lambda _: None,
            transport=httpx.MockTransport(Upstream()),
            broker_transport=transport,
        )
        assert report["status"] == "HELD"
        assert len(report["scenarios"]) == 1
        reads = json.loads((tmp_path / "out/REFETCH.json").read_text())
        assert reads["HAPPY"][0]["body"]["status"] == "PENDING"
    finally:
        transport.close()


def test_partial_malformed_reply_still_refetches_every_known_resource():
    from types import SimpleNamespace

    calls = []

    class Reader:
        def refetch_capture(self, rid, **_kw):
            calls.append(rid)
            return SimpleNamespace(
                data={"id": rid, "status": "COMPLETED", "amount": AMOUNT},
                status_code=200,
                evidence_class="real_sandbox",
                simulated=False,
                correlation_id=rid,
            )

    raw = {
        "exchanges": [
            {
                "direction": "PAYPAL_TO_SHOP",
                "method": "POST",
                "status": 201,
                "url": "https://api-m.sandbox.paypal.com/v2/checkout/orders/O/capture",
                "body_json": {
                    "purchase_units": [
                        {
                            "payments": {
                                "captures": [
                                    {"id": "CAP-1", "amount": AMOUNT, "status": "COMPLETED"},
                                    {"status": "COMPLETED"},
                                ]
                            }
                        }
                    ]
                },
            }
        ]
    }
    rows = sandbox_module().refetch_resources(raw, Reader(), secret_ref="s", graft_id="g")
    assert calls == ["CAP-1"] and rows[0]["id"] == "CAP-1"
    with pytest.raises(RuntimeError, match="capture id"):
        sandbox_module().recorded_resources(raw)


@pytest.mark.parametrize(
    "timing",
    [
        {"approval_timeout_s": float("nan")},
        {"approval_timeout_s": float("inf")},
        {"poll_s": float("nan")},
        {"poll_s": float("inf")},
    ],
)
def test_approval_timing_cannot_disable_the_deadline(timing):
    with pytest.raises(ValueError, match="finite"):
        sandbox_module().SandboxProxy(
            "HAPPY",
            credentials=CREDS,
            authorize_payment=True,
            transport=httpx.MockTransport(Upstream()),
            **timing,
        )
