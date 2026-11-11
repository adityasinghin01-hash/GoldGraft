import pytest

from pieces.agents.component_agents.healer import sample
from pieces.agents.component_cli import create
from pieces.agents.scheduler import tick

from .test_runtime import NOW


@pytest.mark.parametrize(
    "anomaly", ["unknown_effect", "callback_gap", "current_state_incompatible", "none"]
)
def test_healer_no_blind_legacy_cutback(tmp_path, anomaly):
    d = sample("diagnose")
    d["anomaly"] = anomaly
    d["current_state_compatible"] = anomaly == "none"
    p = create("Healer", tmp_path / "h.sqlite", data=d, clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 1
    t = p.control.snapshot(p.run_ref).tasks[0]
    out = p.artifacts.inspect_outputs(t, p.context_for(t.task.task_id))[0]["payload"]
    assert out["cutback_requested"] is False
    assert out["pause_requested"] == (anomaly != "none")


@pytest.mark.parametrize("fault", ["live", "stale"])
def test_healer_requires_qualified_current_observation(tmp_path, fault):
    d = sample("diagnose")
    if fault == "live":
        d["synthetic_observation"] = False
    else:
        d["status"]["generation"] = 2
    p = create("Healer", tmp_path / "h.sqlite", data=d, clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 0
    assert p.model.total_dispatches() == 0


@pytest.mark.parametrize("fault", ["cutback", "restore", "evidence"])
def test_healer_output_cannot_claim_actions(tmp_path, fault):
    p = create("Healer", tmp_path / "h.sqlite", clock=lambda: NOW)
    original = p.model.renderer

    def bad(*args):
        v = original(*args)
        if fault == "cutback":
            v["cutback_requested"] = True
        elif fault == "restore":
            v["text"] = "Old database restored successfully"
        else:
            v["evidence_refs"] = ["private:other-case"]
        return v

    p.model.renderer = bad
    assert tick(p.run_ref, NOW, p).completed == 0
