"""Comprehensive tests for Connection (GU01/GU02) and Providers/Build (GU04/GU05)."""

import pytest
from goldgraft_foundation.ledger import Ledger

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
from pieces.backend.lifecycle import (
    EffectManager,
    EffectStatus,
    LedgerReconciler,
    ReservationConflictError,
    StatePlanner,
    TargetReservationManager,
)
from pieces.runner.artifact_build import ArtifactBuilder
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
    gh = adapter.observe_github_repo("https://github.com/merchant/shop")
    assert gh.verified is True
    assert gh.read_only is True
    assert gh.provider == "github"

    render_obs = adapter.observe_render_service("srv-web-123")
    assert render_obs.verified is True
    assert render_obs.provider == "render"

    workos_obs = adapter.observe_workos_user("user-1", "org-retail")
    assert workos_obs.verified is True
    assert workos_obs.provider == "workos"

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
    plan = planner.create_cutover_plan("graft-1", "NVP", "OrdersV2", ["ORDER-1", "ORDER-2"])
    assert plan.preserved_order_count == 2
    assert plan.approved is True

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
    assert artifact.reproducible is True
    assert artifact.image_tag == "goldgraft-shop:v1.0.0"

    gh_pub = GitHubPublisher()
    pr = gh_pub.publish_pull_request(
        "https://github.com/org/repo",
        "feat/upgrade",
        title="Upgrade to Orders v2",
        commit_sha="abcd1234ef",
    )
    assert pr.pr_id.startswith("pr-")
    assert pr.commit_sha == "abcd1234ef"

    render = RenderDeployer()
    dep = render.deploy_service("srv-test", "goldgraft-shop:v1.0.0")
    assert dep.status == "LIVE"
    assert dep.health_url == "https://srv-test.onrender.com/health"

    pub = ArtifactPublisher()
    pub_rcpt = pub.publish_artifact(
        artifact.artifact_id, "registry.local/image", b"docker_image_bytes"
    )
    assert pub_rcpt.publish_id.startswith("pub-")


def test_upload_limits_retry_and_interrupted_assembly():
    import hashlib

    upload = UploadSessionManager(max_size_bytes=5)
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
    upload.add_chunk(sid, 1, b"de")
    assert upload.finalize_session(sid) == b"abcde"
    assert upload.finalize_session(sid) == b"abcde"
    with pytest.raises(ValueError, match="not active"):
        upload.add_chunk(sid, 0, b"abc")
