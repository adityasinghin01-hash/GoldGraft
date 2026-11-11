import pytest

from pieces.agents.component_agents.orchard_analyst import sample
from pieces.agents.component_cli import create
from pieces.agents.scheduler import tick

from .test_runtime import NOW


@pytest.mark.parametrize(
    "fault", ["tenant", "purpose", "projection", "sql", "metric", "group", "filter", "cohort"]
)
def test_orchard_cross_case_aggregate_denied(tmp_path, fault):
    d = sample("aggregate")
    if fault == "tenant":
        d["tenant_id"] = "other-tenant"
    elif fault == "purpose":
        d["purpose"] = "advertising"
    elif fault == "projection":
        d["projection_ref"] = "projection:other-tenant"
    elif fault == "sql":
        d["query_ref"] = "SELECT:all-transactions"
    elif fault == "metric":
        d["metrics"] = ["raw_transactions"]
    elif fault == "group":
        d["group_by"] = ["customer_email"]
    elif fault == "filter":
        d["filters"] = {"tenant": "*"}
    else:
        d["buckets"][0]["cases"] = 4
        d["buckets"][0]["unverified"] = 4
    p = create("Orchard Analyst", tmp_path / "o.sqlite", data=d, clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 0
    assert p.model.total_dispatches() == p.tools.total_dispatches() == 0


@pytest.mark.parametrize("fault", ["filter", "metric", "claim"])
def test_orchard_dashboard_cannot_widen_scope(tmp_path, fault):
    p = create("Orchard Analyst", tmp_path / "o.sqlite", clock=lambda: NOW)
    original = p.model.renderer

    def bad(*args):
        v = original(*args)
        if fault == "filter":
            v["filters"] = {"tenant": "*"}
        elif fault == "metric":
            v["metrics"] = ["raw_rows"]
        else:
            v["title"] = "All merchants improved revenue"
        return v

    p.model.renderer = bad
    assert tick(p.run_ref, NOW, p).completed == 0
