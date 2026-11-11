"""Actual common guard behaviour for every registered component role, not dict parity."""

import json

import pytest
from goldgraft_contracts.plan5_common import content_digest
from goldgraft_fakes.offline_store import encoded

from pieces.agents.component import inspect_outputs
from pieces.agents.component_agents import IMPLEMENTED_ROLES
from pieces.agents.component_cli import create
from pieces.agents.scheduler import tick

from .test_runtime import NOW


@pytest.fixture(params=IMPLEMENTED_ROLES)
def profile(request, tmp_path):
    return create(request.param, tmp_path / "component.sqlite", clock=lambda: NOW)


def test_positive_output_is_consumed_by_role_inspection(profile):
    p = profile
    assert tick(p.run_ref, NOW, p).completed == 1
    task = p.control.snapshot(p.run_ref).tasks[0]
    outputs = p.artifacts.inspect_outputs(task, p.context_for(task.task.task_id))
    view = inspect_outputs(task.task.role, outputs)
    assert view["role"] == task.task.role and view["evidence_class"] == "scripted"
    assert view["outputs"]
    assert task.output_refs and p.model.total_dispatches() >= 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("case_id", "other-case"),
        ("run_id", "other-run"),
        ("generation", 2),
        ("subject_digest", "e" * 64),
    ],
)
def test_wrong_input_scope_never_calls_model(profile, field, value):
    p = profile
    task = p.control.snapshot(p.run_ref).tasks[0]
    with p.control.store.transaction() as db:
        row = db.execute(
            "SELECT descriptor FROM artifacts WHERE ref=?", (task.task.input_refs[0],)
        ).fetchone()
        d = json.loads(row[0])
        d[field] = value
        db.execute(
            "UPDATE artifacts SET descriptor=? WHERE ref=?", (encoded(d), task.task.input_refs[0])
        )
    assert tick(p.run_ref, NOW, p).completed == 0
    assert p.model.total_dispatches() == p.tools.total_dispatches() == 0


def test_missing_input_holds_without_dispatch(profile):
    p = profile
    with p.control.store.transaction() as db:
        db.execute("DELETE FROM artifacts")
    assert tick(p.run_ref, NOW, p).completed == 0
    assert p.model.total_dispatches() == 0


def test_prohibited_tool_cannot_reach_broker(profile):
    p = profile
    task = p.control.snapshot(p.run_ref).tasks[0]
    turn = "turn:" + content_digest(
        {"run": task.run_id, "generation": 1, "task": task.task.task_id, "attempt": 1, "turn": 0}
    )
    p.model.script(
        turn,
        {
            "kind": "tool_calls",
            "calls": [{"tool": "host.shell", "arguments": {"command": "unsafe"}}],
        },
    )
    assert tick(p.run_ref, NOW, p).completed == 0
    assert p.tools.total_dispatches() == 0


def test_wrong_output_owner_is_not_accepted(profile):
    p = profile
    original = p.artifacts.stage_outputs

    def wrong(*args):
        refs = original(*args)
        with p.control.store.transaction() as db:
            row = db.execute("SELECT descriptor FROM artifacts WHERE ref=?", (refs[0],)).fetchone()
            d = json.loads(row[0])
            d["producer_identity_ref"] = "fake:role:Unrelated"
            db.execute("UPDATE artifacts SET descriptor=? WHERE ref=?", (encoded(d), refs[0]))
        return refs

    p.artifacts.stage_outputs = wrong
    assert tick(p.run_ref, NOW, p).completed == 0
    assert p.control.snapshot(p.run_ref).tasks[0].output_refs == []


def test_wrong_schema_never_becomes_an_output(profile):
    p = profile
    p.model.renderer = lambda *args: {"unrelated": True}
    assert tick(p.run_ref, NOW, p).completed == 0
    assert p.control.snapshot(p.run_ref).tasks[0].output_refs == []


def test_unknown_model_holds_original_turn(profile):
    p = profile
    task = p.control.snapshot(p.run_ref).tasks[0]
    turn = "turn:" + content_digest(
        {"run": task.run_id, "generation": 1, "task": task.task.task_id, "attempt": 1, "turn": 0}
    )
    p.model.script(turn, {"unknown": True})
    assert tick(p.run_ref, NOW, p).completed == 0
    assert tick(p.run_ref, NOW, p).claimed == 0
    assert p.model.total_dispatches() == 1


def test_wrong_prompt_is_rejected_before_dispatch(profile):
    p = profile
    with p.control.store.transaction() as db:
        task = p.control._snapshot(db, p.run_ref).tasks[0]
        p.control._save_task(db, task.model_copy(update={"prompt_digest": "f" * 64}))
    assert tick(p.run_ref, NOW, p).completed == 0
    assert p.model.total_dispatches() == 0
