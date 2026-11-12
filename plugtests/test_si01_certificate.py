"""Private v2 binding/signing tests use synthetic host/verifier counterparts only."""

from dataclasses import replace

import pytest
from goldgraft_contracts.certificate_v2 import CertificateClaims
from goldgraft_contracts.plan5_common import canonical_bytes, content_digest
from goldgraft_fakes._fixtures import example
from pydantic import ValidationError

from integration.private_certificates import issue_private_certificate, verify_private_certificate
from integration.proof_evidence import StoredArtifact
from pieces.proof.lifecycle_evidence import ProofSubject
from plugtests.test_si01_evidence import D, evaluate, setup_evidence


def certificate_setup():
    plan, context, records = setup_evidence()
    result = evaluate(plan, context, records)
    bundle = example("ReviewBundle/1")
    bundle.update(
        bundle_id="bundle",
        case_id="case",
        run_id="run",
        work_package_digest=D,
        artifact_digest="sha256:" + D,
        effective_config_digest=D,
        baseline_snapshot_refs=["fixture:baseline"],
        candidate_snapshot_refs=["fixture:candidate"],
        scenario_result_refs=["fixture:scenario"],
        domain_rule_result_refs=["fixture:domain_rule"],
        security_result_refs=["fixture:security"],
    )
    bundle["bundle_digest"] = content_digest(
        {k: v for k, v in bundle.items() if k != "bundle_digest"}
    )
    context = replace(
        context, review_bundle_ref="fixture:bundle", review_bundle_digest=bundle["bundle_digest"]
    )
    raw = canonical_bytes(bundle)
    descriptor = records["fixture:candidate"].descriptor.model_copy(
        update={
            "ref": "fixture:bundle",
            "schema_id": "ReviewBundle/1",
            "payload_digest": content_digest(bundle),
            "byte_count": len(raw),
            "input_digest": plan.plan_digest,
            "trust": "deterministic_result",
        }
    )
    records["fixture:bundle"] = StoredArtifact(descriptor, raw)
    metadata = {
        **{
            k: getattr(context, k)
            for k in (
                "case_id",
                "run_id",
                "generation",
                "resource_epochs",
                "scope_digest",
                "work_package_digest",
                "policy_digest",
            )
        },
        "cert_id": "fixture-cert",
        "review_bundle_ref": "fixture:bundle",
        "review_bundle_digest": bundle["bundle_digest"],
        "subject_manifest_ref": plan.checks[1].subject_manifest_ref,
        "subject_manifest_digest": plan.checks[1].subject_manifest_digest,
        "proof_plan_ref": plan.plan_id,
        "proof_plan_digest": plan.plan_digest,
        "proof_result_ref": result.result_id,
        "proof_result_digest": result.result_digest,
        "ledger_root": D,
        "source_route": "local_folder",
        "git_source": None,
        "signer_kind": "trusted_service",
        "signer_identity_ref": "fixture:signer",
        "workflow_identity": None,
        "workflow_sha": None,
        "qualification_scope": "component_only",
        "qualification_evidence_refs": ["fixture:component-only"],
        "issued_at": context.now,
        "expires_at": plan.expires_at,
    }

    def subject_for(check, subject, ctx):
        return ProofSubject(
            ctx.case_id,
            ctx.run_id,
            ctx.generation,
            content_digest(ctx.resource_epochs),
            ctx.scope_digest,
            ctx.work_package_digest,
            D,
            D,
            "fixture:runtime-identity",
            "fixture:origin-identity",
        )

    ports = dict(
        resolve=records.get,
        authenticate=lambda *args: True,
        verify_check=lambda payload, *args: payload.outcome == "reproduced",
        subject_for=subject_for,
        qualify=lambda claims, *args: claims.qualification_scope == "component_only",
    )
    signature = dict(
        signature_ref="fixture:signature",
        signature_digest=D,
        transparency_ref="fixture:transparency",
        transparency_digest=D,
        authenticity_ref="fixture:authenticity",
    )
    return metadata, plan, result, context, records, ports, signature


