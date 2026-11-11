"""Shared task/model/tool records and ports only. No agent, scheduler or model client."""

from typing import Annotated, Literal, Protocol, runtime_checkable

from pydantic import Field, StrictBool, model_validator

from .plan5_common import (
    Count,
    Digest,
    EvidenceClass,
    Id,
    Ids,
    Issue,
    OciDigest,
    Operation,
    P5Record,
    Positive,
    Ref,
    Refs,
    Role,
    Utc,
    unique,
    validate_dag,
)


class ArtifactDescriptor(P5Record):
    ref: Ref
    case_id: Id
    run_id: Id
    generation: Positive
    schema_id: Id = Field(alias="schema")
    payload_digest: Digest
    byte_count: Count
    subject_digest: Digest
    input_digest: Digest
    derivation_ref: Ref | None
    producer_identity_ref: Ref
    trust: Literal["model_proposal", "collector_observed", "deterministic_result"]
    evidence_class: EvidenceClass
    created_at: Utc
    expires_at: Utc | None


class SubjectManifest(P5Record):
    source_snapshot_refs: Refs
    source_tree_digest: Digest | None
    oci_manifest_digest: OciDigest | None
    config_digest: Digest | None
    runtime_profile_digest: Digest
    scope_digest: Digest


class SubjectDerivation(P5Record):
    derivation_id: Id
    case_id: Id
    run_id: Id
    generation: Positive
    task_id: Id
    parent_refs: Refs
    parent_subject: Digest
    operation: Literal["candidate_patch", "artifact_build", "evidence_derivation"]
    recipe_or_patch_digest: Digest
    output_refs: Refs
    output_subject: Digest
    collector_identity_ref: Ref
    authenticity_ref: Ref


class TaskSpec(P5Record):
    task_id: Id
    role: Role
    operation: Operation
    dependencies: Annotated[list[Id], Field(max_length=32)]
    input_refs: Refs
    expected_schemas: Annotated[list[Id], Field(min_length=1, max_length=16)]
    output_slot: Id
    workspace_ref: Ref | None
    expected_subject: Digest
    allowed_tool_ids: Ids
    required: StrictBool
    output_subject_policy: Literal[
        "same_subject", "candidate_child", "build_from_source", "derived_evidence"
    ]

    @model_validator(mode="after")
    def capability_ceiling(self):
        from .plan5_tools import allowed_tools, output_schemas, role_operations

        if self.operation not in role_operations(self.role):
            raise ValueError("operation not allowed for role")
        if not set(self.allowed_tool_ids) <= allowed_tools(self.role):
            raise ValueError("tool escalation/legacy tool forbidden")
        if not set(self.expected_schemas) <= output_schemas(self.role):
            raise ValueError("output schema not owned by role")
        if self.output_subject_policy == "candidate_child" and self.role != "Grafter":
            raise ValueError("only Grafter can produce candidate child")
        if self.output_subject_policy == "build_from_source" and self.role != "Builder":
            raise ValueError("only Builder can propose build output lineage")
        unique(self.expected_schemas, "output schemas")
        unique(self.allowed_tool_ids, "tool IDs")
        return self


class PlanProposal(P5Record):
    """Untrusted seed/extension proposal; full dependency resolution requires admission."""

    case_id: Id
    run_id: Id
    generation: Positive
    parent_request_id: Id
    tasks: Annotated[list[TaskSpec], Field(min_length=1, max_length=32)]
    reason_refs: Refs

    @model_validator(mode="after")
    def graph(self):
        validate_dag(self.tasks, "task_id", "dependencies", allow_external=True)
        unique([t.output_slot for t in self.tasks], "output slots")
        return self


class TaskContext(P5Record):
    task_ref: Ref
    case_id: Id
    run_id: Id
    generation: Positive
    lease_epoch: Positive
    role: Role
    operation: Operation
    input_refs: Refs
    expected_subject: Digest
    policy_ref: Ref
    prompt_ref: Ref
    allowed_tool_ids: Ids
    expected_schemas: Ids
    budget_ref: Ref
    deadline: Utc
    checkpoint_ref: Ref | None

    @model_validator(mode="after")
    def declared_capabilities(self):
        from .plan5_tools import allowed_tools, output_schemas, role_operations

        if self.operation not in role_operations(self.role):
            raise ValueError("context operation forbidden for role")
        if not set(self.allowed_tool_ids) <= allowed_tools(self.role):
            raise ValueError("context tool capability escalation")
        if not self.expected_schemas or not set(self.expected_schemas) <= output_schemas(self.role):
            raise ValueError("context output ownership mismatch")
        return self


