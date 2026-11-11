"""Shared delivery/state/exit declarations and ports; no provider or coordinator engine."""

from typing import Annotated, Literal, Protocol, runtime_checkable

from pydantic import Field, StrictBool, model_validator

from .plan5_common import (
    DeliveryOperation,
    Digest,
    Epochs,
    GitCommit,
    Id,
    Ids,
    Issue,
    OciDigest,
    P5Record,
    Positive,
    Ref,
    Refs,
    Text,
    Utc,
    content_digest,
    unique,
    validate_dag,
)

LifecycleStage = Literal[
    "BASELINE_VERIFY",
    "BASELINE_RUN",
    "CANDIDATE_READY",
    "VALIDATING",
    "REVIEW_READY",
    "AWAITING_APPLY",
    "PUBLISHING",
    "MERGING",
    "DEPLOY_PREPARED",
    "DEPLOYING",
    "OBSERVING",
    "FINALISING",
    "EXITING",
    "COMPLETE",
    "HELD",
    "FAILED_SAFE",
    "INCIDENT_UNKNOWN",
]
EffectOperation = Literal[
    "preserve_state",
    "publish_artifact",
    "publish_source",
    "merge_protected",
    "apply_configuration",
    "deploy_exact",
    "finalise",
    "prepare_exit",
    "run_exit",
    "read_exit_evidence",
    "revoke_exit_evidence",
    "configure_ingress",
    "restart_target",
    "revoke_grant",
    "delete_temporary",
    "stop_worker",
    "financial_compensation",
]


class LifecycleRun(P5Record):
    run_id: Id
    case_id: Id
    work_id: Id
    generation: Positive
    work_package_ref: Ref
    work_package_digest: Digest
    resource_graph_digest: Digest
    scope_digest: Digest
    stage: LifecycleStage
    attempt: Positive
    evidence_refs: Refs
    active_effect_refs: Refs
    updated_at: Utc


class LifecycleWorkRequest(P5Record):
    request_id: Id
    run_id: Id
    generation: Positive
    operation_kind: Literal[
        "build_baseline",
        "run_baseline",
        "validate_candidate",
        "build_candidate",
        "run_scenario",
        "run_mutant",
        "validate_driver",
        "selfcheck_recipe",
    ]
    package_ref: Ref
    package_digest: Digest
    input_artifact_refs: Refs
    expected_output_schema: Id
    policy_digest: Digest
    runtime_profile_digest: Digest
    authority_binding_epochs: Epochs
    budget_ref: Ref
    deadline: Utc
    forbidden_effect_codes: Ids


class LifecycleWorkResult(P5Record):
    request_id: Id
    run_id: Id
    generation: Positive
    worker_identity_ref: Ref
    inputs_digest: Digest
    outcome: Literal["completed", "failed", "blocked", "unknown"]
    source_unchanged: StrictBool
    output_artifact_refs: Refs
    evidence_refs: Refs
    completed_at: Utc
    limitation_codes: Ids
    authenticity_ref: Ref

    @model_validator(mode="after")
    def outputs(self):
        if self.outcome == "completed" and (
            not self.output_artifact_refs or not self.evidence_refs
        ):
            raise ValueError("completed worker requires observed output/evidence")
        return self


class ReviewBundle(P5Record):
    bundle_id: Id
    case_id: Id
    run_id: Id
    work_package_digest: Digest
    baseline_snapshot_refs: Refs
    candidate_snapshot_refs: Refs
    patch_digest: Digest
    artifact_digest: OciDigest
    effective_config_digest: Digest
    scenario_result_refs: Refs
    domain_rule_result_refs: Refs
    security_result_refs: Refs
    unsupported_paths: Ids
    missing_evidence_refs: Refs
    recovery_plan_ref: Ref
    proposed_apply_plan_ref: Ref
    bundle_digest: Digest
    created_at: Utc