def test_non_git_certificate_has_no_fabricated_git_or_workflow_fields():
    meta, plan, result, ctx, _, ports, signature = certificate_setup()
    cert = issue_private_certificate(
        meta,
        plan,
        result,
        ctx,
        verify_signed=lambda *args: True,
        signer=lambda payload: signature,
        **ports,
    )
    assert cert.git_source is None and cert.workflow_sha is None
    verified = verify_private_certificate(
        cert, plan, result, ctx, verify_signature=lambda *a: True, **ports
    )
    assert verified.signature_integrity == "verified"
    assert verified.qualification_scope == "component_only"
    assert verified.qualification_state == "verified"
    assert (
        verify_private_certificate(cert, plan, result, ctx, **ports).qualification_state == "held"
    )
    assert (
        verify_private_certificate(
            cert,
            plan,
            result,
            replace(ctx, resource_epochs={"resource": 2}),
            verify_signature=lambda *a: True,
            **ports,
        ).qualification_state
        == "held"
    )


@pytest.mark.parametrize(
    "fault", ["evidence", "bundle_pin", "qualification", "scope", "result", "signer"]
)
def test_failed_gate_never_calls_signer(fault):
    meta, plan, result, ctx, records, ports, signature = certificate_setup()
    calls = []
    if fault == "evidence":
        del records["fixture:security"]
    elif fault == "bundle_pin":
        meta["review_bundle_digest"] = "b" * 64
    elif fault == "qualification":
        ports["qualify"] = None
    elif fault == "scope":
        meta["qualification_scope"] = "sandbox_payment"
    elif fault == "result":
        meta["proof_result_digest"] = "b" * 64
    else:
        ports["authenticate"] = None
    with pytest.raises(ValueError):
        issue_private_certificate(
            meta,
            plan,
            result,
            ctx,
            verify_signed=lambda *args: True,
            signer=lambda payload: calls.append(payload) or signature,
            **ports,
        )
    assert calls == []


@pytest.mark.parametrize(
    "updates",
    [
        {"source_route": "git"},
        {"workflow_sha": "b" * 40},
        {"signer_kind": "github_actions"},
        {"extra": True},
    ],
)
def test_conditional_source_and_signer_fields_are_closed(updates):
    meta, *_ = certificate_setup()
    with pytest.raises(ValidationError):
        CertificateClaims.model_validate({**meta, **updates})


def test_signature_covers_the_exact_private_claims_and_detects_tampering():
    from hashlib import sha256

    meta, plan, result, ctx, _, ports, signature = certificate_setup()
    signed = []
    cert = issue_private_certificate(
        meta,
        plan,
        result,
        ctx,
        verify_signed=lambda *args: True,
        signer=lambda raw: signed.append(raw) or signature,
        **ports,
    )
    expected = sha256(signed[0]).digest()

    def verify(cert, raw, ctx):
        return sha256(raw).digest() == expected

    cert = cert.model_copy(update={"ledger_root": "b" * 64})
    assert (
        verify_private_certificate(
            cert, plan, result, ctx, verify_signature=verify, **ports
        ).signature_integrity
        == "invalid"
    )


def test_rehashed_bundle_cannot_replace_independently_retained_review_pin():
    import json

    meta, plan, result, ctx, records, ports, signature = certificate_setup()
    record = records["fixture:bundle"]
    body = json.loads(record.payload)
    body["recovery_plan_ref"] = "fixture:unreviewed-recovery"
    body["bundle_digest"] = content_digest({k: v for k, v in body.items() if k != "bundle_digest"})
    raw = canonical_bytes(body)
    records["fixture:bundle"] = StoredArtifact(
        record.descriptor.model_copy(
            update={
                "payload_digest": content_digest(body),
                "byte_count": len(raw),
            }
        ),
        raw,
    )
    meta["review_bundle_digest"] = body["bundle_digest"]
    calls = []
    with pytest.raises(ValueError, match="REVIEW_PIN_MISMATCH"):
        issue_private_certificate(
            meta,
            plan,
            result,
            ctx,
            verify_signed=lambda *a: True,
            signer=lambda raw: calls.append(raw) or signature,
            **ports,
        )
    assert calls == []


