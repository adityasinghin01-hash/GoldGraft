"""Saved-case/readiness/Start/cancel records. These are contracts, not HTTP handlers."""

from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import AfterValidator, Field, StrictBool, StrictStr, model_validator

from .connector_adapters import ProviderRef
from .lifecycle import ActionPlan, ApprovalSet, LifecycleRun, ReviewBundle
from .plan5_common import (
    Count,
    Digest,
    Epochs,
    EvidenceClass,
    Id,
    Ids,
    Issue,
    P5Record,
    Positive,
    Ref,
    Refs,
    RelativePath,
    Text,
    Utc,
    content_digest,
    unique,
)
from .work_package import ManifestEntry


def safe_web_url(value):
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValueError("URL must be HTTP(S) without embedded credentials")
    if parsed.fragment:
        raise ValueError("URL fragments forbidden")
    return value


WebUrl = Annotated[StrictStr, Field(min_length=1, max_length=2048), AfterValidator(safe_web_url)]


class ConnectionCase(P5Record):
    case_id: Id
    tenant_id: Id
    requester_id: Id
    shop_url: WebUrl
    created_at: Utc
    graph_ref: Ref | None
    binding_refs: Refs
    status: Literal[
        "draft", "waiting_controller", "checking", "setup_needed", "ready", "accepted", "closed"
    ]


class CheckResult(P5Record):
    check_id: Id
    status: Literal["pass", "missing", "unsupported", "failed", "stale", "unknown"]
    evidence_refs: Refs
    checked_at: Utc
    expires_at: Utc | None
    recovery_code: Id | None

    @model_validator(mode="after")
    def evidence(self):
        if self.status == "pass" and not self.evidence_refs:
            raise ValueError("passing check requires evidence")
        if self.expires_at is not None and self.expires_at <= self.checked_at:
            raise ValueError("check expiry must follow check time")
        return self


class ConnectionReadiness(P5Record):
    readiness_id: Id
    case_id: Id
    actor_id: Id
    work_package_ref: Ref
    work_package_digest: Digest
    resource_graph_digest: Digest
    source_snapshot_refs: Refs
    source_manifest_digest: Digest
    resource_evidence_digests: dict[Id, Digest]
    binding_epochs: Epochs
    scope_digest: Digest
    processing_policy_digest: Digest
    runtime_profile_digest: Digest
    fixture_profile_digest: Digest
    checks: list[CheckResult]
    issued_at: Utc
    expires_at: Utc
    readiness_digest: Digest

    @model_validator(mode="after")
    def checks_unique(self):
        unique([c.check_id for c in self.checks], "readiness checks")
        return self


class ActionIntent(P5Record):
    action_id: Id
    case_id: Id
    actor_id: Id
    readiness_id: Id
    readiness_digest: Digest
    created_at: Utc
    expires_at: Utc


class WorkAcceptance(P5Record):
    action_id: Id
    case_id: Id
    work_id: Id
    accepted_at: Utc
    readiness_digest: Digest
    work_package_digest: Digest
    resource_graph_digest: Digest
    scope_digest: Digest
    source_manifest_digest: Digest
    receipt_ref: Ref


class WorkStatus(P5Record):
    action_id: Id
    case_id: Id
    work_id: Id | None
    state: Literal[
        "submitting",
        "accepted",
        "queued",
        "provisioning",
        "operation_started",
        "held",
        "unknown",
        "cancellation_pending",
        "cancelled",
        "stopped",
        "failed",
    ]
    generation: Positive | None
    last_event_seq: Count
    checked_at: Utc
    evidence_refs: Refs

    @model_validator(mode="after")
    def committed_operation(self):
        if self.generation is not None and self.work_id is None:
            raise ValueError("worker generation requires accepted work")
        if (
            self.state in {"accepted", "queued", "provisioning", "operation_started", "stopped"}
            and self.work_id is None
        ):
            raise ValueError("accepted work state needs work identity")
        if self.state == "operation_started" and (
            self.generation is None or not self.evidence_refs
        ):
            raise ValueError("operation_started requires worker generation and evidence")
        if self.state == "stopped" and not self.evidence_refs:
            raise ValueError("stopped requires trusted termination evidence")
        return self


class WorkerOperation(P5Record):
    operation_id: Id
    work_id: Id
    generation: Positive
    worker_id: Id
    kind: Literal["BASELINE_READ"]
    assignment_digest: Digest
    work_package_digest: Digest
    resource_graph_digest: Digest
    source_manifest_digest: Digest
    scope_digest: Digest
    observed_digest: Digest
    runtime_profile_digest: Digest
    started_at: Utc
    finished_at: Utc
    result: Literal["verified", "failed"]
    evidence_refs: Refs
    authenticity_ref: Ref

    @model_validator(mode="after")
    def observed_evidence(self):
        if self.result == "verified" and (
            not self.evidence_refs or self.observed_digest != self.source_manifest_digest
        ):
            raise ValueError("verified baseline read requires exact source observation/evidence")
        return self


