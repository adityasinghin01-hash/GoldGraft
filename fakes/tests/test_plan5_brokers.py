"""Persistent scripted ModelPort and guarded ToolPort: no actual inference/effects."""

import pytest
from goldgraft_contracts.plan5_common import content_digest
from goldgraft_contracts.registry import validate
from goldgraft_fakes._fixtures import example
from test_plan5_task_control import setup_control


def request(c, lease):
    value = example("ModelTurnRequest/1")
    value.update(
        turn_id="turn-1",
        task_id=lease.task_id,
        generation=lease.generation,
        lease_epoch=lease.lease_epoch,
        context_ref=lease.context_ref,
        context_digest=content_digest(c.context(lease.context_ref)),
        output_schema="RootMap/1",
        allowed_tool_ids=["source.read"],
        budget_reservation_ref="fake:zero-budget",
        model_profile_ref="fake:scripted",
        deadline=c.load(lease).deadline,
    )
    return validate("ModelTurnRequest/1", value)


def invocation(c, lease, *, tool="source.read", arguments=None):
    t = c.load(lease)
    args = arguments or {"snapshot_ref": "fake:source", "path": "shop.php", "max_bytes": 4096}
    ref = c.stage_untrusted(lease, args)
    value = example("ToolInvocation/1")
    value.update(
        invocation_id="invoke-1",
        task_id=t.task.task_id,
        tool_id=tool,
        case_id=t.case_id,
        run_id=t.run_id,
        generation=t.generation,
        lease_epoch=t.lease_epoch,
        arguments_ref=ref,
        arguments_digest=content_digest(args),
        input_digest=t.input_digest,
        state="intended",
        result_refs=[],
        budget_reservation_ref="fake:zero-budget",
        capability_ref="fake:capability:" + t.task.task_id,
        deadline=t.deadline,
    )
    return validate("ToolInvocation/1", value)


@pytest.mark.parametrize("kind", ["final", "tool_calls", "blocked"])
def test_scripted_model_forms_are_persistent_and_untrusted(tmp_path, kind):
    from goldgraft_fakes.model_broker import ScriptedModelBroker

    c, clock, db, proposal = setup_control(tmp_path)
    lease = c.claim("worker", clock[0])
    broker = ScriptedModelBroker(c)
    scripts = {
        "final": {"kind": "final", "payload": example("RootMap/1")},
        "tool_calls": {
            "kind": "tool_calls",
            "calls": [
                {
                    "tool": "source.read",
                    "arguments": {
                        "snapshot_ref": "fake:source",
                        "path": "shop.php",
                        "max_bytes": 10,
                    },
                }
            ],
        },
        "blocked": {"kind": "blocked", "issue": example("Issue/1")},
    }
    broker.script("turn-1", scripts[kind])
    req = request(c, lease)
    result = broker.turn(req)
    assert result.kind == kind and result.usage_receipt_ref.startswith("fake:")
    assert ScriptedModelBroker(c).turn(req) == result
    assert broker.dispatch_count("turn-1") == 1
    if kind == "final":
        raw = c.store.raw(result.final_artifact_ref, scope=lease.task_id)
        assert raw and c.artifact_count() == 0  # staging never earns observed trust
    with pytest.raises(ValueError, match="CONFLICT"):
        broker.turn(req.model_copy(update={"output_token_cap": 2}))


def test_unknown_model_and_tool_never_dispatch_new_identity(tmp_path):
    from goldgraft_fakes.guarded_tools import GuardedOfflineTools
    from goldgraft_fakes.model_broker import ScriptedModelBroker

    c, clock, db, proposal = setup_control(tmp_path)
    lease = c.claim("worker", clock[0])
    model = ScriptedModelBroker(c)
    model.script("turn-1", {"unknown": True})
    req = request(c, lease)
    with pytest.raises(ValueError, match="UNKNOWN"):
        model.turn(req)
    assert ScriptedModelBroker(c).reconcile("turn-1").state == "unknown"
    with pytest.raises(ValueError, match="UNKNOWN"):
        model.turn(req.model_copy(update={"turn_id": "fresh-turn"}))
    assert model.dispatch_count("turn-1") == 1
    tools = GuardedOfflineTools(c)
    inv = invocation(c, lease)
    c.begin_tool(lease, inv)
    tools.script("invoke-1", {"unknown": True})
    assert tools.invoke(inv).state == "unknown"
    assert GuardedOfflineTools(c).reconcile("invoke-1").state == "unknown"
    with pytest.raises(ValueError, match="UNKNOWN"):
        c.begin_tool(lease, inv.model_copy(update={"invocation_id": "fresh-invoke"}))
    assert tools.dispatch_count("invoke-1") == 1


def test_guarded_tool_rechecks_role_args_authority_and_intent(tmp_path):
    from goldgraft_fakes.guarded_tools import GuardedOfflineTools

    c, clock, db, proposal = setup_control(tmp_path)
    lease = c.claim("worker", clock[0])
    tools = GuardedOfflineTools(c)
    inv = invocation(c, lease)
    tools.script("invoke-1", {"payload": {"label": "SCRIPTED", "excerpt": "synthetic source"}})
    with pytest.raises(ValueError, match="MISSING_EVIDENCE"):
        tools.invoke(inv)
    c.begin_tool(lease, inv)
    c.set_authority("fixture:run", False)
    with pytest.raises(ValueError, match="DENIED"):
        tools.invoke(inv)
    assert tools.dispatch_count("invoke-1") == 0
    c.set_authority("fixture:run", True)
    result = tools.invoke(inv)
    assert result.state == "observed"
    assert c.observe_tool(lease, inv.invocation_id, result.result_refs[0]) == result
    assert tools.invoke(inv) == result and tools.dispatch_count("invoke-1") == 1
    raw = c.store.raw(result.result_refs[0], scope=lease.task_id)
    assert b"SCRIPTED" in raw


@pytest.mark.parametrize(
    "patch",
    [
        {"generation": 2},
        {"allowed_tool_ids": ["repo.write"]},
        {"budget_reservation_ref": "missing:reservation"},
        {"model_profile_ref": "real:claude"},
        {"output_token_cap": 4001},
    ],
)
def test_model_denies_unqualified_or_stale_profile_before_dispatch(tmp_path, patch):
    from goldgraft_fakes.model_broker import ScriptedModelBroker

    c, clock, db, proposal = setup_control(tmp_path)
    lease = c.claim("worker", clock[0])
    broker = ScriptedModelBroker(c)
    broker.script("turn-1", {"payload": {}, "kind": "final"})
    with pytest.raises(ValueError):
        broker.turn(request(c, lease).model_copy(update=patch))
    assert broker.dispatch_count("turn-1") == 0
