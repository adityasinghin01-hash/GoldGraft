"""Herald through the actual signed component gateway + own runtime; scripted provider.

Herald's validators are unchanged: only exact closed-catalog text and exact ledger
numbers are accepted. No network: the provider below is a local stand-in.
"""

import json

import pytest

from pieces.agents.herald import HeraldInputs, supported_texts


class CatalogProvider:
    """Reads both projections, then assembles text from call_facts (or misbehaves)."""

    def __init__(self, change=None):
        self.calls, self.change = 0, change

    def count(self, wire):
        return 1000

    def generate(self, wire):
        self.calls += 1
        context = json.loads(wire["messages"][0]["content"])
        facts, cf = context["facts"], context["call_facts"]
        if not context["observations"]:
            blocks = [
                {"name": "status_read", "input": {"run_ref": cf["run_ref"]}},
                {
                    "name": "evidence_summary",
                    "input": {"run_ref": cf["run_ref"], "projection": cf["projection"]},
                },
            ]
        else:
            texts, numbers = supported_texts(HeraldInputs.model_validate(facts))
            payload = dict(context["reference_metadata"], text=texts[1], numbers_used=numbers)
            if self.change:
                self.change(payload)
            blocks = [{"name": "submit_output", "input": payload}]
        return {
            "id": f"msg_h{self.calls}",
            "model": "claude-haiku-5-5",
            "content": [
                dict(b, type="tool_use", id=f"t{self.calls}{i}") for i, b in enumerate(blocks)
            ],
            "usage": {"input_tokens": 1000, "output_tokens": 100},
        }


def run(tmp_path, settings, provider, projection="private_status"):
    from pieces.backend.model_gateway.component_port import ComponentGateway
    from pieces.backend.model_gateway.ledger import Ledger
    from pieces.backend.model_gateway.profile import Profile
    from scripts.live_herald_model_eval import run_case

    ledger = Ledger(tmp_path / "money.sqlite")
    gateway = ComponentGateway(ledger, tmp_path / "signing", Profile(), provider, roles={"Herald"})
    case = {"id": "t", "role": "Herald", "projection": projection, "settings": settings}
    task, result, payload, view, _ = run_case(case, gateway, tmp_path, "b")
    return task, result, payload, view, ledger


def test_model_assembled_catalog_text_is_accepted_with_exact_number(tmp_path):
    task, result, payload, view, ledger = run(tmp_path, {}, CatalogProvider())
    assert task.state == "succeeded", result
    assert payload["producer"]["model"] == "claude-haiku-5-5"
    assert "Inventory contains 5 source indicators." in payload["text"]
    assert payload["numbers_used"][0]["value"] == 5
    assert view["authoritative_status_changed"] is False and view["notifications_sent"] == 0
    assert ledger.snapshot()["spent_micro_usd"] > 0


def test_call_facts_carry_the_catalog_not_the_answer(tmp_path):
    seen = []

    class Spy(CatalogProvider):
        def generate(self, wire):
            seen.append(json.loads(wire["messages"][0]["content"])["call_facts"])
            return super().generate(wire)

    run(tmp_path, {"status": "held", "reason_code": "PROOF_MISSING"}, Spy())
    facts = seen[0]
    assert set(facts["catalog"]) == {"status_text", "reason_text", "asset_text", "limitation"}
    assert "text" not in facts and "numbers_used" not in facts


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.update(text=p["text"].replace("remain unverified", "are verified")),
        lambda p: p.update(text=p["text"] + " All payments are safe."),
        lambda p: p["numbers_used"][0].update(value=6),
        lambda p: p.update(numbers_used=[]),
        lambda p: p.update(kind="PR_BODY"),
    ],
    ids=["paraphrase", "added_claim", "wrong_number", "dropped_number", "wrong_kind"],
)
def test_validators_stay_closed_for_model_text(tmp_path, change):
    task, _, payload, _, _ = run(tmp_path, {}, CatalogProvider(change))
    assert task.state != "succeeded" and payload is None


def test_conflicting_facts_hold_before_any_model_call(tmp_path):
    provider = CatalogProvider()
    task, _, payload, _, _ = run(
        tmp_path, {"status": "unknown", "reason_code": "SOURCE_MISSING"}, provider
    )
    assert task.state != "succeeded" and payload is None and provider.calls == 0


def test_tool_progress_names_both_reads_so_a_model_can_stop_reading(tmp_path):
    seen = []

    class Spy(CatalogProvider):
        def generate(self, wire):
            seen.append(json.loads(wire["messages"][0]["content"])["tool_progress"])
            return super().generate(wire)

    task, *_ = run(tmp_path, {}, Spy())
    assert task.state == "succeeded"
    assert seen == [[], ["status.read", "evidence.summary"]]
