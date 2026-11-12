"""Comprehensive tests for Connection (GU01/GU02) and Providers/Build (GU04/GU05)."""

import sys

import pytest
from goldgraft_contracts.common import Producer, ProducerKind, Stage
from goldgraft_contracts.ledger import EntryType
from goldgraft_foundation.ledger import Ledger

from pieces.backend.callback_gateway import CallbackGateway
from pieces.backend.connection import (
    AuthorityManager,
    CaseManager,
    CaseRole,
    PermissionDeniedError,
    ProviderAdapter,
    ReadinessInspector,
    ResourceGraph,
    SourceAcquisition,
    UploadSessionManager,
)
from pieces.backend.custody_broker import CustodyBroker
from pieces.backend.lifecycle import (
    EffectManager,
    EffectStatus,
    LedgerReconciler,
    ReservationConflictError,
    StatePlanner,
    TargetReservationManager,
)
from pieces.backend.payment_broker import PaymentBroker
from pieces.runner.artifact_build import ArtifactBuilder
from pieces.runner.container_runner import (
    BlockedEgressError,
    ContainerRunner,
    SandboxedProcessBackend,
)
from pieces.runner.sandbox_recorder import SandboxRecorder
from providers import ArtifactPublisher, GitHubPublisher, RenderDeployer


def test_connection_case_and_authority(tmp_path):
    ledger = Ledger()
    case_mgr = CaseManager(ledger=ledger)
    auth_mgr = AuthorityManager(ledger=ledger)

    case = case_mgr.create_case("merchant-1", "workspace-retail", allowed_resources=["repo-1"])
    assert case.status == "CREATED"
    assert case.case_id.startswith("case-")

    case_mgr.bind_controller(case.case_id, "controller-1")
    bound = case_mgr.get_case(case.case_id)
    assert bound.status == "BOUND"
    assert "controller-1" in bound.bound_controllers

    # Grant Reader role
    reader_grant = auth_mgr.grant_role(
        case.case_id,
        "auditor-1",
        CaseRole.READER,
        "github.com/merchant/repo",
        granted_by="admin-1",
    )
    auth_mgr.check_permission(reader_grant.grant_id, CaseRole.READER, "github.com/merchant/repo")

    # Reader cannot perform write/deploy action
    with pytest.raises(PermissionDeniedError, match="Reader escalation denied"):
        auth_mgr.check_permission(
            reader_grant.grant_id, CaseRole.DEPLOYER, "github.com/merchant/repo"
        )


def test_provider_adapters_and_resource_graph():
    adapter = ProviderAdapter()
    gh_offline = adapter.observe_github_repo("https://github.com/merchant/shop")
    assert gh_offline.verified is False
    assert gh_offline.read_only is True
    assert gh_offline.evidence_class == "offline"
    assert "no GitHub token" in str(gh_offline.error)

    # With mock live transport
    class MockTransport:
        def get(self, url, headers=None, timeout=None):
            class Resp:
                status_code = 200

                def json(self):
                    return {
                        "name": "shop",
                        "default_branch": "main",
                        "private": True,
                        "permissions": {"pull": True, "push": False},
                    }

            return Resp()

    live_adapter = ProviderAdapter(transport=MockTransport())
    gh_live = live_adapter.observe_github_repo("https://github.com/merchant/shop", token="ghp_test")
    assert gh_live.verified is True
    assert gh_live.evidence_class == "live"
    assert gh_live.read_only is False  # metadata read alone does not qualify Reader scope

    graph = ResourceGraph()
    graph.add_resource("res-1", "repository", "github.com/org/repo", selected=True)
    graph.add_resource("res-2", "database", "postgres://db", selected=False)

    selected = graph.get_selected_scope()
    assert len(selected) == 1
    assert selected[0].node_id == "res-1"

    boundary = graph.get_workspace_boundary()
    assert "res-1" in boundary["authorized_selected"]
    assert "res-2" in boundary["fenced_unselected"]


def test_source_acquisition_and_upload_sessions(tmp_path):
    acq = SourceAcquisition(quarantine_root=tmp_path / "quarantine")
    asset = acq.acquire_bytes("archive.tar.gz", b"sample payload content")
    assert asset.asset_id.startswith("asset-")
    assert asset.byte_count == len(b"sample payload content")
    assert acq.get_asset(asset.asset_id) is not None

    import hashlib

    full_data = b"chunk1_data_chunk2_data"
    expected_hash = hashlib.sha256(full_data).hexdigest()

    upload_mgr = UploadSessionManager()
    session = upload_mgr.create_session("case-1", "archive.tar.gz", 2, expected_hash)

    upload_mgr.add_chunk(session.session_id, 0, b"chunk1_data_")
    upload_mgr.add_chunk(session.session_id, 1, b"chunk2_data")

    final_bytes = upload_mgr.finalize_session(session.session_id)
    assert final_bytes == full_data


