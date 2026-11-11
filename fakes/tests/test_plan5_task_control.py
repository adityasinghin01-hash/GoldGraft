"""Actual persistent fake transactions, not agents or GU production qualification."""

import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta

import pytest
from goldgraft_contracts.registry import validate
from goldgraft_fakes._fixtures import example

NOW = datetime(2026, 11, 10, 12, tzinfo=UTC)


def setup_control(tmp_path):
    from goldgraft_fakes.task_control import OfflineTaskControl

    clock = [NOW]
    db = tmp_path / "control.sqlite"
    control = OfflineTaskControl(db, clock=lambda: clock[0])
    proposal = example("PlanProposal/1")
    first = proposal["tasks"][0]
    first["task_id"] = "survey"
    first["output_slot"] = "inventory"
    second = dict(
        first,
        task_id="herald",
        role="Herald",
        operation="explain_status",
        dependencies=["survey"],
        expected_schemas=["HeraldText/1"],
        allowed_tool_ids=["status.read"],
        output_slot="text",
    )
    proposal["tasks"] = [first, second]
    proposal = validate("PlanProposal/1", proposal)
    control.seed("fixture:run", proposal, "seed-1")
    return control, clock, db, proposal


def finish_inventory(control, lease):
    task = control.load(lease)
    payload = example("RootMap/1")
    ref = control.artifacts.fixture_output(lease, "RootMap/1", payload)
    result = example("AgentResult/1")
    result.update(
        task_id=task.task.task_id,
        request_id=task.request_id,
        case_id=task.case_id,
        run_id=task.run_id,
        generation=lease.generation,
        lease_epoch=lease.lease_epoch,
        input_digest=task.input_digest,
        output_refs=[ref],
        authenticity_ref="fake:result",
    )
    return control.finish(lease, validate("AgentResult/1", result))


def test_control_restart_and_finish_atomicity(tmp_path):
    c, clock, db, proposal = setup_control(tmp_path)
    lease = c.claim("worker-1", clock[0])
    done = finish_inventory(c, lease)
    assert done.state == "succeeded"
    # A fresh Python process observes the committed next task before outbox acknowledgement.
    code = (
        "import json; from pathlib import Path; "
        "from goldgraft_fakes.task_control import OfflineTaskControl; "
        'c=OfflineTaskControl(Path(__import__("sys").argv[1])); '
        'print(c.snapshot("fixture:run").model_dump_json())'
    )
    snapshot = validate(
        "RunTaskSnapshot/1",
        json.loads(subprocess.check_output([sys.executable, "-c", code, str(db)])),
    )
    assert [(t.task.task_id, t.state) for t in snapshot.tasks] == [
        ("survey", "succeeded"),
        ("herald", "ready"),
    ]
    assert c.accepted_result_count() == 1
    events = c.outbox("fixture:run")
    assert events and c.outbox("fixture:run") == events
    c.ack_event(events[0].event_id)
    assert events[0] not in c.outbox("fixture:run")
    assert c.finish(lease, c.result("survey")).task.task_id == "survey"
    assert c.accepted_result_count() == 1


def test_duplicate_key_and_stale_lease(tmp_path):
    c, clock, db, proposal = setup_control(tmp_path)
    assert len(c.seed("fixture:run", proposal, "seed-1")) == 2
    changed = proposal.model_copy(deep=True)
    changed.tasks[0].output_slot = "different"
    with pytest.raises(ValueError, match="CONFLICT"):
        c.seed("fixture:run", changed, "seed-1")
    first = c.claim("worker-1", clock[0])
    clock[0] += timedelta(seconds=61)
    second = c.claim("worker-2", clock[0])
    assert second.lease_epoch == first.lease_epoch + 1
    with pytest.raises(ValueError, match="STALE"):
        c.load(first)
    assert c.load(second).task.task_id == "survey"
    c.set_authority("fixture:run", False)
    with pytest.raises(ValueError, match="DENIED"):
        c.load(second)


def test_wait_checkpoint_and_exact_wake_survive_restart(tmp_path):
    from goldgraft_fakes.task_control import OfflineTaskControl

    c, clock, db, proposal = setup_control(tmp_path)
    lease = c.claim("worker", clock[0])
    checkpoint = example("TaskCheckpoint/1")
    checkpoint.update(
        task_id="survey",
        generation=1,
        lease_epoch=lease.lease_epoch,
        policy_digest=c.load(lease).policy_digest,
    )
    ref = c.checkpoint(lease, validate("TaskCheckpoint/1", checkpoint))
    wake = example("WakeCondition/1")
    wake.update(
        kind="approval",
        due_at=None,
        expected_digest="a" * 64,
        subject_ref="fixture:exact-plan",
        minimum_version=3,
    )
    wake = validate("WakeCondition/1", wake)
    c.wait(lease, validate("Issue/1", example("Issue/1")), wake)
    fresh = OfflineTaskControl(db, clock=lambda: clock[0])
    assert fresh.snapshot("fixture:run").tasks[0].checkpoint_ref == ref
    assert not fresh.wake("fixture:run", wake.subject_ref, digest="b" * 64, version=3)
    assert not fresh.wake("fixture:run", wake.subject_ref, digest="a" * 64, version=2)
    assert fresh.wake("fixture:run", wake.subject_ref, digest="a" * 64, version=3)
    assert fresh.claim("worker-2", clock[0]).task_id == "survey"


def test_cancel_cannot_be_false_termination_or_output(tmp_path):
    c, clock, db, proposal = setup_control(tmp_path)
    lease = c.claim("worker", clock[0])
    c.cancel("fixture:run", "fake:cancel")
    event_count = len(c.outbox("fixture:run"))
    c.cancel("fixture:run", "fake:cancel")
    assert len(c.outbox("fixture:run")) == event_count
    assert c.snapshot("fixture:run").cancellation_ref == "fake:cancel"
    assert c.claim("another", clock[0]) is None
    with pytest.raises(ValueError):
        finish_inventory(c, lease)
    assert c.accepted_result_count() == 0
