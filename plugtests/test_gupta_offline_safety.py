"""GU negative/fault checks against real local code, not provider qualification.

PayPal payload shape sources (malformed payloads below are intentional negatives):
https://developer.paypal.com/api/payments/v2/
https://developer.paypal.com/api/webhooks/v1/
https://developer.paypal.com/api/nvp-soap/ipn/IPNandPDTVariables/
"""

import hashlib
import io
import sqlite3
import stat
import tarfile
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from goldgraft_contracts.lifecycle import (
    ActionPlan,
    ApplyApproval,
    ApplyAuthority,
    ApprovalSet,
    EffectSlot,
    TargetKey,
    TargetReservation,
    canonical_target_id,
)
from goldgraft_contracts.plan5_common import content_digest
from goldgraft_foundation.ledger import Ledger

from pieces.backend.callback_gateway import CallbackGateway, WebhookSignatureVerifier
from pieces.backend.callback_inbox import CallbackInbox
from pieces.backend.connection import AuthorityManager, CaseRole, PermissionDeniedError
from pieces.backend.connection.acquisition import SourceAcquisition
from pieces.backend.connection.providers import ProviderAdapter
from pieces.backend.control_store import ControlStore
from pieces.backend.custody_broker import CustodyBroker
from pieces.backend.lifecycle.approvals import AuthorizationEscalationError, verify_plan_approvals
from pieces.backend.lifecycle.effects import EffectManager
from pieces.backend.lifecycle.exit import (
    ORDINARY_CAPABILITIES,
    ExitCheckResult,
    ExitController,
    RevocationAck,
)
from pieces.backend.lifecycle.reservations import ReservationConflictError, TargetReservationManager
from pieces.backend.lifecycle.state_plan import StatePlanner
from pieces.backend.payment_broker import (
    BrokerOutcomeUnknown,
    BrokerRefused,
    PaymentBroker,
    to_minor_units,
)
from pieces.runner.artifact_build import ArtifactBuilder
from pieces.runner.container_runner import ContainerRunner, IsolationNotEstablished
from providers import ArtifactPublisher, GitHubPublisher, RenderDeployer

D = "a" * 64
NOW = datetime(2026, 11, 12, tzinfo=UTC)


@pytest.fixture(autouse=True)
def no_ambient_provider_keys(monkeypatch):
    for name in ("GITHUB_TOKEN", "RENDER_API_KEY", "RENDER_DEPLOY_HOOK_URL", "WORKOS_API_KEY"):
        monkeypatch.delenv(name, raising=False)


def ledger(tmp_path, name="audit"):
    return Ledger(f"sqlite:///{tmp_path / (name + '.sqlite')}")


@pytest.mark.parametrize(
    "role,needed,path",
    [
        (CaseRole.READER, CaseRole.READER, "github.com/org/repo-other"),
        (CaseRole.CONTROLLER, CaseRole.DEPLOYER, "github.com/org/repo"),
        (CaseRole.DEPLOYER, CaseRole.ADMIN, "github.com/org/repo"),
    ],
)
def test_authority_rejects_sibling_resources_and_role_confusion(tmp_path, role, needed, path):
    auth = AuthorityManager(ledger(tmp_path))
    grant = auth.grant_role("case", "actor", role, "github.com/org/repo", granted_by="controller")
    with pytest.raises(PermissionDeniedError):
        auth.check_permission(grant.grant_id, needed, path)
    auth.revoke_grant(grant.grant_id)
    with pytest.raises(PermissionDeniedError):
        auth.check_permission(grant.grant_id, CaseRole.READER, "github.com/org/repo/file")


def zip_bytes(entries):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in entries:
            archive.writestr(name, content)
    data = stream.getvalue()
    for name, _ in entries:
        if "\\" in name:
            normalized = name.replace("\\", "/")
            data = data.replace(normalized.encode("utf-8"), name.encode("utf-8"))
    return data