class CollectorAcceptance(P5Record):
    """Receipt for service-only WorkerOperation intake; not proof of site reproduction."""

    operation_id: Id
    work_id: Id
    generation: Positive
    accepted_at: Utc
    receipt_ref: Ref


class WorkCancellation(P5Record):
    cancel_id: Id
    case_id: Id
    action_id: Id
    requested_by: Id
    requested_at: Utc
    state: Literal["intent_recorded", "fenced", "termination_pending", "confirmed", "unknown"]
    work_id: Id | None
    generation: Positive | None
    termination_evidence_refs: Refs

    @model_validator(mode="after")
    def confirmed(self):
        if self.generation is not None and self.work_id is None:
            raise ValueError("generation requires accepted work")
        if (
            self.state == "confirmed"
            and self.work_id is not None
            and not self.termination_evidence_refs
        ):
            raise ValueError("accepted work cancellation needs termination evidence")
        return self


class ActionStatusView(P5Record):
    status: WorkStatus
    acceptance_ref: Ref | None

    @model_validator(mode="after")
    def receipt(self):
        if (self.status.work_id is not None) != (self.acceptance_ref is not None):
            raise ValueError("acceptance receipt required exactly for accepted work")
        return self


class ResourceSummary(P5Record):
    node_id: Id
    label: Text
    provider: ProviderRef
    environment: Id
    controller_state: Literal["unbound", "waiting", "approved", "revoked", "unknown"]
    read_scope_text: Text
    source_snapshot_ref: Ref | None
    check_refs: Refs
    permitted_actions: Ids


class ProcessingRecipient(P5Record):
    name: Text
    purpose: Text
    region_text: Text
    retention_text: Text
    terms_evidence_refs: Refs


class ProcessingDisclosure(P5Record):
    policy_digest: Digest
    recipients: list[ProcessingRecipient]
    copy_scope: Text
    limits: list[Text]
    checked_at: Utc
    status: Literal["qualified", "missing", "stale"]

    @model_validator(mode="after")
    def qualified(self):
        if self.status == "qualified" and (
            not self.recipients or any(not r.terms_evidence_refs for r in self.recipients)
        ):
            raise ValueError("qualified processing requires named recipients and terms evidence")
        return self


class RequiredAction(P5Record):
    kind: Id
    resource_ids: Ids
    enabled: StrictBool
    reason_code: Id | None


class CaseView(P5Record):
    case: ConnectionCase
    state_version: Positive
    last_event_seq: Count
    resources: list[ResourceSummary]
    processing: ProcessingDisclosure | None
    readiness: ConnectionReadiness | None
    pending_action_id: Id | None
    action: ActionStatusView | None
    lifecycle: LifecycleRun | None
    delivery_ref: Ref | None
    required_actions: list[RequiredAction]
    evidence_class: EvidenceClass
    checked_at: Utc

    @model_validator(mode="after")
    def coherent_case(self):
        for value in [self.readiness, self.action.status if self.action else None, self.lifecycle]:
            if value is not None and value.case_id != self.case.case_id:
                raise ValueError("cross-case projection forbidden")
        unique([r.node_id for r in self.resources], "resource summary IDs")
        if self.case.status == "ready" and (
            self.processing is None
            or self.processing.status != "qualified"
            or self.readiness is None
        ):
            raise ValueError("ready case requires processing/readiness evidence")
        return self


class CaseSummary(P5Record):
    case_id: Id
    shop_url: WebUrl
    status: Literal[
        "draft", "waiting_controller", "checking", "setup_needed", "ready", "accepted", "closed"
    ]
    updated_at: Utc


class CaseList(P5Record):
    items: Annotated[list[CaseSummary], Field(max_length=50)]
    next_cursor: Id | None


class DraftCase(P5Record):
    draft_id: Id
    shop_url: WebUrl
    created_at: Utc
    expires_at: Utc
    continuation_ref: Ref
    state: Literal["unclaimed", "claimed", "expired"]


class ProviderIntent(P5Record):
    intent_id: Id
    case_id: Id
    provider_id: Id
    resource_id: Id | None
    purpose: Literal["read_connect", "apply_connect"]
    continuation_ref: Ref
    redirect_url: WebUrl
    expires_at: Utc


class ControllerInvitation(P5Record):
    invitation_id: Id
    case_id: Id
    resource_ids: Ids
    requester_id: Id
    recipient_hint: Text | None
    copy_url: WebUrl
    expires_at: Utc
    status: Literal["pending", "approved", "denied", "expired"]