class AgentTask(P5Record):
    task: TaskSpec
    case_id: Id
    run_id: Id
    generation: Positive
    request_id: Id
    input_digest: Digest
    policy_ref: Ref
    policy_digest: Digest
    prompt_ref: Ref
    prompt_digest: Digest
    model_profile_ref: Ref | None
    state: Literal[
        "pending",
        "ready",
        "leased",
        "running",
        "waiting",
        "retry_due",
        "succeeded",
        "held",
        "unknown",
        "failed",
        "cancelled",
    ]
    state_version: Positive
    attempt: Positive
    created_at: Utc
    deadline: Utc
    next_wake_at: Utc | None
    wake_condition_ref: Ref | None
    lease_owner: Id | None
    lease_epoch: Count
    lease_until: Utc | None
    checkpoint_ref: Ref | None
    output_refs: Refs
    issue: Issue | None

    @model_validator(mode="after")
    def state_fields(self):
        claimed = self.lease_epoch > 0
        if claimed != (self.lease_owner is not None and self.lease_until is not None):
            raise ValueError("lease owner/time/epoch must agree")
        if not claimed and (self.lease_owner is not None or self.lease_until is not None):
            raise ValueError("unclaimed task has no lease")
        if self.state in {"leased", "running"} and not claimed:
            raise ValueError("running task needs lease")
        if self.state == "waiting" and (self.wake_condition_ref is None or self.issue is None):
            raise ValueError("waiting requires persisted wake and issue")
        if self.state == "retry_due" and self.next_wake_at is None:
            raise ValueError("retry needs due timer")
        if self.state == "succeeded" and (not self.output_refs or self.issue is not None):
            raise ValueError("success requires outputs and no issue")
        if self.deadline <= self.created_at:
            raise ValueError("task deadline must follow creation")
        return self


class TaskLease(P5Record):
    task_id: Id
    run_id: Id
    generation: Positive
    worker_id: Id
    lease_epoch: Positive
    task_version: Positive
    lease_until: Utc
    context_ref: Ref


class TaskCheckpoint(P5Record):
    task_id: Id
    generation: Positive
    lease_epoch: Positive
    turn: Annotated[Count, Field(le=12)]
    committed_message_refs: Refs
    invocation_refs: Annotated[list[Ref], Field(max_length=24)]
    staged_output_refs: Refs
    context_digest: Digest
    policy_digest: Digest
    budget_reservation_refs: Refs
    wake_condition_ref: Ref | None
    next_step: Literal["model_turn", "await_tool", "validate_output"]
    created_at: Utc


class AgentResult(P5Record):
    task_id: Id
    request_id: Id
    case_id: Id
    run_id: Id
    generation: Positive
    lease_epoch: Positive
    input_digest: Digest
    outcome: Literal["completed", "blocked", "failed", "unknown"]
    output_refs: Refs
    evidence_refs: Refs
    issue: Issue | None
    completed_at: Utc
    authenticity_ref: Ref

    @model_validator(mode="after")
    def completion(self):
        if self.outcome == "completed":
            if not self.output_refs or self.issue is not None:
                raise ValueError("completed requires outputs and no issue")
        elif self.issue is None:
            raise ValueError("noncompletion requires issue")
        return self


class ExecutionProposal(P5Record):
    task_id: Id
    operation: Literal[
        "build_baseline",
        "build_candidate",
        "validate_driver",
        "run_scenario",
        "run_mutant",
        "selfcheck_recipe",
    ]
    subject_ref: Ref
    recipe_ref: Ref
    scenario_ref: Ref | None
    variant: Literal["OLD", "OLD_TWIN", "NEW"] | None
    requested_output_schemas: Ids
    expected_subject: Digest
    evidence_refs: Refs

    @model_validator(mode="after")
    def scenario_fields(self):
        if self.operation in {"run_scenario", "run_mutant"} and (
            self.scenario_ref is None or self.variant is None
        ):
            raise ValueError("scenario/mutant execution needs exact scenario and variant")
        return self


