import pytest

from pieces.agents.component_agents.librarian import sample
from pieces.agents.component_cli import create
from pieces.agents.scheduler import tick

from .test_runtime import NOW


@pytest.mark.parametrize("operation", ["learn", "selfcheck_recipe"])
def test_librarian_quarantine_and_independent_selfcheck(tmp_path, operation):
    p = create("Librarian", tmp_path / "l.sqlite", operation=operation, clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 1
    t = p.control.snapshot(p.run_ref).tasks[0]
    out = p.artifacts.inspect_outputs(t, p.context_for(t.task.task_id))
    if operation == "learn":
        assert out[0]["payload"]["status"] == "QUARANTINE"


@pytest.mark.parametrize(
    "field",
    [
        "learning_consent",
        "source_rights",
        "synthetic_certified_fixture",
        "completed",
        "deidentified",
        "tenant_id",
        "template_id",
        "independent_fixture_ref",
    ],
)
def test_librarian_no_cross_tenant_source_or_self_promotion(tmp_path, field):
    d = sample("selfcheck_recipe")
    if field == "tenant_id":
        d[field] = "other-tenant"
    elif field == "template_id":
        d[field] = "private merchant code"
    elif field == "independent_fixture_ref":
        d[field] = d["origin_fixture_ref"]
    else:
        d[field] = False
    p = create(
        "Librarian", tmp_path / "l.sqlite", operation="selfcheck_recipe", data=d, clock=lambda: NOW
    )
    assert tick(p.run_ref, NOW, p).completed == 0
    assert p.model.total_dispatches() == 0


@pytest.mark.parametrize("fault", ["active", "signature", "provenance"])
def test_librarian_cannot_promote_or_forge_source_rights(tmp_path, fault):
    p = create("Librarian", tmp_path / "l.sqlite", clock=lambda: NOW)
    original = p.model.renderer

    def bad(*args):
        v = original(*args)
        r = v["outputs"][0]["payload"]
        if fault == "active":
            r["status"] = "ACTIVE"
        elif fault == "signature":
            r["signature"] = "signed-by-model"
        else:
            r["provenance"] = ["private:other-tenant"]
        return v

    p.model.renderer = bad
    assert tick(p.run_ref, NOW, p).completed == 0


def test_librarian_accepts_consistent_model_label_in_quarantine(tmp_path):
    p = create("Librarian", tmp_path / "l.sqlite", clock=lambda: NOW)
    original, planner = p.model.renderer, p.model.planner

    def labelled(*args):
        v = original(*args)
        v["outputs"][1]["payload"]["producer"]["model"] = "qualified-model"
        return v

    def staged(*args):
        calls = planner(*args)
        for c in calls:
            if "drafts" in c:
                c["drafts"]["detection_rule_ref"]["producer"]["model"] = "qualified-model"
        return calls

    p.model.renderer, p.model.planner = labelled, staged
    assert tick(p.run_ref, NOW, p).completed == 1
