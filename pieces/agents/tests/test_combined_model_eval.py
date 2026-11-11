"""Actual two-role graph and gateway with local providers; no network."""

from pieces.backend.model_gateway.broker import Gateway
from pieces.backend.model_gateway.component_port import ComponentGateway
from pieces.backend.model_gateway.ledger import Ledger
from pieces.backend.model_gateway.profile import Profile

from .test_evaluation_gateway import NativeProvider
from .test_herald_gateway import CatalogProvider


def run(tmp_path, source, herald):
    from scripts.live_combined_agents_eval import run_dual

    ledger = Ledger(tmp_path / "money.sqlite")
    profile = Profile()
    return run_dual(
        tmp_path / "state.sqlite",
        Gateway(ledger, tmp_path / "signing", profile, source),
        ComponentGateway(ledger, tmp_path / "signing", profile, herald, roles={"Herald"}),
        "dual-survey",
        "dual-herald",
    ), ledger


def test_real_model_ports_handoff_committed_inventory_to_herald(tmp_path):
    result, ledger = run(tmp_path, NativeProvider(), CatalogProvider())
    assert result["passed"]
    assert result["binding"]["herald_input_refs"] == result["binding"]["surveyor_output_refs"]
    assert result["herald"]["payload"]["numbers_used"][0]["value"] == 1
    assert result["herald"]["view"]["notifications_sent"] == 0
    assert result["surveyor"]["check"]["passed"]
    assert ledger.snapshot()["outstanding_micro_usd"] == 0
    assert ledger.snapshot()["spent_micro_usd"] > 0


def test_source_failure_never_dispatches_herald(tmp_path):
    class BadSource(NativeProvider):
        def generate(self, wire):
            response = super().generate(wire)
            if response["content"][0]["name"] == "submit_inventory":
                response["content"][0]["input"]["touchpoints"][0]["target"]["paypal_mapping_id"] = (
                    "invented"
                )
            return response

    herald = CatalogProvider()
    result, _ = run(tmp_path, BadSource(), herald)
    assert not result["passed"]
    assert result["herald"] is None
    assert herald.calls == 0


def test_herald_cannot_invent_a_count_after_real_handoff(tmp_path):
    herald = CatalogProvider(lambda value: value["numbers_used"][0].update(value=2))
    result, _ = run(tmp_path, NativeProvider(), herald)
    assert not result["passed"]
    assert result["surveyor"]["check"]["passed"]
    assert result["herald"]["payload"] is None
