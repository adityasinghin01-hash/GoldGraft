"""Actual Gupta ports + Vijay code; injected HTTP/verifiers, never real services."""

import importlib.util
import os
import shutil
import subprocess
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from pieces.backend.callback_gateway import CallbackGateway
from pieces.backend.callback_inbox import CallbackInbox
from pieces.backend.custody_broker import CustodyBroker
from pieces.backend.payment_broker import PaymentBroker

ROOT = Path(os.environ.get("VIJAY_WORKSPACE", Path(__file__).resolve().parents[1]))
SHOP = ROOT / "pieces/shops/legacy-php-shop"
PHP = os.environ.get("VIJAY_PHP") or shutil.which("php")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adapter = load("vijay_adapter", SHOP / "candidate/broker_adapter.py")
php_port = load("vijay_php_port", SHOP / "candidate/php_port.py")
callbacks = load("vijay_callbacks", SHOP / "candidate/callbacks.py")
recipes = load("vijay_recipes", SHOP / "lifecycle_recipes.py")
continuity = load("vijay_continuity", SHOP / "candidate/continuity.py")


class InjectedHttp:
    """Scripted HTTP counterpart to exercise the REAL broker implementation."""

    def __init__(self):
        self.order = None
        self.capture = None
        self.refund = None
        self.calls = []

    def response(self, data):
        return type("Response", (), {"status_code": 200, "json": lambda _: deepcopy(data)})()

    def post(self, url, *, headers, json=None, content=None, data=None, timeout=None):
        self.calls.append(("POST", url))
        if url.endswith("/oauth2/token"):
            return self.response({"access_token": "fixture-token"})
        if url.endswith("/v2/checkout/orders"):
            self.order = {"id": "FIXTUREORDER", "status": "CREATED", **deepcopy(json)}
            return self.response(self.order)
        if url.endswith("/capture"):
            self.capture = {
                "id": "FIXTURECAPTURE",
                "status": "COMPLETED",
                "final_capture": True,
                "amount": deepcopy(self.order["purchase_units"][0]["amount"]),
            }
            self.order["status"] = "COMPLETED"
            self.order["purchase_units"][0]["payments"] = {"captures": [self.capture]}
            return self.response(self.order)
        if url.endswith("/refund"):
            assert "capture_id" not in json
            self.refund = {
                "id": "FIXTUREREFUND",
                "status": "COMPLETED",
                **deepcopy(json),
            }
            return self.response(self.refund)
        raise ValueError("unexpected_counterpart_request")

    def get(self, url, *, headers, timeout):
        assert "PayPal-Request-Id" not in headers
        self.calls.append(("GET", url))
        return self.response(
            self.refund
            if "/refunds/" in url
            else self.capture
            if "/captures/" in url
            else self.order
        )


@pytest.fixture
def bound(tmp_path):
    if not PHP:
        pytest.skip("Native PHP unavailable; native boundary tests are not qualified")
    probe = subprocess.run(
        [PHP, "-r", "exit(extension_loaded('pdo_sqlite') ? 0 : 1);"],
        capture_output=True,
        check=False,
    )
    if os.name != "nt" and probe.returncode:
        pytest.skip("PHP PDO SQLite unavailable; native boundary tests are not qualified")
    http = InjectedHttp()
    custody = CustodyBroker()
    ref = custody.store_credentials(
        "fixture",
        {"paypal_client_id": "fixture-id", "paypal_client_secret": "fixture-secret"},
    ).ref
    broker = PaymentBroker(
        custody,
        mode="sandbox",
        transport=http,
        database=tmp_path / "broker.sqlite",
        authorize=lambda *args: True,
    )  # Test authority only; never live.
    port = adapter.BrokerRestAdapter(
        broker, graft_id="fixture", secret_ref=ref, evidence_mode="real_sandbox"
    )
    native = php_port.PhpPort(
        PHP,
        tmp_path / "shop.sqlite",
        merchant_id="TESTSELLER",
        rest=port.rest,
    )
    native.call("open", "fixture-order", {"tee": 1})
    native.call("create", "fixture-order")
    native.call("capture", "fixture-order")
    yield native, broker, http
    broker.close()


def test_actual_php_python_broker_roundtrip_and_restart(bound):
    native, _, http = bound
    assert native.call("view", "fixture-order")["state"] == "PAID"
    count = len(http.calls)
    native.call("capture", "fixture-order")
    assert len(http.calls) == count
    assert native.call("refund", "fixture-order")["state"] == "REFUNDED"
    count = len(http.calls)
    native.call("refund", "fixture-order")
    assert len(http.calls) == count


class InjectedVerifier:
    def __init__(self, state="verified"):
        self.state = state

    def verify(self, *args):
        return self.state


