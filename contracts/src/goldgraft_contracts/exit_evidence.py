"""Bounded executor result and subsequent service read/revocation reconciliation."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .certificate_v2 import SignatureMaterial
from .common import Count
from .plan5_common import Digest, Id, OciDigest, P5Record, Ref, Utc, content_digest, unique
from .proof_evidence import ProofBinding

ORDINARY_CAPABILITIES = frozenset(
    {"source_read", "model_execution", "host_mutation", "worker_dispatch"}
)


class CapabilityDenial(P5Record):
    capability: Literal["source_read", "model_execution", "host_mutation", "worker_dispatch"]
    evidence_ref: Ref
    payload_digest: Digest
    denied_at: Utc


class ExitCriterionObservation(P5Record):
    criterion_ref: Ref
    state: Literal["verified", "failed", "unknown"]
    evidence_ref: Ref
    payload_digest: Digest
    observed_at: Utc


class ExitCheckResult(ProofBinding):
    result_id: Id
    exit_plan_ref: Ref
    exit_plan_digest: Digest
    reservation_ref: Ref
    executor_identity_ref: Ref
    trusted_code_digest: Digest
    final_artifact_digest: OciDigest
    final_config_digest: Digest
    state_digest: Digest
    restart_count: Annotated[Count, Field(le=1)]
    ordinary_denials: list[CapabilityDenial]
    observations: list[ExitCriterionObservation]
    evidence_read_authority_ref: Ref
    outcome: Literal["verified", "held", "failed", "unknown"]
    started_at: Utc
    finished_at: Utc
    result_digest: Digest
    signature: SignatureMaterial

    @model_validator(mode="after")
    def bounded_execution(self):
        unique([x.capability for x in self.ordinary_denials], "ordinary denials")
        unique([x.criterion_ref for x in self.observations], "exit criteria")
        if self.outcome == "verified" and (
            self.restart_count != 1
            or {x.capability for x in self.ordinary_denials} != ORDINARY_CAPABILITIES
            or not self.observations
            or any(x.state != "verified" for x in self.observations)
        ):
            raise ValueError("verified exit result requires bounded restart/denials/observations")
        if any(x.denied_at > self.started_at for x in self.ordinary_denials) or any(
            not self.started_at <= x.observed_at <= self.finished_at for x in self.observations
        ):
            raise ValueError("exit denial/observation ordering invalid")
        fields = self.model_dump(mode="json", exclude={"result_digest", "signature"})
        if content_digest(fields) != self.result_digest:
            raise ValueError("exit result digest mismatch")
        return self


class ExitEvidenceReadReceipt(P5Record):
    authority_ref: Ref
    disclosure_ref: Ref
    read_evidence_ref: Ref
    read_digest: Digest
    read_at: Utc
    revocation_ref: Ref
    revocation_digest: Digest
    revoked_at: Utc

    @model_validator(mode="after")
    def ordered(self):
        if self.revoked_at < self.read_at:
            raise ValueError("evidence-read revocation precedes read")
        return self


class ExitEvidenceReconciliation(ProofBinding):
    exit_plan_ref: Ref
    exit_plan_digest: Digest
    exit_result_ref: Ref
    exit_result_digest: Digest
    exit_manifest_ref: Ref
    exit_manifest_digest: Digest
    evidence_read_receipt: ExitEvidenceReadReceipt
    authenticity_ref: Ref
    checked_at: Utc