@pytest.mark.parametrize(
    "name", ["../escape", "/absolute", "a/../../escape", "a\\escape", "a//file"]
)
def test_archive_traversal_is_rejected_without_extraction(tmp_path, name):
    acq = SourceAcquisition(tmp_path / "quarantine")
    with pytest.raises(ValueError, match="UNSAFE_ARCHIVE_PATH"):
        acq.inspect_archive(zip_bytes([("safe.php", b"safe"), (name, b"canary")]))
    assert list(acq.root.iterdir()) == []
    assert not (tmp_path / "escape").exists()


@pytest.mark.parametrize(
    "entries",
    [
        [("A", b"x"), ("a", b"y")],
        [("parent", b"x"), ("parent/file", b"y")],
        [("parent/file", b"x"), ("parent", b"y")],
    ],
)
def test_archive_collisions_fail_whole_inspection(tmp_path, entries):
    with pytest.raises(ValueError, match="COLLISION"):
        SourceAcquisition(tmp_path).inspect_archive(zip_bytes(entries))


@pytest.mark.parametrize("kind", [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE])
def test_tar_links_and_special_files_are_rejected(tmp_path, kind):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as archive:
        member = tarfile.TarInfo("bad")
        member.type, member.linkname = kind, "../../escape"
        archive.addfile(member)
    with pytest.raises(ValueError, match="UNSUPPORTED_ARCHIVE_ENTRY"):
        SourceAcquisition(tmp_path).inspect_archive(stream.getvalue())


def test_zip_symlink_expansion_and_depth_limits(tmp_path):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        member = zipfile.ZipInfo("link")
        member.create_system = 3
        member.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(member, "../../escape")
    acq = SourceAcquisition(tmp_path, max_bytes=1000, max_file_bytes=200, max_depth=2)
    with pytest.raises(ValueError, match="UNSUPPORTED_ARCHIVE_ENTRY"):
        acq.inspect_archive(stream.getvalue())
    with pytest.raises(ValueError, match="EXPANSION_LIMIT"):
        acq.inspect_archive(zip_bytes([("huge", b"x" * 201)]))
    with pytest.raises(ValueError, match="UNSAFE_ARCHIVE_PATH"):
        acq.inspect_archive(zip_bytes([("a/b/c", b"x")]))


def test_canaries_stay_out_of_safe_manifest_and_essential_omission_holds(tmp_path):
    acq = SourceAcquisition(tmp_path)
    payload = zip_bytes(
        [
            ("src/index.php", b"<?php echo 'hello';"),
            (".env", b"PRIVATE_CANARY"),
            ("binary", b"\xffPRIVATE_CANARY"),
            ("config.php", b"password=PRIVATE_CANARY"),
            ("orders.sql", b"PRIVATE_CANARY"),
            (".gitmodules", b"missing module"),
        ]
    )
    safe, omissions = acq.inspect_archive(payload)
    assert list(safe) == ["src/index.php"] and len(omissions) == 5
    assert b"PRIVATE_CANARY" not in b"".join(safe.values())
    with pytest.raises(ValueError, match="REQUIRED_SOURCE_OMITTED"):
        acq.inspect_archive(payload, required_paths=["config.php"])
    asset = acq.acquire_bytes("shop.zip", payload)
    assert asset.sha256 == hashlib.sha256(payload).hexdigest()
    assert acq.acquire_bytes("shop.zip", payload) == asset
    with pytest.raises(ValueError, match="UNSAFE_FILE_PATH"):
        acq.acquire_bytes("../shop.zip", payload)


def test_control_stores_in_memory_are_not_shared():
    first, second = ControlStore(), ControlStore()
    with first.transaction() as tx:
        tx.run("INSERT INTO ids VALUES (?, ?, ?, ?, ?)", ("one", "key", "hash", 200, "{}"))
    assert second.read("SELECT * FROM ids") == []
    first.close()
    second.close()


