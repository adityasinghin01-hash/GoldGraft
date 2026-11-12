"""Private v2 certificate composition; real signing/custody/qualification are opt-in ports."""

from goldgraft_contracts.certificate_v2 import (
    CertificateClaims,
    CertificateV2,
    CertificateVerification,
    SignatureMaterial,
)
from goldgraft_contracts.plan5_common import canonical_bytes

from integration.promotion import require_current_result
from integration.proof_evidence import review_authenticated_bundle, same_binding


def certificate_payload(certificate):
    fields = certificate.model_dump(mode="json", exclude={"signature"})
    return canonical_bytes(fields)


def require_certificate_claims(
    claims,
    plan,
    result,
    context,
    *,
    resolve,
    authenticate=None,
    verify_check=None,
    subject_for=None,
    qualify=None,
    approve_exclusion=None,
):
    if not same_binding(claims, context) or not claims.issued_at <= context.now < claims.expires_at:
        raise ValueError("CERTIFICATE_STALE")
    if (claims.review_bundle_ref, claims.review_bundle_digest) != (
        context.review_bundle_ref,
        context.review_bundle_digest,
    ):
        raise ValueError("REVIEW_PIN_MISMATCH")
    if claims.expires_at > plan.expires_at or (
        claims.proof_plan_ref,
        claims.proof_plan_digest,
        claims.proof_result_ref,
        claims.proof_result_digest,
    ) != (plan.plan_id, plan.plan_digest, result.result_id, result.result_digest):
        raise ValueError("CERTIFICATE_BINDING")
    require_current_result(
        plan,
        result,
        context,
        resolve=resolve,
        authenticate=authenticate,
        verify_check=verify_check,
        approve_exclusion=approve_exclusion,
    )
    candidate = [c for c in plan.checks if c.kind == "candidate"]
    if len(candidate) != 1 or (
        claims.subject_manifest_ref,
        claims.subject_manifest_digest,
    ) != (candidate[0].subject_manifest_ref, candidate[0].subject_manifest_digest):
        raise ValueError("CERTIFICATE_SUBJECT")
    review_authenticated_bundle(
        plan,
        result,
        context,
        bundle_ref=claims.review_bundle_ref,
        bundle_digest=claims.review_bundle_digest,
        resolve=resolve,
        authenticate=authenticate,
        subject_for=subject_for,
    )
    if claims.qualification_scope != "component_only":
        critical = [c for c in plan.checks if c.critical]
        required_kinds = {
            "baseline",
            "candidate",
            "scenario",
            "domain_rule",
            "security",
            "mutation",
        }
        if not required_kinds <= {c.kind for c in critical}:
            raise ValueError("CRITICAL_COVERAGE_HOLD")
        classes = {"payment": "real_payment", "isolation": "isolation_qualified"}
        if claims.qualification_scope == "merchant_delivery":
            classes["exit"] = "merchant_exit"
        if any(
            not any(c.kind == kind and c.required_evidence_class == level for c in critical)
            for kind, level in classes.items()
        ):
            raise ValueError("QUALIFICATION_HOLD")
        if not context.critical_rule_ids or any(
            not any(c.kind == kind and rule in c.rule_ids for c in critical)
            for rule in context.critical_rule_ids
            for kind in ("domain_rule", "mutation")
        ):
            raise ValueError("CRITICAL_COVERAGE_HOLD")
    # Host verifies exact signer/source/ledger binding, independent payment re-fetch,
    # mutation outcomes/strength and profile-specific delivery gates. No permissive default.
    if qualify is None or qualify(claims, plan, result, context) is not True:
        raise ValueError("QUALIFICATION_HOLD")


def issue_private_certificate(
    metadata,
    plan,
    result,
    context,
    *,
    signer=None,
    verify_signed=None,
    **ports,
):
    claims = CertificateClaims.model_validate(metadata)
    require_certificate_claims(claims, plan, result, context, **ports)
    if signer is None or verify_signed is None:
        raise ValueError("SIGNER_OR_VERIFIER_UNAVAILABLE")
    signature = SignatureMaterial.model_validate(signer(certificate_payload(claims)))
    certificate = CertificateV2(**claims.model_dump(), signature=signature)
    if verify_signed(certificate, certificate_payload(certificate), context) is not True:
        raise ValueError("SIGNATURE_VERIFICATION_FAILED")
    return certificate


def verify_private_certificate(
    certificate, plan, result, context, *, verify_signature=None, **ports
):
    certificate = CertificateV2.model_validate(certificate.model_dump(mode="json"))
    integrity, qualification, reasons = "unverified", "held", ["SIGNATURE_UNAVAILABLE"]
    if verify_signature is not None:
        try:
            valid = verify_signature(certificate, certificate_payload(certificate), context) is True
        except Exception:
            valid = False
        integrity = "verified" if valid else "invalid"
        reasons = ["SIGNATURE_INVALID"] if not valid else ["QUALIFICATION_HOLD"]
        if valid:
            try:
                require_certificate_claims(certificate, plan, result, context, **ports)
                qualification, reasons = "verified", ["VERIFIED"]
            except Exception:
                pass
    return CertificateVerification(
        cert_id=certificate.cert_id,
        case_id=certificate.case_id,
        run_id=certificate.run_id,
        signature_integrity=integrity,
        qualification_scope=certificate.qualification_scope,
        qualification_state=qualification,
        reason_codes=reasons,
        checked_at=context.now,
    )
