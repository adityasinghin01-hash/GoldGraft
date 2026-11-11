import pytest

from pieces.agents.component_agents.adversary import sample
from pieces.agents.component_cli import create
from pieces.agents.scheduler import tick

from .test_runtime import NOW


@pytest.mark.parametrize("operation", ["derive_guards", "run_mutant"])
def test_adversary_uses_guard_sets_and_disposable_fork(tmp_path, operation):
    p = create("Adversary", tmp_path / "a.sqlite", operation=operation, clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 1
    with p.control.store.transaction() as db:
        assert (
            db.execute("SELECT COUNT(*) FROM scripts WHERE namespace='candidate-tree'").fetchone()[
                0
            ]
            == 0
        )


@pytest.mark.parametrize("fault", ["fork", "disposable", "variant", "capture", "candidate"])
def test_adversary_cannot_mutate_candidate(tmp_path, fault):
    d = sample("run_mutant")
    if fault == "fork":
        d["fork_ref"] = d["candidate_ref"]
    elif fault == "disposable":
        d["disposable_fork"] = False
    elif fault == "variant":
        d["variant"] = "OLD"
    elif fault == "capture":
        d["execution_result"]["capture_complete"] = False
    else:
        d["execution_result"]["candidate_mutated"] = True
    p = create(
        "Adversary", tmp_path / "a.sqlite", operation="run_mutant", data=d, clock=lambda: NOW
    )
    assert tick(p.run_ref, NOW, p).completed == 0


@pytest.mark.parametrize("fault", ["guard", "kill", "equivalent"])
def test_adversary_cannot_drop_required_guard_or_self_certify(tmp_path, fault):
    p = create("Adversary", tmp_path / "a.sqlite", clock=lambda: NOW)
    original = p.model.renderer

    def bad(*args):
        v = original(*args)
        if fault == "guard":
            v["outputs"][0]["payload"]["scenarios"] = []
        elif fault == "kill":
            v["outputs"][1]["payload"]["mutants"][0]["killed_by"] = ["guard-captured-before-paid"]
        else:
            v["outputs"][1]["payload"]["mutants"][0]["equivalent_suspect"] = True
        return v

    p.model.renderer = bad
    assert tick(p.run_ref, NOW, p).completed == 0


def test_missing_catalog_guard_stays_explicit(tmp_path):
    d = sample("derive_guards")
    d["mutation_rule_ids"] = []
    p = create("Adversary", tmp_path / "a.sqlite", data=d, clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 1
    t = p.control.snapshot(p.run_ref).tasks[0]
    out = p.artifacts.inspect_outputs(t, p.context_for(t.task.task_id))
    assert out[0]["payload"]["unguarded_rule_ids"] == ["captured-before-paid"]