def test_reservations_restart_fence_unknowns_and_keep_run_ownership(tmp_path):
    database = tmp_path / "reservations.sqlite"
    manager = TargetReservationManager(database=database)
    owned = manager.reserve("service", "case", run_id="run-1")
    with pytest.raises(ReservationConflictError):
        manager.reserve("service", "case", run_id="run-2")
    manager.add_unresolved(owned.reservation_id, "effect:unknown")
    manager.close()
    # Actual DB expiration; stale public dataclass mutation is not authority.
    with sqlite3.connect(database) as db:
        db.execute("UPDATE target_reservations SET expires_at = ?", (NOW.isoformat(),))
    resumed = TargetReservationManager(database=database)
    with pytest.raises(ReservationConflictError, match="unresolved"):
        resumed.reserve("service", "other", run_id="other-run")
    with pytest.raises(ReservationConflictError):
        resumed.require_current(owned.reservation_id, case_id="case", epoch=1, run_id="run-1")
    resumed.resolve_unresolved(owned.reservation_id, "effect:unknown")
    new = resumed.reserve("service", "other", run_id="other-run")
    assert new.fence_epoch == owned.fence_epoch + 1
    with pytest.raises(ReservationConflictError):
        resumed.require_current(owned.reservation_id, case_id="case", epoch=1, run_id="run-1")
    resumed.close()


def test_group_reservation_rolls_back_partial_acquisition_and_cross_instance_race(tmp_path):
    database = tmp_path / "reservation.sqlite"
    first = TargetReservationManager(database=database)
    second = TargetReservationManager(database=database)
    first.reserve("z", "existing")
    with pytest.raises(ReservationConflictError):
        second.reserve_many(["a", "z"], "contender")
    assert first.reserve("a", "winner").case_id == "winner"

    def attempt(manager, case):
        try:
            return manager.reserve("race", case).case_id
        except ReservationConflictError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(attempt, first, "one"), pool.submit(attempt, second, "two")]
        assert sum(f.result() is not None for f in futures) == 1
    first.close()
    second.close()


def test_source_digest_includes_hidden_inputs_boundaries_and_refuses_links(tmp_path):
    builder = ArtifactBuilder()
    (tmp_path / "src").write_bytes(b"source")
    before = builder.calculate_source_digest(tmp_path)
    (tmp_path / ".config").write_bytes(b"one")
    assert builder.calculate_source_digest(tmp_path) != before
    try:
        (tmp_path / "link").symlink_to(tmp_path / "src")
    except OSError:
        pytest.skip("Symlink creation requires elevated privileges on Windows")
    with pytest.raises(ValueError, match="links"):
        builder.calculate_source_digest(tmp_path)


def test_local_artifact_is_immutable_and_never_live_provider_evidence(tmp_path):
    target = tmp_path / "artifact"
    publisher = ArtifactPublisher()
    receipt = publisher.publish_artifact("artifact", str(target), b"exact")
    assert target.read_bytes() == b"exact" and receipt.live is False
    assert publisher.publish_artifact("artifact", str(target), b"exact").digest == receipt.digest
    with pytest.raises(ValueError, match="collision"):
        publisher.publish_artifact("artifact", str(target), b"different")
    with pytest.raises(ValueError, match="Qualified private OCI"):
        publisher.publish_artifact("artifact", "https://registry.example/image", b"exact")


class NoTransport:
    def __getattr__(self, name):
        raise AssertionError("Provider call forbidden")


def test_publish_and_deploy_deny_before_any_call_without_separate_authority():
    github = GitHubPublisher(transport=NoTransport())
    receipt = github.publish_pull_request(
        "https://github.com/org/repo",
        "upgrade",
        title="upgrade",
        commit_sha="a" * 40,
        token="offline-placeholder",
    )
    assert receipt.state == "not_attempted"
    render = RenderDeployer(api_key="offline-placeholder", transport=NoTransport())
    assert render.deploy_service("srv", "repo@sha256:" + D).status == "not_dispatched"
    assert render.deploy_service("srv", "repo:mutable").status == "not_dispatched"
    hook = RenderDeployer(
        deploy_hook_url="https://api.render.com/deploy/srv", transport=NoTransport()
    )
    assert hook.deploy_service("srv", "repo@sha256:" + D).status == "not_dispatched"