class ApplyApproval(P5Record):
    approval_id: Id
    case_id: Id
    controller_id: Id
    action_group_id: Id
    authority_binding_epochs: Epochs
    graph_digest: Digest
    scope_digest: Digest
    reviewed_bundle_digest: Digest
    baseline_digest: Digest
    candidate_digest: Digest
    patch_digest: Digest
    artifact_digest: OciDigest
    config_digest: Digest
    delivery_route: Literal["git_protected", "direct_artifact"]
    source_snapshot_digests: list[Digest]
    source_head: GitCommit | None
    source_base: GitCommit | None
    publication_destination_refs: Refs
    trigger_chain_digest: Digest
    target_resources: Ids
    allowed_actions: list[EffectOperation]
    state_plan_digest: Digest
    recovery_plan_digest: Digest
    policy_digest: Digest
    issued_at: Utc
    expires_at: Utc
    generation: Positive
    action_plan_digest: Digest
    authority_refs: Refs
    revoked_at: Utc | None

    @model_validator(mode="after")
    def route_binding(self):
        if self.delivery_route == "git_protected":
            if self.source_head is None or self.source_base is None:
                raise ValueError("Git route requires real provider heads")
        elif self.source_head is not None or self.source_base is not None:
            raise ValueError("direct artifact route has no Git heads")
        if not (
            self.authority_binding_epochs
            and self.authority_refs
            and self.target_resources
            and self.allowed_actions
            and self.publication_destination_refs
        ):
            raise ValueError("approval requires resource authority, actions and destinations")
        return self


class EffectIntent(P5Record):
    effect_id: Id
    action_group_id: Id
    case_id: Id
    run_id: Id
    generation: Positive
    actor_id: Id
    operation: EffectOperation
    resource_id: Id
    environment_id: Id
    request_digest: Digest
    approval_set_id: Id
    plan_digest: Digest
    slot_id: Id
    resource_epochs: Epochs
    expected_version: Id
    effect_class: Literal["E0", "E1", "E2", "E3", "EU"]
    provider_idempotency_ref: Ref | None
    created_at: Utc
    state: Literal[
        "intended", "submitted", "acknowledged", "observed", "failed", "unknown", "compensated"
    ]
    provider_receipt_ref: Ref | None
    reconciliation_ref: Ref | None

    @model_validator(mode="after")
    def financial_authority(self):
        if self.operation == "financial_compensation" and self.effect_class != "E3":
            raise ValueError("financial compensation requires separate E3 authority")
        if self.state == "observed" and self.provider_receipt_ref is None:
            raise ValueError("observed effect requires receipt")
        return self


class BaselineEvidence(P5Record):
    run_id: Id
    package_digest: Digest
    variant: Literal["OLD", "OLD_TWIN"]
    immutable_source_digest: Digest
    runtime_digest: Digest
    dependency_digest: Digest
    seed_digest: Digest
    scenario_results_ref: Ref
    observed_defects_ref: Ref
    actual_provider_evidence_ref: Ref
    skipped_required: Ids
    outcome: Literal["reproduced", "reproduced_with_defects", "failed", "unknown"]

    @model_validator(mode="after")
    def required_flows(self):
        if self.outcome.startswith("reproduced") and self.skipped_required:
            raise ValueError("required flows cannot be skipped for reproduced outcome")
        return self


class DeploymentObservation(P5Record):
    effect_id: Id
    case_id: Id
    provider: Id
    resource_id: Id
    environment_id: Id
    submitted_artifact_digest: OciDigest
    observed_artifact_digest: OciDigest | None
    observed_config_digest: Digest | None
    provider_deploy_id: Id | None
    provider_status: Text
    current_runtime_evidence_refs: Refs
    checked_at: Utc
    outcome: Literal["pending", "verified", "failed", "unknown"]

    @model_validator(mode="after")
    def observed_subject(self):
        if self.outcome == "verified" and (
            self.observed_artifact_digest != self.submitted_artifact_digest
            or self.observed_config_digest is None
            or not self.current_runtime_evidence_refs
        ):
            raise ValueError("verified deploy requires exact observed image/config/evidence")
        return self


