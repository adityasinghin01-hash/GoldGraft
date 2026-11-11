"""Faults assert durable rows, counts, scope and races; no agent loop is under test."""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from goldgraft_contracts.registry import validate
from goldgraft_fakes._fixtures import example
from test_plan5_brokers import invocation, request
from test_plan5_task_control import finish_inventory, setup_control


def test_concurrent_claimers_have_one_current_lease(tmp_path):
    from goldgraft_fakes.task_control import OfflineTaskControl

    c, clock, db, proposal = setup_control(tmp_path)

    def claim(i):
        return OfflineTaskControl(db, clock=lambda: clock[0]).claim(f"worker-{i}", clock[0])

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(claim, range(2)))
    assert sum(r is not None for r in results) == 1


@pytest.mark.parametrize(
    "boundary,count", [("model_intent_committed", 0), ("model_dispatch_committed", 1)]
)
def test_hard_process_crash_model_identity_and_reservation(tmp_path, boundary, count):
    from goldgraft_fakes.model_broker import ScriptedModelBroker

    c, clock, db, proposal = setup_control(tmp_path)
    lease = c.claim("worker", clock[0])
    req = request(c, lease)
    model = ScriptedModelBroker(c)
    model.script("turn-1", {"kind": "final", "payload": example("RootMap/1")})
    code = """
import json, os, sys
from datetime import datetime
from goldgraft_contracts.registry import validate
from goldgraft_fakes.task_control import OfflineTaskControl
from goldgraft_fakes.model_broker import ScriptedModelBroker
c=OfflineTaskControl(sys.argv[1],clock=lambda:datetime.fromisoformat(sys.argv[2]))
def crash(point):
    if point==sys.argv[3]: os._exit(77)
ScriptedModelBroker(c,fault=crash).turn(validate('ModelTurnRequest/1',json.loads(sys.argv[4])))
"""
    done = subprocess.run(
        [sys.executable, "-c", code, str(db), clock[0].isoformat(), boundary, req.model_dump_json()]
    )
    assert done.returncode == 77 and model.dispatch_count("turn-1") == count
    state = model.reconcile("turn-1")
    assert state.state == ("intended" if count == 0 else "submitted")
    if count:
        assert state.usage_receipt_ref.startswith("fake:reserved-zero")
        with pytest.raises(ValueError, match="UNKNOWN"):
            model.turn(req)
        assert model.dispatch_count("turn-1") == 1
    else:
        assert model.turn(req).kind == "final" and model.dispatch_count("turn-1") == 1


def test_unknown_tool_blocks_false_task_success(tmp_path):
    from goldgraft_fakes.guarded_tools import GuardedOfflineTools

    c, clock, db, proposal = setup_control(tmp_path)
    lease = c.claim("worker", clock[0])
    inv = invocation(c, lease)
    c.begin_tool(lease, inv)
    tool = GuardedOfflineTools(c)
    tool.script(inv.invocation_id, {"unknown": True})
    assert tool.invoke(inv).state == "unknown"
    with pytest.raises(ValueError, match="UNKNOWN"):
        finish_inventory(c, lease)
    assert c.accepted_result_count() == 0


def test_wrong_result_owner_subject_and_private_blob_scope_denied(tmp_path):
    c, clock, db, proposal = setup_control(tmp_path)
    lease = c.claim("worker", clock[0])
    t = c.load(lease)
    source = example("RootMap/1")
    ref = c.artifacts.fixture_output(lease, "RootMap/1", source)
    with c.store.transaction() as connection:
        row = connection.execute("SELECT descriptor FROM artifacts WHERE ref=?", (ref,)).fetchone()
        descriptor = json.loads(row["descriptor"])
        descriptor["subject_digest"] = "f" * 64
        connection.execute(
            "UPDATE artifacts SET descriptor=? WHERE ref=?", (json.dumps(descriptor), ref)
        )
    result = example("AgentResult/1")
    result.update(
        task_id="survey",
        request_id=t.request_id,
        input_digest=t.input_digest,
        output_refs=[ref],
        authenticity_ref="fake:result",
    )
    with pytest.raises(ValueError):
        c.finish(lease, validate("AgentResult/1", result))
    blob = c.stage_untrusted(lease, {"only": "this-task"})
    with pytest.raises(ValueError, match="DENIED"):
        c.store.raw(blob, scope="other-task")


