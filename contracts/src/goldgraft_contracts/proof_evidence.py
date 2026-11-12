"""SI01 scoped evidence contracts. Custody, signatures and current authority are host duties."""

from typing import Annotated, Literal

from pydantic import Field, StrictBool, model_validator

from .plan5_common import (
    Digest,
    Epochs,
    EvidenceClass,
    Id,
    Ids,
    P5Record,
    Positive,
    Ref,
    Refs,
    Text,
    Utc,
    content_digest,
    unique,
)
from .runner import HealDecision


class ProofBinding(P5Record):
    case_id: Id
    run_id: Id
    generation: Positive
    resource_epochs: Epochs
    scope_digest: Digest
    work_package_digest: Digest
    policy_digest: Digest

    @model_validator(mode="after")
    def fenced(self):
        if not self.resource_epochs:
            raise ValueError("current resource epochs required")
        return self


class ProofCheck(P5Record):
    check_id: Id
    flow_id: Id
    kind: Literal[
        "baseline",
        "candidate",
        "scenario",
        "domain_rule",
        "security",
        "mutation",
        "payment",
        "isolation",
        "exit",
    ]
    rule_ids: Ids
    subject_manifest_ref: Ref
    subject_manifest_digest: Digest
    input_digest: Digest
    required_schema: Id
    required_evidence_class: EvidenceClass
    required_trust: Literal["collector_observed", "deterministic_result"]
    critical: StrictBool
    owner_role: Id


class ProofExclusion(P5Record):
    check_id: Id
    reason: Text
    approval_ref: Ref
    approval_digest: Digest


class ProofPlan(ProofBinding):
    plan_id: Id
    checks: Annotated[list[ProofCheck], Field(min_length=1, max_length=256)]
    exclusions: list[ProofExclusion]
    created_at: Utc
    expires_at: Utc
    plan_digest: Digest

    @model_validator(mode="after")
    def complete_plan(self):
        unique([c.check_id for c in self.checks], "proof checks")
        unique([e.check_id for e in self.exclusions], "proof exclusions")
        checks = {c.check_id: c for c in self.checks}
        if any(e.check_id not in checks or checks[e.check_id].critical for e in self.exclusions):
            raise ValueError("only declared noncritical checks may be excluded")
        if not {"baseline", "candidate"} <= {c.kind for c in self.checks if c.critical}:
            raise ValueError("critical baseline and candidate required")
        if (
            content_digest(self.model_dump(mode="json", exclude={"plan_digest"}))
            != self.plan_digest
        ):
            raise ValueError("proof plan digest mismatch")
        return self


ProofReason = Literal[
    "VERIFIED",
    "MISSING",
    "AUTHENTICATION",
    "INVALID",
    "SUBJECT_MISMATCH",
    "STALE",
    "INVENTORY_MISMATCH",
    "EXCLUDED",
    "FAILED",
    "UNKNOWN",
    "UNSUPPORTED",
]


class ProofCheckResult(P5Record):
    check_id: Id
    subject_manifest_ref: Ref
    subject_manifest_digest: Digest
    state: Literal["verified", "missing", "failed", "unknown", "unsupported", "excluded"]
    evidence_refs: Refs
    reason_code: ProofReason

    @model_validator(mode="after")
    def verified(self):
        if self.state == "verified" and (not self.evidence_refs or self.reason_code != "VERIFIED"):
            raise ValueError("verified result requires evidence and fixed reason")
        if self.state != "verified" and self.reason_code == "VERIFIED":
            raise ValueError("unverified result cannot claim verified reason")
        unique(self.evidence_refs, "result evidence")
        return self


class ProofResult(ProofBinding):
    result_id: Id
    plan_ref: Ref
    plan_digest: Digest
    results: Annotated[list[ProofCheckResult], Field(min_length=1, max_length=256)]
    outcome: Literal["ready", "partial", "hold"]
    reason_codes: Annotated[list[ProofReason], Field(min_length=1, max_length=256)]
    checked_at: Utc
    result_digest: Digest

    @model_validator(mode="after")
    def sealed(self):
        unique([r.check_id for r in self.results], "proof results")
        if self.outcome == "ready" and any(
            r.state not in {"verified", "excluded"} for r in self.results
        ):
            raise ValueError("ready cannot contain unresolved evidence")
        if (
            content_digest(self.model_dump(mode="json", exclude={"result_digest"}))
            != self.result_digest
        ):
            raise ValueError("proof result digest mismatch")
        return self


class PromotionDecision(ProofBinding):
    advice: HealDecision
    advice_digest: Digest
    proof_plan_digest: Digest
    proof_result_ref: Ref
    proof_result_digest: Digest
    action: Literal["STEP_UP", "HOLD", "CUTBACK"]
    reason_code: Literal["EVIDENCE_READY", "EVIDENCE_HOLD", "ADVICE_HOLD", "CUTBACK"]
    checked_at: Utc
    expires_at: Utc | None

    @model_validator(mode="after")
    def bounded(self):
        if content_digest(self.advice) != self.advice_digest or self.advice.graft_id != self.run_id:
            raise ValueError("rollout advice digest/run mismatch")
        if self.action == "STEP_UP" and (
            self.advice.action != "STEP_UP" or self.reason_code != "EVIDENCE_READY"
        ):
            raise ValueError("promotion requires passing evidence and step-up advice")
        if self.action == "CUTBACK" and self.advice.action != "CUTBACK":
            raise ValueError("cannot invent cutback advice")
        if self.action == "STEP_UP" and self.expires_at is None:
            raise ValueError("promotion requires expiry")
        if self.expires_at is not None and self.expires_at <= self.checked_at:
            raise ValueError("promotion already expired")
        return self
