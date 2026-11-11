"""Actual submitted pieces composed offline; synthetic evidence never grants live authority."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from goldgraft_contracts.api import CertificateVerifyResult
from goldgraft_contracts.interfaces import Runner
from goldgraft_contracts.registry import validate
from goldgraft_foundation.blobs import LocalBlobStore

from integration.offline import fixture_proof, run_offline
from pieces.backend.app import create_app
from pieces.backend.custody_broker import CustodyBroker
from pieces.backend.payment_broker import PaymentBroker
from pieces.proof.proof import Proof
from pieces.runner.container_runner import ContainerRunner
from pieces.runner.sandbox_recorder import SandboxRecorder

ROOT = Path(__file__).resolve().parents[1]


def job():
    return validate(
        "JobSpec/1",
        {
            "job_id": "integration-fixture",
            "graft_id": "synthetic-c4",
            "stage": "RECORDED",
            "kind": "RECORD",
            "shop_pack_ref": "fixtures://shops/legacy-php-shop/goldgraft-shop.yaml",
            "scenario_ids": ["HAPPY"],
            "mutant_ids": [],
            "variants": ["OLD", "OLD_TWIN", "NEW"],
            "timeouts": {"build_s": 10, "run_s": 10, "total_s": 30},
            "secrets_ref": "secret://offline/unused",
            "signature": None,
        },
    )


@pytest.mark.parametrize(
    "scenario,grade",
    [
        ("HAPPY", "PASS"),
        ("REFUND_TWICE", "PASS_FIXED"),
        ("PENDING", "PROBLEM"),
        ("NOTIFY_DUP", "UNVERIFIED"),
    ],
)
def test_submitted_fixture_runner_feeds_actual_proof(tmp_path, scenario, grade):
    runner = ContainerRunner(blob_store=LocalBlobStore(tmp_path / "blobs"))
    spec = job().model_copy(update={"scenario_ids": [scenario]})
    report = fixture_proof(runner, Proof(), spec)
    assert report["evidence_class"] == "scripted"
    assert report["verdicts"][0]["grade"] == grade
    assert report["real_payment_qualified"] is False


@pytest.mark.parametrize("change", ["wrong_graft", "missing_twin", "duplicate", "wrong_job"])
def test_pipeline_rejects_incomplete_or_cross_case_runner_output(tmp_path, change):
    class AlteredRunner(ContainerRunner):
        def run_job(self, spec):
            result = super().run_job(spec)
            if change == "missing_twin":
                return result.model_copy(update={"raw_capture_refs": result.raw_capture_refs[:2]})
            if change == "duplicate":
                return result.model_copy(
                    update={"raw_capture_refs": [result.raw_capture_refs[0]] * 3}
                )
            if change == "wrong_job":
                return result.model_copy(update={"job_id": "other-job"})
            return result

    spec = job()
    if change == "wrong_graft":
        spec = spec.model_copy(update={"graft_id": "other-case"})
    with pytest.raises(ValueError):
        fixture_proof(AlteredRunner(blob_store=LocalBlobStore(tmp_path)), Proof(), spec)


def test_new_recorder_implements_runner_and_reopens_content_addressed_captures(tmp_path):
    custody = CustodyBroker()
    ref = custody.store_credentials("offline-only", {"paypal_client_id": "synthetic"})
    broker = PaymentBroker(custody_broker=custody)
    recorder = SandboxRecorder(broker=broker, blob_store=LocalBlobStore(tmp_path))
    assert isinstance(recorder, Runner)
    spec = job().model_copy(update={"secrets_ref": ref.to_uri()})
    result = recorder.run_job(spec)
    restarted = SandboxRecorder(broker=broker, blob_store=LocalBlobStore(tmp_path))
    assert result.runner_identity.sha == "UNQUALIFIED-SYNTHETIC"
    for capture_ref in result.raw_capture_refs:
        assert capture_ref.startswith("blob://")
        assert restarted.fetch_capture(capture_ref) == recorder.fetch_capture(capture_ref)


def test_backend_uses_injected_independent_proof_and_returns_shared_wire():
    from goldgraft_fakes import data

    client = TestClient(create_app(proof=Proof()))
    response = client.post(f"/certificates/{data.CERT_ID}/verify")
    assert response.status_code == 200
    result = CertificateVerifyResult.model_validate(response.json())
    assert result.cert_id == data.CERT_ID
    assert result.ok is False  # Synthetic certificate has no authentic signer.
    assert {c.name for c in result.checks} == {
        "SIGNATURE",
        "REKOR",
        "LEDGER_CHAIN",
        "PAYPAL_REFETCH",
    }
    assert client.post("/certificates/unknown/verify").status_code == 404


def test_combined_report_keeps_pr6_simulation_unverified_and_reopens(tmp_path):
    report = run_offline(tmp_path)
    assert report["evidence_class"] == "scripted"
    assert report["payment_recorder"]["proof_status"] == "MISSING_EVIDENCE"
    assert report["payment_recorder"]["cmel_events"] == 0
    assert report["payment_recorder"]["captures_reopened"] == 3
    assert report["provider_calls"] == 0
    assert report["merchant_delivery_qualified"] is False
    assert json.loads((tmp_path / "report.json").read_text()) == report


def test_service_mode_denied_before_any_state_or_provider_effect(tmp_path):
    directory = tmp_path / "must-not-exist"
    with pytest.raises(ValueError, match="UNQUALIFIED"):
        run_offline(directory, mode="service")
    assert not directory.exists()


def test_integration_app_labels_responses_and_rejects_unqualified_callback():
    from integration.app import create_app as integrated_app

    client = TestClient(integrated_app())
    response = client.get("/grafts/demo-1")
    assert response.status_code == 200
    assert response.headers["X-GoldGraft-Evidence-Class"] == "scripted"
    for path in ("/pp/webhook/demo-1", "/gh/webhook"):
        response = client.post(path, json={})
        assert response.status_code == 503
        assert response.headers["content-type"].startswith("application/problem+json")