def test_readiness_inspector():
    inspector = ReadinessInspector()
    report = inspector.inspect(
        "case-1",
        has_case=True,
        has_authority=True,
        has_secrets=True,
        is_read_only_safe=True,
    )
    assert report.overall_status == "READY"

    held_report = inspector.inspect(
        "case-1",
        has_case=True,
        has_authority=False,
        has_secrets=True,
    )
    assert held_report.overall_status == "HELD"


def test_lifecycle_reservations_and_effects():
    res_mgr = TargetReservationManager(default_lease_seconds=60)
    res = res_mgr.reserve("render.com/srv-1", "case-1")
    assert res.released is False

    # Conflicting reservation raises
    with pytest.raises(ReservationConflictError, match="reserved by case"):
        res_mgr.reserve("render.com/srv-1", "case-2")

    res_mgr.release(res.reservation_id)
    res2 = res_mgr.reserve("render.com/srv-1", "case-2")
    assert res2.case_id == "case-2"

    eff_mgr = EffectManager()
    slot = eff_mgr.allocate_slot("case-1", "PUBLISH_PR", "github.com/org/repo", "idem-1")
    assert slot.status == EffectStatus.PENDING

    eff_mgr.record_execution(slot.slot_id, success=True, note="PR created successfully")
    assert slot.status == EffectStatus.EXECUTED


def test_state_plan_and_reconciliation(tmp_path):
    planner = StatePlanner()
    # Unapproved plan due to missing manifests / fence evidence
    plan = planner.create_cutover_plan("graft-1", "NVP", "OrdersV2", ["ORDER-1", "ORDER-2"])
    assert plan.preserved_order_count == 2
    assert plan.approved is False
    assert len(plan.holds) > 0

    # Approved plan with all required evidence
    approved_plan = planner.create_cutover_plan(
        "graft-1",
        "NVP",
        "OrdersV2",
        ["ORDER-1", "ORDER-2"],
        writer_inventory_ref="blob://writer/inv",
        handler_inventory_ref="blob://handler/inv",
        ingress_ref="blob://ingress/route",
        high_water_mark=42,
        fence_epochs={"writer-1": 1},
        export_manifest_ref="blob://export/manifest",
        restore_verified_ref="blob://restore/verified",
        replay_manifest_ref="blob://replay/manifest",
        approvals=["approval-slot-1"],
    )
    assert approved_plan.approved is True
    assert len(approved_plan.holds) == 0

    ledger = Ledger()
    reconciler = LedgerReconciler(ledger=ledger)
    report = reconciler.reconcile_graft("graft-clean")
    assert report.clean is True