class RecoveryPlan(P5Record):
    plan_id: Id
    case_id: Id
    baseline_refs: Refs
    affected_effect_refs: Refs
    state_compatibility_ref: Ref
    original_transaction_routes_ref: Ref
    required_current_authority: Ids
    reversible_effects: Ids
    compensatable_effects: Ids
    irreversible_effects: Ids
    unknown_effects: Ids
    chosen_route: Literal["code_cutback", "config_cutback", "forward_repair", "safe_hold"]
    restore_preconditions_ref: Ref
    verification_case_refs: Refs
    plan_digest: Digest


class ExitItem(P5Record):
    item_id: Id
    owner: Id
    required_for_exit: StrictBool
    state: Literal[
        "preserved",
        "local_denied",
        "termination_pending",
        "revocation_pending",
        "deleted_active",
        "backup_pending",
        "held",
        "exported_unrecallable",
        "confirmed",
        "unknown",
    ]
    evidence_refs: Refs


class ExitManifest(P5Record):
    exit_id: Id
    case_id: Id
    run_id: Id
    merchant_assets_ref: Ref
    temporary_assets_ref: Ref
    legacy_obligations_ref: Ref
    persistent_runtime_evidence_refs: Refs
    post_denial_observation_refs: Refs
    cleanup_items: list[ExitItem]
    outcome: Literal["complete", "pending", "failed_safe", "unknown"]

    @model_validator(mode="after")
    def cleanup_known(self):
        unique([x.item_id for x in self.cleanup_items], "exit items")
        if self.outcome == "complete" and (
            not self.persistent_runtime_evidence_refs
            or not self.post_denial_observation_refs
            or any(
                x.required_for_exit
                and (
                    x.state not in {"preserved", "confirmed", "deleted_active"}
                    or not x.evidence_refs
                )
                for x in self.cleanup_items
            )
        ):
            raise ValueError("required cleanup/current post-denial evidence missing")
        return self


class TargetKey(P5Record):
    provider_id: Id
    account_id: Id
    environment_id: Id
    resource_kind: Id
    resource_id: Id

    @model_validator(mode="after")
    def no_wildcards(self):
        if any("*" in x for x in self.model_dump().values()):
            raise ValueError("target wildcard forbidden")
        return self


def canonical_target_id(target: TargetKey) -> str:
    """Physical-target identity deliberately excludes tenant/case/run."""
    return content_digest(target)


class TargetReservation(P5Record):
    reservation_id: Id
    case_id: Id
    run_id: Id
    action_plan_ref: Ref
    target_keys: list[TargetKey]
    resource_epochs: Epochs
    lease_until: Utc
    expected_version_refs: Refs
    unresolved_effect_refs: Refs
    state: Literal["held", "reconciling", "releasable", "released"]

    @model_validator(mode="after")
    def target_epochs(self):
        keys = [canonical_target_id(t) for t in self.target_keys]
        unique(keys, "canonical targets")
        if not keys or set(keys) != self.resource_epochs.keys():
            raise ValueError("canonical targets/epochs mismatch")
        if self.state in {"released", "releasable"} and self.unresolved_effect_refs:
            raise ValueError("unknown effects retain reservation")
        return self


class EffectSlot(P5Record):
    slot_id: Id
    operation: EffectOperation
    target_key: TargetKey
    effect_class: Literal["E0", "E1", "E2", "E3"]
    depends_on: Annotated[list[Id], Field(max_length=32)]
    artifact_digest: OciDigest | None
    config_digest: Digest | None
    state_plan_digest: Digest | None
    trigger_digest: Digest
    required_authority_refs: Refs
    required_controller_ids: Ids
    expected_version_ref: Ref
    cardinality: Annotated[Positive, Field(le=1)]
    recovery_branch_ref: Ref | None

    @model_validator(mode="after")
    def authority(self):
        if not self.required_authority_refs or not self.required_controller_ids:
            raise ValueError("effect slot requires independent authority/controllers")
        if self.operation == "financial_compensation" and self.effect_class != "E3":
            raise ValueError("compensation requires E3 slot")
        return self


