"""Validate task leases before constructing model context."""

from datetime import UTC, datetime

from goldgraft_contracts.agent_runtime import (
    AgentTask,
    ArtifactPort,
    ControlError,
    ControlFailure,
    TaskContext,
    TaskLease,
)
from goldgraft_contracts.plan5_common import canonical_bytes, content_digest
from goldgraft_contracts.work_package import OmissionManifest, SourceSnapshot

from .ports import ModelPolicy

# Largest declared real-model cumulative ceiling a ticket may carry: $13, the active cap Aditya
# approved on 12 November 2026 ("yes 13."; recorded as cap authority 4a6c4411… in the ledger) for
# agent grounding and Phase 5. Earlier: the $10 all-13-agents phase (11 November), $0.05 and $0.50
# checkpoints. The gateway ledger remains the binding money authority; this is a second
# fail-closed bound.
REAL_MODEL_CEILING_MICRO_USD = 13000000


def reject(code):
    raise ControlFailure(ControlError(code=code, retry_class="none", evidence_refs=[]))


def build_context(
    task: AgentTask,
    lease: TaskLease,
    artifacts: ArtifactPort | None,
    *,
    now: datetime | None = None,
) -> TaskContext:
    now = datetime.now(UTC) if now is None else now

    expected = (
        task.task.task_id,
        task.run_id,
        task.generation,
        task.lease_epoch,
        task.lease_owner,
        task.state_version,
        task.lease_until,
    )
    supplied = (
        lease.task_id,
        lease.run_id,
        lease.generation,
        lease.lease_epoch,
        lease.worker_id,
        lease.task_version,
        lease.lease_until,
    )

    if (
        supplied != expected
        or task.state not in {"leased", "running"}
        or lease.lease_until <= now
        or task.deadline <= now
    ):
        raise ControlFailure(
            ControlError(
                code="STALE",
                retry_class="none",
                evidence_refs=[],
            )
        )

    if artifacts is not None:
        for ref in task.task.input_refs:
            artifact = artifacts.resolve(ref, lease.context_ref)
            expected_scope = (
                task.case_id,
                task.run_id,
                task.generation,
            )
            actual_scope = (
                artifact.case_id,
                artifact.run_id,
                artifact.generation,
            )
            if actual_scope != expected_scope:
                raise ControlFailure(
                    ControlError(
                        code="DENIED",
                        retry_class="none",
                        evidence_refs=[],
                    )
                )
            if artifact.expires_at is not None and artifact.expires_at <= now:
                reject("EXPIRED")
            bound_subject = artifact.subject_digest == task.task.expected_subject
            if not bound_subject and hasattr(artifacts, "validate_input_subject"):
                bound_subject = artifacts.validate_input_subject(lease, artifact)
            if artifact.ref != ref or not bound_subject:
                reject("DENIED")
            if artifact.schema_id == "SourceSnapshot/1":
                if artifact.trust != "collector_observed" or not hasattr(
                    artifacts, "read_artifact"
                ):
                    reject("MISSING_EVIDENCE")
                source = SourceSnapshot.model_validate_json(artifacts.read_artifact(ref, lease))
                if source.snapshot_id != ref or source.case_id != task.case_id:
                    reject("DENIED")
                if source.completeness != "complete_for_declared_scope":
                    reject("MISSING_EVIDENCE")
                omitted = artifacts.resolve(source.omission_manifest_ref, lease.context_ref)
                if (
                    omitted.schema_id != "OmissionManifest/1"
                    or omitted.trust != "collector_observed"
                    or (omitted.case_id, omitted.run_id, omitted.generation, omitted.subject_digest)
                    != (
                        task.case_id,
                        task.run_id,
                        task.generation,
                        task.task.expected_subject,
                    )
                    or (omitted.expires_at is not None and omitted.expires_at <= now)
                ):
                    reject("DENIED")
                omissions = OmissionManifest.model_validate_json(
                    artifacts.read_artifact(source.omission_manifest_ref, lease)
                )
                if any(item.required_for_scope for item in omissions.items):
                    reject("MISSING_EVIDENCE")

    if artifacts is None or not hasattr(artifacts, "ticket"):
        reject("MISSING_EVIDENCE")
    ticket = artifacts.ticket(lease)
    ctx = TaskContext.model_validate(ticket.context.model_dump(mode="json"))
    if not ticket.authority_current:
        reject("DENIED")
    if (ticket.task_id, ctx.case_id, ctx.run_id, ctx.generation, ctx.lease_epoch) != (
        task.task.task_id,
        task.case_id,
        task.run_id,
        task.generation,
        lease.lease_epoch,
    ):
        reject("STALE")
    if (
        ctx.role != task.task.role
        or ctx.operation != task.task.operation
        or ctx.input_refs != task.task.input_refs
        or ctx.expected_subject != task.task.expected_subject
        or ctx.allowed_tool_ids != task.task.allowed_tool_ids
        or ctx.expected_schemas != task.task.expected_schemas
        or ticket.policy_digest != task.policy_digest
        or ticket.prompt_digest != task.prompt_digest
        or ctx.policy_ref != task.policy_ref
        or ctx.prompt_ref != task.prompt_ref
        or ctx.deadline > task.deadline
        or ctx.deadline <= now
    ):
        reject("DENIED")
    operation, accepted = ticket.operation, ticket.acceptance
    if operation is None:
        reject("MISSING_EVIDENCE")
    if (
        accepted.case_id != task.case_id
        or operation.work_id != accepted.work_id
        or operation.generation != task.generation
        or operation.kind != "BASELINE_READ"
        or operation.result != "verified"
        or not operation.evidence_refs
        or operation.work_package_digest != accepted.work_package_digest
        or operation.resource_graph_digest != accepted.resource_graph_digest
        or operation.scope_digest != accepted.scope_digest
        or operation.source_manifest_digest != accepted.source_manifest_digest
        or operation.observed_digest != accepted.source_manifest_digest
    ):
        reject("MISSING_EVIDENCE")
    if ticket.budget is None or ctx.budget_ref != ticket.budget.budget_id:
        reject("BUDGET_EXHAUSTED")
    if ticket.evidence_class != "scripted" or ticket.budget.ceiling_micro_usd != 0:
        if ticket.evidence_class != "real_model" or not hasattr(artifacts, "model_admission"):
            reject("UNSUPPORTED")
        policy = artifacts.model_admission(lease)
        if (
            not isinstance(policy, ModelPolicy)
            or policy.budget_reservation_ref != ctx.budget_ref
            or ticket.budget.ceiling_micro_usd > REAL_MODEL_CEILING_MICRO_USD
        ):
            reject("DENIED")
    if content_digest(task.task.input_refs) != task.input_digest:
        reject("DENIED")
    if len(canonical_bytes(ctx)) > 24000:
        reject("INVALID")
    return ctx