def test_provider_read_is_not_read_only_grant_qualification():
    class Transport:
        def get(self, *args, **kwargs):
            return SimpleNamespace(status_code=200, json=lambda: {"serviceDetails": {}})

    observation = ProviderAdapter(transport=Transport()).observe_render_service(
        "srv", api_key="offline"
    )
    assert observation.verified and not observation.read_only


def test_malformed_provider_observation_holds():
    class Transport:
        def get(self, *args, **kwargs):
            return SimpleNamespace(status_code=200, json=lambda: [])

    observation = ProviderAdapter(transport=Transport()).observe_github_repo(
        "https://github.com/org/repo", token="offline"
    )
    assert not observation.verified and observation.evidence_class == "unknown"


def test_missing_exact_image_never_live_even_when_health_would_succeed():
    class Transport:
        def __init__(self):
            self.urls = []

        def post(self, url, **kwargs):
            return SimpleNamespace(status_code=201, json=lambda: {"id": "dep"})

        def get(self, url, **kwargs):
            self.urls.append(url)
            data = (
                [{"deploy": {"id": "dep", "status": "live"}}]
                if "/deploys?" in url
                else {"serviceDetails": {"url": "https://shop.example"}}
            )
            return SimpleNamespace(status_code=200, json=lambda: data)

    transport = Transport()
    receipt = RenderDeployer(
        api_key="offline", transport=transport, authorize=lambda *args: True
    ).deploy_service("srv", "repo@sha256:" + D)
    assert receipt.status == "unknown" and not receipt.live
    assert all(url.startswith("https://api.render.com/") for url in transport.urls)


def test_money_nonfinite_and_rate_limit_boundaries():
    for value in ("NaN", "Infinity", "-Infinity", "1.001"):
        with pytest.raises(BrokerRefused):
            to_minor_units(value, "USD")
    broker = PaymentBroker()
    with pytest.raises(BrokerRefused, match="floating point"):
        broker.execute_orders_v2(
            "create",
            {"purchase_units": [{"amount": {"currency_code": "USD", "value": 1.25}}]},
            secret_ref="unused",
        )
    with pytest.raises(BrokerRefused, match="Non-finite"):
        broker.execute_nvp("SetExpressCheckout", {"AMT": "NaN"}, secret_ref="unused")
    for limit in (0, 51, True):
        with pytest.raises(ValueError):
            PaymentBroker(rate_limit_per_min=limit)


def test_payment_scope_override_and_idempotency_conflict_denied(tmp_path):
    custody = CustodyBroker()
    ref = custody.store_credentials("shop", {"paypal_client_id": "offline-placeholder"}).to_uri()
    broker = PaymentBroker(custody_broker=custody)
    with pytest.raises(BrokerRefused, match="override"):
        broker.execute_nvp("SetExpressCheckout", {"METHOD": "RefundTransaction"}, secret_ref=ref)
    with pytest.raises(BrokerRefused, match="Unsupported"):
        broker.execute_nvp("ArbitraryOperation", {}, secret_ref=ref)
    broker.execute_nvp(
        "SetExpressCheckout", {"AMT": "1.00"}, secret_ref=ref, idempotency_key="same"
    )
    with pytest.raises(BrokerRefused, match="Idempotency"):
        broker.execute_nvp(
            "RefundTransaction", {"AMT": "1.00"}, secret_ref=ref, idempotency_key="same"
        )
    sandbox = PaymentBroker(custody_broker=custody, mode="sandbox", transport=NoTransport())
    with pytest.raises(BrokerRefused, match="journal"):
        sandbox.execute_nvp("SetExpressCheckout", {}, secret_ref=ref, idempotency_key="one")