def test_artifact_build_and_providers(tmp_path):
    builder = ArtifactBuilder()
    (tmp_path / "test.txt").write_text("sample content")
    source_digest = builder.calculate_source_digest(tmp_path)
    assert len(source_digest) == 64

    artifact = builder.create_artifact_build("graft-1", "goldgraft-shop", "v1.0.0", source_digest)
    assert artifact.outcome == "not_built"
    assert artifact.reproducible is False
    assert artifact.image_tag == "goldgraft-shop:v1.0.0"
    assert artifact.metadata_digest is not None

    gh_pub = GitHubPublisher()
    pr = gh_pub.publish_pull_request(
        "https://github.com/org/repo",
        "feat/upgrade",
        title="Upgrade to Orders v2",
        commit_sha="abcd1234ef",
    )
    assert pr.state == "not_attempted"
    assert pr.pr_id is None
    assert len(pr.receipt_digest) == 64
    assert pr.commit_sha == "abcd1234ef"

    # With mock transport returning created PR
    class MockPRTransport:
        def post(self, url, headers=None, json=None, timeout=None):
            class Resp:
                status_code = 201

                def json(self):
                    return {
                        "number": 42,
                        "html_url": "https://github.com/org/repo/pull/42",
                        "head": {"sha": "abcd1234ef"},
                    }

            return Resp()

    gh_pub_live = GitHubPublisher(transport=MockPRTransport(), authorize=lambda *args: True)
    pr_live = gh_pub_live.publish_pull_request(
        "https://github.com/org/repo",
        "feat/upgrade",
        title="Upgrade to Orders v2",
        commit_sha="abcd1234ef",
        token="ghp_test",
    )
    assert pr_live.state == "created"
    assert pr_live.pr_id == "42"
    assert pr_live.live is True

    render = RenderDeployer()
    dep = render.deploy_service("srv-test", "goldgraft-shop:v1.0.0")
    assert dep.status == "not_dispatched"
    assert dep.live is False
    assert "no Render credential" in str(dep.error)

    pub = ArtifactPublisher()
    pub_rcpt = pub.publish_artifact(
        artifact.artifact_id, str(tmp_path / "registry.local" / "image"), b"docker_image_bytes"
    )
    assert pub_rcpt.publish_id.startswith("pub-")

    # GHCR remote container image publication
    digest = "sha256:" + "a" * 64

    # Requires token
    with pytest.raises(ValueError, match="authority required"):
        pub.publish_container_image(
            artifact.artifact_id, "goldgraft:v1", digest, "ghcr.io/org/goldgraft", token=None
        )

    # Injected transport matching remote digest
    class MockGhcrTransport:
        def get(self, url, headers=None):
            class Response:
                status_code = 200
                headers = {"Docker-Content-Digest": digest}

            return Response()

    live_pub = ArtifactPublisher(transport=MockGhcrTransport())
    rcpt = live_pub.publish_container_image(
        artifact.artifact_id,
        "goldgraft:v1",
        digest,
        "ghcr.io/org/goldgraft",
        token="ghp_test_token_123",
    )
    assert rcpt.live is True
    assert rcpt.digest == digest
    assert "ghcr.io/org/goldgraft@" in rcpt.destination


def test_upload_session_limits_and_traversal_guards():
    upload_mgr = UploadSessionManager(max_size_bytes=1000)

    # 1. Inline size limit (16KB)
    upload_mgr.validate_inline_upload(b"x" * 1024)
    with pytest.raises(ValueError, match="PAYLOAD_TOO_LARGE"):
        upload_mgr.validate_inline_upload(b"x" * (16 * 1024 + 1))

    # 2. Path traversal check
    with pytest.raises(ValueError, match="UNSAFE_FILE_PATH"):
        upload_mgr.create_session("case-1", "../../etc/passwd", 1, "sha")

    with pytest.raises(ValueError, match="UNSAFE_FILE_PATH"):
        upload_mgr.create_session("case-1", "nested/file.txt", 1, "sha")

    # 3. Chunk size limit (1MB)
    session = upload_mgr.create_session("case-1", "safe.bin", 2, "0" * 64)
    with pytest.raises(ValueError, match="CHUNK_TOO_LARGE"):
        upload_mgr.add_chunk(session.session_id, 0, b"x" * (1024 * 1024 + 1))

    # 4. Total size limit
    with pytest.raises(ValueError, match="PAYLOAD_TOO_LARGE"):
        upload_mgr.add_chunk(session.session_id, 0, b"x" * 1001)


def test_isolated_shop_execution_and_redaction(tmp_path):
    from pieces.runner.container_runner import IsolationNotEstablished

    runner = ContainerRunner()
    # Unisolated host execution denied by default
    with pytest.raises(IsolationNotEstablished):
        runner.execute_shop_process(
            shop_dir=tmp_path,
            command=[sys.executable, "-c", "print('hello')"],
        )

    # Opted-in execution redacts secrets
    result = runner.execute_shop_process(
        shop_dir=tmp_path,
        command=[
            sys.executable,
            "-c",
            "print('API_KEY=super_secret_val_123'); print('NORMAL_LINE=hello_world')",
        ],
        allow_host_process=True,
    )
    assert result["exit_code"] == 0
    assert "super_secret_val_123" not in result["stdout"]
    assert "[REDACTED]" in result["stdout"]
    assert "NORMAL_LINE=hello_world" in result["stdout"]
    assert result["isolation_verified"] is False