def test_missing_or_rejecting_signer_verifier_cannot_return_certificate():
    meta, plan, result, ctx, _, ports, signature = certificate_setup()
    calls = []
    with pytest.raises(ValueError, match="SIGNER_OR_VERIFIER"):
        issue_private_certificate(
            meta, plan, result, ctx, signer=lambda raw: calls.append(raw) or signature, **ports
        )
    assert calls == []
    with pytest.raises(ValueError, match="SIGNATURE_VERIFICATION_FAILED"):
        issue_private_certificate(
            meta,
            plan,
            result,
            ctx,
            verify_signed=lambda *a: False,
            signer=lambda raw: signature,
            **ports,
        )


@pytest.mark.parametrize(
    "mode", ["ok", "wrong_case", "exception", "missing_adapter", "revoked_during_read"]
)
def test_private_http_boundary_current_case_tenant_and_revocation(tmp_path, mode):
    from datetime import timedelta

    from fastapi.testclient import TestClient
    from goldgraft_contracts.connection_control import CreateCase
    from goldgraft_foundation.ledger import Ledger

    from pieces.backend.connection.service import CaseService, Principal
    from pieces.backend.service_api import create_service_app

    meta, plan, result, ctx, _, ports, signature = certificate_setup()
    owner = Principal("owner", "tenant", ctx.now + timedelta(hours=1), "csrf")
    foreign = Principal("owner", "foreign", ctx.now + timedelta(hours=1), "csrf")
    service = CaseService(Ledger(f"sqlite:///{tmp_path / 'cases.sqlite'}"), clock=lambda: ctx.now)
    case = service.create_case(owner, CreateCase(shop_url="https://merchant.example.test"), "case")
    cert = issue_private_certificate(
        meta,
        plan,
        result,
        ctx,
        verify_signed=lambda *args: True,
        signer=lambda raw: signature,
        **ports,
    )
    cert = cert.model_copy(update={"case_id": case.case_id})
    calls, sessions = [], {"owner": owner, "foreign": foreign}

    class Views:
        def read(self, tenant, actor, case_id, cert_id):
            calls.append((tenant, actor, case_id, cert_id))
            if mode == "exception":
                raise RuntimeError("PRIVATE_CANARY")
            if mode == "revoked_during_read":
                sessions.clear()
            return cert.model_copy(update={"case_id": "other"}) if mode == "wrong_case" else cert

        def verify(self, *args):
            value = verify_private_certificate(cert, plan, result, ctx, **ports)
            return value

    client = TestClient(
        create_service_app(
            service,
            authenticate=lambda request: sessions.get(request.headers.get("x-fixture-session")),
            certificate_views=None if mode == "missing_adapter" else Views(),
        )
    )
    path = f"/v2/connection-cases/{case.case_id}/certificates/{cert.cert_id}"
    denied = client.get(path, headers={"x-fixture-session": "foreign"})
    assert denied.status_code == 404 and calls == []
    response = client.get(path, headers={"x-fixture-session": "owner"})
    assert (
        response.status_code
        == {
            "ok": 200,
            "wrong_case": 404,
            "exception": 503,
            "missing_adapter": 503,
            "revoked_during_read": 401,
        }[mode]
    )
    assert response.headers["Cache-Control"] == "private, no-store"
    assert "PRIVATE_CANARY" not in response.text
    if mode == "ok":
        check = client.get(path + "/verification", headers={"x-fixture-session": "owner"})
        assert check.status_code == 200 and check.json()["qualification_state"] == "held"
        sessions.clear()
        assert client.get(path, headers={"x-fixture-session": "owner"}).status_code == 401
    assert client.get("/certificates/fixture-cert").status_code == 404