def test_unknown_payment_never_resubmitted_and_survives_restart(tmp_path):
    custody = CustodyBroker()
    ref = custody.store_credentials(
        "shop",
        {
            "nvp_user": "offline-user",
            "nvp_password": "offline-password",
            "nvp_signature": "offline-signature",
        },
    ).to_uri()

    class TimeoutTransport:
        calls = 0

        def post(self, *args, **kwargs):
            self.calls += 1
            raise TimeoutError("lost response")

    transport = TimeoutTransport()
    database = tmp_path / "payment.sqlite"
    broker = PaymentBroker(
        custody_broker=custody,
        mode="sandbox",
        transport=transport,
        database=database,
        authorize=lambda *args: True,
    )
    for _ in range(2):
        with pytest.raises(BrokerOutcomeUnknown):
            broker.execute_nvp(
                "RefundTransaction",
                {"TRANSACTIONID": "txn"},
                secret_ref=ref,
                idempotency_key="refund-one",
            )
    assert transport.calls == 1
    broker.close()
    resumed = PaymentBroker(
        custody_broker=custody,
        mode="sandbox",
        transport=NoTransport(),
        database=database,
        authorize=lambda *args: True,
    )
    with pytest.raises(BrokerOutcomeUnknown, match="reconciliation"):
        resumed.execute_nvp(
            "RefundTransaction",
            {"TRANSACTIONID": "txn"},
            secret_ref=ref,
            idempotency_key="refund-one",
        )
    resumed.close()


def test_guest_credentials_denied_before_execution(tmp_path):
    with pytest.raises(IsolationNotEstablished, match="credential"):
        ContainerRunner().execute_shop_process(
            tmp_path, ["never-executed"], env={"PAYPAL_PASSWORD": "CANARY"}
        )


class Verified:
    def verify(self, *args):
        return "verified"


def test_callback_requires_complete_business_binding_and_never_claims_effect(tmp_path):
    gateway = CallbackGateway(
        ledger(tmp_path), ipn_verifier=Verified(), webhook_verifier=Verified()
    )
    receipt = gateway.handle_ipn("txn_id=tx&payment_status=Completed", {}, graft_id="case")
    assert receipt.verified and not receipt.applied and receipt.binding_ok is False
    wh = gateway.handle_webhook(
        {
            "id": "wh",
            "event_type": "PAYMENT.CAPTURE.COMPLETED",
            "resource": {"id": "order", "payee": {"merchant_id": "merchant"}},
        },
        {},
        graft_id="case",
        expected={
            "order_id": "order",
            "event_type": "PAYMENT.CAPTURE.COMPLETED",
            "merchant_id": "merchant",
            "amount_minor": 100,
            "currency": "USD",
        },
    )
    assert wh.binding_ok is False and "webhook amount is missing" in wh.holds
    assert not wh.applied


def test_callback_persistence_failure_prevents_verifier_and_no_acceptance(tmp_path):
    class FailedInbox:
        def accept(self, *args):
            raise OSError("storage unavailable")

    class NeverVerify:
        def verify(self, *args):
            raise AssertionError("verification before durable receipt")

    gateway = CallbackGateway(ledger(tmp_path), inbox=FailedInbox(), ipn_verifier=NeverVerify())
    with pytest.raises(OSError, match="storage"):
        gateway.handle_ipn("txn_id=tx", {}, graft_id="case")
    assert gateway.ledger.read("case") == []