class CaseEvent(P5Record):
    event_id: Id
    case_id: Id
    sequence: Positive
    state_version: Positive
    kind: Literal[
        "case_changed",
        "readiness_changed",
        "work_changed",
        "lifecycle_changed",
        "delivery_changed",
        "access_changed",
    ]
    payload_ref: Ref
    payload_digest: Digest
    occurred_at: Utc


class PrivateReviewView(P5Record):
    bundle: ReviewBundle
    plan: ActionPlan
    approval_set: ApprovalSet | None
    evidence_summary_refs: Refs
    processing: ProcessingDisclosure
    missing: list[Issue]

    @model_validator(mode="after")
    def exact_review(self):
        if (self.bundle.case_id, self.bundle.run_id, self.bundle.bundle_digest) != (
            self.plan.case_id,
            self.plan.run_id,
            self.plan.review_bundle_digest,
        ):
            raise ValueError("review/plan subject mismatch")
        if self.approval_set is not None and (
            self.approval_set.plan_digest != self.plan.plan_digest
            or self.approval_set.case_id != self.plan.case_id
        ):
            raise ValueError("approval set mismatch")
        return self


class PublicMetric(P5Record):
    name: Text
    value: Text
    evidence_ref: Annotated[StrictStr, Field(pattern=r"^public:[A-Za-z0-9_-]+$")]


class PublicProofView(P5Record):
    public_id: Id
    scope_text: Text
    evidence_class: EvidenceClass
    summary_metrics: list[PublicMetric]
    integrity: Literal["verified", "unverified", "invalid", "unknown"]
    limitations: list[Text]
    checked_at: Utc


class P5Problem(P5Record):
    type: Text
    title: Text
    status: Annotated[Count, Field(ge=400, le=599)]
    detail: Text | None
    instance: Text | None
    code: Id
    request_id: Id
    reason_code: Id
    retry: Literal["never", "status_only", "safe_read", "reauthorise"]
    recovery_action: Id | None
    evidence_refs: Refs


class CreateDraft(P5Record):
    shop_url: WebUrl


class CreateCase(P5Record):
    shop_url: WebUrl


class ClaimDraft(P5Record):
    continuation_ref: Ref


class CreateProviderIntent(P5Record):
    provider_id: Id
    resource_id: Id | None
    purpose: Literal["read_connect", "apply_connect"]


class CreateInvitation(P5Record):
    resource_ids: Annotated[list[Id], Field(min_length=1, max_length=256)]
    recipient_hint: Text | None


class CreateActionIntent(P5Record):
    readiness_id: Id
    readiness_digest: Digest


class StartWorkRequest(P5Record):
    action_id: Id
    readiness_id: Id
    readiness_digest: Digest


class CancelWorkRequest(P5Record):
    cancel_id: Id


class ResumeRunRequest(P5Record):
    expected_state_version: Positive
    scope_digest: Digest


class IssueApplyApproval(P5Record):
    plan_ref: Ref
    plan_digest: Digest
    reviewed_bundle_digest: Digest


class CreateUploadRequest(P5Record):
    intake_collection_limit = 20000
    manifest: Annotated[list[ManifestEntry], Field(min_length=1, max_length=20000)]
    expected_manifest_digest: Digest
    expected_total_bytes: Annotated[Count, Field(le=209715200)]
    binding_epochs: Epochs

    @model_validator(mode="after")
    def exact_manifest(self):
        paths = [e.relative_path.casefold() for e in self.manifest]
        unique(paths, "case-normalized manifest paths")
        kinds = {e.relative_path.casefold(): e.file_type for e in self.manifest}
        for path in paths:
            parts = path.split("/")
            if any(kinds.get("/".join(parts[:i])) == "file" for i in range(1, len(parts))):
                raise ValueError("file/directory path collision")
        if sum(e.bytes for e in self.manifest) != self.expected_total_bytes:
            raise ValueError("manifest total byte mismatch")
        if (
            content_digest([e.model_dump(mode="json") for e in self.manifest])
            != self.expected_manifest_digest
        ):
            raise ValueError("manifest digest mismatch")
        if not self.binding_epochs:
            raise ValueError("upload requires authority epochs")
        return self


class ChunkUploadRequest(P5Record):
    """Multipart metadata only; binary data is a separate bounded part, never a ref."""

    file_path: RelativePath
    offset: Count
    length: Annotated[Positive, Field(le=4194304)]
    sha256: Digest


class FinaliseUploadRequest(P5Record):
    expected_manifest_digest: Digest


class CancelUploadRequest(P5Record):
    pass


class CaseListQuery(P5Record):
    cursor: Id | None
    limit: Annotated[Positive, Field(le=50)]


class CaseEventsQuery(P5Record):
    after: Count | None