@pytest.fixture
def consumer(tmp_path, bound):
    native, _, http = bound
    aead = AESGCM(AESGCM.generate_key(bit_length=128))

    def seal(raw):
        nonce = os.urandom(12)
        return nonce + aead.encrypt(nonce, raw, b"fixture-inbox")

    def unseal(raw):
        return aead.decrypt(raw[:12], raw[12:], b"fixture-inbox")

    inbox = CallbackInbox(database=tmp_path / "inbox.sqlite", seal=seal, unseal=unseal)
    verifier = InjectedVerifier()
    gateway = CallbackGateway(inbox=inbox, webhook_verifier=verifier, ipn_verifier=verifier)
    reconciles = []

    def lookup(local):
        if local == "old-order":
            return {
                "origin": "OLD",
                "transaction_id": "FIXTURE-OLD",
                "receiver_email": "seller@example.invalid",
                "amount_minor": 2500,
            }
        order = native.call("view", local)
        return {**order, "amount_minor": 2500}

    def recheck(local):
        reconciles.append(local)
        if local != "old-order":
            native.call("reconcile", local)

    c = callbacks.CallbackConsumer(
        gateway,
        tmp_path / "effects.sqlite",
        graft_id="fixture",
        lookup_intent=lookup,
        reconcile=recheck,
    )
    yield c, verifier, reconciles, http
    c.close()
    inbox._db.close()


def event():
    return {
        "id": "EVENT-FIXTURE",
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource": {
            "id": "FIXTURECAPTURE",
            "payee": {"merchant_id": "TESTSELLER"},
            "amount": {"currency_code": "USD", "value": "25.00"},
            "supplementary_data": {"related_ids": {"order_id": "FIXTUREORDER"}},
        },
    }


def test_callback_actual_gateway_then_php_get_reconciliation(consumer):
    c, _, reads, http = consumer
    assert (
        c.webhook("fixture-order", event(), {"paypal-transmission-id": "d1"})["status"]
        == "RECONCILED"
    )
    assert reads == ["fixture-order"] and http.calls[-1][0] == "GET"
    assert (
        c.webhook("fixture-order", event(), {"paypal-transmission-id": "d2"})["status"]
        == "DUPLICATE"
    )
    assert reads == ["fixture-order"]


@pytest.mark.parametrize("state", ["invalid", "unknown", "unverified"])
def test_callback_does_not_trust_incoming_verified_flag(consumer, state):
    c, verifier, reads, _ = consumer
    verifier.state = state
    payload = event()
    payload["verified"] = True
    assert c.webhook("fixture-order", payload, {})["status"] == "HOLD"
    assert reads == []


@pytest.mark.parametrize(
    "field,value",
    [("merchant_id", "OTHERMERCHANT"), ("value", "0.01"), ("currency_code", "EUR")],
)
def test_actual_gateway_business_binding_refuses_wrong_subject(consumer, field, value):
    c, _, reads, _ = consumer
    payload = event()
    target = (
        payload["resource"]["payee"] if field == "merchant_id" else payload["resource"]["amount"]
    )
    target[field] = value
    assert c.webhook("fixture-order", payload, {})["status"] == "HOLD" and not reads


def test_callback_identity_and_outage_recovery_are_not_new_payments(consumer):
    c, _, reads, _ = consumer
    original = c.reconcile
    c.reconcile = lambda local: (_ for _ in ()).throw(RuntimeError("offline-outage"))
    assert c.webhook("fixture-order", event(), {"paypal-transmission-id": "d1"})["status"] == "HOLD"
    c.reconcile = original
    assert (
        c.webhook("fixture-order", event(), {"paypal-transmission-id": "d2"})["status"]
        == "RECONCILED"
    )
    payload = event()
    payload["extra"] = "changed message under same business identity"
    assert c.webhook("fixture-order", payload, {"paypal-transmission-id": "d3"})["status"] == "HOLD"
    assert len(reads) == 1


def test_original_ipn_rail_pending_completion_and_duplicate(consumer):
    c, _, reads, _ = consumer
    body = (
        "txn_id=FIXTURE-OLD&receiver_email=seller%40example.invalid"
        "&payment_status=Pending&mc_currency=USD&mc_gross=25.00"
    )
    assert c.ipn("old-order", body, {})["status"] == "RECONCILED"
    complete = body.replace("Pending", "Completed")
    assert c.ipn("old-order", complete, {})["status"] == "RECONCILED"
    assert c.ipn("old-order", complete, {})["status"] == "DUPLICATE"
    assert c.ipn("fixture-order", complete, {})["status"] == "HOLD"
    assert len(reads) == 2


def test_finalisation_uses_actual_asset_model_and_rejects_temporary_dependencies():
    required = [
        "runtime",
        "config",
        "state",
        "credential",
        "callback",
        "origin_handler",
        "exit_executor",
    ]
    assets = []
    for kind in required:
        assets.append(
            {
                "asset_id": kind,
                "kind": kind,
                "ownership": "merchant",
                "target_key": {
                    "provider_id": "fixture",
                    "account_id": "fixture",
                    "environment_id": "sandbox",
                    "resource_kind": kind,
                    "resource_id": "fixture",
                },
                "required_for_operation": True,
                "active_reference_refs": ["fixture://needed"],
                "desired": "keep",
                "authority_refs": ["fixture://authority"],
                "evidence_refs": ["fixture://observed"],
            }
        )
    record = {
        "manifest_id": "fixture",
        "case_id": "fixture",
        "run_id": "fixture",
        "assets": assets,
        "final_artifact_digest": "sha256:" + "a" * 64,
        "final_config_digest": "b" * 64,
        "legacy_obligations_ref": "fixture://legacy",
        "manifest_digest": "c" * 64,
    }
    result = recipes.finalisation_recipe(record)
    assert (
        result["domain_status"] == "READY_FOR_BACKEND_QUALIFICATION"
        and result["qualified"] is False
    )
    record["assets"][0]["ownership"] = "shared_service"
    assert recipes.finalisation_recipe(record)["domain_status"] == "HOLD"
    record["assets"][0]["desired"] = "delete"
    with pytest.raises(ValueError):
        recipes.finalisation_recipe(record)