def test_callback_unknown_is_retryable_and_receipt_identity_is_case_scoped(tmp_path):
    class RetryVerifier:
        calls = 0

        def verify(self, *args):
            self.calls += 1
            return "unknown" if self.calls == 1 else "verified"

    verifier = RetryVerifier()
    gateway = CallbackGateway(ledger(tmp_path), ipn_verifier=verifier)
    headers = {"paypal-delivery-id": "one"}
    first = gateway.handle_ipn("txn_id=tx", headers, graft_id="case")
    assert first.verification == "unknown"
    assert gateway.inbox.raw("case", "IPN", "one") == b"txn_id=tx"
    assert gateway.handle_ipn("txn_id=tx", headers, graft_id="case").verified
    assert gateway.handle_ipn("txn_id=tx", headers, graft_id="case").status == "DUPLICATE"
    assert gateway.handle_ipn("txn_id=tx", headers, graft_id="other").status == "VERIFIED"
    with pytest.raises(ValueError, match="IDENTITY_CONFLICT"):
        gateway.handle_ipn("txn_id=changed", headers, graft_id="case")


def test_private_callback_store_bounds_and_requires_encryption_for_persistence(tmp_path):
    with pytest.raises(ValueError, match="encryption"):
        CallbackInbox(database=tmp_path / "raw.sqlite")
    inbox = CallbackInbox(max_body_bytes=3, max_receipts=1)
    inbox.accept("case", "IPN", "one", b"raw")
    with pytest.raises(ValueError, match="QUOTA"):
        inbox.accept("case", "IPN", "two", b"raw")
    with pytest.raises(ValueError, match="LIMIT"):
        inbox.accept("case", "IPN", "one", b"oversized")
    inbox.close()


def test_webhook_incomplete_transmission_headers_never_verifies():
    verifier = WebhookSignatureVerifier(
        token="offline", webhook_id="listener", transport=NoTransport()
    )
    assert (
        verifier.verify(
            {},
            {
                "paypal-transmission-id": "one",
                "paypal-transmission-sig": "sig",
                "paypal-auth-algo": "SHA256withRSA",
            },
        )
        == "invalid"
    )


def test_invalid_state_fences_and_empty_manifests_never_approve():
    plan = StatePlanner().create_cutover_plan(
        "case",
        "NVP",
        "OrdersV2",
        [],
        writer_inventory_ref="",
        handler_inventory_ref="",
        ingress_ref="",
        high_water_mark=True,
        fence_epochs={"writer": -1},
        export_manifest_ref="",
        restore_verified_ref="",
        replay_manifest_ref="",
        approvals=["approval"],
    )
    assert not plan.approved and len(plan.holds) >= 8


def test_exit_shared_cleanup_denied_before_side_effects_and_forged_executor_held(tmp_path):
    class Executor:
        identity_ref = "merchant-executor"

        def run_exit_check(self):
            return ExitCheckResult("wrong-executor", True, "recovered", ["blob:evidence"], True)

    executor = Executor()
    controller = ExitController(ledger(tmp_path))
    held = controller.execute_merchant_exit(
        "case",
        actor_name="owner",
        idempotency_key="exit",
        executor=executor,
        token_keys=["shared-grant"],
    )
    assert held.outcome == "held" and not controller._revoked_tokens
    permitted = ExitController(
        ledger(tmp_path, "other"),
        authorize_exit=lambda *args: True,
        authenticate_result=lambda *args: True,
    )
    revocations = [RevocationAck(c, True, "blob:ack") for c in ORDINARY_CAPABILITIES]
    unknown = permitted.execute_merchant_exit(
        "case",
        actor_name="owner",
        idempotency_key="exit",
        executor=executor,
        revocations=revocations,
        exit_evidence_ack=RevocationAck("exit_evidence", True, "blob:ack"),
    )
    assert unknown.outcome == "unknown" and not unknown.verified_clean


