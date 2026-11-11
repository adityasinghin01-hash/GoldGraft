"""Actual bounded runtime against injected persistent offline counterparts."""

from datetime import UTC, datetime

import pytest

NOW = datetime(2026, 11, 10, 12, tzinfo=UTC)


def profile(tmp_path, *, scenario="two_task_read"):
    from goldgraft_fakes.plan5_profile import create_profile

    return create_profile(tmp_path / "runtime.sqlite", scenario=scenario, clock=lambda: NOW)


def test_one_run_advances_two_scripted_tasks(tmp_path):
    from pieces.agents.scheduler import tick

    ports = profile(tmp_path)
    report = tick("fake:runtime-run", NOW, ports)
    assert report.completed == 2
    snapshot = ports.control.snapshot("fake:runtime-run")
    assert [t.state for t in snapshot.tasks] == ["succeeded", "succeeded"]
    assert ports.control.accepted_result_count() == 2
    assert all(
        ports.artifacts.resolve(r, ports.context_for(t.task.task_id)).evidence_class == "scripted"
        for t in snapshot.tasks
        for r in t.output_refs
    )


def test_missing_baseline_operation_denies_before_model(tmp_path):
    from pieces.agents.scheduler import tick

    ports = profile(tmp_path, scenario="missing_operation")
    report = tick("fake:runtime-run", NOW, ports)
    assert report.completed == 0
    assert ports.model.total_dispatches() == 0
    assert ports.control.snapshot("fake:runtime-run").tasks[0].state == "held"


@pytest.mark.parametrize(
    "scenario,reason",
    [
        ("invalid_output", "INVALID_MODEL_OUTPUT"),
        ("prohibited_tool", "DENIED"),
        ("model_unknown", "UNKNOWN"),
        ("tool_unknown", "UNKNOWN"),
        ("missing_input", "MISSING_EVIDENCE"),
        ("zero_budget_missing", "BUDGET_EXHAUSTED"),
    ],
)
def test_required_missing_or_unsafe_work_holds(tmp_path, scenario, reason):
    from pieces.agents.scheduler import tick

    ports = profile(tmp_path, scenario=scenario)
    report = tick("fake:runtime-run", NOW, ports)
    first = ports.control.snapshot("fake:runtime-run").tasks[0]
    assert report.completed == 0
    assert first.state in {"held", "unknown"}
    assert first.issue.code == reason
    if scenario == "invalid_output":
        assert ports.model.total_dispatches() == 2
    if scenario == "prohibited_tool":
        assert ports.tools.total_dispatches() == 0


def test_stop_fences_new_tasks(tmp_path):
    from pieces.agents.scheduler import tick

    ports = profile(tmp_path)
    ports.control.cancel("fake:runtime-run", "fake:cancel")
    assert tick("fake:runtime-run", NOW, ports).completed == 0
    assert ports.model.total_dispatches() == 0
