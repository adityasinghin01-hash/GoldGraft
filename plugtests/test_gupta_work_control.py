"""Actual transactional GU03 component tests; no runtime/provider qualification."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from goldgraft_contracts.connection_control import (
    CheckResult,
    ConnectionReadiness,
    CreateActionIntent,
    CreateCase,
    StartWorkRequest,
    WorkerOperation,
)
from goldgraft_contracts.plan5_common import content_digest
from goldgraft_foundation.ledger import Ledger
from sqlalchemy import select

from pieces.backend.connection.service import CaseService, Principal, ServiceError
from pieces.backend.connection.work import WorkControl, work
from pieces.backend.service_api import create_service_app

NOW = datetime(2026, 11, 12, tzinfo=UTC)
D = "a" * 64


@pytest.fixture
def rig(tmp_path):
    clock = [NOW]
    ledger = Ledger(f"sqlite:///{tmp_path / 'work.sqlite'}")
    cases = CaseService(ledger, clock=lambda: clock[0])
    principal = Principal("owner", "tenant", NOW + timedelta(hours=1), "csrf")
    case = cases.create_case(principal, CreateCase(shop_url="https://shop.example"), "new")
    ready = ConnectionReadiness(
        readiness_id="ready",
        case_id=case.case_id,
        actor_id="owner",
        work_package_ref="blob:package",
        work_package_digest=D,
        resource_graph_digest=D,
        source_snapshot_refs=["blob:snapshot"],
        source_manifest_digest=D,
        resource_evidence_digests={"binding": D},
        binding_epochs={"binding": 1},
        scope_digest=D,
        processing_policy_digest=D,
        runtime_profile_digest=D,
        fixture_profile_digest=D,
        checks=[
            CheckResult(
                check_id="authority",
                status="pass",
                evidence_refs=["blob:check"],
                checked_at=NOW,
                expires_at=NOW + timedelta(minutes=10),
                recovery_code=None,
            )
        ],
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=10),
        readiness_digest=D,
    )
    current = [ready]
    control = WorkControl(
        cases,
        readiness_resolver=lambda *args: current[0],
        required_checks={"authority"},
        authenticate_operation=lambda p, v: v.authenticity_ref == "trusted:signature",
        authenticate_termination=lambda c, refs: refs == ["trusted:termination"],
    )
    return control, cases, principal, case.case_id, ready, current, clock


def intent(rig, key="intent"):
    control, _, principal, case_id, ready, *_ = rig
    action = control.create_intent(
        principal,
        case_id,
        CreateActionIntent(
            readiness_id=ready.readiness_id, readiness_digest=ready.readiness_digest
        ),
        key,
    )
    body = StartWorkRequest(
        action_id=action.action_id,
        readiness_id=ready.readiness_id,
        readiness_digest=ready.readiness_digest,
    )
    return action, body


def test_commit_lost_response_restart_and_cancel_keeps_immutable_receipt(rig):
    control, cases, owner, case_id, ready, *_ = rig
    action, body = intent(rig)
    receipt = control.start(owner, case_id, body, "start")
    restarted = WorkControl(
        CaseService(Ledger(str(cases.ledger.engine.url)), clock=cases.clock),
        readiness_resolver=lambda *args: ready,
        required_checks={"authority"},
    )
    assert restarted.start(owner, case_id, body, "start") == receipt
    assert restarted.status(owner, case_id, action.action_id).status.state == "queued"
    restarted.cancel(owner, case_id, action.action_id, "cancel")
    assert restarted.start(owner, case_id, body, "start") == receipt
    assert restarted.status(owner, case_id, action.action_id).status.state == "cancellation_pending"
    with pytest.raises(ServiceError, match="IDEMPOTENCY_CONFLICT"):
        restarted.start(owner, case_id, body, "another-key")


def test_crash_before_commit_rolls_back_receipt_and_outbox(rig, monkeypatch):
    control, cases, owner, case_id, *_ = rig
    _, body = intent(rig)
    original = control._append

    def fail_after_append(tx, record):
        original(tx, record)
        raise RuntimeError("crash")

    monkeypatch.setattr(control, "_append", fail_after_append)
    with pytest.raises(RuntimeError, match="crash"):
        control.start(owner, case_id, body, "start")
    with cases.ledger.engine.connect() as db:
        assert db.execute(select(work)).all() == []
    assert not [e for e in cases.ledger.read(case_id) if e.schema_ == "WorkAcceptance/1"]
    monkeypatch.setattr(control, "_append", original)
    assert control.start(owner, case_id, body, "start").work_id


def test_concurrent_starts_have_one_outbox_and_ledger_receipt(rig):
    control, cases, owner, case_id, *_ = rig
    _, body = intent(rig)
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda _: control.start(owner, case_id, body, "start"), range(12)))
    assert len({r.work_id for r in results}) == 1
    with cases.ledger.engine.connect() as db:
        assert len(db.execute(select(work)).all()) == 1
    assert len([e for e in cases.ledger.read(case_id) if e.schema_ == "WorkAcceptance/1"]) == 1


def test_different_actions_same_case_conflict(rig):
    control, _, owner, case_id, *_ = rig
    _, body = intent(rig)
    control.start(owner, case_id, body, "start")
    _, second = intent(rig, "other-intent")
    with pytest.raises(ServiceError, match="ACTIVE_WORK_CONFLICT"):
        control.start(owner, case_id, second, "second-start")


def test_stop_before_acceptance_survives_restart(rig):
    control, cases, owner, case_id, ready, *_ = rig
    action, body = intent(rig)
    cancel = control.cancel(owner, case_id, action.action_id, "cancel")
    assert cancel.work_id is None and cancel.generation is None and cancel.state == "confirmed"
    restarted = WorkControl(
        cases, readiness_resolver=lambda *args: ready, required_checks={"authority"}
    )
    with pytest.raises(ServiceError, match="ACTION_CANCELLED"):
        restarted.start(owner, case_id, body, "start")
    assert restarted.status(owner, case_id, action.action_id).status.state == "cancelled"


@pytest.mark.parametrize("change", ["expiry", "epoch", "policy", "missing", "unknown"])
def test_stale_readiness_never_accepts(rig, change):
    control, _, owner, case_id, ready, current, clock = rig
    _, body = intent(rig)
    values = ready.model_dump()
    if change == "expiry":
        clock[0] += timedelta(minutes=11)
    elif change == "epoch":
        values["binding_epochs"] = {"binding": 2}
    elif change == "policy":
        values["processing_policy_digest"] = "b" * 64
    elif change == "missing":
        values["checks"] = []
    else:
        values["checks"][0]["status"] = "unknown"
    current[0] = ConnectionReadiness.model_validate(values)
    with pytest.raises(ServiceError, match="READINESS_STALE"):
        control.start(owner, case_id, body, "start")


def claimed(rig):
    control, _, owner, case_id, ready, *_ = rig
    action, body = intent(rig)
    receipt = control.start(owner, case_id, body, "start")
    generation = control.claim(
        case_id, receipt.work_id, worker_id="supervisor", assignment_digest=D
    )
    operation = WorkerOperation(
        operation_id="baseline-read",
        work_id=receipt.work_id,
        generation=generation,
        worker_id="supervisor",
        kind="BASELINE_READ",
        assignment_digest=D,
        work_package_digest=D,
        resource_graph_digest=D,
        source_manifest_digest=D,
        scope_digest=D,
        observed_digest=D,
        runtime_profile_digest=D,
        started_at=NOW,
        finished_at=NOW,
        result="verified",
        evidence_refs=["blob:observation"],
        authenticity_ref="trusted:signature",
    )
    supervisor = Principal("supervisor", "tenant", NOW + timedelta(hours=1), "csrf", "service")
    return action, receipt, operation, supervisor


def test_claim_is_not_operation_and_only_authenticated_observation_advances(rig):
    control, cases, owner, case_id, *_ = rig
    action, receipt, operation, supervisor = claimed(rig)
    assert control.status(owner, case_id, action.action_id).status.state == "provisioning"
    forged = operation.model_copy(update={"authenticity_ref": "guest:claim"})
    with pytest.raises(ServiceError, match="UNAUTHENTICATED"):
        control.operation(supervisor, forged)
    first = control.operation(supervisor, operation)
    again = control.operation(supervisor, operation)
    assert first.operation_id == again.operation_id
    assert control.status(owner, case_id, action.action_id).status.state == "operation_started"
    assert len([e for e in cases.ledger.read(case_id) if e.schema_ == "WorkerOperation/1"]) == 1
    with pytest.raises(ServiceError, match="WORK_NOT_QUEUED"):
        control.claim(case_id, receipt.work_id, worker_id="duplicate", assignment_digest=D)


@pytest.mark.parametrize(
    "change", ["generation", "assignment", "scope", "worker", "expiry", "tenant"]
)
def test_stale_or_wrong_worker_rejected(rig, change):
    control, _, owner, case_id, ready, current, clock = rig
    action, _, operation, supervisor = claimed(rig)
    field = {
        "generation": "generation",
        "assignment": "assignment_digest",
        "scope": "scope_digest",
        "worker": "worker_id",
    }.get(change)
    if field:
        operation = operation.model_copy(update={field: 2 if field == "generation" else "b" * 64})
    elif change == "tenant":
        supervisor = Principal(
            "supervisor", "other-tenant", NOW + timedelta(hours=1), "csrf", "service"
        )
    else:
        clock[0] += timedelta(seconds=61)
    with pytest.raises(ServiceError):
        control.operation(supervisor, operation)
    assert control.status(owner, case_id, action.action_id).status.state == "provisioning"


def test_cancel_fences_old_worker_and_termination_needs_evidence(rig):
    control, _, owner, case_id, *_ = rig
    action, _, operation, supervisor = claimed(rig)
    cancel = control.cancel(owner, case_id, action.action_id, "cancel")
    assert cancel.state == "termination_pending" and cancel.generation == operation.generation + 1
    with pytest.raises(ServiceError, match="STALE_WORKER"):
        control.operation(supervisor, operation)
    with pytest.raises(ServiceError, match="TERMINATION_UNVERIFIED"):
        control.confirm_termination(case_id, action.action_id, ["guest:timeout"])
    assert control.status(owner, case_id, action.action_id).status.state == "cancellation_pending"
    confirmed = control.confirm_termination(case_id, action.action_id, ["trusted:termination"])
    assert confirmed.state == "confirmed"
    assert control.status(owner, case_id, action.action_id).status.state == "stopped"


def test_http_action_routes_use_real_control_and_cross_tenant_denies(rig):
    control, cases, owner, case_id, ready, *_ = rig
    app = create_service_app(
        cases,
        work_control=control,
        allowed_origins={"https://gg.example"},
        authenticate=lambda request: owner,
    )
    client = TestClient(app)
    assert {"start_work", "worker_operation"} <= app.state.implemented_service_routes
    headers = {"Origin": "https://gg.example", "X-CSRF-Token": "csrf", "Idempotency-Key": "intent"}
    base = f"/v2/connection-cases/{case_id}"
    response = client.post(
        base + "/action-intents",
        headers=headers,
        json={"readiness_id": ready.readiness_id, "readiness_digest": ready.readiness_digest},
    )
    assert response.status_code == 201, response.text
    action_id = response.json()["action_id"]
    started = client.post(
        base + "/actions",
        headers={**headers, "Idempotency-Key": "start"},
        json={
            "action_id": action_id,
            "readiness_id": ready.readiness_id,
            "readiness_digest": ready.readiness_digest,
        },
    )
    assert started.status_code == 202, started.text
    assert client.get(base + "/actions/" + action_id).json()["status"]["state"] == "queued"
    foreign = Principal("owner", "foreign", NOW + timedelta(hours=1), "csrf")
    with pytest.raises(ServiceError, match="CASE_UNAVAILABLE"):
        control.status(foreign, case_id, action_id)
    assert content_digest(started.json())


def test_start_stop_transaction_race_never_resurrects_work(rig):
    control, cases, owner, case_id, *_ = rig
    action, body = intent(rig)

    def start():
        try:
            return control.start(owner, case_id, body, "start")
        except ServiceError as exc:
            assert exc.code == "ACTION_CANCELLED"
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        started = pool.submit(start)
        stopped = pool.submit(control.cancel, owner, case_id, action.action_id, "cancel")
        receipt, cancellation = started.result(), stopped.result()
    if receipt is None:
        assert cancellation.work_id is None and cancellation.state == "confirmed"
        with pytest.raises(ServiceError, match="ACTION_CANCELLED"):
            control.start(owner, case_id, body, "start")
    else:
        assert cancellation.work_id == receipt.work_id
        assert control.start(owner, case_id, body, "start") == receipt
        assert (
            control.status(owner, case_id, action.action_id).status.state == "cancellation_pending"
        )
    events = cases.events(owner, case_id)
    assert [e.sequence for e in events] == list(range(1, len(events) + 1))
    assert events[-1].kind == "work_changed"