def approval_records():
    target = TargetKey(
        provider_id="render",
        account_id="merchant",
        environment_id="production",
        resource_kind="service",
        resource_id="srv",
    )
    target_id = canonical_target_id(target)
    slot = EffectSlot(
        slot_id="deploy",
        operation="deploy_exact",
        target_key=target,
        effect_class="E2",
        depends_on=[],
        artifact_digest="sha256:" + D,
        config_digest=D,
        state_plan_digest=D,
        trigger_digest=D,
        required_authority_refs=["blob:authority"],
        required_controller_ids=["host-controller"],
        expected_version_ref="blob:version",
        cardinality=1,
        recovery_branch_ref=None,
    )
    plan = ActionPlan(
        plan_id="plan",
        case_id="case",
        run_id="run",
        generation=1,
        graph_digest=D,
        scope_digest=D,
        review_bundle_digest=D,
        policy_digest=D,
        slots=[slot],
        recovery_plan_ref="blob:recovery",
        state_plan_ref="blob:state",
        finalisation_plan_ref="blob:final",
        exit_plan_ref="blob:exit",
        budget_ref="blob:budget",
        expires_at=NOW + timedelta(minutes=5),
        plan_digest=D,
    )
    plan = plan.model_copy(
        update={
            "plan_digest": content_digest(plan.model_dump(mode="json", exclude={"plan_digest"}))
        }
    )
    authority = ApplyAuthority(
        authority_id="authority",
        controller_id="host-controller",
        delegate_id=None,
        target_key=target,
        actions=["deploy_exact"],
        role_evidence_refs=["blob:role"],
        grant_epoch=1,
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=5),
        revoked_at=None,
    )
    approval = ApplyApproval(
        approval_id="approval",
        case_id="case",
        controller_id="host-controller",
        action_group_id="group",
        authority_binding_epochs={"authority": 1},
        graph_digest=D,
        scope_digest=D,
        reviewed_bundle_digest=D,
        baseline_digest=D,
        candidate_digest=D,
        patch_digest=D,
        artifact_digest="sha256:" + D,
        config_digest=D,
        delivery_route="direct_artifact",
        source_snapshot_digests=[D],
        source_head=None,
        source_base=None,
        publication_destination_refs=["blob:private-merchant-registry"],
        trigger_chain_digest=D,
        target_resources=[target_id],
        allowed_actions=["deploy_exact"],
        state_plan_digest=D,
        recovery_plan_digest=D,
        policy_digest=D,
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=5),
        generation=1,
        action_plan_digest=plan.plan_digest,
        authority_refs=["blob:authority"],
        revoked_at=None,
    )
    approvals = ApprovalSet(
        approval_set_id="approvals",
        case_id="case",
        run_id="run",
        generation=1,
        plan_digest=plan.plan_digest,
        required_controller_ids=["host-controller"],
        approval_refs=["blob:approval"],
        authority_epochs={"authority": 1},
        checked_at=NOW,
        state="complete",
    )
    reservation = TargetReservation(
        reservation_id="reservation",
        case_id="case",
        run_id="run",
        action_plan_ref="blob:plan",
        target_keys=[target],
        resource_epochs={target_id: 1},
        lease_until=NOW + timedelta(minutes=5),
        expected_version_refs=["blob:version"],
        unresolved_effect_refs=[],
        state="held",
    )
    return (
        plan,
        approvals,
        dict(
            authorities={"blob:authority": authority},
            approvals={"blob:approval": approval},
            reservation=reservation,
            current_authority_epochs={"authority": 1},
            current_resource_epochs={target_id: 1},
            required_controllers_by_target={target_id: ["host-controller"]},
            current_version_refs={target_id: "blob:version"},
            reservation_plan_digest=plan.plan_digest,
            now=NOW,
        ),
    )


def test_exact_plan_approvals_and_effect_slot_cardinality_survive_restart(tmp_path):
    plan, approvals, inputs = approval_records()
    assert verify_plan_approvals(plan, approvals, **inputs)
    database = tmp_path / "effects.sqlite"
    effects = EffectManager(database=database)
    first = effects.allocate_plan_slot(plan, "deploy")
    effects.mark_unknown(first.slot_id, "provider response lost")
    effects.close()
    resumed = EffectManager(database=database)
    again = resumed.allocate_plan_slot(plan, "deploy")
    assert again.slot_id == first.slot_id and again.status == "UNKNOWN"
    with pytest.raises(ValueError, match="Unknown action plan slot"):
        resumed.allocate_plan_slot(plan, "extra-deploy")
    resumed.close()