def test_scratch_copy_process_is_not_isolation_and_screens_egress(tmp_path):
    # Setup test file in original shop dir
    orig_file = tmp_path / "app.py"
    orig_file.write_text("print('original')", encoding="utf-8")

    runner = ContainerRunner(isolation=SandboxedProcessBackend())

    # 1. Successful isolated execution modifies scratch copy, preserving original directory
    result = runner.execute_shop_process(
        shop_dir=tmp_path,
        command=[
            sys.executable,
            "-c",
            "import pathlib\n"
            "pathlib.Path('mutated.txt').write_text('mutated')\n"
            "print('isolated_ok')",
        ],
    )
    assert result["exit_code"] == 0
    assert "isolated_ok" in result["stdout"]
    # A host process in a scratch copy is not isolation, and says so.
    assert result["isolation_verified"] is False
    assert result["termination_confirmed"] is True
    assert result["execution_boundary"] == "host_process_scratch_copy"
    # Relative writes land in the scratch copy, not the source folder
    assert not (tmp_path / "mutated.txt").exists()
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "print('original')"

    # 2. Blocked egress to metadata endpoint
    with pytest.raises(BlockedEgressError, match="metadata"):
        runner.execute_shop_process(
            shop_dir=tmp_path,
            command=["curl", "http://169.254.169.254/latest/meta-data/"],
        )

    # 3. Blocked egress to private network
    with pytest.raises(BlockedEgressError, match="private network"):
        runner.execute_shop_process(
            shop_dir=tmp_path,
            command=["curl", "http://10.0.0.1/admin"],
        )


def test_authenticated_callback_gateway():
    ledger = Ledger()
    gateway = CallbackGateway(ledger=ledger)

    # Webhook without verifier: unverified receipt with hold
    wh_receipt = gateway.handle_webhook(
        event_payload={"id": "WH-TEST-1", "event_type": "PAYMENT.CAPTURE.COMPLETED"},
        headers={
            "paypal-transmission-sig": "test-signature",
            "paypal-cert-url": "https://api.sandbox.paypal.com/v1/certs/1",
        },
        graft_id="graft-wh-1",
    )
    assert wh_receipt.verified is False
    assert wh_receipt.status == "UNVERIFIED"
    assert "no webhook signature verifier configured" in wh_receipt.holds

    # With configured verifier
    class MockVerifier:
        def verify(self, payload_or_body, headers):
            return "verified"

    verified_gateway = CallbackGateway(
        ledger=ledger, webhook_verifier=MockVerifier(), ipn_verifier=MockVerifier()
    )
    wh_ok = verified_gateway.handle_webhook(
        event_payload={"id": "WH-TEST-2", "event_type": "PAYMENT.CAPTURE.COMPLETED"},
        headers={"paypal-transmission-sig": "sig"},
        graft_id="graft-wh-2",
    )
    assert wh_ok.verified is True
    assert wh_ok.status == "VERIFIED"

    ipn_ok = verified_gateway.handle_ipn(
        raw_body="cmd=_notify-validate&payment_status=Completed&txn_id=TXN123",
        headers={},
        graft_id="graft-ipn-2",
    )
    assert ipn_ok.verified is True
    assert ipn_ok.status == "VERIFIED"


def test_interrupted_operation_recovery(tmp_path):
    ledger = Ledger(database_url=f"sqlite:///{tmp_path / 'test_reconcile.db'}")
    producer = Producer(kind=ProducerKind.SERVICE, name="TestRunner", version="1.0.0")

    # Append an interrupted in-flight stage
    ledger.append(
        graft_id="graft-interrupted",
        type=EntryType.STAGE.value,
        producer=producer.model_dump(),
        schema="StageChange/1",
        payload={
            "graft_id": "graft-interrupted",
            "from_stage": Stage.CREATED.value,
            "to_stage": Stage.GRAFTED.value,
            "attempt": 1,
            "reason": "Started grafting shop",
            "actor": {"kind": "service", "name": "runner"},
            "evidence_refs": [],
        },
        idempotency_key="graft-start",
    )

    reconciler = LedgerReconciler(ledger=ledger)
    report = reconciler.reconcile_interrupted_operation("graft-interrupted")
    assert report.clean is False
    assert report.last_known_stage == Stage.GRAFTED.value
    assert report.reconciled_stage == Stage.CUTBACK.value
    assert report.reconciled_entry_seq is not None

    # Inspect that the newly appended entry brought the ledger into CUTBACK
    clean_check = reconciler.reconcile_graft("graft-interrupted")
    assert clean_check.reconciled_stage == Stage.CUTBACK.value


def test_payment_broker_live_and_evidence_class():
    custody = CustodyBroker()
    ledger = Ledger()

    broker_scripted = PaymentBroker(custody_broker=custody, ledger=ledger, live=False)
    assert broker_scripted.evidence_class == "scripted"

    broker_live = PaymentBroker(custody_broker=custody, ledger=ledger, live=True)
    assert broker_live.evidence_class == "real_sandbox"

    # Synthetic recorder accepts only scripted broker
    recorder_1 = SandboxRecorder(broker=broker_scripted)
    assert recorder_1 is not None

    with pytest.raises(
        ValueError, match="SandboxRecorder generates synthetic exchanges in process"
    ):
        SandboxRecorder(broker=broker_live)