class ActionPlan(P5Record):
    plan_id: Id
    case_id: Id
    run_id: Id
    generation: Positive
    graph_digest: Digest
    scope_digest: Digest
    review_bundle_digest: Digest
    policy_digest: Digest
    slots: Annotated[list[EffectSlot], Field(min_length=1, max_length=32)]
    recovery_plan_ref: Ref
    state_plan_ref: Ref
    finalisation_plan_ref: Ref
    exit_plan_ref: Ref
    budget_ref: Ref
    expires_at: Utc
    plan_digest: Digest

    @model_validator(mode="after")
    def slots_dag(self):
        validate_dag(self.slots, "slot_id", "depends_on")
        return self


class ApplyAuthority(P5Record):
    authority_id: Id
    controller_id: Id
    delegate_id: Id | None
    target_key: TargetKey
    actions: list[EffectOperation]
    role_evidence_refs: Refs
    grant_epoch: Positive
    issued_at: Utc
    expires_at: Utc
    revoked_at: Utc | None


class ApprovalSet(P5Record):
    approval_set_id: Id
    case_id: Id
    run_id: Id
    generation: Positive
    plan_digest: Digest
    required_controller_ids: Ids
    approval_refs: Refs
    authority_epochs: Epochs
    checked_at: Utc
    state: Literal["complete", "missing", "stale", "revoked"]

    @model_validator(mode="after")
    def complete_shape(self):
        unique(self.required_controller_ids, "controller IDs")
        unique(self.approval_refs, "approval refs")
        if self.state == "complete" and not (
            self.required_controller_ids and self.approval_refs and self.authority_epochs
        ):
            raise ValueError("complete approval set requires controllers/approvals/epochs")
        return self


class StateCutover(P5Record):
    cutover_id: Id
    case_id: Id
    run_id: Id
    generation: Positive
    writer_inventory_ref: Ref
    handler_inventory_ref: Ref
    ingress_ref: Ref
    origin_route_ref: Ref
    admission_ref: Ref
    drain_evidence_refs: Refs
    fence_epochs: Epochs
    high_water_ref: Ref
    export_manifest_ref: Ref
    restore_manifest_ref: Ref
    replay_manifest_ref: Ref
    state_digest: Digest
    schema_digest: Digest
    pending_external_effect_refs: Refs
    evidence_refs: Refs
    outcome: Literal[
        "prepared", "fenced", "exported", "restored", "replayed", "verified", "held", "unknown"
    ]

    @model_validator(mode="after")
    def verified(self):
        if self.outcome == "verified" and (
            not self.evidence_refs or not self.fence_epochs or self.pending_external_effect_refs
        ):
            raise ValueError("verified state requires fence/evidence and no unknown effects")
        return self


class ArtifactBuild(P5Record):
    build_id: Id
    case_id: Id
    run_id: Id
    generation: Positive
    source_snapshot_refs: Refs
    source_tree_digest: Digest
    recipe_digest: Digest
    dependency_digest: Digest
    build_config_digest: Digest
    platform: Literal["linux/amd64"]
    oci_manifest_digest: OciDigest
    export_tar_digest: Digest
    layer_digests: list[OciDigest]
    runtime_profile_digest: Digest
    exact_image_test_refs: Refs
    leak_scan_refs: Refs
    provenance_ref: Ref
    collector_identity_ref: Ref
    authenticity_ref: Ref
    outcome: Literal["built", "tested", "held", "failed", "unknown"]

    @model_validator(mode="after")
    def tested(self):
        if not self.source_snapshot_refs or not self.layer_digests:
            raise ValueError("build must identify source and layers")
        if self.outcome == "tested" and (not self.exact_image_test_refs or not self.leak_scan_refs):
            raise ValueError("tested image requires actual exact-image tests and leak scans")
        return self