@pytest.mark.parametrize(
    "fault",
    [
        "image",
        "missing-controller",
        "revoked",
        "expired",
        "epoch",
        "reservation",
        "target",
        "trigger",
        "operation",
        "resource-epoch",
        "actual-controller",
        "version",
        "reservation-plan",
    ],
)
def test_partial_stale_or_mismatched_approval_never_authorizes(fault):
    plan, approvals, inputs = approval_records()
    approval = inputs["approvals"]["blob:approval"]
    authority = inputs["authorities"]["blob:authority"]
    if fault == "image":
        inputs["approvals"]["blob:approval"] = approval.model_copy(
            update={"artifact_digest": "sha256:" + "b" * 64}
        )
    elif fault == "missing-controller":
        approvals = approvals.model_copy(update={"required_controller_ids": []})
    elif fault == "revoked":
        inputs["authorities"]["blob:authority"] = authority.model_copy(update={"revoked_at": NOW})
    elif fault == "expired":
        inputs["approvals"]["blob:approval"] = approval.model_copy(update={"expires_at": NOW})
    elif fault == "epoch":
        inputs["current_authority_epochs"] = {"authority": 2}
    elif fault == "reservation":
        inputs["reservation"] = inputs["reservation"].model_copy(
            update={"unresolved_effect_refs": ["blob:unknown"]}
        )
    elif fault == "target":
        inputs["approvals"]["blob:approval"] = approval.model_copy(
            update={"target_resources": ["other"]}
        )
    elif fault == "trigger":
        inputs["approvals"]["blob:approval"] = approval.model_copy(
            update={"trigger_chain_digest": "b" * 64}
        )
    elif fault == "resource-epoch":
        inputs["current_resource_epochs"] = {next(iter(inputs["current_resource_epochs"])): 2}
    elif fault == "actual-controller":
        inputs["required_controllers_by_target"] = {}
    elif fault == "version":
        inputs["current_version_refs"] = {}
    elif fault == "reservation-plan":
        inputs["reservation_plan_digest"] = "b" * 64
    else:
        inputs["authorities"]["blob:authority"] = authority.model_copy(
            update={"actions": ["publish_source"]}
        )
    with pytest.raises(AuthorizationEscalationError):
        verify_plan_approvals(plan, approvals, **inputs)


def test_receipt_phase_does_not_verify_and_retry_uses_original_bytes(tmp_path):
    class Verifier:
        calls = []

        def verify(self, raw, headers):
            self.calls.append(raw)
            return "unknown"

    verifier = Verifier()
    database = tmp_path / "inbox.sqlite"
    # Identity codec deliberately tests storage/restart only, NOT encryption.
    # Production host key management and an authenticated encryption codec are blocked.
    inbox = CallbackInbox(database=database, seal=lambda b: b, unseal=lambda b: b)
    gateway = CallbackGateway(ledger(tmp_path), inbox=inbox, ipn_verifier=verifier)
    received = gateway.receive_ipn("txn_id=offline%2Btest", {}, graft_id="case")
    assert received.verification == "unverified" and not received.applied and not verifier.calls
    inbox.close()
    resumed = CallbackInbox(database=database, seal=lambda b: b, unseal=lambda b: b)
    gateway = CallbackGateway(ledger(tmp_path), inbox=resumed, ipn_verifier=verifier)
    assert gateway.retry_ipn(received.delivery_id, graft_id="case").verification == "unknown"
    assert verifier.calls == ["txn_id=offline%2Btest"]
    resumed.close()
