import pytest
from goldgraft_contracts.plan5_common import content_digest

from pieces.agents.proof_gate import evaluate
from pieces.agents.repair import request
from pieces.agents.scheduler import tick
from pieces.agents.workflow import candidate, create, execution

from .test_proof_gate import ProofPort
from .test_runtime import NOW


class FailurePort:
    identity = "fake:SH"

    def __init__(self, reason):
        self.reason = reason

    def failure(self, expected):
        return dict(
            fingerprint=content_digest(self.reason),
            candidate_ref=expected["candidate_ref"],
            image_digest=expected["image_digest"],
            required_rule=expected["required_rules"][0],
            evidence_class="scripted",
        )


def test_repair_rebuilds_subject_and_exhausts(tmp_path):
    p = create(tmp_path / "r.sqlite", clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 12
    old = ProofPort().evaluate(
        __import__("pieces.agents.proof_gate", fromlist=["request"]).request(p)
    )
    old_tree = candidate(p)["tree"]
    old_image = execution(p, "candidate-build")["image_digest"]
    assert (
        request(
            p, FailurePort("failure-1"), {"checkout.php": "<?php capture_order(); // repair one"}
        )
        == "repair-grafter-1"
    )
    assert tick(p.run_ref, NOW, p).completed == 5
    assert candidate(p, "repair-grafter-1")["tree"] != old_tree
    assert execution(p, "repair-build-1")["image_digest"] != old_image

    class StaleProof:
        identity = "fake:SH"

        def evaluate(self, expected):
            return old

    with pytest.raises(ValueError):
        evaluate(p, StaleProof())
    with pytest.raises(ValueError, match="repeated unchanged"):
        request(
            p, FailurePort("failure-1"), {"checkout.php": "<?php capture_order(); // same failure"}
        )
    assert (
        request(
            p, FailurePort("failure-2"), {"checkout.php": "<?php capture_order(); // repair two"}
        )
        == "repair-grafter-2"
    )
    assert tick(p.run_ref, NOW, p).completed == 5
    with pytest.raises(ValueError, match="limit exhausted"):
        request(p, FailurePort("failure-3"), {"checkout.php": "<?php capture_order(); // third"})
    assert len(p.control.snapshot(p.run_ref).tasks) == 22
    assert evaluate(p, ProofPort())["offline_proof_prerequisites"] is True