class Asset(P5Record):
    asset_id: Id
    kind: Literal[
        "source",
        "image",
        "registry",
        "runtime",
        "config",
        "state",
        "credential",
        "callback",
        "origin_handler",
        "grant",
        "worker",
        "copy",
        "record",
        "exit_executor",
    ]
    ownership: Literal["merchant", "shared_service", "exclusive_run"]
    target_key: TargetKey
    required_for_operation: StrictBool
    active_reference_refs: Refs
    desired: Literal["keep", "deny_revoke", "delete", "retain_policy"]
    authority_refs: Refs
    evidence_refs: Refs

    @model_validator(mode="after")
    def preserve_operational(self):
        if self.required_for_operation and self.desired != "keep":
            raise ValueError("required merchant operational asset must remain")
        if self.ownership != "exclusive_run" and self.desired in {"delete", "deny_revoke"}:
            raise ValueError("shared/merchant asset cleanup requires separate wider-impact plan")
        return self


class AssetManifest(P5Record):
    manifest_id: Id
    case_id: Id
    run_id: Id
    assets: list[Asset]
    final_artifact_digest: OciDigest
    final_config_digest: Digest
    legacy_obligations_ref: Ref
    manifest_digest: Digest

    @model_validator(mode="after")
    def asset_ids(self):
        unique([a.asset_id for a in self.assets], "asset IDs")
        return self


class FinalisationPlan(P5Record):
    finalisation_id: Id
    case_id: Id
    run_id: Id
    generation: Positive
    desired_asset_manifest_ref: Ref
    dependency_check_refs: Refs
    candidate_change_required: StrictBool
    final_candidate_ref: Ref | None
    validation_request_refs: Refs
    required_action_slot_ids: Ids
    independence_criteria_refs: Refs
    plan_digest: Digest

    @model_validator(mode="after")
    def changed_candidate(self):
        if self.candidate_change_required and self.final_candidate_ref is None:
            raise ValueError("changed final candidate requires new exact reference")
        return self


class ExitCheckPlan(P5Record):
    exit_plan_id: Id
    case_id: Id
    run_id: Id
    generation: Positive
    reservation_ref: Ref
    executor_identity_ref: Ref
    trusted_code_digest: Digest
    final_artifact_digest: OciDigest
    final_config_digest: Digest
    state_digest: Digest
    criteria_refs: Refs
    allowed_restart_count: Annotated[Positive, Field(le=1)]
    recovery_plan_ref: Ref
    budget_ref: Ref
    deadline: Utc
    private_evidence_destination_ref: Ref
    evidence_read_authority_ref: Ref
    failure_route_ref: Ref
    authority_refs: Refs
    plan_digest: Digest


class DeliverySnapshot(P5Record):
    case_id: Id
    run_id: Id
    generation: Positive
    state_version: Positive
    lifecycle_ref: Ref
    graph_ref: Ref
    review_ref: Ref | None
    action_plan_ref: Ref | None
    approval_set_ref: Ref | None
    reservation_ref: Ref | None
    state_cutover_ref: Ref | None
    deployment_ref: Ref | None
    final_asset_manifest_ref: Ref | None
    exit_plan_ref: Ref | None
    exit_manifest_ref: Ref | None
    current_evidence_refs: Refs
    pending_effect_refs: Refs
    cancellation_ref: Ref | None
    issue: Issue | None
    checked_at: Utc


