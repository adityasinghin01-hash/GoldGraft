import pytest

from pieces.agents.component_agents.architect import sample
from pieces.agents.component_cli import create
from pieces.agents.scheduler import tick

from .test_runtime import NOW


@pytest.mark.parametrize(
    "fault", ["api", "mapping", "family", "scope", "missing", "contract", "docs"]
)
def test_architect_unknown_api_holds(tmp_path, fault):
    d = sample("architect")
    if fault == "api":
        d["mappings"][0]["symbol"] = "imaginary_capture"
    elif fault == "mapping":
        d["mappings"][0]["mapping_id"] = "wrong-map"
    elif fault == "family":
        d["root_map"]["touchpoints"][0]["family"] = "RECURRING_NVP"
    elif fault == "scope":
        d["mappings"][0]["payment_only"] = False
    elif fault == "missing":
        d["root_map"]["touchpoints"] = []
    elif fault == "contract":
        d["final_contract"] = False
    else:
        d["catalog"]["qualified_fixture"] = False
    p = create("Architect", tmp_path / "a.sqlite", data=d, clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 0
    assert p.model.total_dispatches() == 0


@pytest.mark.parametrize("fault", ["api", "delta", "scope"])
def test_architect_untrusted_output_cannot_broaden_plan(tmp_path, fault):
    p = create("Architect", tmp_path / "a.sqlite", clock=lambda: NOW)
    original = p.model.renderer

    def bad(*args):
        v = original(*args)
        if fault == "api":
            v["items"][0]["target_op"] = "invented_api"
        elif fault == "delta":
            v["items"][0]["delta_ids"] = ["waive-capture"]
        else:
            v["items"][0]["paypal_only"] = False
        return v

    p.model.renderer = bad
    assert tick(p.run_ref, NOW, p).completed == 0