def test_tool_output_bounds_and_sensitive_values_denied(tmp_path):
    from goldgraft_fakes.guarded_tools import GuardedOfflineTools

    c, clock, db, proposal = setup_control(tmp_path)
    lease = c.claim("worker", clock[0])
    inv = invocation(
        c, lease, arguments={"snapshot_ref": "fake:source", "path": "shop.php", "max_bytes": 4}
    )
    c.begin_tool(lease, inv)
    tools = GuardedOfflineTools(c)
    tools.script(inv.invocation_id, {"payload": {"excerpt": "more than four bytes"}})
    with pytest.raises(ValueError):
        tools.invoke(inv)
    assert tools.dispatch_count(inv.invocation_id) == 1


def test_extend_cas_and_missing_or_changed_dependency_denied(tmp_path):
    c, clock, db, proposal = setup_control(tmp_path)
    extra = proposal.model_copy(deep=True)
    extra.tasks = [
        extra.tasks[1].model_copy(update={"task_id": "herald-two", "output_slot": "text-two"})
    ]
    old = c.snapshot("fixture:run")
    with pytest.raises(ValueError, match="STALE"):
        c.extend("fixture:run", old.state_version - 1, extra, "extend-1")
    assert len(c.extend("fixture:run", old.state_version, extra, "extend-1")) == 1
    assert len(c.snapshot("fixture:run").tasks) == 3


def test_renew_preserves_fence_and_expired_wait_holds(tmp_path):
    from goldgraft_contracts.agent_runtime import TaskControl

    c, clock, db, proposal = setup_control(tmp_path)
    assert isinstance(c, TaskControl)
    lease = c.claim("worker", clock[0])
    clock[0] += timedelta(seconds=30)
    renewed = c.renew(lease, clock[0])
    assert renewed.lease_epoch == lease.lease_epoch and renewed.lease_until > lease.lease_until
    wake = example("WakeCondition/1")
    wake.update(due_at=clock[0], expires_at=clock[0] + timedelta(seconds=2))
    c.wait(renewed, validate("Issue/1", example("Issue/1")), validate("WakeCondition/1", wake))
    clock[0] += timedelta(seconds=3)
    assert not c.wake("fixture:run", wake["subject_ref"], digest=None, version=99)
    assert c.snapshot("fixture:run").tasks[0].state == "held"


@pytest.mark.parametrize("bad", ["../outside", "http://169.254.169.254/", "/etc/passwd"])
def test_tool_path_escapes_deny_before_dispatch(tmp_path, bad):
    from goldgraft_fakes.guarded_tools import GuardedOfflineTools

    c, clock, db, proposal = setup_control(tmp_path)
    lease = c.claim("worker", clock[0])
    inv = invocation(
        c, lease, arguments={"snapshot_ref": "fake:source", "path": bad, "max_bytes": 64}
    )
    c.begin_tool(lease, inv)
    tools = GuardedOfflineTools(c)
    with pytest.raises(ValueError):
        tools.invoke(inv)
    assert tools.dispatch_count(inv.invocation_id) == 0


def test_secret_like_tool_payload_is_never_committed_as_result(tmp_path):
    from goldgraft_fakes.guarded_tools import GuardedOfflineTools

    c, clock, db, proposal = setup_control(tmp_path)
    lease = c.claim("worker", clock[0])
    inv = invocation(c, lease)
    c.begin_tool(lease, inv)
    tools = GuardedOfflineTools(c)
    tools.script(inv.invocation_id, {"payload": {"excerpt": "Bearer SYNTHETIC_PRIVATE_CANARY"}})
    with pytest.raises(ValueError):
        tools.invoke(inv)
    assert tools.reconcile(inv.invocation_id).state == "submitted"
    assert not tools.reconcile(inv.invocation_id).result_refs


def test_tool_dispatch_crash_reconciles_original_after_reclaim(tmp_path):
    from goldgraft_fakes.guarded_tools import GuardedOfflineTools

    c, clock, db, proposal = setup_control(tmp_path)
    lease = c.claim("worker", clock[0])
    inv = invocation(c, lease)
    c.begin_tool(lease, inv)

    class Crash(Exception):
        pass

    def crash(boundary):
        raise Crash(boundary)

    with pytest.raises(Crash):
        GuardedOfflineTools(c, fault=crash).invoke(inv)
    clock[0] += timedelta(seconds=61)
    new_lease = c.claim("new-worker", clock[0])
    tools = GuardedOfflineTools(c)
    assert tools.reconcile(inv.invocation_id).state == "submitted"
    with pytest.raises(ValueError):
        tools.invoke(inv)
    new = invocation(c, new_lease).model_copy(update={"invocation_id": "new-id"})
    with pytest.raises(ValueError, match="UNKNOWN"):
        c.begin_tool(new_lease, new)
    assert tools.dispatch_count(inv.invocation_id) == 1
