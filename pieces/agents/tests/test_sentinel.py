"""Sentinel is advisory; test actual runtime and mandatory code guards separately."""

import pytest

from pieces.agents.component_agents.sentinel import sample
from pieces.agents.component_cli import create
from pieces.agents.scheduler import tick

from .test_runtime import NOW, profile


def test_sentinel_audits_and_requests_hold_without_claiming_termination(tmp_path):
    p = create("Sentinel", tmp_path / "sentinel.sqlite", clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 1
    t = p.control.snapshot(p.run_ref).tasks[0]
    outputs = p.artifacts.inspect_outputs(t, p.context_for(t.task.task_id))
    alert = outputs[0]["payload"]
    assert alert["severity"] == "CRITICAL"
    assert alert["halted_agent"] is None
    assert "not confirmed" in alert["message"]
    assert p.tools.total_dispatches() == 2


@pytest.mark.parametrize("change", ["gap", "wrong_case", "wrong_generation"])
def test_missing_or_wrong_audit_evidence_holds_before_model(tmp_path, change):
    data = sample("audit")
    if change == "gap":
        data["events"][0]["sequence"] = 2
    elif change == "wrong_case":
        data["events"][0]["case_id"] = "other"
    else:
        data["events"][0]["generation"] = 2
    p = create("Sentinel", tmp_path / "bad.sqlite", data=data, clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 0
    assert p.model.total_dispatches() == p.tools.total_dispatches() == 0


def test_sentinel_absence_does_not_disable_guards(tmp_path):
    p = profile(tmp_path, scenario="prohibited_tool")
    assert tick("fake:runtime-run", NOW, p).completed == 0
    assert p.tools.total_dispatches() == 0


def test_model_cannot_claim_halt_success(tmp_path):
    p = create("Sentinel", tmp_path / "forge.sqlite", clock=lambda: NOW)
    original = p.model.renderer

    def bad(*args):
        value = original(*args)
        value["halted_agent"] = "unrelated-worker"
        return value

    p.model.renderer = bad
    assert tick(p.run_ref, NOW, p).completed == 0
    assert p.control.snapshot(p.run_ref).tasks[0].output_refs == []