def test_upload_limits_retry_and_interrupted_assembly(tmp_path):
    import hashlib

    database = tmp_path / "uploads.sqlite3"
    upload = UploadSessionManager(max_size_bytes=5, database=database)
    digest = hashlib.sha256(b"abcde").hexdigest()
    session = upload.create_session("case-1", "file", 2, digest)
    sid = session.session_id
    first = upload.add_chunk(sid, 0, b"abc")
    assert upload.create_session("case-1", "file", 2, digest).session_id == sid
    assert upload.add_chunk(sid, 0, b"abc") == first
    with pytest.raises(ValueError, match="retry"):
        upload.add_chunk(sid, 0, b"bad")
    with pytest.raises(ValueError, match="Missing chunks"):
        upload.finalize_session(sid)
    with pytest.raises(ValueError, match="index"):
        upload.add_chunk(sid, 2, b"x")
    with pytest.raises(ValueError, match="size limit"):
        upload.add_chunk(sid, 1, b"toolong")
    upload.close()
    upload = UploadSessionManager(max_size_bytes=5, database=database)
    assert upload.create_session("case-1", "file", 2, digest).received_chunks[0] == first
    upload.add_chunk(sid, 1, b"de")
    assert upload.finalize_session(sid) == b"abcde"
    assert upload.finalize_session(sid) == b"abcde"
    with pytest.raises(ValueError, match="not active"):
        upload.add_chunk(sid, 0, b"abc")
    upload.close()


def test_unknown_effect_survives_restart_without_resetting_intent(tmp_path):
    database = tmp_path / "effects.sqlite3"
    args = ("case-1", "PUBLISH_PR", "github.com/org/repo", "request-1")
    first = EffectManager(database=database)
    intent = first.allocate_slot(*args)
    first.mark_unknown(intent.slot_id, "Request timed out")
    first.close()

    resumed = EffectManager(database=database)
    unknown = resumed.allocate_slot(*args)
    assert unknown.slot_id == intent.slot_id and unknown.status == EffectStatus.UNKNOWN
    assert unknown.reconciliation_note == "Request timed out"
    with pytest.raises(ValueError, match="reconciliation note"):
        resumed.record_execution(unknown.slot_id, success=True)
    completed = resumed.record_execution(unknown.slot_id, success=True, note="PR receipt read")
    assert completed.status == EffectStatus.EXECUTED
    with pytest.raises(ValueError, match="terminal effect"):
        resumed.mark_unknown(completed.slot_id, "Old retry")
    resumed.close()


def test_failed_reconciled_and_compensated_effects_keep_one_durable_slot(tmp_path):
    database = tmp_path / "effects.sqlite3"
    mgr = EffectManager(database=database)
    slot = mgr.allocate_slot("case-1", "DEPLOY", "render.com/srv-1", "request-1")
    # A failed effect is FAILED, not rolled back, and may be retried on the same slot.
    assert mgr.record_execution(slot.slot_id, success=False).status == EffectStatus.FAILED
    mgr.mark_unknown(slot.slot_id, "Retry timed out")
    with pytest.raises(ValueError, match="reconciliation note"):
        mgr.reconcile(slot.slot_id, observed=True, note=" ")
    done = mgr.reconcile(slot.slot_id, observed=True, note="Deploy receipt read")
    assert done.status == EffectStatus.EXECUTED and done.attempts == 1
    with pytest.raises(ValueError, match="only a UNKNOWN effect"):
        mgr.reconcile(slot.slot_id, observed=False, note="late")
    with pytest.raises(ValueError, match="separate financial authority"):
        mgr.record_compensation(slot.slot_id, authority_ref="")
    mgr.record_compensation(slot.slot_id, authority_ref="approval-7", note="Refunded")
    mgr.close()

    resumed = EffectManager(database=database)
    again = resumed.allocate_slot("case-1", "DEPLOY", "render.com/srv-1", "request-1")
    assert again.slot_id == slot.slot_id
    assert (again.status, again.compensation_ref) == (EffectStatus.COMPENSATED, "approval-7")
    with pytest.raises(ValueError, match="terminal effect"):
        resumed.record_execution(again.slot_id, success=True, note="replay")
    pending = resumed.allocate_slot("case-1", "DEPLOY", "render.com/srv-1", "request-2")
    with pytest.raises(ValueError, match="only a EXECUTED effect"):
        resumed.record_compensation(pending.slot_id, authority_ref="approval-8")
    resumed.close()


