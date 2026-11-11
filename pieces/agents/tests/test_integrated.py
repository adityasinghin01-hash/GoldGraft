"""Offline checks for the integrated thirteen-role run policy (no model, no network)."""

import pytest
from goldgraft_contracts.plan5_common import content_digest

from pieces.agents import integrated
from pieces.agents.scheduler import tick

SURVEY = {
    "accepted": True,
    "output_ref": "fake:root-map:legacy-php-shop",
    "source_digest": content_digest("legacy-php-shop-source"),
}


def _run(path, run):
    p = integrated.create(path)
    w = integrated.WithRun(p, run)
    for _ in range(4):
        if tick(p.run_ref, p.clock(), w).claimed == 0:
            break
    return p, {t.task.task_id: t for t in p.control.snapshot(p.run_ref).tasks}


def test_gardener_admits_only_the_survey_and_the_chain_waits_for_it(tmp_path):
    p, tasks = _run(tmp_path / "b.sqlite", {})
    assert list(tasks) == [integrated.GARDENER]
    assert tasks[integrated.GARDENER].state == "succeeded"
    assert integrated.admitted_survey(p)["node"]["task_id"] == integrated.SURVEY
    assert integrated.advance(p.run_ref, integrated.WithRun(p, {})) is None  # no survey yet


def test_rejected_survey_never_admits_the_baseline(tmp_path):
    _, tasks = _run(tmp_path / "b.sqlite", {"survey": dict(SURVEY, accepted=False)})
    assert integrated.BASE not in tasks


def test_full_chain_and_side_branches_complete_offline(tmp_path):
    run = {"survey": SURVEY, "learning_consent": True, "source_rights": True}
    p, tasks = _run(tmp_path / "b.sqlite", run)
    assert [s[0] for s in integrated.ALL_STAGES if tasks[s[0]].state != "succeeded"] == []
    roles = {t.task.role for t in tasks.values()} | {"Surveyor", "Herald"}
    assert roles == set(integrated.ROLES) and len(roles) == 13


def test_baseline_builds_exactly_the_surveyed_source(tmp_path):
    p, tasks = _run(tmp_path / "b.sqlite", {"survey": SURVEY})
    data = (
        p.artifacts.role_inputs_for(integrated.BASE)
        if hasattr(p.artifacts, "role_inputs_for")
        else None
    )
    edges = {e["task"]: e for e in integrated.edges(p)}
    assert edges[integrated.BASE]["dependencies"] == [integrated.GARDENER]
    assert tasks["baseline-old"].state == "succeeded"
    # every chain task consumed at least one committed predecessor output
    for task_id, *_ in integrated.ALL_STAGES[1:]:
        assert edges[task_id]["predecessor_outputs_consumed"], task_id
    assert data is None or data["source_tree_digest"] == SURVEY["source_digest"]


def test_sentinel_events_are_scoped_to_this_run(tmp_path):
    run = {"survey": SURVEY, "hostile_fingerprint_seed": "x"}
    p, tasks = _run(tmp_path / "b.sqlite", run)
    data = integrated.stage_data(p, "sentinel-audit", "Sentinel", "audit", run)
    head = tasks[integrated.GARDENER]
    assert {(e["case_id"], e["run_id"]) for e in data["events"]} == {(head.case_id, head.run_id)}
    assert data["events"][-1]["kind"] == "secret_attempt"


@pytest.mark.parametrize(
    "codes,expected",
    [
        ([], "haiku8"),
        (["INVALID_MODEL_OUTPUT"], "haiku8"),
        (["INVALID_MODEL_OUTPUT", "TURN_LIMIT"], "sonnet"),
        (["MISSING_EVIDENCE", "DENIED", "BUDGET_EXHAUSTED"], "haiku8"),  # never escalates
    ],
)
def test_two_named_haiku_failures_move_a_shape_to_sonnet(codes, expected):
    routing = {}
    for code in codes:
        integrated.record_failure(routing, "Explorer", "run_scenario", "haiku8", code)
    data = integrated.implementation("Explorer").sample("run_scenario")
    profile, escalated = integrated.route("Explorer", "run_scenario", data, routing)
    assert profile == expected and escalated == (expected == "sonnet")


def test_qualified_sonnet_routes_stay_sonnet():
    data = integrated.implementation("Architect").sample("architect")
    assert integrated.route("Architect", "architect", data, {}) == ("sonnet", False)


@pytest.mark.parametrize(
    "line,held",
    [
        ('$a["NAME$i"] = 1;', False),  # plain variable read: data
        ('$a = "Total $amount for $name";', False),
        ('$a = "x {$obj->call()}";', True),  # complex interpolation keeps the hold
        ('$a = "x ${name}";', True),
        ('$a = "x $obj->prop";', True),
        ('$a = "x $arr[0]";', True),
    ],
)
def test_only_plain_variable_interpolation_counts_as_data(line, held):
    from pieces.agents.source_references import discover_component_gaps

    gaps = discover_component_gaps({"a.php": "<?php\n" + line + "\n"})
    assert bool(gaps) == held


def test_sample_shop_package_is_complete_for_scope():
    from pathlib import Path

    from pieces.agents.source_references import discover_component_gaps

    root = Path(__file__).resolve().parents[3] / "fixtures/shops/legacy-php-shop/src"
    files = {str(p.relative_to(root)): p.read_text() for p in sorted(root.rglob("*.php"))}
    assert discover_component_gaps(files) == []
