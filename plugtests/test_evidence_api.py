"""Exercise evidence routing with server-side case grants and a trusted fixture store."""

from dataclasses import replace
from hashlib import sha256

from fastapi.testclient import TestClient

from integration.app import create_app
from pieces.proof.lifecycle_evidence import EvidenceState, Observation, Requirement

from .test_lifecycle_evidence import BASELINE, CANDIDATE


def test_evidence_routes_enforce_case_scope_revocation_and_projection(tmp_path):
    from integration.service import FixtureRun

    grants = {
        ("reviewer", BASELINE.case_id, "private"),
        ("reader", BASELINE.case_id, "public"),
    }
    reads = []
    payload = b"private capture: customer and transaction"
    observation = Observation(
        "baseline", BASELINE, EvidenceState.VERIFIED, sha256(payload).hexdigest(), False
    )
    private_check = "customer contact and capture transaction"
    requirements = {
        "baseline": Requirement(BASELINE),
        "candidate": Requirement(CANDIDATE),
        private_check: Requirement(CANDIDATE, critical=False),
    }

    def authorize(request, case_id, visibility):
        return (request.headers.get("authorization"), case_id, visibility) in grants

    def load(case_id):
        reads.append(case_id)
        return requirements, [
            (observation, payload),
            (replace(observation, check="candidate", subject=CANDIDATE), b"modified"),
        ]

    client = TestClient(create_app(
        service=FixtureRun(tmp_path), evidence_authorize=authorize, evidence_loader=load
    ))
    base = f"/cases/{BASELINE.case_id}/evidence"
    assert client.get(f"{base}/private").status_code == 404
    assert client.get(f"{base}/private", headers={"authorization": "reader"}).status_code == 404
    assert client.get(
        "/cases/other/evidence/private", headers={"authorization": "reviewer"}
    ).status_code == 404
    assert not reads

    response = client.get(f"{base}/private", headers={"authorization": "reviewer"})
    assert response.status_code == 200 and response.headers["cache-control"] == "private, no-store"
    assert response.json()["disposition"] == "HOLD"
    assert response.json()["verified_count"] == 1
    assert private_check in response.text

    response = client.get(f"{base}/public", headers={"authorization": "reader"})
    assert response.json() == {
        "disposition": "HOLD",
        "verified_count": 1,
        "gap_count": 2,
        "gap_reasons": ["MISSING"],
    }
    grants.remove(("reviewer", BASELINE.case_id, "private"))
    assert client.get(f"{base}/private", headers={"authorization": "reviewer"}).status_code == 404
    assert len(reads) == 2


def test_payment_dry_run_uses_fixture_proof_without_a_provider(tmp_path):
    import pytest

    from scripts.live_paypal_sandbox_payment import run_sandbox_payment

    report = run_sandbox_payment(dry_run=True, state_dir=tmp_path / "fixture")
    assert report["live"] is False and report["provider_calls"] == 0
    assert report["fixture_verdicts"]["HAPPY"] == "PASS"
    assert report["simulated_payment_proof"] == "MISSING_EVIDENCE"
    with pytest.raises(ValueError, match="qualified payment transport"):
        run_sandbox_payment(state_dir=tmp_path / "live")
    assert not (tmp_path / "live").exists()