class ModelTurnRequest(P5Record):
    turn_id: Id
    task_id: Id
    generation: Positive
    lease_epoch: Positive
    model_profile_ref: Ref
    context_ref: Ref
    context_digest: Digest
    allowed_tool_ids: Ids
    output_schema: Id
    input_token_cap: Annotated[Positive, Field(le=24000)]
    output_token_cap: Annotated[Positive, Field(le=4000)]
    budget_reservation_ref: Ref
    deadline: Utc


class ToolCall(P5Record):
    call_id: Id
    tool: Id
    arguments_ref: Ref
    arguments_digest: Digest


class ModelTurnResult(P5Record):
    turn_id: Id
    task_id: Id
    kind: Literal["tool_calls", "final", "blocked"]
    calls: Annotated[list[ToolCall], Field(max_length=4)]
    final_artifact_ref: Ref | None
    issue: Issue | None
    usage_receipt_ref: Ref
    provider_receipt_ref: Ref | None

    @model_validator(mode="after")
    def exclusive_form(self):
        unique([c.call_id for c in self.calls], "call IDs")
        valid = {
            "tool_calls": bool(self.calls)
            and self.final_artifact_ref is None
            and self.issue is None,
            "final": not self.calls and self.final_artifact_ref is not None and self.issue is None,
            "blocked": not self.calls
            and self.final_artifact_ref is None
            and self.issue is not None,
        }
        if not valid[self.kind]:
            raise ValueError("model result must have exactly its declared conditional form")
        return self


class ModelTurnStatus(P5Record):
    turn_id: Id
    task_id: Id
    state: Literal["intended", "submitted", "observed", "failed", "unknown"]
    result_ref: Ref | None
    usage_receipt_ref: Ref | None
    checked_at: Utc
    issue: Issue | None

    @model_validator(mode="after")
    def observed(self):
        if self.state == "observed" and (self.result_ref is None or self.usage_receipt_ref is None):
            raise ValueError("observed turn requires result and usage receipt")
        if self.state in {"failed", "unknown"} and self.issue is None:
            raise ValueError("failed/unknown turn requires issue")
        return self


class ToolInvocation(P5Record):
    invocation_id: Id
    task_id: Id
    case_id: Id
    run_id: Id
    generation: Positive
    lease_epoch: Positive
    tool_id: Id
    arguments_ref: Ref
    arguments_digest: Digest
    input_digest: Digest
    capability_ref: Ref
    budget_reservation_ref: Ref
    deadline: Utc
    state: Literal["intended", "submitted", "observed", "denied", "failed", "unknown"]
    result_refs: Refs
    effect_ref: Ref | None
    issue: Issue | None

    @model_validator(mode="after")
    def observed(self):
        if self.state == "observed" and not self.result_refs:
            raise ValueError("observed tool requires result refs")
        if self.state in {"denied", "failed", "unknown"} and self.issue is None:
            raise ValueError("denied/failed/unknown tool requires issue")
        return self


class TaskEvent(P5Record):
    event_id: Id
    case_id: Id
    run_id: Id
    generation: Positive
    task_id: Id | None
    sequence: Positive
    kind: Literal[
        "task_ready",
        "task_changed",
        "tool_observed",
        "approval_changed",
        "cancellation_changed",
        "timer_due",
        "evidence_changed",
    ]
    payload_ref: Ref
    payload_digest: Digest
    causation_id: Id
    correlation_id: Id
    occurred_at: Utc


class RunTaskSnapshot(P5Record):
    case_id: Id
    run_id: Id
    generation: Positive
    state_version: Positive
    tasks: Annotated[list[AgentTask], Field(max_length=32)]
    last_event_seq: Count
    cancellation_ref: Ref | None

    @model_validator(mode="after")
    def coherent_tasks(self):
        unique([t.task.task_id for t in self.tasks], "task IDs")
        if any(
            (t.case_id, t.run_id, t.generation) != (self.case_id, self.run_id, self.generation)
            for t in self.tasks
        ):
            raise ValueError("mixed case/run/generation in task snapshot")
        return self