def test_control_store_transactions_and_fencing(tmp_path):
    from pieces.backend.control_store import ControlStore

    db_path = tmp_path / "test_control.db"
    store = ControlStore(db_path)

    # 1. Insert session and case inside transaction
    with store.transaction() as tx:
        tx.run(
            "INSERT INTO cases (case_id, tenant_id, requester_id, shop_url, "
            "status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "case-100",
                "tenant-1",
                "user-1",
                "https://shop.local",
                "OPEN",
                "2026-11-12T00:00:00Z",
                "2026-11-12T00:00:00Z",
            ),
        )
        tx.run(
            "INSERT INTO members (case_id, principal_id, role) VALUES (?, ?, ?)",
            ("case-100", "user-1", "OWNER"),
        )

    # Verify read outside transaction
    case_row = store.read("SELECT * FROM cases WHERE case_id = ?", ("case-100",))
    assert len(case_row) == 1
    assert case_row[0]["tenant_id"] == "tenant-1"

    # 2. Work generation lease & fencing
    with store.transaction() as tx:
        tx.run(
            "INSERT INTO work (work_id, action_id, case_id, state, generation, lease_until) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("work-1", "act-1", "case-100", "LEASED", 1, "2026-11-12T01:00:00Z"),
        )

    work_row = store.read("SELECT * FROM work WHERE work_id = ?", ("work-1",))
    assert work_row[0]["generation"] == 1

    # 3. Cancellation and tombstone
    with store.transaction() as tx:
        tx.run(
            "INSERT INTO cancellations (cancel_id, case_id, action_id, "
            "requested_by, requested_at, state, generation) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("cancel-1", "case-100", "act-1", "user-1", "2026-11-12T00:30:00Z", "CANCELLED", 1),
        )
        tx.run(
            "INSERT INTO tombstones (action_id, cancel_id, created_at) VALUES (?, ?, ?)",
            ("act-1", "cancel-1", "2026-11-12T00:30:00Z"),
        )

    tombstone = store.read("SELECT * FROM tombstones WHERE action_id = ?", ("act-1",))
    assert len(tombstone) == 1
    assert tombstone[0]["cancel_id"] == "cancel-1"

    # 4. Rollback test on transaction failure
    with pytest.raises(RuntimeError):
        with store.transaction() as tx:
            tx.run(
                "INSERT INTO cases (case_id, tenant_id, requester_id, shop_url, "
                "status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("case-failed", "tenant-1", "user-1", "url", "OPEN", "now", "now"),
            )
            raise RuntimeError("simulated crash during write")

    failed_case = store.read("SELECT * FROM cases WHERE case_id = ?", ("case-failed",))
    assert len(failed_case) == 0

    store.close()


def test_e2b_backend_never_falls_back_to_a_host_process(tmp_path):
    from pieces.runner.container_runner import E2BIsolationBackend, IsolationNotEstablished

    marker = tmp_path / "ran.txt"
    runner = ContainerRunner(isolation=E2BIsolationBackend(api_key="e2b_test_key"))
    with pytest.raises(IsolationNotEstablished, match="authorize_remote"):
        runner.execute_shop_process(
            shop_dir=tmp_path,
            command=[sys.executable, "-c", f"open({str(marker)!r}, 'w').write('x')"],
        )
    assert not marker.exists()
    with pytest.raises(IsolationNotEstablished, match="E2B_API_KEY"):
        E2BIsolationBackend(api_key="").run(["true"], cwd=tmp_path, env={}, timeout_s=1)


def test_custody_never_hands_process_credentials_to_an_unknown_shop(monkeypatch):
    monkeypatch.setenv("PAYPAL_CLIENT_ID", "operator-sandbox-id")
    monkeypatch.setenv("PAYPAL_CLIENT_SECRET", "operator-sandbox-secret")
    assert CustodyBroker().resolve_credentials("doppler://goldgraft/shops/other/secrets") == {}
    named = "doppler://goldgraft/shops/operator-sandbox/secrets"
    broker = CustodyBroker(env_sandbox_ref=named)
    assert broker.resolve_credentials("doppler://goldgraft/shops/other/secrets") == {}
    assert broker.resolve_credentials(named)["paypal_client_id"] == "operator-sandbox-id"
