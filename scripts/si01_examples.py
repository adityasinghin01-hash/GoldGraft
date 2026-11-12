"""Deterministic synthetic SI01 boundary examples; never signing or qualification."""

from copy import deepcopy

from goldgraft_contracts.plan5_common import content_digest
from goldgraft_contracts.registry import validate

D = "a" * 64
START = "2026-11-10T00:00:00Z"
END = "2026-11-11T00:00:00Z"


def samples():
    binding = dict(
        case_id="case-demo",
        run_id="run-demo",
        generation=1,
        resource_epochs={"synthetic-resource": 1},
        scope_digest=D,
        work_package_digest=D,
        policy_digest=D,
    )
    signature = dict(
        signature_ref="fixture:signature",
        signature_digest=D,
        transparency_ref="fixture:transparency",
        transparency_digest=D,
        authenticity_ref="fixture:authenticity",
    )
    checks = [
        dict(
            check_id="fixture:" + kind,
            flow_id="synthetic-checkout",
            kind=kind,
            rule_ids=[],
            subject_manifest_ref="fixture:subject",
            subject_manifest_digest=D,
            input_digest=D,
            required_schema="BaselineEvidence/1",
            required_evidence_class="component_offline",
            required_trust="collector_observed",
            critical=True,
            owner_role="collector",
        )
        for kind in ("baseline", "candidate")
    ]
    plan = dict(
        **binding,
        plan_id="fixture:proof-plan",
        checks=checks,
        exclusions=[],
        created_at=START,
        expires_at=END,
    )
    plan["plan_digest"] = content_digest(plan)
    result = dict(
        **binding,
        result_id="fixture:proof-result",
        plan_ref=plan["plan_id"],
        plan_digest=plan["plan_digest"],
        results=[
            dict(
                check_id=c["check_id"],
                subject_manifest_ref=c["subject_manifest_ref"],
                subject_manifest_digest=D,
                state="unknown",
                evidence_refs=[],
                reason_code="UNKNOWN",
            )
            for c in checks
        ],
        outcome="hold",
        reason_codes=["UNKNOWN"],
        checked_at=START,
    )
    result["result_digest"] = content_digest(result)
    from goldgraft_fakes._fixtures import example

    advice = example("HealDecision/1")
    advice.update(
        graft_id="run-demo", from_stage_pct=0, to_stage_pct=0, action="HOLD", hard_stop=None
    )
    promotion = dict(
        **binding,
        advice=advice,
        advice_digest=content_digest(advice),
        proof_plan_digest=plan["plan_digest"],
        proof_result_ref=result["result_id"],
        proof_result_digest=result["result_digest"],
        action="HOLD",
        reason_code="EVIDENCE_HOLD",
        checked_at=START,
        expires_at=END,
    )
    certificate = dict(
        **binding,
        cert_id="synthetic-private-cert",
        review_bundle_ref="fixture:review-bundle",
        review_bundle_digest=D,
        subject_manifest_ref="fixture:subject",
        subject_manifest_digest=D,
        proof_plan_ref=plan["plan_id"],
        proof_plan_digest=plan["plan_digest"],
        proof_result_ref=result["result_id"],
        proof_result_digest=result["result_digest"],
        ledger_root=D,
        source_route="local_folder",
        git_source=None,
        signer_kind="trusted_service",
        signer_identity_ref="fixture:signer",
        workflow_identity=None,
        workflow_sha=None,
        qualification_scope="component_only",
        qualification_evidence_refs=["fixture:synthetic-only"],
        issued_at=START,
        expires_at=END,
        signature=signature,
    )
    verification = dict(
        cert_id=certificate["cert_id"],
        case_id="case-demo",
        run_id="run-demo",
        signature_integrity="unverified",
        qualification_scope="component_only",
        qualification_state="held",
        reason_codes=["SYNTHETIC_ONLY"],
        checked_at=START,
    )
    exit_result = dict(
        **binding,
        result_id="fixture:exit-result",
        exit_plan_ref="fixture:exit-plan",
        exit_plan_digest=D,
        reservation_ref="fixture:reservation",
        executor_identity_ref="fixture:executor",
        trusted_code_digest=D,
        final_artifact_digest="sha256:" + D,
        final_config_digest=D,
        state_digest=D,
        restart_count=0,
        ordinary_denials=[],
        observations=[],
        evidence_read_authority_ref="fixture:evidence-read",
        outcome="held",
        started_at=START,
        finished_at=START,
    )
    exit_result["result_digest"] = content_digest(exit_result)
    exit_result["signature"] = signature
    closure = dict(
        **binding,
        exit_plan_ref="fixture:exit-plan",
        exit_plan_digest=D,
        exit_result_ref=exit_result["result_id"],
        exit_result_digest=content_digest(exit_result),
        exit_manifest_ref="fixture:exit-manifest",
        exit_manifest_digest=D,
        evidence_read_receipt=dict(
            authority_ref="fixture:evidence-read",
            disclosure_ref="fixture:disclosure",
            read_evidence_ref="fixture:read",
            read_digest=D,
            read_at=START,
            revocation_ref="fixture:read-revocation",
            revocation_digest=D,
            revoked_at=START,
        ),
        authenticity_ref="fixture:closure-auth",
        checked_at=START,
    )
    values = {
        "ProofPlan/1": plan,
        "ProofResult/1": result,
        "PromotionDecision/1": promotion,
        "Certificate/2": certificate,
        "CertificateVerification/1": verification,
        "ExitCheckResult/1": exit_result,
        "ExitEvidenceReconciliation/1": closure,
    }
    return {key: validate(key, value).model_dump(mode="json") for key, value in values.items()}


def sample(schema):
    return deepcopy(samples()[schema])
