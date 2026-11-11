import pytest

from pieces.agents.proof_gate import evaluate, request
from pieces.agents.scheduler import tick
from pieces.agents.workflow import create

from .test_runtime import NOW


class ProofPort:
    identity = "fake:SH"

    def __init__(self, fault=None):
        self.fault = fault

    def evaluate(self, expected):
        value = {k: v for k, v in expected.items() if k not in {"required_flows", "required_rules"}}
        value.update(
            evidence_class="scripted",
            required_flows_observed=expected["required_flows"],
            guarded_rule_ids=expected["required_rules"],
            unguarded_rule_ids=[],
            required_failures=[],
            score=1.0,
            complete=True,
        )
        if self.fault == "flow":
            value["required_flows_observed"] = []
        elif self.fault == "image":
            value["image_digest"] = "sha256:" + "e" * 64
        elif self.fault == "source":
            value["source_tree_digest"] = "e" * 64
        elif self.fault == "refs":
            value["input_refs"] = []
        elif self.fault == "guard":
            value["unguarded_rule_ids"] = ["captured-before-paid"]
        elif self.fault == "failure":
            value["required_failures"] = ["capture"]
        elif self.fault == "complete":
            value["complete"] = False
        return value


@pytest.fixture
def completed(tmp_path):
    p = create(tmp_path / "p.sqlite", clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 12
    return p


def test_independent_proof_is_used_by_own_gate(completed):
    view = evaluate(completed, ProofPort())
    assert view["offline_proof_prerequisites"] is True
    assert view["merchant_review_authority"] is False
    assert request(completed)["input_refs"]


@pytest.mark.parametrize(
    "fault", ["flow", "image", "source", "refs", "guard", "failure", "complete", None]
)
def test_independent_proof_missing_not_high_score(completed, fault):
    with pytest.raises(ValueError):
        evaluate(completed, ProofPort(fault) if fault else None)
