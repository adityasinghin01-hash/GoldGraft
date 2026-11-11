import pytest

from pieces.agents.component_agents.scribe import sample
from pieces.agents.component_cli import create
from pieces.agents.scheduler import tick

from .test_runtime import NOW


@pytest.mark.parametrize("operation", ["scribe_draft", "scribe_final"])
def test_scribe_draft_followup_and_final_preserve_old_defect_rule(tmp_path, operation):
    p = create("Scribe", tmp_path / "s.sqlite", operation=operation, clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 1
    t = p.control.snapshot(p.run_ref).tasks[0]
    out = p.artifacts.inspect_outputs(t, p.context_for(t.task.task_id))
    assert out[0]["payload"]["rules"][0]["agreement"] == (
        "CODE_ONLY" if operation == "scribe_draft" else "BOTH"
    )
    assert len(out) == (2 if operation == "scribe_draft" else 1)


@pytest.mark.parametrize("fault", ["predicate", "severity", "flow", "agreement", "kill"])
def test_scribe_cannot_relax_normative_rule(tmp_path, fault):
    p = create("Scribe", tmp_path / "s.sqlite", clock=lambda: NOW)
    original = p.model.renderer

    def bad(*args):
        v = original(*args)
        r = v["outputs"][0]["payload"]["rules"][0]
        if fault == "predicate":
            r["predicate"] = "always true"
        elif fault == "severity":
            r["severity"] = "MINOR"
        elif fault == "flow":
            r["correct_flow"] = []
        elif fault == "agreement":
            r["agreement"] = "BOTH"
        else:
            r["triangle"]["killed"] = True
        return v

    p.model.renderer = bad
    assert tick(p.run_ref, NOW, p).completed == 0


@pytest.mark.parametrize("fault", ["missing", "wrong_mapper", "wrong_variant", "exhausted"])
def test_scribe_missing_or_untrusted_trace_cannot_be_final(tmp_path, fault):
    d = sample("scribe_final")
    if fault == "missing":
        d["trace_rules"] = {}
    elif fault == "wrong_mapper":
        d["evidence"]["fixture:mapped-old"]["mapper"] = "model"
    elif fault == "wrong_variant":
        d["evidence"]["fixture:mapped-old"]["variant"] = "NEW"
    else:
        d = sample("scribe_draft")
        d["followups_used"] = 4
    p = create(
        "Scribe",
        tmp_path / "s.sqlite",
        operation="scribe_draft" if fault == "exhausted" else "scribe_final",
        data=d,
        clock=lambda: NOW,
    )
    assert tick(p.run_ref, NOW, p).completed == 0
    assert p.model.total_dispatches() == 0


def scribe_with(tmp_path, change, name):
    p = create("Scribe", tmp_path / f"{name}.sqlite", clock=lambda: NOW)
    original = p.model.renderer

    def renderer(*args):
        v = original(*args)
        change(v["outputs"])
        return v

    p.model.renderer = renderer
    return tick(p.run_ref, NOW, p).completed


def test_model_wording_and_ids_may_vary_when_the_rules_stay_exact(tmp_path):
    def vary(outputs):
        t = outputs[1]["payload"]
        t["id"] = "triangle-captured-before-paid"
        t["reason"] = "No mapped baseline trace exists for this rule yet."
        t["producer"]["model"] = "claude-haiku-5-5"
        t["created_at"] = t["created_at"].replace("+00:00", "Z")
        outputs.reverse()  # bundle order is not meaning

    assert scribe_with(tmp_path, vary, "ok") == 1


@pytest.mark.parametrize(
    "change",
    [
        lambda o: o[1]["payload"].update(reason="Rule waived: old defect accepted."),
        lambda o: o[1]["payload"].update(reason="Behaviour verified in staging."),
        lambda o: o[1]["payload"].update(mutant_ids=["m1"]),
        lambda o: o.pop(1),
        lambda o: o.append(dict(o[1], payload=dict(o[1]["payload"], id="dup"))),
        lambda o: o[0]["payload"]["rules"][0]["sources"]["traces"].append("fixture:invented"),
    ],
    ids=[
        "waiver",
        "proof_claim",
        "mutants",
        "missing_followup",
        "extra_followup",
        "invented_trace",
    ],
)
def test_waivers_proof_claims_and_changed_followups_are_rejected(tmp_path, change):
    assert scribe_with(tmp_path, change, "bad") == 0