def test_state_and_exit_recipes_inspect_actual_state_with_current_models(tmp_path, bound):
    native, _, _ = bound
    inventory = continuity.inspect(native.database)
    state = dict(
        cutover_id="fixture",
        case_id="fixture",
        run_id="fixture",
        generation=1,
        **{
            key: "fixture://" + key
            for key in (
                "writer_inventory_ref",
                "handler_inventory_ref",
                "ingress_ref",
                "origin_route_ref",
                "admission_ref",
                "high_water_ref",
                "export_manifest_ref",
                "restore_manifest_ref",
                "replay_manifest_ref",
            )
        },
        drain_evidence_refs=["fixture://drain"],
        fence_epochs={"fixture": 1},
        state_digest=inventory["snapshot_sha256"],
        schema_digest=inventory["schema_sha256"],
        pending_external_effect_refs=[],
        evidence_refs=["fixture://evidence"],
        outcome="verified",
    )
    assert recipes.state_recipe(state, candidate_database=native.database)["qualified"] is False
    state["pending_external_effect_refs"] = ["fixture://unknown"]
    with pytest.raises(ValueError):
        recipes.state_recipe(state, candidate_database=native.database)
    now = datetime.now(UTC)
    plan = dict(
        exit_plan_id="fixture",
        case_id="fixture",
        run_id="fixture",
        generation=1,
        **{
            key: "fixture://" + key
            for key in (
                "reservation_ref",
                "executor_identity_ref",
                "recovery_plan_ref",
                "budget_ref",
                "private_evidence_destination_ref",
                "evidence_read_authority_ref",
                "failure_route_ref",
            )
        },
        trusted_code_digest="a" * 64,
        final_artifact_digest="sha256:" + "b" * 64,
        final_config_digest="c" * 64,
        state_digest=inventory["snapshot_sha256"],
        criteria_refs=["fixture://criteria"],
        allowed_restart_count=1,
        deadline=(now + timedelta(hours=1)).isoformat(),
        authority_refs=["fixture://authority"],
        plan_digest="d" * 64,
    )
    assert (
        recipes.exit_check_recipe(
            plan,
            before_database=native.database,
            after_database=native.database,
            now=now,
        )["domain_status"]
        == "READY_FOR_BACKEND_QUALIFICATION"
    )
    plan["deadline"] = (now - timedelta(seconds=1)).isoformat()
    assert (
        recipes.exit_check_recipe(
            plan,
            before_database=native.database,
            after_database=native.database,
            now=now,
        )["domain_status"]
        == "HOLD"
    )


@pytest.mark.parametrize("stage", [0, 1, 10, 50])
def test_actual_proof_promotion_is_consumed_without_reimplementing_maths(stage):
    from goldgraft_contracts.runner import GuardEvent

    from pieces.proof.proof import Proof

    rollout = load("vijay_rollout", ROOT / "pieces/switch-libs/python/rollout.py")
    # Deliberately artificial contrasting populations exercise the real proof
    # implementation's STEP_UP branch. These are NOT observed buyer outcomes.
    events = []
    for index in range(30):
        for path, kinds in [("OLD", ["APPROVED"]), ("NEW", ["APPROVED", "CAPTURED"])]:
            for kind in kinds:
                events.append(
                    GuardEvent(
                        graft_id="fixture",
                        shop_id="fixture",
                        path=path,
                        event=kind,
                        order_ref=f"fixture-{index}",
                        latency_ms=1,
                        ts=datetime.now(UTC),
                        lib_version="offline-fixture",
                    )
                )
    decision = Proof().heal_decide("fixture", stage, events)
    assert str(decision.action) == "STEP_UP"
    assert (
        rollout.proposed_stage(
            decision.model_dump(mode="json"), graft_id="fixture", current_stage=stage
        )
        == decision.to_stage_pct
    )
    cutback = Proof().heal_decide("fixture", stage, events, ["synthetic controlled fault"])
    assert str(cutback.action) == "CUTBACK"
    assert (
        rollout.proposed_stage(
            cutback.model_dump(mode="json"), graft_id="fixture", current_stage=stage
        )
        == 0
    )


def test_actual_proof_with_no_traffic_holds_promotion():
    from pieces.proof.proof import Proof

    decision = Proof().heal_decide("fixture", 10, [])
    assert str(decision.action) == "HOLD" and decision.to_stage_pct == 10
