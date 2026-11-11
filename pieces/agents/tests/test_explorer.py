import pytest

from pieces.agents.component_agents.explorer import sample
from pieces.agents.component_cli import create
from pieces.agents.scheduler import tick

from .test_runtime import NOW


@pytest.mark.parametrize("variant", ["OLD", "OLD_TWIN", "NEW"])
def test_explorer_baseline_discovery_and_exact_candidate(tmp_path, variant):
    d = sample("run_scenario")
    d["variant"] = variant
    d["execution_result"]["variant"] = variant
    d["execution_result"]["capture_ref"] = "fixture:capture:" + variant
    if variant == "NEW":
        d["final_contract_ref"] = "fixture:final-contract"
    p = create("Explorer", tmp_path / "e.sqlite", data=d, clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 1


@pytest.mark.parametrize(
    "fault",
    [
        "capture",
        "variant",
        "flow",
        "subject",
        "recorder",
        "incomplete",
        "unknown",
        "contract",
        "driver",
    ],
)
def test_explorer_missing_capture_stays_unverified(tmp_path, fault):
    d = sample("run_scenario")
    if fault == "capture":
        d["execution_result"]["capture_ref"] = None
    elif fault == "variant":
        d["execution_result"]["variant"] = "NEW"
    elif fault == "flow":
        d["execution_result"]["flow"] = "refund"
    elif fault == "subject":
        d["execution_result"]["source_tree_digest"] = "e" * 64
    elif fault == "recorder":
        d["execution_result"]["recorder"] = "model:invented"
    elif fault == "incomplete":
        d["execution_result"]["complete"] = False
    elif fault == "unknown":
        d["execution_state"] = "unknown"
    elif fault == "contract":
        d["variant"] = "NEW"
    else:
        d["driver_valid"] = False
    p = create("Explorer", tmp_path / "e.sqlite", data=d, clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 0
    assert tick(p.run_ref, NOW, p).claimed == 0
    with p.control.store.transaction() as db:
        assert (
            db.execute("SELECT COUNT(*) FROM scripts WHERE namespace='component-job'").fetchone()[0]
            <= 1
        )
