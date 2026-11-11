import pytest

from pieces.agents.component_agents.gardener import sample
from pieces.agents.component_cli import create
from pieces.agents.scheduler import tick

from .test_runtime import NOW


def test_gardener_proposes_but_does_not_dispatch_tasks(tmp_path):
    p = create("Gardener", tmp_path / "g.sqlite", clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 1
    assert len(p.control.snapshot(p.run_ref).tasks) == 1
    task = p.control.snapshot(p.run_ref).tasks[0]
    output = p.artifacts.inspect_outputs(task, p.context_for(task.task.task_id))[0]["payload"]
    assert output["tasks"][0]["role"] == "Surveyor"
    assert output["tasks"][0]["required"] is True


@pytest.mark.parametrize("key", ["accepted", "baseline_verified"])
def test_unverified_plan_holds_without_model(tmp_path, key):
    data = sample("propose_plan")
    data[key] = False
    p = create("Gardener", tmp_path / "bad.sqlite", data=data, clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 0
    assert p.model.total_dispatches() == 0


@pytest.mark.parametrize("change", ["deploy", "cycle", "optional", "future_ref", "future_subject"])
def test_plan_cannot_add_deploy_cycle_or_weaken_scope(tmp_path, change):
    p = create("Gardener", tmp_path / "bad.sqlite", clock=lambda: NOW)
    original = p.model.renderer

    def bad(*args):
        value = original(*args)
        node = value["tasks"][0]
        if change == "deploy":
            node["operation"] = "deploy"
        elif change == "cycle":
            node["dependencies"] = [node["task_id"]]
        elif change == "optional":
            node["required"] = False
        elif change == "future_ref":
            node["input_refs"] = ["invented:future-image"]
        else:
            node["expected_subject"] = "f" * 64
        return value

    p.model.renderer = bad
    assert tick(p.run_ref, NOW, p).completed == 0
    assert p.control.snapshot(p.run_ref).tasks[0].output_refs == []


def test_every_required_task_gets_its_own_surveyor_node(tmp_path):
    data = dict(sample("propose_plan"), required_task_ids=["survey-a", "survey-b", "survey-c"])
    p = create("Gardener", tmp_path / "multi.sqlite", data=data, clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 1
    task = p.control.snapshot(p.run_ref).tasks[0]
    plan = p.artifacts.inspect_outputs(task, p.context_for(task.task.task_id))[0]["payload"]
    assert sorted(t["task_id"] for t in plan["tasks"]) == ["survey-a", "survey-b", "survey-c"]
    assert len({t["output_slot"] for t in plan["tasks"]}) == 3


def test_plan_that_actual_admission_would_refuse_is_rejected(tmp_path):
    data = dict(sample("propose_plan"), required_task_ids=["survey-a", "survey-b"])
    p = create("Gardener", tmp_path / "slots.sqlite", data=data, clock=lambda: NOW)
    original = p.model.renderer

    def same_slot(*args):
        value = original(*args)
        for node in value["tasks"]:
            node["output_slot"] = "planned.inventory"
        return value

    p.model.renderer = same_slot
    assert tick(p.run_ref, NOW, p).completed == 0


def test_model_facts_expose_scoped_ids_without_the_plan(tmp_path):
    from pieces.agents.component_agents.gardener import facts

    p = create("Gardener", tmp_path / "f.sqlite", clock=lambda: NOW)
    task = p.control.snapshot(p.run_ref).tasks[0]
    from pieces.agents.component_agents.gardener import Input

    f = facts(task, Input.model_validate(sample("propose_plan")))
    assert f["parent_request_id"] == task.request_id and f["run_ref"] == "fake:runtime-run"
    assert "tasks" not in f


@pytest.mark.parametrize(
    ("count", "model"), [(1, "haiku"), (5, "haiku"), (6, "sonnet"), (9, "sonnet")]
)
def test_plan_size_routes_the_model_before_dispatch(count, model):
    from pieces.agents.component_agents.gardener import Input, route

    data = dict(sample("propose_plan"), required_task_ids=[f"s-{i}" for i in range(count)])
    assert route(Input.model_validate(data)) == model
