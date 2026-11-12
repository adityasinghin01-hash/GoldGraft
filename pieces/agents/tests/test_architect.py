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


def test_architect_accepts_grounded_handoff_wording_and_reordered_sets(tmp_path):
    p = create("Architect", tmp_path / "a.sqlite", clock=lambda: NOW)
    original = p.model.renderer

    def explain(*args):
        v = original(*args)
        v["handoff"] = ["Pinned fixture documentation; independent proof required before apply."]
        v["target_experience"].reverse()
        return v

    p.model.renderer = explain
    assert tick(p.run_ref, NOW, p).completed == 1


def test_architect_conflicting_final_evidence_cannot_be_accepted(tmp_path):
    d = sample("architect")
    d["evidence"]["fixture:final-contract"]["final"] = False
    p = create("Architect", tmp_path / "a.sqlite", data=d, clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 0


def test_architect_routes_larger_or_annotated_evidence_before_dispatch():
    from pieces.agents.component_agents.architect import Input, route

    d = sample("architect")
    assert route(Input.model_validate(d)) == "sonnet"
    d["evidence"]["fixture:final-contract"]["note"] = "untrusted annotation"
    assert route(Input.model_validate(d)) == "sonnet"
    d["evidence"]["fixture:final-contract"].pop("note")
    d["mappings"] *= 2
    assert route(Input.model_validate(d)) == "sonnet"


def orders_profile():
    from pieces.agents.integrated import ORDERS_CATALOG

    data = sample("architect")
    data["catalog"] = dict(ORDERS_CATALOG)
    data["root_map"]["touchpoints"][0]["target"]["paypal_mapping_id"] = "nvp-capture"
    data["mappings"][0].update(symbol="gg_capture_order", mapping_id="nvp-capture")
    return data


def test_pinned_orders_profile_declares_only_the_required_comparison_mappings(tmp_path):
    from pieces.agents.component_agents.architect import Input, draft

    data = orders_profile()
    plan = draft(Input.model_validate(data))
    expected = {"D_TOKEN_ORDER", "D_TXN_CAPTURE", "D_APPROVE", "D_LEDGER_READ"}
    assert {delta["id"] for delta in plan["deltas"]} == expected
    assert set(plan["items"][0]["delta_ids"]) == expected
    p = create("Architect", tmp_path / "a.sqlite", data=data, clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 1


def test_pinned_profile_does_not_allow_model_to_invent_a_money_waiver(tmp_path):
    p = create("Architect", tmp_path / "a.sqlite", data=orders_profile(), clock=lambda: NOW)
    original = p.model.renderer

    def waive(*args):
        value = original(*args)
        value["deltas"].append(
            {"id": "ignore-money", "mapping_id": "x", "description": "ignore amounts"}
        )
        return value

    p.model.renderer = waive
    assert tick(p.run_ref, NOW, p).completed == 0