class WakeCondition(P5Record):
    condition_id: Id
    case_id: Id
    run_id: Id
    generation: Positive
    kind: Literal["timer", "task_result", "authority", "approval", "counterpart", "tool_reconcile"]
    subject_ref: Ref
    expected_digest: Digest | None
    minimum_version: Count
    owner: Id
    due_at: Utc | None
    expires_at: Utc

    @model_validator(mode="after")
    def observable_wake(self):
        if self.kind in {"timer", "tool_reconcile"} and self.due_at is None:
            raise ValueError("timer/reconciliation requires due_at")
        if self.kind == "approval" and self.expected_digest is None:
            raise ValueError("approval wake binds exact plan digest")
        if self.due_at is not None and self.due_at >= self.expires_at:
            raise ValueError("wake expires before due time")
        return self


class ModelBudget(P5Record):
    """Cumulative micro-USD accounting declaration, not a spend authorisation."""

    budget_id: Id
    target_micro_usd: Annotated[Count, Field(le=15000000)]
    ceiling_micro_usd: Annotated[Count, Field(le=20000000)]
    spent_micro_usd: Count
    outstanding_micro_usd: Count
    unknown_micro_usd: Count
    pricing_ref: Ref

    @model_validator(mode="after")
    def cap(self):
        if self.target_micro_usd > self.ceiling_micro_usd or (
            self.spent_micro_usd + self.outstanding_micro_usd + self.unknown_micro_usd
            > self.ceiling_micro_usd
        ):
            raise ValueError("cumulative budget cap exceeded")
        return self


class ControlError(P5Record):
    code: Literal[
        "INVALID",
        "DENIED",
        "NOT_FOUND",
        "CONFLICT",
        "STALE",
        "EXPIRED",
        "CANCELLED",
        "UNKNOWN",
        "BUDGET_EXHAUSTED",
        "MISSING_EVIDENCE",
        "UNSUPPORTED",
    ]
    retry_class: Literal["none", "safe_read", "reconcile", "reauthorise"]
    evidence_refs: Refs


class ControlFailure(Exception):
    """Only the closed error record crosses a service boundary; no raw input text."""

    def __init__(self, error: ControlError):
        self.error = error
        super().__init__(error.code)


@runtime_checkable
class TaskControl(Protocol):
    def seed(self, run_ref: Ref, proposal: PlanProposal, key: Id) -> list[AgentTask]: ...
    def extend(
        self, run_ref: Ref, expected_run_version: Positive, proposal: PlanProposal, key: Id
    ) -> list[AgentTask]: ...
    def claim(self, worker_id: Id, now: Utc) -> TaskLease | None: ...
    def load(self, lease: TaskLease) -> AgentTask: ...
    def renew(self, lease: TaskLease, now: Utc) -> TaskLease: ...
    def checkpoint(self, lease: TaskLease, value: TaskCheckpoint) -> Ref: ...
    def begin_tool(self, lease: TaskLease, value: ToolInvocation) -> ToolInvocation: ...
    def observe_tool(
        self, lease: TaskLease, invocation_id: Id, result_ref: Ref
    ) -> ToolInvocation: ...
    def finish(self, lease: TaskLease, result: AgentResult) -> AgentTask: ...
    def wait(self, lease: TaskLease, issue: Issue, condition: WakeCondition) -> AgentTask: ...
    def snapshot(self, run_ref: Ref) -> RunTaskSnapshot: ...
    def cancel(self, run_ref: Ref, cancellation_ref: Ref) -> RunTaskSnapshot: ...


@runtime_checkable
class ArtifactPort(Protocol):
    def resolve(self, ref: Ref, task_context: Ref) -> ArtifactDescriptor: ...
    def stage(self, task_id: Id, schema: Id, payload_ref: Ref, subject: Digest) -> Ref: ...


@runtime_checkable
class ModelPort(Protocol):
    def turn(self, request: ModelTurnRequest) -> ModelTurnResult: ...
    def reconcile(self, turn_id: Id) -> ModelTurnStatus: ...


@runtime_checkable
class ToolPort(Protocol):
    def invoke(self, invocation: ToolInvocation) -> ToolInvocation: ...
    def reconcile(self, invocation_id: Id) -> ToolInvocation: ...
