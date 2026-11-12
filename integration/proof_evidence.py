"""Authenticate SI01 artifacts before composing the existing proof component.

Resolvers return private bytes, not authority. The host authentication hook must
verify custody/producer role/evidence qualification for those exact bytes and the
current tenant/resource epochs. No production authenticator is installed here.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from goldgraft_contracts.agent_runtime import ArtifactDescriptor
from goldgraft_contracts.plan5_common import content_digest
from goldgraft_contracts.plan5_validation import ArtifactBinding, validate_artifact
from goldgraft_contracts.proof_evidence import ProofCheck, ProofPlan, ProofResult


@dataclass(frozen=True)
class StoredArtifact:
    descriptor: ArtifactDescriptor
    payload: bytes


@dataclass(frozen=True)
class EvidenceContext:
    """Trusted host snapshot, independently resolved from accepted work/current authority."""

    tenant_id: str
    case_id: str
    run_id: str
    generation: int
    resource_epochs: dict[str, int]
    scope_digest: str
    work_package_digest: str
    policy_digest: str
    plan_digest: str
    required_checks: tuple[ProofCheck, ...]
    now: datetime
    review_bundle_ref: str | None = None
    review_bundle_digest: str | None = None
    critical_rule_ids: frozenset[str] = frozenset()


type Resolve = Callable[[str], StoredArtifact | None]
type Authenticate = Callable[[StoredArtifact, EvidenceContext, str], bool]


def same_binding(value, context):
    return all(
        getattr(value, key) == getattr(context, key)
        for key in (
            "case_id",
            "run_id",
            "generation",
            "resource_epochs",
            "scope_digest",
            "work_package_digest",
            "policy_digest",
        )
    )


def accept_artifact(
    ref,
    context,
    *,
    resolve,
    authenticate,
    schema,
    subject_digest,
    input_digest,
    trust,
    owner_role,
    evidence_class=None,
):
    """No identity/class claim in a descriptor substitutes for host authentication."""
    record = resolve(ref)
    if record is None:
        raise ValueError("MISSING")
    descriptor = record.descriptor
    if (
        descriptor.ref != ref
        or authenticate is None
        or authenticate(record, context, owner_role) is not True
    ):
        raise ValueError("AUTHENTICATION")
    if descriptor.created_at > context.now:
        raise ValueError("STALE")
    if evidence_class is not None and descriptor.evidence_class != evidence_class:
        raise ValueError("INVALID")
    binding = ArtifactBinding(
        tenant_id=context.tenant_id,
        case_id=context.case_id,
        run_id=context.run_id,
        generation=context.generation,
        subject_digest=subject_digest,
        input_digest=input_digest,
        schema=schema,
        producer_identity_ref=descriptor.producer_identity_ref,
        producer_role=owner_role,
        allowed_trust=frozenset(trust),
    )
    return validate_artifact(
        descriptor,
        record.payload,
        binding,
        authenticated_tenant=context.tenant_id,
        authenticated_producer=descriptor.producer_identity_ref,
        now=context.now,
    )


def evaluate_plan(
    plan: ProofPlan,
    context: EvidenceContext,
    *,
    resolve: Resolve,
    authenticate: Authenticate | None = None,
    approve_exclusion=None,
    verify_check=None,
) -> ProofResult:
    """Deterministic evidence sufficiency, never apply authority or external qualification."""
    # Revalidate even callers using model_copy/model_construct cannot bypass seals.
    plan = ProofPlan.model_validate(plan.model_dump(mode="json"))
    reasons = []
    if not same_binding(plan, context) or plan.plan_digest != context.plan_digest:
        reasons.append("SUBJECT_MISMATCH")
    if not plan.created_at <= context.now < plan.expires_at:
        reasons.append("STALE")
    expected = {c.check_id: c for c in context.required_checks}
    actual = {c.check_id: c for c in plan.checks}
    if not expected or len(expected) != len(context.required_checks) or actual != expected:
        reasons.append("INVENTORY_MISMATCH")
    exclusions = {e.check_id: e for e in plan.exclusions}
    results = []
    for check in plan.checks:
        reason, state, refs = "VERIFIED", "verified", [check.check_id]
        try:
            if reasons:
                raise ValueError(reasons[0])
            if check.check_id in exclusions:
                if (
                    approve_exclusion is None
                    or approve_exclusion(exclusions[check.check_id], context) is not True
                ):
                    raise ValueError("AUTHENTICATION")
                reason, state, refs = (
                    "EXCLUDED",
                    "excluded",
                    [exclusions[check.check_id].approval_ref],
                )
            else:
                subject = accept_artifact(
                    check.subject_manifest_ref,
                    context,
                    resolve=resolve,
                    authenticate=authenticate,
                    schema="SubjectManifest/1",
                    subject_digest=check.subject_manifest_digest,
                    input_digest=check.input_digest,
                    trust={"collector_observed"},
                    owner_role="collector",
                )
                if (
                    content_digest(subject) != check.subject_manifest_digest
                    or subject.scope_digest != context.scope_digest
                ):
                    raise ValueError("SUBJECT_MISMATCH")
                payload = accept_artifact(
                    check.check_id,
                    context,
                    resolve=resolve,
                    authenticate=authenticate,
                    schema=check.required_schema,
                    subject_digest=check.subject_manifest_digest,
                    input_digest=check.input_digest,
                    trust={check.required_trust},
                    owner_role=check.owner_role,
                    evidence_class=check.required_evidence_class,
                )
                for key in ("case_id", "run_id", "generation"):
                    if hasattr(payload, key) and getattr(payload, key) != getattr(context, key):
                        raise ValueError("SUBJECT_MISMATCH")
                if (
                    hasattr(payload, "package_digest")
                    and payload.package_digest != context.work_package_digest
                ):
                    raise ValueError("SUBJECT_MISMATCH")
                # Typed evidence is not necessarily successful evidence. An explicit
                # negative/unknown status or limitation cannot be promoted to VERIFIED.
                outcome = getattr(payload, "outcome", None)
                if outcome in {"failed", "failed_safe", "held", "blocked", "unknown", "pending"}:
                    raise ValueError(
                        "FAILED" if outcome in {"failed", "failed_safe"} else "UNKNOWN"
                    )
                if (
                    verify_check is None
                    or verify_check(payload, check, subject, context) is not True
                ):
                    raise ValueError("FAILED")
        except Exception as exc:
            code = str(exc)
            reason = (
                code
                if code
                in {
                    "MISSING",
                    "AUTHENTICATION",
                    "SUBJECT_MISMATCH",
                    "STALE",
                    "INVENTORY_MISMATCH",
                    "FAILED",
                    "UNKNOWN",
                    "UNSUPPORTED",
                }
                else "INVALID"
            )
            state = (
                "missing"
                if reason == "MISSING"
                else "failed"
                if reason == "FAILED" and check.kind == "payment"
                else "unknown"
            )
            refs = []
        results.append(
            dict(
                check_id=check.check_id,
                subject_manifest_ref=check.subject_manifest_ref,
                subject_manifest_digest=check.subject_manifest_digest,
                state=state,
                evidence_refs=refs,
                reason_code=reason,
            )
        )
    unresolved = {r["check_id"] for r in results if r["state"] not in {"verified", "excluded"}}
    outcome = (
        "hold"
        if reasons or any(c.critical and c.check_id in unresolved for c in plan.checks)
        else ("partial" if unresolved else "ready")
    )
    fields = {
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
    }
    fields.update(
        result_id="proof-"
        + content_digest([plan.plan_digest, results, context.now.isoformat()])[:32],
        plan_ref=plan.plan_id,
        plan_digest=plan.plan_digest,
        results=results,
        outcome=outcome,
        reason_codes=sorted(set(reasons + [r["reason_code"] for r in results])),
        checked_at=context.now.isoformat().replace("+00:00", "Z"),
    )
    return ProofResult.model_validate({**fields, "result_digest": content_digest(fields)})


def review_authenticated_bundle(
    plan,
    result,
    context,
    *,
    bundle_ref,
    bundle_digest,
    resolve,
    authenticate,
    subject_for,
):
    """Map current shared evidence into Singhal's existing review_bundle checker.

    subject_for is a trusted host mapping of runtime/origin identities, not a
    model declaration. Image/config/package/scope and the complete epoch set are
    checked again here; no missing OCI identity is filled with a source hash.
    """
    from pieces.proof.lifecycle_evidence import (
        Disposition,
        EvidenceState,
        Observation,
        ProofSubject,
        Requirement,
        review_bundle,
    )

    required, observations, by_kind = {}, [], {}
    verified = {r.check_id: r for r in result.results}
    for check in plan.checks:
        if verified[check.check_id].state == "excluded" and not check.critical:
            continue
        subject = accept_artifact(
            check.subject_manifest_ref,
            context,
            resolve=resolve,
            authenticate=authenticate,
            schema="SubjectManifest/1",
            subject_digest=check.subject_manifest_digest,
            input_digest=check.input_digest,
            trust={"collector_observed"},
            owner_role="collector",
        )
        if content_digest(subject) != check.subject_manifest_digest or subject_for is None:
            raise ValueError("SUBJECT_MISMATCH")
        mapped = subject_for(check, subject, context)
        if (
            not isinstance(mapped, ProofSubject)
            or not mapped.complete()
            or (
                mapped.case_id,
                mapped.run_id,
                mapped.generation,
                mapped.fence,
                mapped.scope_digest,
                mapped.package_digest,
                "sha256:" + mapped.image_digest,
                mapped.config_digest,
            )
            != (
                context.case_id,
                context.run_id,
                context.generation,
                content_digest(context.resource_epochs),
                context.scope_digest,
                context.work_package_digest,
                subject.oci_manifest_digest,
                subject.config_digest,
            )
        ):
            raise ValueError("SUBJECT_MISMATCH")
        required[check.check_id] = Requirement(mapped, check.critical)
        row = verified[check.check_id]
        record = resolve(check.check_id)
        if record is None or row.state != "verified":
            raise ValueError("MISSING")
        observations.append(
            Observation(
                check.check_id,
                mapped,
                EvidenceState.VERIFIED,
                record.descriptor.payload_digest,
                False,
            )
        )
        if check.kind in {"baseline", "candidate"}:
            if check.kind in by_kind:
                raise ValueError("UNSUPPORTED")
            by_kind[check.kind] = check
            required[check.kind] = Requirement(mapped, True)
            observations.append(
                Observation(
                    check.kind,
                    mapped,
                    EvidenceState.VERIFIED,
                    record.descriptor.payload_digest,
                    False,
                )
            )
    candidate = by_kind["candidate"]
    bundle = accept_artifact(
        bundle_ref,
        context,
        resolve=resolve,
        authenticate=authenticate,
        schema="ReviewBundle/1",
        subject_digest=candidate.subject_manifest_digest,
        input_digest=plan.plan_digest,
        trust={"collector_observed", "deterministic_result"},
        owner_role="proof",
    )
    review = review_bundle(bundle, required, observations, expected_bundle_digest=bundle_digest)
    if review.disposition != Disposition.READY:
        raise ValueError("REVIEW_HOLD")
    return bundle