class DeliveryDecision(P5Record):
    case_id: Id
    run_id: Id
    generation: Positive
    expected_state_version: Positive
    kind: Literal["request", "wait", "hold", "incident", "complete"]
    operation: DeliveryOperation | None
    input_refs: Refs
    existing_effect_ref: Ref | None
    slot_id: Id | None
    reason_code: Id
    next_wake_at: Utc | None

    @model_validator(mode="after")
    def conditional_request(self):
        consequential = {
            "publish_artifact",
            "publish_source",
            "merge_protected",
            "apply_configuration",
            "deploy_exact",
            "preserve_state",
            "finalise",
            "run_exit",
            "revoke_exit_evidence",
        }
        if self.kind != "request":
            if (
                self.operation is not None
                or self.slot_id is not None
                or self.existing_effect_ref is not None
            ):
                raise ValueError("nonrequest cannot dispatch operation/slot/effect")
        elif self.operation is None or not self.input_refs:
            raise ValueError("request requires operation and inputs")
        elif self.operation in consequential and self.slot_id is None:
            raise ValueError("consequential operation requires approved slot")
        if self.operation == "reconcile_effect" and (
            self.existing_effect_ref is None or self.slot_id is not None
        ):
            raise ValueError("reconcile original effect; no new slot")
        if self.operation != "reconcile_effect" and self.existing_effect_ref is not None:
            raise ValueError("only reconciliation refers existing effect")
        return self


class PredicateResult(P5Record):
    predicate: Literal[
        "can_review", "can_prepare_apply", "can_submit_slot", "upgrade_verified", "exit_complete"
    ]
    slot_id: Id | None
    status: Literal["pass", "missing", "stale", "failed", "unknown"]
    evidence_refs: Refs
    subject_digest: Digest
    checked_at: Utc

    @model_validator(mode="after")
    def exact_slot(self):
        if (self.predicate == "can_submit_slot") != (self.slot_id is not None):
            raise ValueError("slot predicate requires exact slot, other predicates have none")
        if self.status == "pass" and not self.evidence_refs:
            raise ValueError("predicate pass requires evidence")
        return self


class ResolvedDeliveryView(P5Record):
    snapshot: DeliverySnapshot
    lifecycle: LifecycleRun
    delivery_route: Literal["git_protected", "direct_artifact"]
    review: ReviewBundle | None
    plan: ActionPlan | None
    approvals: ApprovalSet | None
    reservation: TargetReservation | None
    state_cutover: StateCutover | None
    deployment: DeploymentObservation | None
    final_assets: AssetManifest | None
    exit_plan: ExitCheckPlan | None
    exit_manifest: ExitManifest | None
    predicate_results: list[PredicateResult]

    @model_validator(mode="after")
    def coherent_records(self):
        s = self.snapshot
        for name in [
            "lifecycle",
            "review",
            "plan",
            "approvals",
            "reservation",
            "state_cutover",
            "deployment",
            "final_assets",
            "exit_plan",
            "exit_manifest",
        ]:
            value = getattr(self, name)
            if value is None:
                continue
            for field in ["case_id", "run_id", "generation"]:
                if hasattr(value, field) and getattr(value, field) != getattr(s, field):
                    raise ValueError("mixed delivery record identity/generation")
        if self.delivery_route == "direct_artifact" and self.lifecycle.stage == "MERGING":
            raise ValueError("direct artifact route cannot merge")
        if (
            self.plan is not None
            and self.approvals is not None
            and self.plan.plan_digest != self.approvals.plan_digest
        ):
            raise ValueError("approval plan mismatch")
        unique([(p.predicate, p.slot_id) for p in self.predicate_results], "predicate slots")
        return self


class LifecycleWorkRequestReceipt(P5Record):
    request_id: Id
    run_id: Id
    generation: Positive
    accepted_at: Utc
    request_digest: Digest


class PendingResult(P5Record):
    request_id: Id
    state: Literal["queued", "running", "waiting", "unknown"]
    evidence_refs: Refs
    checked_at: Utc


@runtime_checkable
class DeliveryPort(Protocol):
    def submit(self, decision: DeliveryDecision, request_id: Id) -> LifecycleWorkRequestReceipt: ...
    def status(self, request_id: Id) -> LifecycleWorkResult | PendingResult: ...
    def snapshot(self, run_ref: Ref) -> DeliverySnapshot: ...
