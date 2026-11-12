/* Generated from Python contracts. Do not edit. */

export type ActionId = string;
export type ActorId = string;
export type CaseId = string;
export type CreatedAt = string;
export type ExpiresAt = string;
export type ReadinessDigest = string;
export type ReadinessId = string;
export type BudgetRef = string;
export type CaseId1 = string;
export type ExitPlanRef = string;
export type ExpiresAt1 = string;
export type FinalisationPlanRef = string;
export type Generation = number;
export type GraphDigest = string;
export type PlanDigest = string;
export type PlanId = string;
export type PolicyDigest = string;
export type RecoveryPlanRef = string;
export type ReviewBundleDigest = string;
export type RunId = string;
export type ScopeDigest = string;
/**
 * @minItems 1
 * @maxItems 32
 */
export type Slots = [EffectSlot, ...EffectSlot[]];
export type ArtifactDigest = string | null;
export type Cardinality = number;
export type ConfigDigest = string | null;
/**
 * @maxItems 32
 */
export type DependsOn = string[];
export type EffectClass = "E0" | "E1" | "E2" | "E3";
export type ExpectedVersionRef = string;
export type Operation =
  | "preserve_state"
  | "publish_artifact"
  | "publish_source"
  | "merge_protected"
  | "apply_configuration"
  | "deploy_exact"
  | "finalise"
  | "prepare_exit"
  | "run_exit"
  | "read_exit_evidence"
  | "revoke_exit_evidence"
  | "configure_ingress"
  | "restart_target"
  | "revoke_grant"
  | "delete_temporary"
  | "stop_worker"
  | "financial_compensation";
export type RecoveryBranchRef = string | null;
/**
 * @maxItems 256
 */
export type RequiredAuthorityRefs = string[];
/**
 * @maxItems 256
 */
export type RequiredControllerIds = string[];
export type SlotId = string;
export type StatePlanDigest = string | null;
export type AccountId = string;
export type EnvironmentId = string;
export type ProviderId = string;
export type ResourceId = string;
export type ResourceKind = string;
export type TriggerDigest = string;
export type StatePlanRef = string;
export type AcceptanceRef = string | null;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "WorkStatus".
 */
export type WorkStatus =
  | {
      action_id: ActionId1;
      case_id: CaseId2;
      checked_at: CheckedAt;
      evidence_refs: EvidenceRefs;
      generation: Generation1;
      last_event_seq: LastEventSeq;
      state: State;
      work_id: WorkId;
    }
  | {
      action_id: ActionId1;
      case_id: CaseId2;
      checked_at: CheckedAt;
      evidence_refs: EvidenceRefs;
      generation: Generation1;
      last_event_seq: LastEventSeq;
      state: State1;
      work_id: string;
    }
  | {
      action_id: ActionId1;
      case_id: CaseId2;
      checked_at: CheckedAt;
      evidence_refs: EvidenceRefs1;
      generation: number;
      last_event_seq: LastEventSeq;
      state: State2;
      work_id: string;
    }
  | {
      action_id: ActionId1;
      case_id: CaseId2;
      checked_at: CheckedAt;
      evidence_refs: EvidenceRefs2;
      generation: Generation1;
      last_event_seq: LastEventSeq;
      state: State3;
      work_id: string;
    };
export type ActionId1 = string;
export type CaseId2 = string;
export type CheckedAt = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs = string[];
export type Generation1 = number | null;
export type LastEventSeq = number;
export type State = "submitting" | "held" | "unknown" | "cancellation_pending" | "cancelled" | "failed";
export type WorkId = string | null;
export type State1 = "accepted" | "queued" | "provisioning";
/**
 * @minItems 1
 * @maxItems 256
 */
export type EvidenceRefs1 = [string, ...string[]];
export type State2 = "operation_started";
/**
 * @minItems 1
 * @maxItems 256
 */
export type EvidenceRefs2 = [string, ...string[]];
export type State3 = "stopped";
/**
 * @maxItems 256
 */
export type Limitations = string[];
/**
 * @maxItems 256
 */
export type Operations = (
  | "source_read"
  | "deployment_read"
  | "artifact_identity"
  | "route_read"
  | "config_evidence"
  | "controller_role"
  | "revocation_observation"
)[];
export type AccountId1 = string | null;
export type AdapterVersion = string;
export type ProviderId1 = string;
export type Qualification = "proposed" | "implemented" | "account_tested" | "correspondence_qualified" | "e2e_tested";
/**
 * @maxItems 256
 */
export type QualificationRefs = string[];
export type Basis = "observed" | "provider_reported" | "controller_attested";
export type Capability = string;
export type CaseId3 = string;
export type CheckedAt1 = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs3 = string[];
export type ExpiresAt2 = string | null;
export type NodeId = string;
export type ObservationId = string;
export type Status = "available" | "changed" | "revoked" | "unsupported" | "unknown";
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "AgentResultV1".
 */
export type AgentResultV1 =
  | {
      authenticity_ref: AuthenticityRef;
      case_id: CaseId4;
      completed_at: CompletedAt;
      evidence_refs: EvidenceRefs4;
      generation: Generation2;
      input_digest: InputDigest;
      issue: null;
      lease_epoch: LeaseEpoch;
      outcome: Outcome;
      output_refs: OutputRefs;
      request_id: RequestId;
      run_id: RunId1;
      task_id: TaskId;
    }
  | {
      authenticity_ref: AuthenticityRef;
      case_id: CaseId4;
      completed_at: CompletedAt;
      evidence_refs: EvidenceRefs4;
      generation: Generation2;
      input_digest: InputDigest;
      issue: Issue;
      lease_epoch: LeaseEpoch;
      outcome: Outcome1;
      output_refs: OutputRefs1;
      request_id: RequestId;
      run_id: RunId1;
      task_id: TaskId;
    };
export type AuthenticityRef = string;
export type CaseId4 = string;
export type CompletedAt = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs4 = string[];
export type Generation2 = number;
export type InputDigest = string;
export type LeaseEpoch = number;
export type Outcome = "completed";
/**
 * @minItems 1
 * @maxItems 256
 */
export type OutputRefs = [string, ...string[]];
export type RequestId = string;
export type RunId1 = string;
export type TaskId = string;
export type Code = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs5 = string[];
export type InputRef = string | null;
export type OwnerRole = string;
export type Recovery =
  | "retry_read"
  | "reconnect"
  | "supply_input"
  | "review_scope"
  | "reapprove"
  | "await_counterpart"
  | "reconcile"
  | "unsupported";
export type Outcome1 = "blocked" | "failed" | "unknown";
/**
 * @maxItems 256
 */
export type OutputRefs1 = string[];
export type Attempt = number;
export type CaseId5 = string;
export type CheckpointRef = string | null;
export type CreatedAt1 = string;
export type Deadline = string;
export type Generation3 = number;
export type InputDigest1 = string;
export type LeaseEpoch1 = number;
export type LeaseOwner = string | null;
export type LeaseUntil = string | null;
export type ModelProfileRef = string | null;
export type NextWakeAt = string | null;
/**
 * @maxItems 256
 */
export type OutputRefs2 = string[];
export type PolicyDigest1 = string;
export type PolicyRef = string;
export type PromptDigest = string;
export type PromptRef = string;
export type RequestId1 = string;
export type RunId2 = string;
export type State4 =
  | "pending"
  | "ready"
  | "leased"
  | "running"
  | "waiting"
  | "retry_due"
  | "succeeded"
  | "held"
  | "unknown"
  | "failed"
  | "cancelled";
export type StateVersion = number;
/**
 * @maxItems 256
 */
export type AllowedToolIds = string[];
/**
 * @maxItems 32
 */
export type Dependencies = string[];
/**
 * @minItems 1
 * @maxItems 16
 */
export type ExpectedSchemas = [string, ...string[]];
export type ExpectedSubject = string;
/**
 * @maxItems 256
 */
export type InputRefs = string[];
export type Operation1 =
  | "verify_package"
  | "survey"
  | "explain_status"
  | "audit"
  | "propose_plan"
  | "build_baseline"
  | "build_candidate"
  | "validate_driver"
  | "run_scenario"
  | "scribe_draft"
  | "scribe_final"
  | "architect"
  | "candidate_patch"
  | "run_mutant"
  | "derive_guards"
  | "diagnose"
  | "learn"
  | "selfcheck_recipe"
  | "aggregate";
export type OutputSlot = string;
export type OutputSubjectPolicy = "same_subject" | "candidate_child" | "build_from_source" | "derived_evidence";
export type Required = boolean;
export type Role =
  | "Gardener"
  | "Surveyor"
  | "Builder"
  | "Explorer"
  | "Scribe"
  | "Architect"
  | "Grafter"
  | "Adversary"
  | "Healer"
  | "Librarian"
  | "Herald"
  | "Orchard Analyst"
  | "Sentinel";
export type TaskId1 = string;
export type WorkspaceRef = string | null;
export type WakeConditionRef = string | null;
export type ProjectionRef = string;
export type QueryRef = string;
export type CreatedAt2 = string;
export type EvidenceRefs6 = string[];
export type GraftId = string;
export type HaltedAgent = string | null;
export type Id = string;
export type Message = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ProducerKind".
 */
export type ProducerKind = "agent" | "service";
export type Model = string | null;
export type Name = string;
export type Version = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Severity".
 */
export type Severity = "CRITICAL" | "MAJOR" | "MINOR";
export type MaxMatches = number;
export type RuleRef = string;
export type SnapshotRef = string;
export type ActionGroupId = string;
export type ActionPlanDigest = string;
/**
 * @maxItems 256
 */
export type AllowedActions = (
  | "preserve_state"
  | "publish_artifact"
  | "publish_source"
  | "merge_protected"
  | "apply_configuration"
  | "deploy_exact"
  | "finalise"
  | "prepare_exit"
  | "run_exit"
  | "read_exit_evidence"
  | "revoke_exit_evidence"
  | "configure_ingress"
  | "restart_target"
  | "revoke_grant"
  | "delete_temporary"
  | "stop_worker"
  | "financial_compensation"
)[];
export type ApprovalId = string;
export type ArtifactDigest1 = string;
/**
 * @maxItems 256
 */
export type AuthorityRefs = string[];
export type BaselineDigest = string;
export type CandidateDigest = string;
export type CaseId6 = string;
export type ConfigDigest1 = string;
export type ControllerId = string;
export type DeliveryRoute = "git_protected" | "direct_artifact";
export type ExpiresAt3 = string;
export type Generation4 = number;
export type GraphDigest1 = string;
export type IssuedAt = string;
export type PatchDigest = string;
export type PolicyDigest2 = string;
/**
 * @maxItems 256
 */
export type PublicationDestinationRefs = string[];
export type RecoveryPlanDigest = string;
export type ReviewedBundleDigest = string;
export type RevokedAt = string | null;
export type ScopeDigest1 = string;
export type SourceBase = string | null;
export type SourceHead = string | null;
/**
 * @maxItems 256
 */
export type SourceSnapshotDigests = string[];
export type StatePlanDigest1 = string;
/**
 * @maxItems 256
 */
export type TargetResources = string[];
export type TriggerChainDigest = string;
/**
 * @maxItems 256
 */
export type Actions = (
  | "preserve_state"
  | "publish_artifact"
  | "publish_source"
  | "merge_protected"
  | "apply_configuration"
  | "deploy_exact"
  | "finalise"
  | "prepare_exit"
  | "run_exit"
  | "read_exit_evidence"
  | "revoke_exit_evidence"
  | "configure_ingress"
  | "restart_target"
  | "revoke_grant"
  | "delete_temporary"
  | "stop_worker"
  | "financial_compensation"
)[];
export type AuthorityId = string;
export type ControllerId1 = string;
export type DelegateId = string | null;
export type ExpiresAt4 = string;
export type GrantEpoch = number;
export type IssuedAt1 = string;
export type RevokedAt1 = string | null;
/**
 * @maxItems 256
 */
export type RoleEvidenceRefs = string[];
/**
 * @maxItems 256
 */
export type ApprovalRefs = string[];
export type ApprovalSetId = string;
export type CaseId7 = string;
export type CheckedAt2 = string;
export type Generation5 = number;
export type PlanDigest1 = string;
/**
 * @maxItems 256
 */
export type RequiredControllerIds1 = string[];
export type RunId3 = string;
export type State5 = "complete" | "missing" | "stale" | "revoked";
export type AuthenticityRef1 = string;
export type BuildConfigDigest = string;
export type BuildId = string;
export type CaseId8 = string;
export type CollectorIdentityRef = string;
export type DependencyDigest = string;
/**
 * @maxItems 256
 */
export type ExactImageTestRefs = string[];
export type ExportTarDigest = string;
export type Generation6 = number;
/**
 * @maxItems 256
 */
export type LayerDigests = string[];
/**
 * @maxItems 256
 */
export type LeakScanRefs = string[];
export type OciManifestDigest = string;
export type Outcome2 = "built" | "tested" | "held" | "failed" | "unknown";
export type Platform = "linux/amd64";
export type ProvenanceRef = string;
export type RecipeDigest = string;
export type RunId4 = string;
export type RuntimeProfileDigest = string;
/**
 * @maxItems 256
 */
export type SourceSnapshotRefs = string[];
export type SourceTreeDigest = string;
export type ByteCount = number;
export type CaseId9 = string;
export type CreatedAt3 = string;
export type DerivationRef = string | null;
export type EvidenceClass =
  | "scripted"
  | "component_offline"
  | "real_model"
  | "real_provider"
  | "real_payment"
  | "isolation_qualified"
  | "merchant_exit";
export type ExpiresAt5 = string | null;
export type Generation7 = number;
export type InputDigest2 = string;
export type PayloadDigest = string;
export type ProducerIdentityRef = string;
export type Ref = string;
export type RunId5 = string;
export type Schema = string;
export type SubjectDigest = string;
export type Trust = "model_proposal" | "collector_observed" | "deterministic_result";
/**
 * @maxItems 256
 */
export type ActiveReferenceRefs = string[];
export type AssetId = string;
/**
 * @maxItems 256
 */
export type AuthorityRefs1 = string[];
export type Desired = "keep" | "deny_revoke" | "delete" | "retain_policy";
/**
 * @maxItems 256
 */
export type EvidenceRefs7 = string[];
export type Kind =
  | "source"
  | "image"
  | "registry"
  | "runtime"
  | "config"
  | "state"
  | "credential"
  | "callback"
  | "origin_handler"
  | "grant"
  | "worker"
  | "copy"
  | "record"
  | "exit_executor";
export type Ownership = "merchant" | "shared_service" | "exclusive_run";
export type RequiredForOperation = boolean;
/**
 * @maxItems 256
 */
export type ActiveReferenceRefs1 = string[];
export type AssetId1 = string;
/**
 * @maxItems 256
 */
export type AuthorityRefs2 = string[];
export type Desired1 = "keep" | "deny_revoke" | "delete" | "retain_policy";
/**
 * @maxItems 256
 */
export type EvidenceRefs8 = string[];
export type Kind1 =
  | "source"
  | "image"
  | "registry"
  | "runtime"
  | "config"
  | "state"
  | "credential"
  | "callback"
  | "origin_handler"
  | "grant"
  | "worker"
  | "copy"
  | "record"
  | "exit_executor";
export type Ownership1 = "merchant" | "shared_service" | "exclusive_run";
export type RequiredForOperation1 = boolean;
/**
 * @maxItems 256
 */
export type Assets = Asset[];
export type CaseId10 = string;
export type FinalArtifactDigest = string;
export type FinalConfigDigest = string;
export type LegacyObligationsRef = string;
export type ManifestDigest = string;
export type ManifestId = string;
export type RunId6 = string;
export type Assignee = string;
export type Attempt1 = number;
export type CreatedAt4 = string;
export type GraftId1 = string;
export type Id1 = string;
export type InputRefs1 = string[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Stage".
 */
export type Stage =
  | "CREATED"
  | "GATED"
  | "SURVEYED"
  | "BUILT"
  | "LINKS_PROVEN"
  | "DELIVERED"
  | "RECORDED"
  | "CONTRACTED"
  | "ATTACK_PLANNED"
  | "GRAFTED"
  | "PROVING"
  | "REPAIRING"
  | "CERTIFIED"
  | "PARTIAL"
  | "FAILED"
  | "PR_OPEN"
  | "MERGED"
  | "SHADOW"
  | "HEAL_1"
  | "HEAL_10"
  | "HEAL_50"
  | "LIVE_100"
  | "CLEANUP_PR"
  | "DONE"
  | "CUTBACK";
export type AfterSeq = number;
export type RunRef = string;
export type ActualProviderEvidenceRef = string;
export type DependencyDigest1 = string;
export type ImmutableSourceDigest = string;
export type ObservedDefectsRef = string;
export type Outcome3 = "reproduced" | "reproduced_with_defects" | "failed" | "unknown";
export type PackageDigest = string;
export type RunId7 = string;
export type RuntimeDigest = string;
export type ScenarioResultsRef = string;
export type SeedDigest = string;
/**
 * @maxItems 256
 */
export type SkippedRequired = string[];
export type Variant = "OLD" | "OLD_TWIN";
export type Agent = string;
export type CapUsd = number;
export type GraftId2 = string;
export type Model1 = string;
export type TokensCached = number;
export type TokensIn = number;
export type TokensOut = number;
export type Usd = number;
export type GraftId3 = string;
export type ItemsHash = string | null;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Kind".
 */
export type Kind2 =
  | "INTENT"
  | "APPROVE"
  | "AUTHORIZE"
  | "CAPTURE"
  | "VOID"
  | "SHOP_PAID"
  | "SHOP_PENDING"
  | "SHOP_UNPAID"
  | "NOTIFY"
  | "NOTIFY_VERIFIED"
  | "NOTIFY_REJECTED"
  | "REFUND"
  | "RECUR_SETUP"
  | "RECUR_CHARGE"
  | "ERROR";
export type Currency =
  | "AUD"
  | "BRL"
  | "CAD"
  | "CHF"
  | "CNY"
  | "CZK"
  | "DKK"
  | "EUR"
  | "GBP"
  | "HKD"
  | "HUF"
  | "ILS"
  | "JPY"
  | "MXN"
  | "MYR"
  | "NOK"
  | "NZD"
  | "PHP"
  | "PLN"
  | "RUB"
  | "SEK"
  | "SGD"
  | "THB"
  | "TWD"
  | "USD";
export type Minor = number;
export type Noise = string[];
export type OrderRef = string;
export type CaptureId = string | null;
export type DebugId = string | null;
export type LegacyToken = string | null;
export type OrderId = string | null;
export type ProfileId = string | null;
export type RefundId = string | null;
export type TxnId = string | null;
export type RawRef = string;
export type RunId8 = string;
export type ScenarioId = string;
export type Seq = number;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Source".
 */
export type Source = "SHOP_HTTP" | "SHOP_DB" | "PAYPAL_CALL" | "PAYPAL_LEDGER" | "NOTIFICATION";
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "StatusNorm".
 */
export type StatusNorm = "COMPLETED" | "PENDING" | "DECLINED" | "REFUNDED" | "FAILED";
export type TMs = number;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Variant".
 */
export type Variant1 = "OLD" | "OLD_TWIN" | "NEW";
export type CancelId = string;
export type ExpectedTree = string;
export type PatchRef = string;
export type WorkspaceRef1 = string;
export type CaseId11 = string;
export type EventId = string;
export type Kind3 =
  "case_changed" | "readiness_changed" | "work_changed" | "lifecycle_changed" | "delivery_changed" | "access_changed";
export type OccurredAt = string;
export type PayloadDigest1 = string;
export type PayloadRef = string;
export type Sequence = number;
export type StateVersion1 = number;
export type After = number | null;
export type CaseId12 = string;
export type ShopUrl = string;
export type Status1 = "draft" | "waiting_controller" | "checking" | "setup_needed" | "ready" | "accepted" | "closed";
export type UpdatedAt = string;
/**
 * @maxItems 50
 */
export type Items = CaseSummary[];
export type NextCursor = string | null;
export type Cursor = string | null;
export type Limit = number;
export type CaseId13 = string;
export type ShopUrl1 = string;
export type Status2 = "draft" | "waiting_controller" | "checking" | "setup_needed" | "ready" | "accepted" | "closed";
export type UpdatedAt1 = string;
export type AcceptanceRef1 = string | null;
/**
 * @maxItems 256
 */
export type BindingRefs = string[];
export type CaseId14 = string;
export type CreatedAt5 = string;
export type GraphRef = string | null;
export type RequesterId = string;
export type ShopUrl2 = string;
export type Status3 = "draft" | "waiting_controller" | "checking" | "setup_needed" | "ready" | "accepted" | "closed";
export type TenantId = string;
export type CheckedAt3 = string;
export type DeliveryRef = string | null;
export type EvidenceClass1 =
  | "scripted"
  | "component_offline"
  | "real_model"
  | "real_provider"
  | "real_payment"
  | "isolation_qualified"
  | "merchant_exit";
export type LastEventSeq1 = number;
/**
 * @maxItems 256
 */
export type ActiveEffectRefs = string[];
export type Attempt2 = number;
export type CaseId15 = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs9 = string[];
export type Generation8 = number;
export type ResourceGraphDigest = string;
export type RunId9 = string;
export type ScopeDigest2 = string;
export type Stage1 =
  | "BASELINE_VERIFY"
  | "BASELINE_RUN"
  | "CANDIDATE_READY"
  | "VALIDATING"
  | "REVIEW_READY"
  | "AWAITING_APPLY"
  | "PUBLISHING"
  | "MERGING"
  | "DEPLOY_PREPARED"
  | "DEPLOYING"
  | "OBSERVING"
  | "FINALISING"
  | "EXITING"
  | "COMPLETE"
  | "HELD"
  | "FAILED_SAFE"
  | "INCIDENT_UNKNOWN";
export type UpdatedAt2 = string;
export type WorkId1 = string;
export type WorkPackageDigest = string;
export type WorkPackageRef = string;
export type PendingActionId = string | null;
export type CheckedAt4 = string;
export type CopyScope = string;
/**
 * @maxItems 256
 */
export type Limits = string[];
export type PolicyDigest3 = string;
export type Name1 = string;
export type Purpose = string;
export type RegionText = string;
export type RetentionText = string;
/**
 * @maxItems 256
 */
export type TermsEvidenceRefs = string[];
/**
 * @maxItems 256
 */
export type Recipients = ProcessingRecipient[];
export type Status4 = "qualified" | "missing" | "stale";
export type ActorId1 = string;
export type CaseId16 = string;
export type CheckId = string;
export type CheckedAt5 = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs10 = string[];
export type ExpiresAt6 = string | null;
export type RecoveryCode = string | null;
export type Status5 = "pass" | "missing" | "unsupported" | "failed" | "stale" | "unknown";
/**
 * @maxItems 256
 */
export type Checks = CheckResult[];
export type ExpiresAt7 = string;
export type FixtureProfileDigest = string;
export type IssuedAt2 = string;
export type ProcessingPolicyDigest = string;
export type ReadinessDigest1 = string;
export type ReadinessId1 = string;
export type ResourceGraphDigest1 = string;
export type RuntimeProfileDigest1 = string;
export type ScopeDigest3 = string;
export type SourceManifestDigest = string;
/**
 * @maxItems 256
 */
export type SourceSnapshotRefs1 = string[];
export type WorkPackageDigest1 = string;
export type WorkPackageRef1 = string;
export type Enabled = boolean;
export type Kind4 = string;
export type ReasonCode = string | null;
/**
 * @maxItems 256
 */
export type ResourceIds = string[];
/**
 * @maxItems 256
 */
export type RequiredActions = RequiredAction[];
/**
 * @maxItems 256
 */
export type CheckRefs = string[];
export type ControllerState = "unbound" | "waiting" | "approved" | "revoked" | "unknown";
export type Environment = string;
export type Label = string;
export type NodeId1 = string;
/**
 * @maxItems 256
 */
export type PermittedActions = string[];
export type ReadScopeText = string;
export type SourceSnapshotRef = string | null;
/**
 * @maxItems 256
 */
export type Resources = ResourceSummary[];
export type StateVersion2 = number;
export type Branch = string;
export type CertId = string;
export type CommitNew = string;
export type CommitOld = string;
export type Tokens = number;
export type Usd1 = number;
export type IssuedAt3 = string;
export type LedgerRoot = string;
export type OtsProof = string | null;
export type CaptureId1 = string;
export type DebugId1 = string;
export type OrderId1 = string;
export type Scenario = string;
export type PaypalEvidence = PayPalEvidence[];
export type EquivalentDropped = number;
export type Killed = number;
export type MutantsTotal = number;
export type Score = number;
export type RekorEntry = string;
export type Repo = string;
export type NA = number;
export type Pass = number;
export type PassFixed = number;
export type Problem = number;
export type Scenarios = number;
export type Unverified = number;
export type Sha = string;
export type Workflow = string;
export type DepsBlocked = number;
export type InjectionAttemptsBlocked = number;
export type SecretsFound = number;
export type ShopId = string;
export type Signature = string;
export type MissesLearned = number;
export type Precision = number;
export type Recall = number;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CertificateV2".
 */
export type CertificateV2 =
  | {
      case_id: CaseId17;
      cert_id: CertId1;
      expires_at: ExpiresAt8;
      generation: Generation9;
      git_source: CertificateGitSource;
      issued_at: IssuedAt4;
      ledger_root: LedgerRoot1;
      policy_digest: PolicyDigest4;
      proof_plan_digest: ProofPlanDigest;
      proof_plan_ref: ProofPlanRef;
      proof_result_digest: ProofResultDigest;
      proof_result_ref: ProofResultRef;
      qualification_evidence_refs: QualificationEvidenceRefs;
      qualification_scope: QualificationScope;
      resource_epochs: ResourceEpochs;
      review_bundle_digest: ReviewBundleDigest1;
      review_bundle_ref: ReviewBundleRef;
      run_id: RunId10;
      scope_digest: ScopeDigest4;
      signature: SignatureMaterial;
      signer_identity_ref: SignerIdentityRef;
      signer_kind: SignerKind;
      source_route: SourceRoute;
      subject_manifest_digest: SubjectManifestDigest;
      subject_manifest_ref: SubjectManifestRef;
      work_package_digest: WorkPackageDigest2;
      workflow_identity: string;
      workflow_sha: string;
    }
  | {
      case_id: CaseId17;
      cert_id: CertId1;
      expires_at: ExpiresAt8;
      generation: Generation9;
      git_source: CertificateGitSource;
      issued_at: IssuedAt4;
      ledger_root: LedgerRoot1;
      policy_digest: PolicyDigest4;
      proof_plan_digest: ProofPlanDigest;
      proof_plan_ref: ProofPlanRef;
      proof_result_digest: ProofResultDigest;
      proof_result_ref: ProofResultRef;
      qualification_evidence_refs: QualificationEvidenceRefs;
      qualification_scope: QualificationScope;
      resource_epochs: ResourceEpochs;
      review_bundle_digest: ReviewBundleDigest1;
      review_bundle_ref: ReviewBundleRef;
      run_id: RunId10;
      scope_digest: ScopeDigest4;
      signature: SignatureMaterial;
      signer_identity_ref: SignerIdentityRef;
      signer_kind: SignerKind1;
      source_route: SourceRoute1;
      subject_manifest_digest: SubjectManifestDigest;
      subject_manifest_ref: SubjectManifestRef;
      work_package_digest: WorkPackageDigest2;
      workflow_identity: null;
      workflow_sha: null;
    }
  | {
      case_id: CaseId17;
      cert_id: CertId1;
      expires_at: ExpiresAt8;
      generation: Generation9;
      git_source: null;
      issued_at: IssuedAt4;
      ledger_root: LedgerRoot1;
      policy_digest: PolicyDigest4;
      proof_plan_digest: ProofPlanDigest;
      proof_plan_ref: ProofPlanRef;
      proof_result_digest: ProofResultDigest;
      proof_result_ref: ProofResultRef;
      qualification_evidence_refs: QualificationEvidenceRefs;
      qualification_scope: QualificationScope;
      resource_epochs: ResourceEpochs;
      review_bundle_digest: ReviewBundleDigest1;
      review_bundle_ref: ReviewBundleRef;
      run_id: RunId10;
      scope_digest: ScopeDigest4;
      signature: SignatureMaterial;
      signer_identity_ref: SignerIdentityRef;
      signer_kind: SignerKind2;
      source_route: SourceRoute2;
      subject_manifest_digest: SubjectManifestDigest;
      subject_manifest_ref: SubjectManifestRef;
      work_package_digest: WorkPackageDigest2;
      workflow_identity: string;
      workflow_sha: string;
    }
  | {
      case_id: CaseId17;
      cert_id: CertId1;
      expires_at: ExpiresAt8;
      generation: Generation9;
      git_source: null;
      issued_at: IssuedAt4;
      ledger_root: LedgerRoot1;
      policy_digest: PolicyDigest4;
      proof_plan_digest: ProofPlanDigest;
      proof_plan_ref: ProofPlanRef;
      proof_result_digest: ProofResultDigest;
      proof_result_ref: ProofResultRef;
      qualification_evidence_refs: QualificationEvidenceRefs;
      qualification_scope: QualificationScope;
      resource_epochs: ResourceEpochs;
      review_bundle_digest: ReviewBundleDigest1;
      review_bundle_ref: ReviewBundleRef;
      run_id: RunId10;
      scope_digest: ScopeDigest4;
      signature: SignatureMaterial;
      signer_identity_ref: SignerIdentityRef;
      signer_kind: SignerKind3;
      source_route: SourceRoute3;
      subject_manifest_digest: SubjectManifestDigest;
      subject_manifest_ref: SubjectManifestRef;
      work_package_digest: WorkPackageDigest2;
      workflow_identity: null;
      workflow_sha: null;
    };
export type CaseId17 = string;
export type CertId1 = string;
export type ExpiresAt8 = string;
export type Generation9 = number;
export type Branch1 = string;
export type CommitNew1 = string;
export type CommitOld1 = string;
export type RepositoryRef = string;
export type IssuedAt4 = string;
export type LedgerRoot1 = string;
export type PolicyDigest4 = string;
export type ProofPlanDigest = string;
export type ProofPlanRef = string;
export type ProofResultDigest = string;
export type ProofResultRef = string;
/**
 * @maxItems 256
 */
export type QualificationEvidenceRefs = string[];
export type QualificationScope = "component_only" | "sandbox_payment" | "merchant_delivery";
export type ReviewBundleDigest1 = string;
export type ReviewBundleRef = string;
export type RunId10 = string;
export type ScopeDigest4 = string;
export type AuthenticityRef2 = string;
export type SignatureDigest = string;
export type SignatureRef = string;
export type TransparencyDigest = string;
export type TransparencyRef = string;
export type SignerIdentityRef = string;
export type SignerKind = "github_actions";
export type SourceRoute = "git";
export type SubjectManifestDigest = string;
export type SubjectManifestRef = string;
export type WorkPackageDigest2 = string;
export type SignerKind1 = "trusted_service";
export type SourceRoute1 = "git";
export type SignerKind2 = "github_actions";
export type SourceRoute2 = "local_folder" | "cloud_files" | "host_export";
export type SignerKind3 = "trusted_service";
export type SourceRoute3 = "local_folder" | "cloud_files" | "host_export";
export type CaseId18 = string;
export type CertId2 = string;
export type CheckedAt6 = string;
export type QualificationScope1 = "component_only" | "sandbox_payment" | "merchant_delivery";
export type QualificationState = "verified" | "held";
/**
 * @maxItems 256
 */
export type ReasonCodes = string[];
export type RunId11 = string;
export type SignatureIntegrity = "verified" | "unverified" | "invalid";
export type Branch2 = string;
export type Commit = string;
export type PlanItemIds = string[];
export type Summary = string;
export type Changes = Change[];
export type CreatedAt6 = string;
export type GraftId4 = string;
export type Id2 = string;
export type OpenItemIds = string[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ChangeListV2".
 */
export type ChangeListV2 =
  | {
      baseline_snapshot_ref: BaselineSnapshotRef;
      branch: null;
      candidate_snapshot_ref: CandidateSnapshotRef;
      changes: Changes1;
      created_at: CreatedAt7;
      graft_id: GraftId5;
      id: Id3;
      open_item_ids: OpenItemIds1;
      patch_digest: PatchDigest1;
      producer: Producer;
      provenance: Provenance;
    }
  | {
      baseline_snapshot_ref: BaselineSnapshotRef;
      branch: string;
      candidate_snapshot_ref: CandidateSnapshotRef;
      changes: Changes2;
      created_at: CreatedAt7;
      graft_id: GraftId5;
      id: Id3;
      open_item_ids: OpenItemIds1;
      patch_digest: PatchDigest1;
      producer: Producer;
      provenance: Provenance1;
    };
export type BaselineSnapshotRef = string;
export type CandidateSnapshotRef = string;
export type Commit1 = string | null;
/**
 * @maxItems 256
 */
export type PlanItemIds1 = string[];
export type Summary1 = string;
/**
 * @maxItems 256
 */
export type Changes1 = (SnapshotChange & {
  commit?: null;
})[];
export type CreatedAt7 = string;
export type GraftId5 = string;
export type Id3 = string;
/**
 * @maxItems 256
 */
export type OpenItemIds1 = string[];
export type PatchDigest1 = string;
export type Provenance = "snapshot";
/**
 * @minItems 1
 * @maxItems 256
 */
export type Changes2 = [
  SnapshotChange & {
    commit?: string;
  },
  ...(SnapshotChange & {
    commit?: string;
  })[]
];
export type Provenance1 = "git";
export type CheckId1 = string;
export type CheckedAt7 = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs11 = string[];
export type ExpiresAt9 = string | null;
export type RecoveryCode1 = string | null;
export type Status6 = "pass" | "missing" | "unsupported" | "failed" | "stale" | "unknown";
export type BlobRef = string;
export type FilePath = string;
export type Length = number;
export type Offset = number;
export type Sha256 = string;
export type UploadId = string;
export type FilePath1 = string;
export type Length1 = number;
export type Offset1 = number;
export type ReceivedAt = string;
export type Sha2561 = string;
export type UploadId1 = string;
export type FilePath2 = string;
export type Length2 = number;
export type Offset2 = number;
export type Sha2562 = string;
export type ContinuationRef = string;
export type AcceptedAt = string;
export type Generation10 = number;
export type OperationId = string;
export type ReceiptRef = string;
export type WorkId2 = string;
export type BuildContextRef = string | null;
export type ConfigurationManifestRef = string;
/**
 * @maxItems 256
 */
export type ControllerBindingRefs = string[];
/**
 * @maxItems 256
 */
export type CorrespondenceEvidenceRefs = string[];
export type DependencyManifestRef = string;
export type NodeId2 = string;
export type Purpose1 = string;
export type RuntimeProfileRef = string;
export type SourceSnapshotRef1 = string | null;
export type BuildContextRef1 = string | null;
export type ConfigurationManifestRef1 = string;
/**
 * @maxItems 256
 */
export type ControllerBindingRefs1 = string[];
/**
 * @maxItems 256
 */
export type CorrespondenceEvidenceRefs1 = string[];
export type DependencyManifestRef1 = string;
export type NodeId3 = string;
export type Purpose2 = string;
export type RuntimeProfileRef1 = string;
export type SourceSnapshotRef2 = string | null;
/**
 * @maxItems 256
 */
export type Components = Component[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ConfigurationEntryV1".
 */
export type ConfigurationEntryV1 =
  | {
      evidence_refs: EvidenceRefs12;
      kind: Kind5;
      name: Name2;
      required: Required1;
      secret_ref: null;
      value: string;
    }
  | {
      evidence_refs: EvidenceRefs12;
      kind: Kind6;
      name: Name2;
      required: Required1;
      secret_ref: string;
      value: null;
    };
/**
 * @maxItems 256
 */
export type EvidenceRefs12 = string[];
export type Kind5 = "public_value";
export type Name2 = string;
export type Required1 = boolean;
export type Kind6 = "secret_reference";
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ConfigurationEntry".
 */
export type ConfigurationEntry =
  | {
      evidence_refs: EvidenceRefs13;
      kind: Kind7;
      name: Name3;
      required: Required2;
      secret_ref: null;
      value: string;
    }
  | {
      evidence_refs: EvidenceRefs13;
      kind: Kind8;
      name: Name3;
      required: Required2;
      secret_ref: string;
      value: null;
    };
/**
 * @maxItems 256
 */
export type EvidenceRefs13 = string[];
export type Kind7 = "public_value";
export type Name3 = string;
export type Required2 = boolean;
export type Kind8 = "secret_reference";
/**
 * @maxItems 256
 */
export type Entries = ConfigurationEntry[];
export type NvpOk = boolean;
export type RestOk = boolean;
export type VersionMatch = boolean;
export type WebhookOk = boolean;
export type Repo1 = string | null;
export type SecretsRef = string;
export type ShopId1 = string;
export type Site = string | null;
/**
 * @maxItems 256
 */
export type BindingRefs1 = string[];
export type CaseId19 = string;
export type CreatedAt8 = string;
export type GraphRef1 = string | null;
export type RequesterId1 = string;
export type ShopUrl3 = string;
export type Status7 = "draft" | "waiting_controller" | "checking" | "setup_needed" | "ready" | "accepted" | "closed";
export type TenantId1 = string;
export type ActorId2 = string;
export type CaseId20 = string;
/**
 * @maxItems 256
 */
export type Checks1 = CheckResult[];
export type ExpiresAt10 = string;
export type FixtureProfileDigest1 = string;
export type IssuedAt5 = string;
export type ProcessingPolicyDigest1 = string;
export type ReadinessDigest2 = string;
export type ReadinessId2 = string;
export type ResourceGraphDigest2 = string;
export type RuntimeProfileDigest2 = string;
export type ScopeDigest5 = string;
export type SourceManifestDigest1 = string;
/**
 * @maxItems 256
 */
export type SourceSnapshotRefs2 = string[];
export type WorkPackageDigest3 = string;
export type WorkPackageRef2 = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Agreement".
 */
export type Agreement = "BOTH" | "CODE_ONLY" | "TRACE_ONLY";
export type CorrectFlow = string[];
export type CounterExamples = string[];
export type Id4 = string;
export type Predicate = string;
export type Code1 = string[];
export type Traces = string[];
export type Title = string;
export type Killed1 = boolean;
export type Mutants = string[];
export type Scenarios1 = string[];
export type Rules = Rule[];
export type ShopId2 = string;
export type Code2 =
  | "INVALID"
  | "DENIED"
  | "NOT_FOUND"
  | "CONFLICT"
  | "STALE"
  | "EXPIRED"
  | "CANCELLED"
  | "UNKNOWN"
  | "BUDGET_EXHAUSTED"
  | "MISSING_EVIDENCE"
  | "UNSUPPORTED";
/**
 * @maxItems 256
 */
export type EvidenceRefs14 = string[];
export type RetryClass = "none" | "safe_read" | "reconcile" | "reauthorise";
export type CaseId21 = string;
export type CopyUrl = string;
export type ExpiresAt11 = string;
export type InvitationId = string;
export type RecipientHint = string | null;
export type RequesterId2 = string;
/**
 * @maxItems 256
 */
export type ResourceIds1 = string[];
export type Status8 = "pending" | "approved" | "denied" | "expired";
export type ReadinessDigest3 = string;
export type ReadinessId3 = string;
export type ShopUrl4 = string;
export type ShopUrl5 = string;
export type RecipientHint1 = string | null;
/**
 * @minItems 1
 * @maxItems 256
 */
export type ResourceIds2 = [string, ...string[]];
export type ProviderId2 = string;
export type Purpose3 = "read_connect" | "apply_connect";
export type ResourceId1 = string | null;
export type ExpectedManifestDigest = string;
export type ExpectedTotalBytes = number;
/**
 * @minItems 1
 * @maxItems 20000
 */
export type Manifest = [ManifestEntry, ...ManifestEntry[]];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ManifestEntry".
 */
export type ManifestEntry =
  | {
      bytes: Bytes;
      file_type: FileType;
      relative_path: RelativePath;
      sha256: string;
    }
  | {
      bytes: 0;
      file_type: FileType1;
      relative_path: RelativePath;
      sha256: null;
    };
export type Bytes = number;
export type FileType = "file";
export type RelativePath = string;
export type FileType1 = "directory";
export type CreatedAt9 = string;
export type EvidenceRefs15 = string[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "JsonValue".
 */
export type JsonValue =
  | boolean
  | number
  | string
  | JsonValue[]
  | {
      [k: string]: JsonValue;
    }
  | null;
export type GraftId6 = string;
export type GroupBy = string[];
export type Id5 = string;
export type Metrics = string[];
export type Question = string;
export type Title1 = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "DeliveryDecisionV1".
 */
export type DeliveryDecisionV1 =
  | {
      case_id: CaseId22;
      existing_effect_ref: ExistingEffectRef;
      expected_state_version: ExpectedStateVersion;
      generation: Generation11;
      input_refs: InputRefs2;
      kind: Kind9;
      next_wake_at: NextWakeAt1;
      operation:
        | "review_evaluate"
        | "plan_apply"
        | "reserve_targets"
        | "preserve_state"
        | "publish_artifact"
        | "publish_source"
        | "merge_protected"
        | "apply_configuration"
        | "deploy_exact"
        | "reconcile_effect"
        | "observe_target"
        | "finalise"
        | "prepare_exit"
        | "run_exit"
        | "read_exit_evidence"
        | "revoke_exit_evidence"
        | "reconcile_cleanup";
      reason_code: ReasonCode1;
      run_id: RunId12;
      slot_id: SlotId1;
    }
  | {
      case_id: CaseId22;
      existing_effect_ref: null;
      expected_state_version: ExpectedStateVersion;
      generation: Generation11;
      input_refs: InputRefs3;
      kind: Kind10;
      next_wake_at: NextWakeAt1;
      operation: null;
      reason_code: ReasonCode1;
      run_id: RunId12;
      slot_id: null;
    };
export type CaseId22 = string;
export type ExistingEffectRef = string | null;
export type ExpectedStateVersion = number;
export type Generation11 = number;
/**
 * @minItems 1
 * @maxItems 256
 */
export type InputRefs2 = [string, ...string[]];
export type Kind9 = "request";
export type NextWakeAt1 = string | null;
export type ReasonCode1 = string;
export type RunId12 = string;
export type SlotId1 = string | null;
/**
 * @maxItems 256
 */
export type InputRefs3 = string[];
export type Kind10 = "wait" | "hold" | "incident" | "complete";
export type ActionPlanRef = string | null;
export type ApprovalSetRef = string | null;
export type CancellationRef = string | null;
export type CaseId23 = string;
export type CheckedAt8 = string;
/**
 * @maxItems 256
 */
export type CurrentEvidenceRefs = string[];
export type DeploymentRef = string | null;
export type ExitManifestRef = string | null;
export type ExitPlanRef1 = string | null;
export type FinalAssetManifestRef = string | null;
export type Generation12 = number;
export type GraphRef2 = string;
export type LifecycleRef = string;
/**
 * @maxItems 256
 */
export type PendingEffectRefs = string[];
export type ReservationRef = string | null;
export type ReviewRef = string | null;
export type RunId13 = string;
export type StateCutoverRef = string | null;
export type StateVersion3 = number;
export type AccessMode = "fixture" | "sandbox_broker" | "read_evidence" | "unavailable";
export type AuthorityRef = string | null;
/**
 * @maxItems 256
 */
export type ComponentIds = string[];
export type DependencyId = string;
export type Limitation = string;
export type Purpose4 = string;
export type TestIdentityRef = string | null;
export type Package = string;
export type RecipeRef = string;
export type Version1 = string;
export type AccessMode1 = "fixture" | "sandbox_broker" | "read_evidence" | "unavailable";
export type AuthorityRef1 = string | null;
/**
 * @maxItems 256
 */
export type ComponentIds1 = string[];
export type DependencyId1 = string;
export type Limitation1 = string;
export type Purpose5 = string;
export type TestIdentityRef1 = string | null;
/**
 * @maxItems 256
 */
export type Dependencies1 = Dependency[];
export type CaseId24 = string;
export type CheckedAt9 = string;
/**
 * @maxItems 256
 */
export type CurrentRuntimeEvidenceRefs = string[];
export type EffectId = string;
export type EnvironmentId1 = string;
export type ObservedArtifactDigest = string | null;
export type ObservedConfigDigest = string | null;
export type Outcome4 = "pending" | "verified" | "failed" | "unknown";
export type Provider = string;
export type ProviderDeployId = string | null;
export type ProviderStatus = string;
export type ResourceId2 = string;
export type SubmittedArtifactDigest = string;
export type CreatedAt10 = string;
export type EvidenceRefs16 = string[];
export type GraftId7 = string;
export type Id6 = string;
export type Language = string;
export type Operation2 = string;
export type Pattern = string;
export type CatalogRef = string;
export type Topic = string;
export type Version2 = string;
export type ContinuationRef1 = string;
export type CreatedAt11 = string;
export type DraftId = string;
export type ExpiresAt12 = string;
export type ShopUrl6 = string;
export type State6 = "unclaimed" | "claimed" | "expired";
export type ProvenRuns = number;
export type DriverStep1 = string;
export type ApiStep1 = string;
export type PaypalMockResponseCode = string;
export type Steps = (DriverStep | ApiStep | MockStep)[];
export type ActionGroupId1 = string;
export type ActorId3 = string;
export type ApprovalSetId1 = string;
export type CaseId25 = string;
export type CreatedAt12 = string;
export type EffectClass1 = "E0" | "E1" | "E2" | "E3" | "EU";
export type EffectId1 = string;
export type EnvironmentId2 = string;
export type ExpectedVersion = string;
export type Generation13 = number;
export type Operation3 =
  | "preserve_state"
  | "publish_artifact"
  | "publish_source"
  | "merge_protected"
  | "apply_configuration"
  | "deploy_exact"
  | "finalise"
  | "prepare_exit"
  | "run_exit"
  | "read_exit_evidence"
  | "revoke_exit_evidence"
  | "configure_ingress"
  | "restart_target"
  | "revoke_grant"
  | "delete_temporary"
  | "stop_worker"
  | "financial_compensation";
export type PlanDigest2 = string;
export type ProviderIdempotencyRef = string | null;
export type ProviderReceiptRef = string | null;
export type ReconciliationRef = string | null;
export type RequestDigest = string;
export type ResourceId3 = string;
export type RunId14 = string;
export type SlotId2 = string;
export type State7 = "intended" | "submitted" | "acknowledged" | "observed" | "failed" | "unknown" | "compensated";
export type ArtifactDigest2 = string | null;
export type Cardinality1 = number;
export type ConfigDigest2 = string | null;
/**
 * @maxItems 32
 */
export type DependsOn1 = string[];
export type EffectClass2 = "E0" | "E1" | "E2" | "E3";
export type ExpectedVersionRef1 = string;
export type Operation4 =
  | "preserve_state"
  | "publish_artifact"
  | "publish_source"
  | "merge_protected"
  | "apply_configuration"
  | "deploy_exact"
  | "finalise"
  | "prepare_exit"
  | "run_exit"
  | "read_exit_evidence"
  | "revoke_exit_evidence"
  | "configure_ingress"
  | "restart_target"
  | "revoke_grant"
  | "delete_temporary"
  | "stop_worker"
  | "financial_compensation";
export type RecoveryBranchRef1 = string | null;
/**
 * @maxItems 256
 */
export type RequiredAuthorityRefs1 = string[];
/**
 * @maxItems 256
 */
export type RequiredControllerIds2 = string[];
export type SlotId3 = string;
export type StatePlanDigest2 = string | null;
export type TriggerDigest1 = string;
export type MaxBytes = number;
export type Ref1 = string;
export type Projection = "private_status" | "public_safe";
export type RunRef1 = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs17 = string[];
export type ExpectedSubject1 = string;
export type Operation5 =
  "build_baseline" | "build_candidate" | "validate_driver" | "run_scenario" | "run_mutant" | "selfcheck_recipe";
export type RecipeRef1 = string;
/**
 * @maxItems 256
 */
export type RequestedOutputSchemas = string[];
export type ScenarioRef = string | null;
export type SubjectRef = string;
export type TaskId2 = string;
export type Variant2 = ("OLD" | "OLD_TWIN" | "NEW") | null;
export type ProposalRef = string;
export type RequestId2 = string;
export type AllowedRestartCount = number;
/**
 * @maxItems 256
 */
export type AuthorityRefs3 = string[];
export type BudgetRef1 = string;
export type CaseId26 = string;
/**
 * @maxItems 256
 */
export type CriteriaRefs = string[];
export type Deadline1 = string;
export type EvidenceReadAuthorityRef = string;
export type ExecutorIdentityRef = string;
export type ExitPlanId = string;
export type FailureRouteRef = string;
export type FinalArtifactDigest1 = string;
export type FinalConfigDigest1 = string;
export type Generation14 = number;
export type PlanDigest3 = string;
export type PrivateEvidenceDestinationRef = string;
export type RecoveryPlanRef1 = string;
export type ReservationRef1 = string;
export type RunId15 = string;
export type StateDigest = string;
export type TrustedCodeDigest = string;
export type CaseId27 = string;
export type EvidenceReadAuthorityRef1 = string;
export type ExecutorIdentityRef1 = string;
export type ExitPlanDigest = string;
export type ExitPlanRef2 = string;
export type FinalArtifactDigest2 = string;
export type FinalConfigDigest2 = string;
export type FinishedAt = string;
export type Generation15 = number;
export type CriterionRef = string;
export type EvidenceRef = string;
export type ObservedAt = string;
export type PayloadDigest2 = string;
export type State8 = "verified" | "failed" | "unknown";
/**
 * @maxItems 256
 */
export type Observations = ExitCriterionObservation[];
export type Capability1 = "source_read" | "model_execution" | "host_mutation" | "worker_dispatch";
export type DeniedAt = string;
export type EvidenceRef1 = string;
export type PayloadDigest3 = string;
/**
 * @maxItems 256
 */
export type OrdinaryDenials = CapabilityDenial[];
export type Outcome5 = "verified" | "held" | "failed" | "unknown";
export type PolicyDigest5 = string;
export type ReservationRef2 = string;
export type RestartCount = number;
export type ResultDigest = string;
export type ResultId = string;
export type RunId16 = string;
export type ScopeDigest6 = string;
export type StartedAt = string;
export type StateDigest1 = string;
export type TrustedCodeDigest1 = string;
export type WorkPackageDigest4 = string;
export type AuthenticityRef3 = string;
export type CaseId28 = string;
export type CheckedAt10 = string;
export type AuthorityRef2 = string;
export type DisclosureRef = string;
export type ReadAt = string;
export type ReadDigest = string;
export type ReadEvidenceRef = string;
export type RevocationDigest = string;
export type RevocationRef = string;
export type RevokedAt2 = string;
export type ExitManifestDigest = string;
export type ExitManifestRef1 = string;
export type ExitPlanDigest1 = string;
export type ExitPlanRef3 = string;
export type ExitResultDigest = string;
export type ExitResultRef = string;
export type Generation16 = number;
export type PolicyDigest6 = string;
export type RunId17 = string;
export type ScopeDigest7 = string;
export type WorkPackageDigest5 = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs18 = string[];
export type ItemId = string;
export type Owner = string;
export type RequiredForExit = boolean;
export type State9 =
  | "preserved"
  | "local_denied"
  | "termination_pending"
  | "revocation_pending"
  | "deleted_active"
  | "backup_pending"
  | "held"
  | "exported_unrecallable"
  | "confirmed"
  | "unknown";
export type CaseId29 = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs19 = string[];
export type ItemId1 = string;
export type Owner1 = string;
export type RequiredForExit1 = boolean;
export type State10 =
  | "preserved"
  | "local_denied"
  | "termination_pending"
  | "revocation_pending"
  | "deleted_active"
  | "backup_pending"
  | "held"
  | "exported_unrecallable"
  | "confirmed"
  | "unknown";
/**
 * @maxItems 256
 */
export type CleanupItems = ExitItem[];
export type ExitId = string;
export type LegacyObligationsRef1 = string;
export type MerchantAssetsRef = string;
export type Outcome6 = "complete" | "pending" | "failed_safe" | "unknown";
/**
 * @maxItems 256
 */
export type PersistentRuntimeEvidenceRefs = string[];
/**
 * @maxItems 256
 */
export type PostDenialObservationRefs = string[];
export type RunId18 = string;
export type TemporaryAssetsRef = string;
export type CandidateChangeRequired = boolean;
export type CaseId30 = string;
/**
 * @maxItems 256
 */
export type DependencyCheckRefs = string[];
export type DesiredAssetManifestRef = string;
export type FinalCandidateRef = string | null;
export type FinalisationId = string;
export type Generation17 = number;
/**
 * @maxItems 256
 */
export type IndependenceCriteriaRefs = string[];
export type PlanDigest4 = string;
/**
 * @maxItems 256
 */
export type RequiredActionSlotIds = string[];
export type RunId19 = string;
/**
 * @maxItems 256
 */
export type ValidationRequestRefs = string[];
export type ExpectedManifestDigest1 = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "GuardEventKind".
 */
export type GuardEventKind = "ATTEMPT" | "APPROVED" | "CAPTURED" | "DECLINED" | "ERROR" | "REFUNDED";
export type GraftId8 = string;
export type LatencyMs = number;
export type LibVersion = string;
export type OrderRef1 = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Side".
 */
export type Side = "OLD" | "NEW";
export type ShopId3 = string;
export type Signature1 = string | null;
export type Ts = string;
export type FreezeWindowAdvice = string;
export type Amount = number;
export type Currency1 =
  | "AUD"
  | "BRL"
  | "CAD"
  | "CHF"
  | "CNY"
  | "CZK"
  | "DKK"
  | "EUR"
  | "GBP"
  | "HKD"
  | "HUF"
  | "ILS"
  | "JPY"
  | "MXN"
  | "MYR"
  | "NOK"
  | "NZD"
  | "PHP"
  | "PLN"
  | "RUB"
  | "SEK"
  | "SGD"
  | "THB"
  | "TWD"
  | "USD";
export type CustomerRef = string;
export type Cycle = string;
export type Id7 = string;
export type NextBilling = string | null;
export type Source1 = string;
export type Status9 = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HandoffType".
 */
export type HandoffType = "BILLING_AGREEMENT" | "RECURRING_PROFILE";
export type Records = HandoffRecord[];
export type Duplicates = string[];
export type Inactive = number;
export type TotalsPerCurrency = Money[];
export type Amount1 = number;
export type Currency2 =
  | "AUD"
  | "BRL"
  | "CAD"
  | "CHF"
  | "CNY"
  | "CZK"
  | "DKK"
  | "EUR"
  | "GBP"
  | "HKD"
  | "HUF"
  | "ILS"
  | "JPY"
  | "MXN"
  | "MYR"
  | "NOK"
  | "NZD"
  | "PHP"
  | "PLN"
  | "RUB"
  | "SEK"
  | "SGD"
  | "THB"
  | "TWD"
  | "USD";
export type CustomerRef1 = string;
export type Cycle1 = string;
export type Id8 = string;
export type NextBilling1 = string | null;
export type Source2 = string;
export type Status10 = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HealAction".
 */
export type HealAction = "HOLD" | "STEP_UP" | "CUTBACK";
export type FromStagePct = 0 | 1 | 10 | 50 | 100;
export type GraftId9 = string;
export type HardStop = string | null;
export type Reason = string;
export type NNew = number;
export type NOld = number;
export type ProbNewNotWorse = number;
export type SuccessNew = number;
export type SuccessOld = number;
export type Threshold = number;
export type ToStagePct = 0 | 1 | 10 | 50 | 100;
export type CreatedAt13 = string;
export type CutbackRequested = boolean;
export type EvidenceRefs20 = string[];
export type GraftId10 = string;
export type Id9 = string;
export type PauseRequested = boolean;
export type StagePct = 0 | 1 | 10 | 50 | 100;
export type Text = string;
export type CreatedAt14 = string;
export type GraftId11 = string;
export type Id10 = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HeraldKind".
 */
export type HeraldKind = "GRAFT_CARD" | "PR_BODY" | "HANDOFF" | "VERDICT_EXPLAIN";
export type EntryHash = string;
export type JsonPointer = string;
export type Value = number;
export type NumbersUsed = LedgerNumber[];
export type Text1 = string;
export type Code3 = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs21 = string[];
export type InputRef1 = string | null;
export type OwnerRole1 = string;
export type Recovery1 =
  | "retry_read"
  | "reconnect"
  | "supply_input"
  | "review_scope"
  | "reapprove"
  | "await_counterpart"
  | "reconcile"
  | "unsupported";
export type PlanDigest5 = string;
export type PlanRef = string;
export type ReviewedBundleDigest1 = string;
export type Artifacts = string[];
export type Error = string | null;
export type Finished = string;
export type JobId = string;
export type LogsRef = string;
export type RateLimitPauses = number;
export type RawCaptureRefs = string[];
export type RunId20 = string;
export type Sha1 = string;
export type Workflow1 = string;
export type Started = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "JobStatus".
 */
export type JobStatus = "OK" | "FAILED" | "TIMEOUT" | "BLOCKED";
export type GraftId12 = string;
export type JobId1 = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "JobKind".
 */
export type JobKind = "BUILD" | "RECORD" | "PROVE" | "MUTANT_RUN" | "SHADOW" | "GAUNTLET";
export type MutantIds = string[];
export type ScenarioIds = string[];
export type SecretsRef1 = string;
export type ShopPackRef = string;
export type Signature2 = string | null;
export type BuildS = number;
export type RunS = number;
export type TotalS = number;
/**
 * @minItems 1
 */
export type Variants = [Variant1, ...Variant1[]];
export type CreatedAt15 = string;
export type GraftId13 = string;
export type Id11 = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Lane".
 */
export type Lane = "FULL" | "NO-RUNTIME" | "NO-CODE";
export type Reason1 = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "LedgerEntryV1".
 */
export type LedgerEntryV1 =
  | {
      entry_hash: EntryHash1;
      graft_id: GraftId14;
      inputs: Inputs;
      payload:
        | boolean
        | number
        | string
        | JsonValue[]
        | {
            [k: string]: JsonValue;
          }
        | null;
      payload_hash: PayloadHash;
      payload_ref?: never;
      prev_hash: PrevHash;
      producer: Producer;
      schema: Schema1;
      seq: Seq1;
      ts: Ts1;
      type: EntryType;
    }
  | {
      entry_hash: EntryHash1;
      graft_id: GraftId14;
      inputs: Inputs;
      payload?: never;
      payload_hash: PayloadHash;
      payload_ref: string;
      prev_hash: PrevHash;
      producer: Producer;
      schema: Schema1;
      seq: Seq1;
      ts: Ts1;
      type: EntryType;
    };
export type EntryHash1 = string;
export type GraftId14 = string;
export type Inputs = string[];
export type PayloadHash = string;
export type PrevHash = string;
export type Schema1 = string;
export type Seq1 = number;
export type Ts1 = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "EntryType".
 */
export type EntryType = "STAGE" | "ARTIFACT" | "MESSAGE" | "VERDICT" | "SWITCH" | "ALERT" | "COST";
/**
 * @maxItems 256
 */
export type ActiveEffectRefs1 = string[];
export type Attempt3 = number;
export type CaseId31 = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs22 = string[];
export type Generation18 = number;
export type ResourceGraphDigest3 = string;
export type RunId21 = string;
export type ScopeDigest8 = string;
export type Stage2 =
  | "BASELINE_VERIFY"
  | "BASELINE_RUN"
  | "CANDIDATE_READY"
  | "VALIDATING"
  | "REVIEW_READY"
  | "AWAITING_APPLY"
  | "PUBLISHING"
  | "MERGING"
  | "DEPLOY_PREPARED"
  | "DEPLOYING"
  | "OBSERVING"
  | "FINALISING"
  | "EXITING"
  | "COMPLETE"
  | "HELD"
  | "FAILED_SAFE"
  | "INCIDENT_UNKNOWN";
export type UpdatedAt3 = string;
export type WorkId3 = string;
export type WorkPackageDigest6 = string;
export type WorkPackageRef3 = string;
export type BudgetRef2 = string;
export type Deadline2 = string;
export type ExpectedOutputSchema = string;
/**
 * @maxItems 256
 */
export type ForbiddenEffectCodes = string[];
export type Generation19 = number;
/**
 * @maxItems 256
 */
export type InputArtifactRefs = string[];
export type OperationKind =
  | "build_baseline"
  | "run_baseline"
  | "validate_candidate"
  | "build_candidate"
  | "run_scenario"
  | "run_mutant"
  | "validate_driver"
  | "selfcheck_recipe";
export type PackageDigest1 = string;
export type PackageRef = string;
export type PolicyDigest7 = string;
export type RequestId3 = string;
export type RunId22 = string;
export type RuntimeProfileDigest3 = string;
export type AcceptedAt1 = string;
export type Generation20 = number;
export type RequestDigest1 = string;
export type RequestId4 = string;
export type RunId23 = string;
export type AuthenticityRef4 = string;
export type CompletedAt1 = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs23 = string[];
export type Generation21 = number;
export type InputsDigest = string;
/**
 * @maxItems 256
 */
export type LimitationCodes = string[];
export type Outcome7 = "completed" | "failed" | "blocked" | "unknown";
/**
 * @maxItems 256
 */
export type OutputArtifactRefs = string[];
export type RequestId5 = string;
export type RunId24 = string;
export type SourceUnchanged = boolean;
export type WorkerIdentityRef = string;
export type HostedButtonId = string | null;
export type NewLinkUrl = string;
export type OldFormFields = {
  [k: string]: string;
} | null;
export type Page = string;
export type SnippetHtml = string;
export type Buttons = LinkButton[];
export type CaptureId2 = string;
export type Link = string;
export type OrderId2 = string;
export type Proofs = LinkProof[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "UntouchedKind".
 */
export type UntouchedKind = "Donate" | "Subscribe";
export type Untouched = UntouchedKind[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ManifestEntryV1".
 */
export type ManifestEntryV1 =
  | {
      bytes: Bytes1;
      file_type: FileType2;
      relative_path: RelativePath1;
      sha256: string;
    }
  | {
      bytes: 0;
      file_type: FileType3;
      relative_path: RelativePath1;
      sha256: null;
    };
export type Bytes1 = number;
export type FileType2 = "file";
export type RelativePath1 = string;
export type FileType3 = "directory";
export type Notes = string;
export type SignalFields = string[];
export type Source3 = string;
export type BudgetId = string;
export type CeilingMicroUsd = number;
export type OutstandingMicroUsd = number;
export type PricingRef = string;
export type SpentMicroUsd = number;
export type TargetMicroUsd = number;
export type UnknownMicroUsd = number;
/**
 * @maxItems 256
 */
export type AllowedToolIds1 = string[];
export type BudgetReservationRef = string;
export type ContextDigest = string;
export type ContextRef = string;
export type Deadline3 = string;
export type Generation22 = number;
export type InputTokenCap = number;
export type LeaseEpoch2 = number;
export type ModelProfileRef1 = string;
export type OutputSchema = string;
export type OutputTokenCap = number;
export type TaskId3 = string;
export type TurnId = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ModelTurnResultV1".
 */
export type ModelTurnResultV1 =
  | {
      calls: Calls;
      final_artifact_ref: null;
      issue: null;
      kind: Kind11;
      provider_receipt_ref: ProviderReceiptRef1;
      task_id: TaskId4;
      turn_id: TurnId1;
      usage_receipt_ref: UsageReceiptRef;
    }
  | {
      calls: Calls1;
      final_artifact_ref: string;
      issue: null;
      kind: Kind12;
      provider_receipt_ref: ProviderReceiptRef1;
      task_id: TaskId4;
      turn_id: TurnId1;
      usage_receipt_ref: UsageReceiptRef;
    }
  | {
      calls: Calls2;
      final_artifact_ref: null;
      issue: Issue;
      kind: Kind13;
      provider_receipt_ref: ProviderReceiptRef1;
      task_id: TaskId4;
      turn_id: TurnId1;
      usage_receipt_ref: UsageReceiptRef;
    };
/**
 * @minItems 1
 * @maxItems 4
 */
export type Calls = [ToolCall, ...ToolCall[]];
export type ArgumentsDigest = string;
export type ArgumentsRef = string;
export type CallId = string;
export type Tool = string;
export type Kind11 = "tool_calls";
export type ProviderReceiptRef1 = string | null;
export type TaskId4 = string;
export type TurnId1 = string;
export type UsageReceiptRef = string;
/**
 * @maxItems 0
 */
export type Calls1 = ToolCall[];
export type Kind12 = "final";
/**
 * @maxItems 0
 */
export type Calls2 = ToolCall[];
export type Kind13 = "blocked";
export type CheckedAt11 = string;
export type ResultRef = string | null;
export type State11 = "intended" | "submitted" | "observed" | "failed" | "unknown";
export type TaskId5 = string;
export type TurnId2 = string;
export type UsageReceiptRef1 = string | null;
export type Currency3 =
  | "AUD"
  | "BRL"
  | "CAD"
  | "CHF"
  | "CNY"
  | "CZK"
  | "DKK"
  | "EUR"
  | "GBP"
  | "HKD"
  | "HUF"
  | "ILS"
  | "JPY"
  | "MXN"
  | "MYR"
  | "NOK"
  | "NZD"
  | "PHP"
  | "PLN"
  | "RUB"
  | "SEK"
  | "SGD"
  | "THB"
  | "TWD"
  | "USD";
export type Minor1 = number;
export type EquivalentSuspect = boolean;
export type Id12 = string;
export type KilledBy = string[];
export type File = string;
export type Line = number;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "MutantOp".
 */
export type MutantOp = "M1" | "M2" | "M3" | "M4" | "M5" | "M6" | "M7" | "M8" | "M9" | "M10" | "M11" | "M12";
export type Patch = string;
export type Rule1 = string;
export type CreatedAt16 = string;
export type GraftId15 = string;
export type Id13 = string;
export type EquivalentSuspect1 = boolean;
export type Id14 = string;
export type KilledBy1 = string[];
export type Patch1 = string;
export type Rule2 = string;
export type Mutants1 = Mutant[];
export type UnguardedRuleIds = string[];
export type Fault = string;
export type RulesBroken = string[];
export type ComponentId = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs24 = string[];
export type Path = string | null;
export type ReasonCode2 = string;
export type RequiredForScope = boolean;
export type ComponentId1 = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs25 = string[];
export type Path1 = string | null;
export type ReasonCode3 = string;
export type RequiredForScope1 = boolean;
/**
 * @maxItems 256
 */
export type Items1 = Omission[];
export type Code4 = string;
export type Detail = string | null;
/**
 * @maxItems 256
 */
export type EvidenceRefs26 = string[];
export type Instance = string | null;
export type ReasonCode4 = string;
export type RecoveryAction = string | null;
export type RequestId6 = string;
export type Retry = "never" | "status_only" | "safe_read" | "reauthorise";
export type Status11 = number;
export type Title2 = string;
export type Type = string;
export type CheckedAt12 = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs27 = string[];
export type RequestId7 = string;
export type State12 = "queued" | "running" | "waiting" | "unknown";
export type CaseId32 = string;
export type Generation23 = number;
export type ParentRequestId = string;
/**
 * @maxItems 256
 */
export type ReasonRefs = string[];
export type RunId25 = string;
/**
 * @minItems 1
 * @maxItems 32
 */
export type Tasks = [TaskSpec, ...TaskSpec[]];
export type CheckedAt13 = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs28 = string[];
export type Predicate1 = "can_review" | "can_prepare_apply" | "can_submit_slot" | "upgrade_verified" | "exit_complete";
export type SlotId4 = string | null;
export type Status12 = "pass" | "missing" | "stale" | "failed" | "unknown";
export type SubjectDigest1 = string;
/**
 * @maxItems 256
 */
export type ApprovalRefs1 = string[];
export type ApprovalSetId2 = string;
export type CaseId33 = string;
export type CheckedAt14 = string;
export type Generation24 = number;
export type PlanDigest6 = string;
/**
 * @maxItems 256
 */
export type RequiredControllerIds3 = string[];
export type RunId26 = string;
export type State13 = "complete" | "missing" | "stale" | "revoked";
export type ArtifactDigest3 = string;
/**
 * @maxItems 256
 */
export type BaselineSnapshotRefs = string[];
export type BundleDigest = string;
export type BundleId = string;
/**
 * @maxItems 256
 */
export type CandidateSnapshotRefs = string[];
export type CaseId34 = string;
export type CreatedAt17 = string;
/**
 * @maxItems 256
 */
export type DomainRuleResultRefs = string[];
export type EffectiveConfigDigest = string;
/**
 * @maxItems 256
 */
export type MissingEvidenceRefs = string[];
export type PatchDigest2 = string;
export type ProposedApplyPlanRef = string;
export type RecoveryPlanRef2 = string;
export type RunId27 = string;
/**
 * @maxItems 256
 */
export type ScenarioResultRefs = string[];
/**
 * @maxItems 256
 */
export type SecurityResultRefs = string[];
/**
 * @maxItems 256
 */
export type UnsupportedPaths = string[];
export type WorkPackageDigest7 = string;
/**
 * @maxItems 256
 */
export type EvidenceSummaryRefs = string[];
/**
 * @maxItems 256
 */
export type Missing = Issue[];
export type BudgetRef3 = string;
export type CaseId35 = string;
export type ExitPlanRef4 = string;
export type ExpiresAt13 = string;
export type FinalisationPlanRef1 = string;
export type Generation25 = number;
export type GraphDigest2 = string;
export type PlanDigest7 = string;
export type PlanId1 = string;
export type PolicyDigest8 = string;
export type RecoveryPlanRef3 = string;
export type ReviewBundleDigest2 = string;
export type RunId28 = string;
export type ScopeDigest9 = string;
/**
 * @minItems 1
 * @maxItems 32
 */
export type Slots1 = [EffectSlot, ...EffectSlot[]];
export type StatePlanRef1 = string;
export type DeadlineNotes = string[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Family".
 */
export type Family =
  | "WPS"
  | "EC_NVP"
  | "EC_SOAP"
  | "DIRECT_PAYMENT"
  | "RECURRING_NVP"
  | "BILLING_AGREEMENT"
  | "IPN"
  | "PDT"
  | "CHECKOUT_JS_V4"
  | "JS_V5"
  | "REST_V1"
  | "SERVER_SDK_OLD"
  | "PAYFLOW"
  | "BUTTON_HOSTED";
export type FamiliesFound = Family[];
export type FilesOrPages = string[];
export type NextStep = string;
export type OfficialModernModuleAvailable = boolean | null;
export type CheckedAt15 = string;
export type CopyScope1 = string;
/**
 * @maxItems 256
 */
export type Limits1 = string[];
export type PolicyDigest9 = string;
/**
 * @maxItems 256
 */
export type Recipients1 = ProcessingRecipient[];
export type Status13 = "qualified" | "missing" | "stale";
export type Name4 = string;
export type Purpose6 = string;
export type RegionText1 = string;
export type RetentionText1 = string;
/**
 * @maxItems 256
 */
export type TermsEvidenceRefs1 = string[];
export type Action = "STEP_UP" | "HOLD" | "CUTBACK";
export type FromStagePct1 = 0 | 1 | 10 | 50 | 100;
export type GraftId16 = string;
export type HardStop1 = string | null;
export type Reason2 = string;
export type ToStagePct1 = 0 | 1 | 10 | 50 | 100;
export type AdviceDigest = string;
export type CaseId36 = string;
export type CheckedAt16 = string;
export type ExpiresAt14 = string | null;
export type Generation26 = number;
export type PolicyDigest10 = string;
export type ProofPlanDigest1 = string;
export type ProofResultDigest1 = string;
export type ProofResultRef1 = string;
export type ReasonCode5 = "EVIDENCE_READY" | "EVIDENCE_HOLD" | "ADVICE_HOLD" | "CUTBACK";
export type RunId29 = string;
export type ScopeDigest10 = string;
export type WorkPackageDigest8 = string;
export type CaseId37 = string;
/**
 * @minItems 1
 * @maxItems 256
 */
export type Checks2 = [ProofCheck, ...ProofCheck[]];
export type CheckId2 = string;
export type Critical = boolean;
export type FlowId = string;
export type InputDigest3 = string;
export type Kind14 =
  "baseline" | "candidate" | "scenario" | "domain_rule" | "security" | "mutation" | "payment" | "isolation" | "exit";
export type OwnerRole2 = string;
export type RequiredEvidenceClass =
  | "scripted"
  | "component_offline"
  | "real_model"
  | "real_provider"
  | "real_payment"
  | "isolation_qualified"
  | "merchant_exit";
export type RequiredSchema = string;
export type RequiredTrust = "collector_observed" | "deterministic_result";
/**
 * @maxItems 256
 */
export type RuleIds = string[];
export type SubjectManifestDigest1 = string;
export type SubjectManifestRef1 = string;
export type CreatedAt18 = string;
export type ApprovalDigest = string;
export type ApprovalRef = string;
export type CheckId3 = string;
export type Reason3 = string;
/**
 * @maxItems 256
 */
export type Exclusions = ProofExclusion[];
export type ExpiresAt15 = string;
export type Generation27 = number;
export type PlanDigest8 = string;
export type PlanId2 = string;
export type PolicyDigest11 = string;
export type RunId30 = string;
export type ScopeDigest11 = string;
export type WorkPackageDigest9 = string;
export type CaseId38 = string;
export type CheckedAt17 = string;
export type Generation28 = number;
export type Outcome8 = "ready" | "partial" | "hold";
export type PlanDigest9 = string;
export type PlanRef1 = string;
export type PolicyDigest12 = string;
/**
 * @minItems 1
 * @maxItems 256
 */
export type ReasonCodes1 = [
  (
    | "VERIFIED"
    | "MISSING"
    | "AUTHENTICATION"
    | "INVALID"
    | "SUBJECT_MISMATCH"
    | "STALE"
    | "INVENTORY_MISMATCH"
    | "EXCLUDED"
    | "FAILED"
    | "UNKNOWN"
    | "UNSUPPORTED"
  ),
  ...(
    | "VERIFIED"
    | "MISSING"
    | "AUTHENTICATION"
    | "INVALID"
    | "SUBJECT_MISMATCH"
    | "STALE"
    | "INVENTORY_MISMATCH"
    | "EXCLUDED"
    | "FAILED"
    | "UNKNOWN"
    | "UNSUPPORTED"
  )[]
];
export type ResultDigest1 = string;
export type ResultId1 = string;
/**
 * @minItems 1
 * @maxItems 256
 */
export type Results = [ProofCheckResult, ...ProofCheckResult[]];
export type CheckId4 = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs29 = string[];
export type ReasonCode6 =
  | "VERIFIED"
  | "MISSING"
  | "AUTHENTICATION"
  | "INVALID"
  | "SUBJECT_MISMATCH"
  | "STALE"
  | "INVENTORY_MISMATCH"
  | "EXCLUDED"
  | "FAILED"
  | "UNKNOWN"
  | "UNSUPPORTED";
export type State14 = "verified" | "missing" | "failed" | "unknown" | "unsupported" | "excluded";
export type SubjectManifestDigest2 = string;
export type SubjectManifestRef2 = string;
export type RunId31 = string;
export type ScopeDigest12 = string;
export type WorkPackageDigest10 = string;
export type EquivalentDropped1 = number;
export type Killed2 = number;
export type Score1 = number;
export type Total = number;
export type CaseId39 = string;
export type ContinuationRef2 = string;
export type ExpiresAt16 = string;
export type IntentId = string;
export type ProviderId3 = string;
export type Purpose7 = "read_connect" | "apply_connect";
export type RedirectUrl = string;
export type ResourceId4 = string | null;
export type AccountId2 = string | null;
export type AdapterVersion1 = string;
export type ProviderId4 = string;
export type EvidenceRef2 = string;
export type Name5 = string;
export type Value1 = string;
export type CheckedAt18 = string;
export type EvidenceClass2 =
  | "scripted"
  | "component_offline"
  | "real_model"
  | "real_provider"
  | "real_payment"
  | "isolation_qualified"
  | "merchant_exit";
export type Integrity = "verified" | "unverified" | "invalid" | "unknown";
/**
 * @maxItems 256
 */
export type Limitations1 = string[];
export type PublicId = string;
export type ScopeText = string;
export type EvidenceRef3 = string;
export type Name6 = string;
export type Value2 = string;
/**
 * @maxItems 256
 */
export type SummaryMetrics = PublicMetric[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RawExchange".
 */
export type RawExchange =
  | {
      body_json?: never;
      body_text: string;
      db_change?: DbChange | null;
      direction: Direction;
      headers: Headers;
      method: Method;
      seq: Seq2;
      status?: Status14;
      t_ms: TMs1;
      url: Url;
    }
  | {
      body_json:
        | boolean
        | number
        | string
        | JsonValue[]
        | {
            [k: string]: JsonValue;
          }
        | null;
      body_text?: never;
      db_change?: DbChange | null;
      direction: Direction;
      headers: Headers;
      method: Method;
      seq: Seq2;
      status?: Status14;
      t_ms: TMs1;
      url: Url;
    }
  | {
      body_json?: never;
      body_text?: never;
      db_change?: DbChange | null;
      direction: "SHOP_DB_WRITE";
      headers: Headers;
      method: Method;
      seq: Seq2;
      status?: Status14;
      t_ms: TMs1;
      url: Url;
    };
export type After1 = {
  [k: string]: JsonValue;
} | null;
export type Before = {
  [k: string]: JsonValue;
} | null;
export type Table = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Direction".
 */
export type Direction =
  "SHOP_TO_PAYPAL" | "PAYPAL_TO_SHOP" | "BROWSER_TO_SHOP" | "PAYPAL_NOTIFY_TO_SHOP" | "SHOP_DB_WRITE";
export type Method = string;
export type Seq2 = number;
export type Status14 = number | null;
export type TMs1 = number;
export type Url = string;
export type Exchanges = RawExchange[];
export type GraftId17 = string;
export type RunId32 = string;
export type ScenarioId1 = string;
export type Confidence = number;
export type Compose = string;
export type Dockerfile = string;
export type DriverTemplate = string;
export type Seed = string;
export type AstShapeHash = string;
export type Framework = string;
export type Lang = string;
export type Id15 = string;
export type Provenance2 = string[];
export type Scenarios2 = string[];
export type Signature3 = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RecipeStatus".
 */
export type RecipeStatus = "QUARANTINE" | "ACTIVE" | "RETIRED";
export type Transform = string;
export type CatalogRef1 = string;
export type Fingerprint1 = string;
export type DetectionRuleRef = string | null;
export type RecipeRef2 = string;
/**
 * @maxItems 256
 */
export type AffectedEffectRefs = string[];
/**
 * @maxItems 256
 */
export type BaselineRefs = string[];
export type CaseId40 = string;
export type ChosenRoute = "code_cutback" | "config_cutback" | "forward_repair" | "safe_hold";
/**
 * @maxItems 256
 */
export type CompensatableEffects = string[];
/**
 * @maxItems 256
 */
export type IrreversibleEffects = string[];
export type OriginalTransactionRoutesRef = string;
export type PlanDigest10 = string;
export type PlanId3 = string;
/**
 * @maxItems 256
 */
export type RequiredCurrentAuthority = string[];
export type RestorePreconditionsRef = string;
/**
 * @maxItems 256
 */
export type ReversibleEffects = string[];
export type StateCompatibilityRef = string;
/**
 * @maxItems 256
 */
export type UnknownEffects = string[];
/**
 * @maxItems 256
 */
export type VerificationCaseRefs = string[];
export type Enabled1 = boolean;
export type Kind15 = string;
export type ReasonCode7 = string | null;
/**
 * @maxItems 256
 */
export type ResourceIds3 = string[];
/**
 * @maxItems 256
 */
export type AcceptanceRuleIds = string[];
export type FlowId1 = string;
export type Limitation2 = string | null;
/**
 * @maxItems 256
 */
export type OriginRoutes = string[];
export type PaymentFamily = string;
export type Required3 = boolean;
/**
 * @maxItems 256
 */
export type ScenarioRefs = string[];
/**
 * @maxItems 256
 */
export type AcceptanceRuleIds1 = string[];
export type FlowId2 = string;
export type Limitation3 = string | null;
/**
 * @maxItems 256
 */
export type OriginRoutes1 = string[];
export type PaymentFamily1 = string;
export type Required4 = boolean;
/**
 * @maxItems 256
 */
export type ScenarioRefs1 = string[];
/**
 * @maxItems 256
 */
export type Flows = RequiredFlow[];
export type DeliveryRoute1 = "git_protected" | "direct_artifact";
export type CaseId41 = string;
export type CheckedAt19 = string;
/**
 * @maxItems 256
 */
export type CurrentRuntimeEvidenceRefs1 = string[];
export type EffectId2 = string;
export type EnvironmentId3 = string;
export type ObservedArtifactDigest1 = string | null;
export type ObservedConfigDigest1 = string | null;
export type Outcome9 = "pending" | "verified" | "failed" | "unknown";
export type Provider1 = string;
export type ProviderDeployId1 = string | null;
export type ProviderStatus1 = string;
export type ResourceId5 = string;
export type SubmittedArtifactDigest1 = string;
export type CaseId42 = string;
/**
 * @maxItems 256
 */
export type CleanupItems1 = ExitItem[];
export type ExitId1 = string;
export type LegacyObligationsRef2 = string;
export type MerchantAssetsRef1 = string;
export type Outcome10 = "complete" | "pending" | "failed_safe" | "unknown";
/**
 * @maxItems 256
 */
export type PersistentRuntimeEvidenceRefs1 = string[];
/**
 * @maxItems 256
 */
export type PostDenialObservationRefs1 = string[];
export type RunId33 = string;
export type TemporaryAssetsRef1 = string;
export type AllowedRestartCount1 = number;
/**
 * @maxItems 256
 */
export type AuthorityRefs4 = string[];
export type BudgetRef4 = string;
export type CaseId43 = string;
/**
 * @maxItems 256
 */
export type CriteriaRefs1 = string[];
export type Deadline4 = string;
export type EvidenceReadAuthorityRef2 = string;
export type ExecutorIdentityRef2 = string;
export type ExitPlanId1 = string;
export type FailureRouteRef1 = string;
export type FinalArtifactDigest3 = string;
export type FinalConfigDigest3 = string;
export type Generation29 = number;
export type PlanDigest11 = string;
export type PrivateEvidenceDestinationRef1 = string;
export type RecoveryPlanRef4 = string;
export type ReservationRef3 = string;
export type RunId34 = string;
export type StateDigest2 = string;
export type TrustedCodeDigest2 = string;
/**
 * @maxItems 256
 */
export type Assets1 = Asset[];
export type CaseId44 = string;
export type FinalArtifactDigest4 = string;
export type FinalConfigDigest4 = string;
export type LegacyObligationsRef3 = string;
export type ManifestDigest1 = string;
export type ManifestId1 = string;
export type RunId35 = string;
export type CheckedAt20 = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs30 = string[];
export type Predicate2 = "can_review" | "can_prepare_apply" | "can_submit_slot" | "upgrade_verified" | "exit_complete";
export type SlotId5 = string | null;
export type Status15 = "pass" | "missing" | "stale" | "failed" | "unknown";
export type SubjectDigest2 = string;
/**
 * @maxItems 256
 */
export type PredicateResults = PredicateResult[];
export type ActionPlanRef1 = string;
export type CaseId45 = string;
/**
 * @maxItems 256
 */
export type ExpectedVersionRefs = string[];
export type LeaseUntil1 = string;
export type ReservationId = string;
export type RunId36 = string;
export type State15 = "held" | "reconciling" | "releasable" | "released";
/**
 * @maxItems 256
 */
export type TargetKeys = TargetKey[];
/**
 * @maxItems 256
 */
export type UnresolvedEffectRefs = string[];
export type ActionPlanRef2 = string | null;
export type ApprovalSetRef1 = string | null;
export type CancellationRef1 = string | null;
export type CaseId46 = string;
export type CheckedAt21 = string;
/**
 * @maxItems 256
 */
export type CurrentEvidenceRefs1 = string[];
export type DeploymentRef1 = string | null;
export type ExitManifestRef2 = string | null;
export type ExitPlanRef5 = string | null;
export type FinalAssetManifestRef1 = string | null;
export type Generation30 = number;
export type GraphRef3 = string;
export type LifecycleRef1 = string;
/**
 * @maxItems 256
 */
export type PendingEffectRefs1 = string[];
export type ReservationRef4 = string | null;
export type ReviewRef1 = string | null;
export type RunId37 = string;
export type StateCutoverRef1 = string | null;
export type StateVersion4 = number;
export type AdmissionRef = string;
export type CaseId47 = string;
export type CutoverId = string;
/**
 * @maxItems 256
 */
export type DrainEvidenceRefs = string[];
/**
 * @maxItems 256
 */
export type EvidenceRefs31 = string[];
export type ExportManifestRef = string;
export type Generation31 = number;
export type HandlerInventoryRef = string;
export type HighWaterRef = string;
export type IngressRef = string;
export type OriginRouteRef = string;
export type Outcome11 = "prepared" | "fenced" | "exported" | "restored" | "replayed" | "verified" | "held" | "unknown";
/**
 * @maxItems 256
 */
export type PendingExternalEffectRefs = string[];
export type ReplayManifestRef = string;
export type RestoreManifestRef = string;
export type RunId38 = string;
export type SchemaDigest = string;
export type StateDigest3 = string;
export type WriterInventoryRef = string;
export type ApprovedAt = string;
export type AuthorityBasis = "provider_verified" | "controller_attested";
/**
 * @maxItems 256
 */
export type AuthorityEvidenceRefs = string[];
export type BindingId = string;
export type CaseId48 = string;
export type CheckedAt22 = string;
export type ControllerId2 = string;
export type Epoch = number;
/**
 * @maxItems 256
 */
export type GrantedActions = ("view" | "connect" | "start" | "review")[];
export type NodeId4 = string;
export type PrincipalId = string;
export type Role1 = "requester" | "controller" | "reviewer";
/**
 * @maxItems 256
 */
export type Recipients2 = ResourceRecipient[];
export type RelationDigest = string;
export type RequesterId3 = string;
export type RevokedAt3 = string | null;
export type EdgeId = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs32 = string[];
export type FromNode = string;
export type Relation = "builds_from" | "routes_to" | "stores_state_in" | "receives_callback_from" | "depends_on";
export type RequiredForScope2 = boolean;
export type ToNode = string;
export type CaseId49 = string;
export type EdgeId1 = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs33 = string[];
export type FromNode1 = string;
export type Relation1 = "builds_from" | "routes_to" | "stores_state_in" | "receives_callback_from" | "depends_on";
export type RequiredForScope3 = boolean;
export type ToNode1 = string;
/**
 * @maxItems 256
 */
export type Edges = ResourceEdge[];
export type GraphDigest3 = string;
export type GraphId = string;
/**
 * @maxItems 256
 */
export type BindingRefs2 = string[];
export type EnvironmentId4 = string | null;
/**
 * @maxItems 256
 */
export type EvidenceRefs34 = string[];
export type Kind16 =
  "source" | "frontend" | "backend" | "datastore" | "callback" | "scheduled_job" | "external_service" | "artifact";
export type NodeId5 = string;
export type ProviderResourceId = string | null;
export type RequiredForScope4 = boolean;
export type Kind17 = "git_commit" | "provider_revision_set" | "capture";
export type Value3 = string;
/**
 * @maxItems 256
 */
export type Nodes = ResourceNode[];
/**
 * @maxItems 256
 */
export type BindingRefs3 = string[];
export type EnvironmentId5 = string | null;
/**
 * @maxItems 256
 */
export type EvidenceRefs35 = string[];
export type Kind18 =
  "source" | "frontend" | "backend" | "datastore" | "callback" | "scheduled_job" | "external_service" | "artifact";
export type NodeId6 = string;
export type ProviderResourceId1 = string | null;
export type RequiredForScope5 = boolean;
export type PrincipalId1 = string;
export type Role2 = "requester" | "controller" | "reviewer";
/**
 * @maxItems 256
 */
export type CheckRefs1 = string[];
export type ControllerState1 = "unbound" | "waiting" | "approved" | "revoked" | "unknown";
export type Environment1 = string;
export type Label1 = string;
export type NodeId7 = string;
/**
 * @maxItems 256
 */
export type PermittedActions1 = string[];
export type ReadScopeText1 = string;
export type SourceSnapshotRef3 = string | null;
export type ExpectedStateVersion1 = number;
export type ScopeDigest13 = string;
export type ArtifactDigest4 = string;
/**
 * @maxItems 256
 */
export type BaselineSnapshotRefs1 = string[];
export type BundleDigest1 = string;
export type BundleId1 = string;
/**
 * @maxItems 256
 */
export type CandidateSnapshotRefs1 = string[];
export type CaseId50 = string;
export type CreatedAt19 = string;
/**
 * @maxItems 256
 */
export type DomainRuleResultRefs1 = string[];
export type EffectiveConfigDigest1 = string;
/**
 * @maxItems 256
 */
export type MissingEvidenceRefs1 = string[];
export type PatchDigest3 = string;
export type ProposedApplyPlanRef1 = string;
export type RecoveryPlanRef5 = string;
export type RunId39 = string;
/**
 * @maxItems 256
 */
export type ScenarioResultRefs1 = string[];
/**
 * @maxItems 256
 */
export type SecurityResultRefs1 = string[];
/**
 * @maxItems 256
 */
export type UnsupportedPaths1 = string[];
export type WorkPackageDigest11 = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Lens".
 */
export type Lens = "code" | "runtime" | "site" | "account";
export type LensesRun = Lens[];
export type Selector = string;
export type Url1 = string;
export type Tcode = string;
export type Approve = (FileLocation | SiteLocation | AccountLocation)[];
export type Capture = (FileLocation | SiteLocation | AccountLocation)[];
export type Create = (FileLocation | SiteLocation | AccountLocation)[];
export type MarkPaid = (FileLocation | SiteLocation | AccountLocation)[];
export type Notify = (FileLocation | SiteLocation | AccountLocation)[];
export type Recurring = (FileLocation | SiteLocation | AccountLocation)[];
export type Refund = (FileLocation | SiteLocation | AccountLocation)[];
export type MatchedByStatic = number;
export type Misses = string[];
export type RuntimeCallsTotal = number;
export type ShopId4 = string;
export type Db = string;
export type Framework1 = string;
export type Lang1 = string;
export type Confidence1 = number;
export type Id16 = string;
export type Lenses = Lens[];
export type Live = boolean;
export type Location = FileLocation | SiteLocation | AccountLocation;
export type Operation6 = string;
export type PaypalOnly = boolean;
export type PaypalMappingId = string;
export type RestOp = string;
export type Touchpoints = Touchpoint[];
export type CorrectFlow1 = string[];
export type CounterExamples1 = string[];
export type Id17 = string;
export type Predicate3 = string;
export type Title3 = string;
export type CancellationRef2 = string | null;
export type CaseId51 = string;
export type Generation32 = number;
export type LastEventSeq2 = number;
export type RunId40 = string;
export type StateVersion5 = number;
export type Attempt4 = number;
export type CaseId52 = string;
export type CheckpointRef1 = string | null;
export type CreatedAt20 = string;
export type Deadline5 = string;
export type Generation33 = number;
export type InputDigest4 = string;
export type LeaseEpoch3 = number;
export type LeaseOwner1 = string | null;
export type LeaseUntil2 = string | null;
export type ModelProfileRef2 = string | null;
export type NextWakeAt2 = string | null;
/**
 * @maxItems 256
 */
export type OutputRefs3 = string[];
export type PolicyDigest13 = string;
export type PolicyRef1 = string;
export type PromptDigest1 = string;
export type PromptRef1 = string;
export type RequestId8 = string;
export type RunId41 = string;
export type State16 =
  | "pending"
  | "ready"
  | "leased"
  | "running"
  | "waiting"
  | "retry_due"
  | "succeeded"
  | "held"
  | "unknown"
  | "failed"
  | "cancelled";
export type StateVersion6 = number;
export type WakeConditionRef1 = string | null;
/**
 * @maxItems 32
 */
export type Tasks1 = AgentTask[];
export type BaseUrl = string;
export type Compose1 = string;
export type Seed1 = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs36 = string[];
export type ReasonCode8 = string;
export type RunRef2 = string;
export type FlakeFreeRuns = number;
export type PassesOnOld = boolean;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ScenarioFamily".
 */
export type ScenarioFamily =
  | "HAPPY"
  | "CANCEL"
  | "DECLINE"
  | "PAYER_ACTION"
  | "DOUBLE"
  | "LOST_RESPONSE"
  | "TAMPER"
  | "PENDING"
  | "REFUND"
  | "REFUND_TWICE"
  | "NOTIFY_FORGED"
  | "NOTIFY_DUP"
  | "RESTART"
  | "RENEWAL"
  | "EDGE_CURRENCY"
  | "PROPERTY";
export type Id18 = string;
export type Rules1 = string[];
export type Steps1 = (DriverStep | ApiStep | MockStep)[];
export type CreatedAt21 = string;
export type GraftId18 = string;
export type Id19 = string;
export type Id20 = string;
export type Rules2 = string[];
export type Steps2 = (DriverStep | ApiStep | MockStep)[];
export type Scenarios3 = Scenario1[];
export type UnguardedRuleIds1 = string[];
export type MutantSetRef = string;
export type ScenarioSetRef = string;
export type Touchpoints1 = Touchpoint[];
export type BuyerScript = string;
export type EnvNeeded = string[];
export type Framework2 = string;
export type HealthUrl = string;
export type Language1 = string;
export type Licence = string;
export type Name7 = string;
export type Port = number;
export type ScenariosSupported = string[];
export type ShopId5 = string;
export type Commit2 = string;
export type Repo2 = string;
export type Start = ComposeStart | CommandStart;
export type ComposeFile = string;
export type Command = string;
export type MaxBytes1 = number;
export type Path2 = string;
export type SnapshotRef1 = string;
export type Kind19 = "git_commit" | "provider_revision_set" | "capture";
export type Value4 = string;
/**
 * @maxItems 256
 */
export type AuthorityBindingRefs = string[];
export type CapturedAt = string;
export type CaseId53 = string;
export type Completeness = "complete_for_declared_scope" | "incomplete" | "unknown";
export type FileCount = number;
export type ManifestDigest2 = string;
export type OmissionManifestRef = string;
export type ProvenanceClass = "provider_reported" | "controller_attested" | "verified_build_link";
export type SnapshotId = string;
export type SourceKind = "git" | "local_folder" | "cloud_files" | "host_export";
export type SourceResourceId = string | null;
export type TotalBytes = number;
export type Name8 = string;
export type Attempt5 = number;
export type EvidenceRefs37 = string[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "StageName".
 */
export type StageName = Stage | ("LANE_NO_CODE" | "LANE_NO_RUNTIME" | "LANE_MAP_ONLY");
export type GraftId19 = string;
export type Reason4 = string;
export type ActionId2 = string;
export type ReadinessDigest4 = string;
export type ReadinessId4 = string;
export type AdmissionRef1 = string;
export type CaseId54 = string;
export type CutoverId1 = string;
/**
 * @maxItems 256
 */
export type DrainEvidenceRefs1 = string[];
/**
 * @maxItems 256
 */
export type EvidenceRefs38 = string[];
export type ExportManifestRef1 = string;
export type Generation34 = number;
export type HandlerInventoryRef1 = string;
export type HighWaterRef1 = string;
export type IngressRef1 = string;
export type OriginRouteRef1 = string;
export type Outcome12 = "prepared" | "fenced" | "exported" | "restored" | "replayed" | "verified" | "held" | "unknown";
/**
 * @maxItems 256
 */
export type PendingExternalEffectRefs1 = string[];
export type ReplayManifestRef1 = string;
export type RestoreManifestRef1 = string;
export type RunId42 = string;
export type SchemaDigest1 = string;
export type StateDigest4 = string;
export type WriterInventoryRef1 = string;
export type RunRef3 = string;
export type AuthenticityRef5 = string;
export type CaseId55 = string;
export type CollectorIdentityRef1 = string;
export type DerivationId = string;
export type Generation35 = number;
export type Operation7 = "candidate_patch" | "artifact_build" | "evidence_derivation";
/**
 * @maxItems 256
 */
export type OutputRefs4 = string[];
export type OutputSubject = string;
/**
 * @maxItems 256
 */
export type ParentRefs = string[];
export type ParentSubject = string;
export type RecipeOrPatchDigest = string;
export type RunId43 = string;
export type TaskId6 = string;
export type ConfigDigest3 = string | null;
export type OciManifestDigest1 = string | null;
export type RuntimeProfileDigest4 = string;
export type ScopeDigest14 = string;
/**
 * @maxItems 256
 */
export type SourceSnapshotRefs3 = string[];
export type SourceTreeDigest1 = string | null;
export type ExpiresAt17 = string;
export type GraftId20 = string;
export type OriginRules = string[];
export type Signature4 = string;
export type StagePct1 = 0 | 1 | 10 | 50 | 100;
export type Version3 = number;
export type AccountId3 = string;
export type EnvironmentId6 = string;
export type ProviderId5 = string;
export type ResourceId6 = string;
export type ResourceKind1 = string;
export type Description = string;
export type Id21 = string;
export type MappingId = string;
export type Deltas = IntentDelta[];
export type Handoff = string[];
export type DeltaIds = string[];
export type MappingId1 = string;
export type PaypalOnly1 = boolean;
export type TargetOp = string;
export type Touchpoint1 = string;
export type Items2 = PlanItem[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "PlanOrder".
 */
export type PlanOrder = "READ_BOTH" | "NEW_FLOWS_BEHIND_SWITCH" | "CLEANUP";
export type Order = PlanOrder[];
export type OriginRules1 = string[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "PlanPath".
 */
export type PlanPath = "OFFICIAL_MODULE" | "REWRITE" | "LINKS";
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "TargetExperience".
 */
export type TargetExperience1 =
  "V6" | "ORDERS_V2" | "WEBHOOKS" | "VAULT" | "PAY_LATER_MSG" | "PLACEMENT" | "AGENT_READY_CHECK";
export type TargetExperience = TargetExperience1[];
export type ActionPlanRef3 = string;
export type CaseId56 = string;
/**
 * @maxItems 256
 */
export type ExpectedVersionRefs1 = string[];
export type LeaseUntil3 = string;
export type ReservationId1 = string;
export type RunId44 = string;
export type State17 = "held" | "reconciling" | "releasable" | "released";
/**
 * @maxItems 256
 */
export type TargetKeys1 = TargetKey[];
/**
 * @maxItems 256
 */
export type UnresolvedEffectRefs1 = string[];
/**
 * @maxItems 256
 */
export type BudgetReservationRefs = string[];
/**
 * @maxItems 256
 */
export type CommittedMessageRefs = string[];
export type ContextDigest1 = string;
export type CreatedAt22 = string;
export type Generation36 = number;
/**
 * @maxItems 24
 */
export type InvocationRefs = string[];
export type LeaseEpoch4 = number;
export type NextStep1 = "model_turn" | "await_tool" | "validate_output";
export type PolicyDigest14 = string;
/**
 * @maxItems 256
 */
export type StagedOutputRefs = string[];
export type TaskId7 = string;
export type Turn = number;
export type WakeConditionRef2 = string | null;
/**
 * @maxItems 256
 */
export type AllowedToolIds2 = string[];
export type BudgetRef5 = string;
export type CaseId57 = string;
export type CheckpointRef2 = string | null;
export type Deadline6 = string;
/**
 * @maxItems 256
 */
export type ExpectedSchemas1 = string[];
export type ExpectedSubject2 = string;
export type Generation37 = number;
/**
 * @maxItems 256
 */
export type InputRefs4 = string[];
export type LeaseEpoch5 = number;
export type Operation8 =
  | "verify_package"
  | "survey"
  | "explain_status"
  | "audit"
  | "propose_plan"
  | "build_baseline"
  | "build_candidate"
  | "validate_driver"
  | "run_scenario"
  | "scribe_draft"
  | "scribe_final"
  | "architect"
  | "candidate_patch"
  | "run_mutant"
  | "derive_guards"
  | "diagnose"
  | "learn"
  | "selfcheck_recipe"
  | "aggregate";
export type PolicyRef2 = string;
export type PromptRef2 = string;
export type Role3 =
  | "Gardener"
  | "Surveyor"
  | "Builder"
  | "Explorer"
  | "Scribe"
  | "Architect"
  | "Grafter"
  | "Adversary"
  | "Healer"
  | "Librarian"
  | "Herald"
  | "Orchard Analyst"
  | "Sentinel";
export type RunId45 = string;
export type TaskRef = string;
export type CaseId58 = string;
export type CausationId = string;
export type CorrelationId = string;
export type EventId1 = string;
export type Generation38 = number;
export type Kind20 =
  | "task_ready"
  | "task_changed"
  | "tool_observed"
  | "approval_changed"
  | "cancellation_changed"
  | "timer_due"
  | "evidence_changed";
export type OccurredAt1 = string;
export type PayloadDigest4 = string;
export type PayloadRef1 = string;
export type RunId46 = string;
export type Sequence1 = number;
export type TaskId8 = string | null;
export type ContextRef1 = string;
export type Generation39 = number;
export type LeaseEpoch6 = number;
export type LeaseUntil4 = string;
export type RunId47 = string;
export type TaskId9 = string;
export type TaskVersion = number;
export type WorkerId = string;
/**
 * @maxItems 256
 */
export type AllowedToolIds3 = string[];
/**
 * @maxItems 32
 */
export type Dependencies2 = string[];
/**
 * @minItems 1
 * @maxItems 16
 */
export type ExpectedSchemas2 = [string, ...string[]];
export type ExpectedSubject3 = string;
/**
 * @maxItems 256
 */
export type InputRefs5 = string[];
export type Operation9 =
  | "verify_package"
  | "survey"
  | "explain_status"
  | "audit"
  | "propose_plan"
  | "build_baseline"
  | "build_candidate"
  | "validate_driver"
  | "run_scenario"
  | "scribe_draft"
  | "scribe_final"
  | "architect"
  | "candidate_patch"
  | "run_mutant"
  | "derive_guards"
  | "diagnose"
  | "learn"
  | "selfcheck_recipe"
  | "aggregate";
export type OutputSlot1 = string;
export type OutputSubjectPolicy1 = "same_subject" | "candidate_child" | "build_from_source" | "derived_evidence";
export type Required5 = boolean;
export type Role4 =
  | "Gardener"
  | "Surveyor"
  | "Builder"
  | "Explorer"
  | "Scribe"
  | "Architect"
  | "Grafter"
  | "Adversary"
  | "Healer"
  | "Librarian"
  | "Herald"
  | "Orchard Analyst"
  | "Sentinel";
export type TaskId10 = string;
export type WorkspaceRef2 = string | null;
export type ArgumentsDigest1 = string;
export type ArgumentsRef1 = string;
export type CallId1 = string;
export type Tool1 = string;
export type ArgumentsDigest2 = string;
export type ArgumentsRef2 = string;
export type BudgetReservationRef1 = string;
export type CapabilityRef = string;
export type CaseId59 = string;
export type Deadline7 = string;
export type EffectRef = string | null;
export type Generation40 = number;
export type InputDigest5 = string;
export type InvocationId = string;
export type LeaseEpoch7 = number;
/**
 * @maxItems 256
 */
export type ResultRefs = string[];
export type RunId48 = string;
export type State18 = "intended" | "submitted" | "observed" | "denied" | "failed" | "unknown";
export type TaskId11 = string;
export type ToolId = string;
export type CreatedAt23 = string;
export type GraftId21 = string;
export type Id22 = string;
export type MutantIds1 = string[];
export type Reason5 = string;
export type RuleId = string;
export type ScenarioIds1 = string[];
/**
 * @maxItems 256
 */
export type Items3 = Issue[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "UploadSessionV1".
 */
export type UploadSessionV1 =
  | {
      binding_epochs: BindingEpochs3;
      case_id: CaseId60;
      contributor_id: ContributorId;
      created_at: CreatedAt24;
      expected_manifest_digest: ExpectedManifestDigest2;
      expected_manifest_ref: ExpectedManifestRef;
      expected_total_bytes: ExpectedTotalBytes1;
      expires_at: ExpiresAt18;
      finalised_snapshot_ref: string;
      received_chunk_refs: ReceivedChunkRefs;
      state: State19;
      upload_id: UploadId2;
    }
  | {
      binding_epochs: BindingEpochs3;
      case_id: CaseId60;
      contributor_id: ContributorId;
      created_at: CreatedAt24;
      expected_manifest_digest: ExpectedManifestDigest2;
      expected_manifest_ref: ExpectedManifestRef;
      expected_total_bytes: ExpectedTotalBytes1;
      expires_at: ExpiresAt18;
      finalised_snapshot_ref: null;
      received_chunk_refs: ReceivedChunkRefs;
      state: State20;
      upload_id: UploadId2;
    };
export type CaseId60 = string;
export type ContributorId = string;
export type CreatedAt24 = string;
export type ExpectedManifestDigest2 = string;
export type ExpectedManifestRef = string;
export type ExpectedTotalBytes1 = number;
export type ExpiresAt18 = string;
/**
 * @maxItems 100000
 */
export type ReceivedChunkRefs = string[];
export type State19 = "finalised";
export type UploadId2 = string;
export type State20 = "pending" | "receiving" | "cancelled" | "expired";
export type DeltasApplied = string[];
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Grade".
 */
export type Grade = "PROBLEM" | "UNVERIFIED" | "PASS" | "PASS_FIXED" | "N/A";
export type NoiseMasked = string[];
export type ParityDiff = JsonValue[];
export type Evidence = string[];
export type Rule3 = string;
export type RuleHits = RuleHit[];
export type ScenarioId2 = string;
export type CaseId61 = string;
export type ConditionId = string;
export type DueAt = string | null;
export type ExpectedDigest = string | null;
export type ExpiresAt19 = string;
export type Generation41 = number;
export type Kind21 = "timer" | "task_result" | "authority" | "approval" | "counterpart" | "tool_reconcile";
export type MinimumVersion = number;
export type Owner2 = string;
export type RunId49 = string;
export type SubjectRef1 = string;
export type AcceptedAt2 = string;
export type ActionId3 = string;
export type CaseId62 = string;
export type ReadinessDigest5 = string;
export type ReceiptRef1 = string;
export type ResourceGraphDigest4 = string;
export type ScopeDigest15 = string;
export type SourceManifestDigest2 = string;
export type WorkId4 = string;
export type WorkPackageDigest12 = string;
export type ActionId4 = string;
export type CancelId1 = string;
export type CaseId63 = string;
export type Generation42 = number | null;
export type RequestedAt = string;
export type RequestedBy = string;
export type State21 = "intent_recorded" | "fenced" | "termination_pending" | "confirmed" | "unknown";
/**
 * @maxItems 256
 */
export type TerminationEvidenceRefs = string[];
export type WorkId5 = string | null;
export type AcquisitionExpiresAt = string;
export type BaselineManifestDigest = string;
export type CaseId64 = string;
export type Completeness1 = "sufficient_for_declared_static_scope" | "incomplete" | "unknown";
export type ComponentsRef = string;
export type CustodyPolicyDigest = string;
export type DeliveryFeasibilityRef = string;
export type ExternalDependenciesRef = string;
export type FixtureProfileDigest2 = string;
export type OmissionManifestRef1 = string;
export type ProcessingPolicyDigest2 = string;
/**
 * @maxItems 256
 */
export type RequiredFlowRefs = string[];
export type ResourceGraphDigest5 = string;
export type ResourceGraphRef = string;
export type RuntimeProfileDigest5 = string;
export type ScopeDigest16 = string;
/**
 * @maxItems 256
 */
export type SourceSnapshotRefs4 = string[];
/**
 * @maxItems 256
 */
export type StateRecipeRefs = string[];
/**
 * @maxItems 256
 */
export type SyntheticSeedRefs = string[];
export type UnresolvedRequirementsRef = string;
export type WorkPackageId = string;
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "WorkStatusV1".
 */
export type WorkStatusV1 =
  | {
      action_id: ActionId5;
      case_id: CaseId65;
      checked_at: CheckedAt23;
      evidence_refs: EvidenceRefs39;
      generation: Generation43;
      last_event_seq: LastEventSeq3;
      state: State22;
      work_id: WorkId6;
    }
  | {
      action_id: ActionId5;
      case_id: CaseId65;
      checked_at: CheckedAt23;
      evidence_refs: EvidenceRefs39;
      generation: Generation43;
      last_event_seq: LastEventSeq3;
      state: State23;
      work_id: string;
    }
  | {
      action_id: ActionId5;
      case_id: CaseId65;
      checked_at: CheckedAt23;
      evidence_refs: EvidenceRefs40;
      generation: number;
      last_event_seq: LastEventSeq3;
      state: State24;
      work_id: string;
    }
  | {
      action_id: ActionId5;
      case_id: CaseId65;
      checked_at: CheckedAt23;
      evidence_refs: EvidenceRefs41;
      generation: Generation43;
      last_event_seq: LastEventSeq3;
      state: State25;
      work_id: string;
    };
export type ActionId5 = string;
export type CaseId65 = string;
export type CheckedAt23 = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs39 = string[];
export type Generation43 = number | null;
export type LastEventSeq3 = number;
export type State22 = "submitting" | "held" | "unknown" | "cancellation_pending" | "cancelled" | "failed";
export type WorkId6 = string | null;
export type State23 = "accepted" | "queued" | "provisioning";
/**
 * @minItems 1
 * @maxItems 256
 */
export type EvidenceRefs40 = [string, ...string[]];
export type State24 = "operation_started";
/**
 * @minItems 1
 * @maxItems 256
 */
export type EvidenceRefs41 = [string, ...string[]];
export type State25 = "stopped";
export type AssignmentDigest = string;
export type AuthenticityRef6 = string;
/**
 * @maxItems 256
 */
export type EvidenceRefs42 = string[];
export type FinishedAt1 = string;
export type Generation44 = number;
export type Kind22 = "BASELINE_READ";
export type ObservedDigest = string;
export type OperationId1 = string;
export type ResourceGraphDigest6 = string;
export type Result = "verified" | "failed";
export type RuntimeProfileDigest6 = string;
export type ScopeDigest17 = string;
export type SourceManifestDigest3 = string;
export type StartedAt1 = string;
export type WorkId7 = string;
export type WorkPackageDigest13 = string;
export type WorkerId1 = string;

export interface GoldGraftContracts {
  ActionIntentV1: ActionIntentV1;
  ActionPlanV1: ActionPlanV1;
  ActionStatusViewV1: ActionStatusViewV1;
  AdapterCapabilitiesV1: AdapterCapabilitiesV1;
  AdapterObservationV1: AdapterObservationV1;
  AgentResultV1: AgentResultV1;
  AgentTaskV1: AgentTaskV1;
  AggregateReadArgsV1: AggregateReadArgsV1;
  AlertV1: AlertV1;
  AnalysisMatchesArgsV1: AnalysisMatchesArgsV1;
  ApplyApprovalV1: ApplyApprovalV1;
  ApplyAuthorityV1: ApplyAuthorityV1;
  ApprovalSetV1: ApprovalSetV1;
  ArtifactBuildV1: ArtifactBuildV1;
  ArtifactDescriptorV1: ArtifactDescriptorV1;
  AssetV1: AssetV1;
  AssetManifestV1: AssetManifestV1;
  AssignmentV1: AssignmentV1;
  AuditSummaryArgsV1: AuditSummaryArgsV1;
  BaselineEvidenceV1: BaselineEvidenceV1;
  BudgetRecordV1: BudgetRecordV1;
  CMELV1: CMELV1;
  CancelUploadRequestV1: CancelUploadRequestV1;
  CancelWorkRequestV1: CancelWorkRequestV1;
  CandidatePatchArgsV1: CandidatePatchArgsV1;
  CaseEventV1: CaseEventV1;
  CaseEventsQueryV1: CaseEventsQueryV1;
  CaseListV1: CaseListV1;
  CaseListQueryV1: CaseListQueryV1;
  CaseSummaryV1: CaseSummaryV1;
  CaseViewV1: CaseViewV1;
  CertificateV1: CertificateV1;
  CertificateV2: CertificateV2;
  CertificateVerificationV1: CertificateVerificationV1;
  ChangeListV1: ChangeListV1;
  ChangeListV2: ChangeListV2;
  CheckResultV1: CheckResultV1;
  ChunkV1: ChunkV1;
  ChunkReceiptV1: ChunkReceiptV1;
  ChunkUploadRequestV1: ChunkUploadRequestV1;
  ClaimDraftV1: ClaimDraftV1;
  CollectorAcceptanceV1: CollectorAcceptanceV1;
  ComponentV1: ComponentV1;
  ComponentManifestV1: ComponentManifestV1;
  ConfigurationEntryV1: ConfigurationEntryV1;
  ConfigurationManifestV1: ConfigurationManifestV1;
  ConnectionV1: ConnectionV1;
  ConnectionCaseV1: ConnectionCaseV1;
  ConnectionReadinessV1: ConnectionReadinessV1;
  ContractV1: ContractV1;
  ControlErrorV1: ControlErrorV1;
  ControllerInvitationV1: ControllerInvitationV1;
  CreateActionIntentV1: CreateActionIntentV1;
  CreateCaseV1: CreateCaseV1;
  CreateDraftV1: CreateDraftV1;
  CreateInvitationV1: CreateInvitationV1;
  CreateProviderIntentV1: CreateProviderIntentV1;
  CreateUploadRequestV1: CreateUploadRequestV1;
  DashboardSpecV1: DashboardSpecV1;
  DeliveryDecisionV1: DeliveryDecisionV1;
  DeliverySnapshotV1: DeliverySnapshotV1;
  DependencyV1: DependencyV1;
  DependencyInspectArgsV1: DependencyInspectArgsV1;
  DependencyManifestV1: DependencyManifestV1;
  DeploymentObservationV1: DeploymentObservationV1;
  DetectionRuleV1: DetectionRuleV1;
  DocsLookupArgsV1: DocsLookupArgsV1;
  DraftCaseV1: DraftCaseV1;
  DriverV1: DriverV1;
  EffectIntentV1: EffectIntentV1;
  EffectSlotV1: EffectSlotV1;
  EvidenceReadArgsV1: EvidenceReadArgsV1;
  EvidenceSummaryArgsV1: EvidenceSummaryArgsV1;
  ExecutionProposalV1: ExecutionProposalV1;
  ExecutionRequestArgsV1: ExecutionRequestArgsV1;
  ExecutionStatusArgsV1: ExecutionStatusArgsV1;
  ExitCheckPlanV1: ExitCheckPlanV1;
  ExitCheckResultV1: ExitCheckResultV1;
  ExitEvidenceReconciliationV1: ExitEvidenceReconciliationV1;
  ExitItemV1: ExitItemV1;
  ExitManifestV1: ExitManifestV1;
  FinalisationPlanV1: FinalisationPlanV1;
  FinaliseUploadRequestV1: FinaliseUploadRequestV1;
  GuardEventV1: GuardEventV1;
  HandoffPackV1: HandoffPackV1;
  HandoffRecordV1: HandoffRecordV1;
  HealDecisionV1: HealDecisionV1;
  HealNoteV1: HealNoteV1;
  HeraldTextV1: HeraldTextV1;
  IssueV1: IssueV1;
  IssueApplyApprovalV1: IssueApplyApprovalV1;
  JobResultV1: JobResultV1;
  JobSpecV1: JobSpecV1;
  LaneChangeV1: LaneChangeV1;
  LedgerEntryV1: LedgerEntryV1;
  LifecycleRunV1: LifecycleRunV1;
  LifecycleWorkRequestV1: LifecycleWorkRequestV1;
  LifecycleWorkRequestReceiptV1: LifecycleWorkRequestReceiptV1;
  LifecycleWorkResultV1: LifecycleWorkResultV1;
  LinksPackV1: LinksPackV1;
  ManifestEntryV1: ManifestEntryV1;
  MappingRowV1: MappingRowV1;
  ModelBudgetV1: ModelBudgetV1;
  ModelTurnRequestV1: ModelTurnRequestV1;
  ModelTurnResultV1: ModelTurnResultV1;
  ModelTurnStatusV1: ModelTurnStatusV1;
  MoneyV1: MoneyV1;
  MutantV1: MutantV1;
  MutantSetV1: MutantSetV1;
  MutationOperatorV1: MutationOperatorV1;
  OmissionV1: OmissionV1;
  OmissionManifestV1: OmissionManifestV1;
  P5ProblemV1: P5ProblemV1;
  PendingResultV1: PendingResultV1;
  PlanProposalV1: PlanProposalV1;
  PredicateResultV1: PredicateResultV1;
  PrivateReviewViewV1: PrivateReviewViewV1;
  ProbeResultV1: ProbeResultV1;
  ProcessingDisclosureV1: ProcessingDisclosureV1;
  ProcessingRecipientV1: ProcessingRecipientV1;
  PromotionDecisionV1: PromotionDecisionV1;
  ProofPlanV1: ProofPlanV1;
  ProofResultV1: ProofResultV1;
  ProofStrengthV1: ProofStrengthV1;
  ProviderIntentV1: ProviderIntentV1;
  ProviderRefV1: ProviderRefV1;
  PublicMetricV1: PublicMetricV1;
  PublicProofViewV1: PublicProofViewV1;
  RawCaptureV1: RawCaptureV1;
  RecipeV1: RecipeV1;
  RecipeLookupArgsV1: RecipeLookupArgsV1;
  RecipeStageArgsV1: RecipeStageArgsV1;
  RecoveryPlanV1: RecoveryPlanV1;
  RequiredActionV1: RequiredActionV1;
  RequiredFlowV1: RequiredFlowV1;
  RequiredFlowManifestV1: RequiredFlowManifestV1;
  ResolvedDeliveryViewV1: ResolvedDeliveryViewV1;
  ResourceBindingV1: ResourceBindingV1;
  ResourceEdgeV1: ResourceEdgeV1;
  ResourceGraphV1: ResourceGraphV1;
  ResourceNodeV1: ResourceNodeV1;
  ResourceRecipientV1: ResourceRecipientV1;
  ResourceSummaryV1: ResourceSummaryV1;
  ResumeRunRequestV1: ResumeRunRequestV1;
  ReviewBundleV1: ReviewBundleV1;
  RootMapV1: RootMapV1;
  RuleV1: RuleV1;
  RunTaskSnapshotV1: RunTaskSnapshotV1;
  RunnableShopV1: RunnableShopV1;
  SafetyRequestHoldArgsV1: SafetyRequestHoldArgsV1;
  ScenarioV1: ScenarioV1;
  ScenarioSetV1: ScenarioSetV1;
  ScenarioStageArgsV1: ScenarioStageArgsV1;
  ShopPackV1: ShopPackV1;
  SourceReadArgsV1: SourceReadArgsV1;
  SourceRevisionV1: SourceRevisionV1;
  SourceSnapshotV1: SourceSnapshotV1;
  StageChangeV1: StageChangeV1;
  StartWorkRequestV1: StartWorkRequestV1;
  StateCutoverV1: StateCutoverV1;
  StatusReadArgsV1: StatusReadArgsV1;
  SubjectDerivationV1: SubjectDerivationV1;
  SubjectManifestV1: SubjectManifestV1;
  SwitchConfigV1: SwitchConfigV1;
  TargetKeyV1: TargetKeyV1;
  TargetPlanV1: TargetPlanV1;
  TargetReservationV1: TargetReservationV1;
  TaskCheckpointV1: TaskCheckpointV1;
  TaskContextV1: TaskContextV1;
  TaskEventV1: TaskEventV1;
  TaskLeaseV1: TaskLeaseV1;
  TaskSpecV1: TaskSpecV1;
  ToolCallV1: ToolCallV1;
  ToolInvocationV1: ToolInvocationV1;
  TriangleRequestV1: TriangleRequestV1;
  UnresolvedInputsV1: UnresolvedInputsV1;
  UploadSessionV1: UploadSessionV1;
  VerdictV1: VerdictV1;
  WakeConditionV1: WakeConditionV1;
  WorkAcceptanceV1: WorkAcceptanceV1;
  WorkCancellationV1: WorkCancellationV1;
  WorkPackageV1: WorkPackageV1;
  WorkStatusV1: WorkStatusV1;
  WorkerOperationV1: WorkerOperationV1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ActionIntentV1".
 */
export interface ActionIntentV1 {
  action_id: ActionId;
  actor_id: ActorId;
  case_id: CaseId;
  created_at: CreatedAt;
  expires_at: ExpiresAt;
  readiness_digest: ReadinessDigest;
  readiness_id: ReadinessId;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ActionPlanV1".
 */
export interface ActionPlanV1 {
  budget_ref: BudgetRef;
  case_id: CaseId1;
  exit_plan_ref: ExitPlanRef;
  expires_at: ExpiresAt1;
  finalisation_plan_ref: FinalisationPlanRef;
  generation: Generation;
  graph_digest: GraphDigest;
  plan_digest: PlanDigest;
  plan_id: PlanId;
  policy_digest: PolicyDigest;
  recovery_plan_ref: RecoveryPlanRef;
  review_bundle_digest: ReviewBundleDigest;
  run_id: RunId;
  scope_digest: ScopeDigest;
  slots: Slots;
  state_plan_ref: StatePlanRef;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "EffectSlot".
 */
export interface EffectSlot {
  artifact_digest: ArtifactDigest;
  cardinality: Cardinality;
  config_digest: ConfigDigest;
  depends_on: DependsOn;
  effect_class: EffectClass;
  expected_version_ref: ExpectedVersionRef;
  operation: Operation;
  recovery_branch_ref: RecoveryBranchRef;
  required_authority_refs: RequiredAuthorityRefs;
  required_controller_ids: RequiredControllerIds;
  slot_id: SlotId;
  state_plan_digest: StatePlanDigest;
  target_key: TargetKey;
  trigger_digest: TriggerDigest;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "TargetKey".
 */
export interface TargetKey {
  account_id: AccountId;
  environment_id: EnvironmentId;
  provider_id: ProviderId;
  resource_id: ResourceId;
  resource_kind: ResourceKind;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ActionStatusViewV1".
 */
export interface ActionStatusViewV1 {
  acceptance_ref: AcceptanceRef;
  status: WorkStatus;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "AdapterCapabilitiesV1".
 */
export interface AdapterCapabilitiesV1 {
  limitations: Limitations;
  operations: Operations;
  provider: ProviderRef;
  qualification: Qualification;
  qualification_refs: QualificationRefs;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ProviderRef".
 */
export interface ProviderRef {
  account_id: AccountId1;
  adapter_version: AdapterVersion;
  provider_id: ProviderId1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "AdapterObservationV1".
 */
export interface AdapterObservationV1 {
  basis: Basis;
  capability: Capability;
  case_id: CaseId3;
  checked_at: CheckedAt1;
  evidence_refs: EvidenceRefs3;
  expires_at: ExpiresAt2;
  node_id: NodeId;
  observation_id: ObservationId;
  status: Status;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Issue".
 */
export interface Issue {
  code: Code;
  evidence_refs: EvidenceRefs5;
  input_ref: InputRef;
  owner_role: OwnerRole;
  recovery: Recovery;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "AgentTaskV1".
 */
export interface AgentTaskV1 {
  attempt: Attempt;
  case_id: CaseId5;
  checkpoint_ref: CheckpointRef;
  created_at: CreatedAt1;
  deadline: Deadline;
  generation: Generation3;
  input_digest: InputDigest1;
  issue: Issue | null;
  lease_epoch: LeaseEpoch1;
  lease_owner: LeaseOwner;
  lease_until: LeaseUntil;
  model_profile_ref: ModelProfileRef;
  next_wake_at: NextWakeAt;
  output_refs: OutputRefs2;
  policy_digest: PolicyDigest1;
  policy_ref: PolicyRef;
  prompt_digest: PromptDigest;
  prompt_ref: PromptRef;
  request_id: RequestId1;
  run_id: RunId2;
  state: State4;
  state_version: StateVersion;
  task: TaskSpec;
  wake_condition_ref: WakeConditionRef;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "TaskSpec".
 */
export interface TaskSpec {
  allowed_tool_ids: AllowedToolIds;
  dependencies: Dependencies;
  expected_schemas: ExpectedSchemas;
  expected_subject: ExpectedSubject;
  input_refs: InputRefs;
  operation: Operation1;
  output_slot: OutputSlot;
  output_subject_policy: OutputSubjectPolicy;
  required: Required;
  role: Role;
  task_id: TaskId1;
  workspace_ref: WorkspaceRef;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "AggregateReadArgsV1".
 */
export interface AggregateReadArgsV1 {
  projection_ref: ProjectionRef;
  query_ref: QueryRef;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "AlertV1".
 */
export interface AlertV1 {
  created_at: CreatedAt2;
  evidence_refs: EvidenceRefs6;
  graft_id: GraftId;
  halted_agent?: HaltedAgent;
  id: Id;
  message: Message;
  producer: Producer;
  severity: Severity;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Producer".
 */
export interface Producer {
  kind: ProducerKind;
  model?: Model;
  name: Name;
  version: Version;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "AnalysisMatchesArgsV1".
 */
export interface AnalysisMatchesArgsV1 {
  max_matches: MaxMatches;
  rule_ref: RuleRef;
  snapshot_ref: SnapshotRef;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ApplyApprovalV1".
 */
export interface ApplyApprovalV1 {
  action_group_id: ActionGroupId;
  action_plan_digest: ActionPlanDigest;
  allowed_actions: AllowedActions;
  approval_id: ApprovalId;
  artifact_digest: ArtifactDigest1;
  authority_binding_epochs: AuthorityBindingEpochs;
  authority_refs: AuthorityRefs;
  baseline_digest: BaselineDigest;
  candidate_digest: CandidateDigest;
  case_id: CaseId6;
  config_digest: ConfigDigest1;
  controller_id: ControllerId;
  delivery_route: DeliveryRoute;
  expires_at: ExpiresAt3;
  generation: Generation4;
  graph_digest: GraphDigest1;
  issued_at: IssuedAt;
  patch_digest: PatchDigest;
  policy_digest: PolicyDigest2;
  publication_destination_refs: PublicationDestinationRefs;
  recovery_plan_digest: RecoveryPlanDigest;
  reviewed_bundle_digest: ReviewedBundleDigest;
  revoked_at: RevokedAt;
  scope_digest: ScopeDigest1;
  source_base: SourceBase;
  source_head: SourceHead;
  source_snapshot_digests: SourceSnapshotDigests;
  state_plan_digest: StatePlanDigest1;
  target_resources: TargetResources;
  trigger_chain_digest: TriggerChainDigest;
}
export interface AuthorityBindingEpochs {
  /**
   * This interface was referenced by `AuthorityBindingEpochs`'s JSON-Schema definition
   * via the `patternProperty` "^\S+$".
   */
  [k: string]: number;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ApplyAuthorityV1".
 */
export interface ApplyAuthorityV1 {
  actions: Actions;
  authority_id: AuthorityId;
  controller_id: ControllerId1;
  delegate_id: DelegateId;
  expires_at: ExpiresAt4;
  grant_epoch: GrantEpoch;
  issued_at: IssuedAt1;
  revoked_at: RevokedAt1;
  role_evidence_refs: RoleEvidenceRefs;
  target_key: TargetKey;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ApprovalSetV1".
 */
export interface ApprovalSetV1 {
  approval_refs: ApprovalRefs;
  approval_set_id: ApprovalSetId;
  authority_epochs: AuthorityEpochs;
  case_id: CaseId7;
  checked_at: CheckedAt2;
  generation: Generation5;
  plan_digest: PlanDigest1;
  required_controller_ids: RequiredControllerIds1;
  run_id: RunId3;
  state: State5;
}
export interface AuthorityEpochs {
  /**
   * This interface was referenced by `AuthorityEpochs`'s JSON-Schema definition
   * via the `patternProperty` "^\S+$".
   */
  [k: string]: number;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ArtifactBuildV1".
 */
export interface ArtifactBuildV1 {
  authenticity_ref: AuthenticityRef1;
  build_config_digest: BuildConfigDigest;
  build_id: BuildId;
  case_id: CaseId8;
  collector_identity_ref: CollectorIdentityRef;
  dependency_digest: DependencyDigest;
  exact_image_test_refs: ExactImageTestRefs;
  export_tar_digest: ExportTarDigest;
  generation: Generation6;
  layer_digests: LayerDigests;
  leak_scan_refs: LeakScanRefs;
  oci_manifest_digest: OciManifestDigest;
  outcome: Outcome2;
  platform: Platform;
  provenance_ref: ProvenanceRef;
  recipe_digest: RecipeDigest;
  run_id: RunId4;
  runtime_profile_digest: RuntimeProfileDigest;
  source_snapshot_refs: SourceSnapshotRefs;
  source_tree_digest: SourceTreeDigest;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ArtifactDescriptorV1".
 */
export interface ArtifactDescriptorV1 {
  byte_count: ByteCount;
  case_id: CaseId9;
  created_at: CreatedAt3;
  derivation_ref: DerivationRef;
  evidence_class: EvidenceClass;
  expires_at: ExpiresAt5;
  generation: Generation7;
  input_digest: InputDigest2;
  payload_digest: PayloadDigest;
  producer_identity_ref: ProducerIdentityRef;
  ref: Ref;
  run_id: RunId5;
  schema: Schema;
  subject_digest: SubjectDigest;
  trust: Trust;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "AssetV1".
 */
export interface AssetV1 {
  active_reference_refs: ActiveReferenceRefs;
  asset_id: AssetId;
  authority_refs: AuthorityRefs1;
  desired: Desired;
  evidence_refs: EvidenceRefs7;
  kind: Kind;
  ownership: Ownership;
  required_for_operation: RequiredForOperation;
  target_key: TargetKey;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "AssetManifestV1".
 */
export interface AssetManifestV1 {
  assets: Assets;
  case_id: CaseId10;
  final_artifact_digest: FinalArtifactDigest;
  final_config_digest: FinalConfigDigest;
  legacy_obligations_ref: LegacyObligationsRef;
  manifest_digest: ManifestDigest;
  manifest_id: ManifestId;
  run_id: RunId6;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Asset".
 */
export interface Asset {
  active_reference_refs: ActiveReferenceRefs1;
  asset_id: AssetId1;
  authority_refs: AuthorityRefs2;
  desired: Desired1;
  evidence_refs: EvidenceRefs8;
  kind: Kind1;
  ownership: Ownership1;
  required_for_operation: RequiredForOperation1;
  target_key: TargetKey;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "AssignmentV1".
 */
export interface AssignmentV1 {
  assignee: Assignee;
  attempt: Attempt1;
  created_at: CreatedAt4;
  graft_id: GraftId1;
  id: Id1;
  input_refs: InputRefs1;
  producer: Producer;
  stage: Stage;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "AuditSummaryArgsV1".
 */
export interface AuditSummaryArgsV1 {
  after_seq: AfterSeq;
  run_ref: RunRef;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "BaselineEvidenceV1".
 */
export interface BaselineEvidenceV1 {
  actual_provider_evidence_ref: ActualProviderEvidenceRef;
  dependency_digest: DependencyDigest1;
  immutable_source_digest: ImmutableSourceDigest;
  observed_defects_ref: ObservedDefectsRef;
  outcome: Outcome3;
  package_digest: PackageDigest;
  run_id: RunId7;
  runtime_digest: RuntimeDigest;
  scenario_results_ref: ScenarioResultsRef;
  seed_digest: SeedDigest;
  skipped_required: SkippedRequired;
  variant: Variant;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "BudgetRecordV1".
 */
export interface BudgetRecordV1 {
  agent: Agent;
  cap_usd: CapUsd;
  graft_id: GraftId2;
  model: Model1;
  tokens_cached: TokensCached;
  tokens_in: TokensIn;
  tokens_out: TokensOut;
  usd: Usd;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CMELV1".
 */
export interface CMELV1 {
  graft_id: GraftId3;
  items_hash?: ItemsHash;
  kind: Kind2;
  money?: Money | null;
  noise: Noise;
  order_ref: OrderRef;
  pp: PayPalRefs;
  raw_ref: RawRef;
  run_id: RunId8;
  scenario_id: ScenarioId;
  seq: Seq;
  source: Source;
  status_norm?: StatusNorm | null;
  t_ms: TMs;
  variant: Variant1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Money".
 */
export interface Money {
  currency: Currency;
  minor: Minor;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "PayPalRefs".
 */
export interface PayPalRefs {
  capture_id?: CaptureId;
  debug_id?: DebugId;
  legacy_token?: LegacyToken;
  order_id?: OrderId;
  profile_id?: ProfileId;
  refund_id?: RefundId;
  txn_id?: TxnId;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CancelUploadRequestV1".
 */
export interface CancelUploadRequestV1 {}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CancelWorkRequestV1".
 */
export interface CancelWorkRequestV1 {
  cancel_id: CancelId;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CandidatePatchArgsV1".
 */
export interface CandidatePatchArgsV1 {
  expected_tree: ExpectedTree;
  patch_ref: PatchRef;
  workspace_ref: WorkspaceRef1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CaseEventV1".
 */
export interface CaseEventV1 {
  case_id: CaseId11;
  event_id: EventId;
  kind: Kind3;
  occurred_at: OccurredAt;
  payload_digest: PayloadDigest1;
  payload_ref: PayloadRef;
  sequence: Sequence;
  state_version: StateVersion1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CaseEventsQueryV1".
 */
export interface CaseEventsQueryV1 {
  after: After;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CaseListV1".
 */
export interface CaseListV1 {
  items: Items;
  next_cursor: NextCursor;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CaseSummary".
 */
export interface CaseSummary {
  case_id: CaseId12;
  shop_url: ShopUrl;
  status: Status1;
  updated_at: UpdatedAt;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CaseListQueryV1".
 */
export interface CaseListQueryV1 {
  cursor: Cursor;
  limit: Limit;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CaseSummaryV1".
 */
export interface CaseSummaryV1 {
  case_id: CaseId13;
  shop_url: ShopUrl1;
  status: Status2;
  updated_at: UpdatedAt1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CaseViewV1".
 */
export interface CaseViewV1 {
  action: ActionStatusView | null;
  case: ConnectionCase;
  checked_at: CheckedAt3;
  delivery_ref: DeliveryRef;
  evidence_class: EvidenceClass1;
  last_event_seq: LastEventSeq1;
  lifecycle: LifecycleRun | null;
  pending_action_id: PendingActionId;
  processing: ProcessingDisclosure | null;
  readiness: ConnectionReadiness | null;
  required_actions: RequiredActions;
  resources: Resources;
  state_version: StateVersion2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ActionStatusView".
 */
export interface ActionStatusView {
  acceptance_ref: AcceptanceRef1;
  status: WorkStatus;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ConnectionCase".
 */
export interface ConnectionCase {
  binding_refs: BindingRefs;
  case_id: CaseId14;
  created_at: CreatedAt5;
  graph_ref: GraphRef;
  requester_id: RequesterId;
  shop_url: ShopUrl2;
  status: Status3;
  tenant_id: TenantId;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "LifecycleRun".
 */
export interface LifecycleRun {
  active_effect_refs: ActiveEffectRefs;
  attempt: Attempt2;
  case_id: CaseId15;
  evidence_refs: EvidenceRefs9;
  generation: Generation8;
  resource_graph_digest: ResourceGraphDigest;
  run_id: RunId9;
  scope_digest: ScopeDigest2;
  stage: Stage1;
  updated_at: UpdatedAt2;
  work_id: WorkId1;
  work_package_digest: WorkPackageDigest;
  work_package_ref: WorkPackageRef;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ProcessingDisclosure".
 */
export interface ProcessingDisclosure {
  checked_at: CheckedAt4;
  copy_scope: CopyScope;
  limits: Limits;
  policy_digest: PolicyDigest3;
  recipients: Recipients;
  status: Status4;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ProcessingRecipient".
 */
export interface ProcessingRecipient {
  name: Name1;
  purpose: Purpose;
  region_text: RegionText;
  retention_text: RetentionText;
  terms_evidence_refs: TermsEvidenceRefs;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ConnectionReadiness".
 */
export interface ConnectionReadiness {
  actor_id: ActorId1;
  binding_epochs: BindingEpochs;
  case_id: CaseId16;
  checks: Checks;
  expires_at: ExpiresAt7;
  fixture_profile_digest: FixtureProfileDigest;
  issued_at: IssuedAt2;
  processing_policy_digest: ProcessingPolicyDigest;
  readiness_digest: ReadinessDigest1;
  readiness_id: ReadinessId1;
  resource_evidence_digests: ResourceEvidenceDigests;
  resource_graph_digest: ResourceGraphDigest1;
  runtime_profile_digest: RuntimeProfileDigest1;
  scope_digest: ScopeDigest3;
  source_manifest_digest: SourceManifestDigest;
  source_snapshot_refs: SourceSnapshotRefs1;
  work_package_digest: WorkPackageDigest1;
  work_package_ref: WorkPackageRef1;
}
export interface BindingEpochs {
  /**
   * This interface was referenced by `BindingEpochs`'s JSON-Schema definition
   * via the `patternProperty` "^\S+$".
   */
  [k: string]: number;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CheckResult".
 */
export interface CheckResult {
  check_id: CheckId;
  checked_at: CheckedAt5;
  evidence_refs: EvidenceRefs10;
  expires_at: ExpiresAt6;
  recovery_code: RecoveryCode;
  status: Status5;
}
export interface ResourceEvidenceDigests {
  /**
   * This interface was referenced by `ResourceEvidenceDigests`'s JSON-Schema definition
   * via the `patternProperty` "^\S+$".
   */
  [k: string]: string;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RequiredAction".
 */
export interface RequiredAction {
  enabled: Enabled;
  kind: Kind4;
  reason_code: ReasonCode;
  resource_ids: ResourceIds;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ResourceSummary".
 */
export interface ResourceSummary {
  check_refs: CheckRefs;
  controller_state: ControllerState;
  environment: Environment;
  label: Label;
  node_id: NodeId1;
  permitted_actions: PermittedActions;
  provider: ProviderRef;
  read_scope_text: ReadScopeText;
  source_snapshot_ref: SourceSnapshotRef;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CertificateV1".
 */
export interface CertificateV1 {
  branch: Branch;
  cert_id: CertId;
  commit_new: CommitNew;
  commit_old: CommitOld;
  cost: CertificateCost;
  issued_at: IssuedAt3;
  ledger_root: LedgerRoot;
  ots_proof?: OtsProof;
  paypal_evidence: PaypalEvidence;
  proof_strength: CertificateStrength;
  rekor_entry: RekorEntry;
  repo: Repo;
  results: CertificateResults;
  runner_identity: RunnerIdentity;
  security: CertificateSecurity;
  shop_id: ShopId;
  signature: Signature;
  survey: CertificateSurvey;
  time: Time;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CertificateCost".
 */
export interface CertificateCost {
  tokens: Tokens;
  usd: Usd1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "PayPalEvidence".
 */
export interface PayPalEvidence {
  capture_id: CaptureId1;
  debug_id: DebugId1;
  order_id: OrderId1;
  scenario: Scenario;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CertificateStrength".
 */
export interface CertificateStrength {
  equivalent_dropped: EquivalentDropped;
  killed: Killed;
  mutants_total: MutantsTotal;
  score: Score;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CertificateResults".
 */
export interface CertificateResults {
  n_a: NA;
  pass: Pass;
  pass_fixed: PassFixed;
  problem: Problem;
  scenarios: Scenarios;
  unverified: Unverified;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RunnerIdentity".
 */
export interface RunnerIdentity {
  sha: Sha;
  workflow: Workflow;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CertificateSecurity".
 */
export interface CertificateSecurity {
  deps_blocked: DepsBlocked;
  injection_attempts_blocked: InjectionAttemptsBlocked;
  secrets_found: SecretsFound;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CertificateSurvey".
 */
export interface CertificateSurvey {
  misses_learned: MissesLearned;
  precision: Precision;
  recall: Recall;
}
export interface Time {
  [k: string]: number;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CertificateGitSource".
 */
export interface CertificateGitSource {
  branch: Branch1;
  commit_new: CommitNew1;
  commit_old: CommitOld1;
  repository_ref: RepositoryRef;
}
export interface ResourceEpochs {
  /**
   * This interface was referenced by `ResourceEpochs`'s JSON-Schema definition
   * via the `patternProperty` "^\S+$".
   */
  [k: string]: number;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "SignatureMaterial".
 */
export interface SignatureMaterial {
  authenticity_ref: AuthenticityRef2;
  signature_digest: SignatureDigest;
  signature_ref: SignatureRef;
  transparency_digest: TransparencyDigest;
  transparency_ref: TransparencyRef;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CertificateVerificationV1".
 */
export interface CertificateVerificationV1 {
  case_id: CaseId18;
  cert_id: CertId2;
  checked_at: CheckedAt6;
  qualification_scope: QualificationScope1;
  qualification_state: QualificationState;
  reason_codes: ReasonCodes;
  run_id: RunId11;
  signature_integrity: SignatureIntegrity;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ChangeListV1".
 */
export interface ChangeListV1 {
  branch: Branch2;
  changes: Changes;
  created_at: CreatedAt6;
  graft_id: GraftId4;
  id: Id2;
  open_item_ids: OpenItemIds;
  producer: Producer;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Change".
 */
export interface Change {
  commit: Commit;
  plan_item_ids: PlanItemIds;
  summary: Summary;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "SnapshotChange".
 */
export interface SnapshotChange {
  commit: Commit1;
  plan_item_ids: PlanItemIds1;
  summary: Summary1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CheckResultV1".
 */
export interface CheckResultV1 {
  check_id: CheckId1;
  checked_at: CheckedAt7;
  evidence_refs: EvidenceRefs11;
  expires_at: ExpiresAt9;
  recovery_code: RecoveryCode1;
  status: Status6;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ChunkV1".
 */
export interface ChunkV1 {
  blob_ref: BlobRef;
  file_path: FilePath;
  length: Length;
  offset: Offset;
  sha256: Sha256;
  upload_id: UploadId;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ChunkReceiptV1".
 */
export interface ChunkReceiptV1 {
  file_path: FilePath1;
  length: Length1;
  offset: Offset1;
  received_at: ReceivedAt;
  sha256: Sha2561;
  upload_id: UploadId1;
}
/**
 * Multipart metadata only; binary data is a separate bounded part, never a ref.
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ChunkUploadRequestV1".
 */
export interface ChunkUploadRequestV1 {
  file_path: FilePath2;
  length: Length2;
  offset: Offset2;
  sha256: Sha2562;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ClaimDraftV1".
 */
export interface ClaimDraftV1 {
  continuation_ref: ContinuationRef;
}
/**
 * Receipt for service-only WorkerOperation intake; not proof of site reproduction.
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CollectorAcceptanceV1".
 */
export interface CollectorAcceptanceV1 {
  accepted_at: AcceptedAt;
  generation: Generation10;
  operation_id: OperationId;
  receipt_ref: ReceiptRef;
  work_id: WorkId2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ComponentV1".
 */
export interface ComponentV1 {
  build_context_ref: BuildContextRef;
  configuration_manifest_ref: ConfigurationManifestRef;
  controller_binding_refs: ControllerBindingRefs;
  correspondence_evidence_refs: CorrespondenceEvidenceRefs;
  dependency_manifest_ref: DependencyManifestRef;
  node_id: NodeId2;
  purpose: Purpose1;
  runtime_profile_ref: RuntimeProfileRef;
  source_snapshot_ref: SourceSnapshotRef1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ComponentManifestV1".
 */
export interface ComponentManifestV1 {
  components: Components;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Component".
 */
export interface Component {
  build_context_ref: BuildContextRef1;
  configuration_manifest_ref: ConfigurationManifestRef1;
  controller_binding_refs: ControllerBindingRefs1;
  correspondence_evidence_refs: CorrespondenceEvidenceRefs1;
  dependency_manifest_ref: DependencyManifestRef1;
  node_id: NodeId3;
  purpose: Purpose2;
  runtime_profile_ref: RuntimeProfileRef1;
  source_snapshot_ref: SourceSnapshotRef2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ConfigurationManifestV1".
 */
export interface ConfigurationManifestV1 {
  entries: Entries;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ConnectionV1".
 */
export interface ConnectionV1 {
  checks: ConnectionChecks;
  repo: Repo1;
  secrets_ref: SecretsRef;
  shop_id: ShopId1;
  site: Site;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ConnectionChecks".
 */
export interface ConnectionChecks {
  nvp_ok: NvpOk;
  rest_ok: RestOk;
  version_match: VersionMatch;
  webhook_ok: WebhookOk;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ConnectionCaseV1".
 */
export interface ConnectionCaseV1 {
  binding_refs: BindingRefs1;
  case_id: CaseId19;
  created_at: CreatedAt8;
  graph_ref: GraphRef1;
  requester_id: RequesterId1;
  shop_url: ShopUrl3;
  status: Status7;
  tenant_id: TenantId1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ConnectionReadinessV1".
 */
export interface ConnectionReadinessV1 {
  actor_id: ActorId2;
  binding_epochs: BindingEpochs1;
  case_id: CaseId20;
  checks: Checks1;
  expires_at: ExpiresAt10;
  fixture_profile_digest: FixtureProfileDigest1;
  issued_at: IssuedAt5;
  processing_policy_digest: ProcessingPolicyDigest1;
  readiness_digest: ReadinessDigest2;
  readiness_id: ReadinessId2;
  resource_evidence_digests: ResourceEvidenceDigests1;
  resource_graph_digest: ResourceGraphDigest2;
  runtime_profile_digest: RuntimeProfileDigest2;
  scope_digest: ScopeDigest5;
  source_manifest_digest: SourceManifestDigest1;
  source_snapshot_refs: SourceSnapshotRefs2;
  work_package_digest: WorkPackageDigest3;
  work_package_ref: WorkPackageRef2;
}
export interface BindingEpochs1 {
  /**
   * This interface was referenced by `BindingEpochs1`'s JSON-Schema definition
   * via the `patternProperty` "^\S+$".
   */
  [k: string]: number;
}
export interface ResourceEvidenceDigests1 {
  /**
   * This interface was referenced by `ResourceEvidenceDigests1`'s JSON-Schema definition
   * via the `patternProperty` "^\S+$".
   */
  [k: string]: string;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ContractV1".
 */
export interface ContractV1 {
  rules: Rules;
  shop_id: ShopId2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Rule".
 */
export interface Rule {
  agreement: Agreement;
  correct_flow: CorrectFlow;
  counter_examples: CounterExamples;
  id: Id4;
  predicate: Predicate;
  severity: Severity;
  sources: RuleSources;
  title: Title;
  triangle: Triangle;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RuleSources".
 */
export interface RuleSources {
  code: Code1;
  traces: Traces;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Triangle".
 */
export interface Triangle {
  killed: Killed1;
  mutants: Mutants;
  scenarios: Scenarios1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ControlErrorV1".
 */
export interface ControlErrorV1 {
  code: Code2;
  evidence_refs: EvidenceRefs14;
  retry_class: RetryClass;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ControllerInvitationV1".
 */
export interface ControllerInvitationV1 {
  case_id: CaseId21;
  copy_url: CopyUrl;
  expires_at: ExpiresAt11;
  invitation_id: InvitationId;
  recipient_hint: RecipientHint;
  requester_id: RequesterId2;
  resource_ids: ResourceIds1;
  status: Status8;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CreateActionIntentV1".
 */
export interface CreateActionIntentV1 {
  readiness_digest: ReadinessDigest3;
  readiness_id: ReadinessId3;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CreateCaseV1".
 */
export interface CreateCaseV1 {
  shop_url: ShopUrl4;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CreateDraftV1".
 */
export interface CreateDraftV1 {
  shop_url: ShopUrl5;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CreateInvitationV1".
 */
export interface CreateInvitationV1 {
  recipient_hint: RecipientHint1;
  resource_ids: ResourceIds2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CreateProviderIntentV1".
 */
export interface CreateProviderIntentV1 {
  provider_id: ProviderId2;
  purpose: Purpose3;
  resource_id: ResourceId1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CreateUploadRequestV1".
 */
export interface CreateUploadRequestV1 {
  binding_epochs: BindingEpochs2;
  expected_manifest_digest: ExpectedManifestDigest;
  expected_total_bytes: ExpectedTotalBytes;
  manifest: Manifest;
}
export interface BindingEpochs2 {
  /**
   * This interface was referenced by `BindingEpochs2`'s JSON-Schema definition
   * via the `patternProperty` "^\S+$".
   */
  [k: string]: number;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "DashboardSpecV1".
 */
export interface DashboardSpecV1 {
  created_at: CreatedAt9;
  evidence_refs: EvidenceRefs15;
  filters: Filters;
  graft_id: GraftId6;
  group_by: GroupBy;
  id: Id5;
  metrics: Metrics;
  producer: Producer;
  question: Question;
  title: Title1;
}
export interface Filters {
  [k: string]: JsonValue;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "DeliverySnapshotV1".
 */
export interface DeliverySnapshotV1 {
  action_plan_ref: ActionPlanRef;
  approval_set_ref: ApprovalSetRef;
  cancellation_ref: CancellationRef;
  case_id: CaseId23;
  checked_at: CheckedAt8;
  current_evidence_refs: CurrentEvidenceRefs;
  deployment_ref: DeploymentRef;
  exit_manifest_ref: ExitManifestRef;
  exit_plan_ref: ExitPlanRef1;
  final_asset_manifest_ref: FinalAssetManifestRef;
  generation: Generation12;
  graph_ref: GraphRef2;
  issue: Issue | null;
  lifecycle_ref: LifecycleRef;
  pending_effect_refs: PendingEffectRefs;
  reservation_ref: ReservationRef;
  review_ref: ReviewRef;
  run_id: RunId13;
  state_cutover_ref: StateCutoverRef;
  state_version: StateVersion3;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "DependencyV1".
 */
export interface DependencyV1 {
  access_mode: AccessMode;
  authority_ref: AuthorityRef;
  component_ids: ComponentIds;
  dependency_id: DependencyId;
  limitation: Limitation;
  purpose: Purpose4;
  test_identity_ref: TestIdentityRef;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "DependencyInspectArgsV1".
 */
export interface DependencyInspectArgsV1 {
  package: Package;
  recipe_ref: RecipeRef;
  version: Version1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "DependencyManifestV1".
 */
export interface DependencyManifestV1 {
  dependencies: Dependencies1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Dependency".
 */
export interface Dependency {
  access_mode: AccessMode1;
  authority_ref: AuthorityRef1;
  component_ids: ComponentIds1;
  dependency_id: DependencyId1;
  limitation: Limitation1;
  purpose: Purpose5;
  test_identity_ref: TestIdentityRef1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "DeploymentObservationV1".
 */
export interface DeploymentObservationV1 {
  case_id: CaseId24;
  checked_at: CheckedAt9;
  current_runtime_evidence_refs: CurrentRuntimeEvidenceRefs;
  effect_id: EffectId;
  environment_id: EnvironmentId1;
  observed_artifact_digest: ObservedArtifactDigest;
  observed_config_digest: ObservedConfigDigest;
  outcome: Outcome4;
  provider: Provider;
  provider_deploy_id: ProviderDeployId;
  provider_status: ProviderStatus;
  resource_id: ResourceId2;
  submitted_artifact_digest: SubmittedArtifactDigest;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "DetectionRuleV1".
 */
export interface DetectionRuleV1 {
  created_at: CreatedAt10;
  evidence_refs: EvidenceRefs16;
  graft_id: GraftId7;
  id: Id6;
  language: Language;
  operation: Operation2;
  pattern: Pattern;
  producer: Producer;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "DocsLookupArgsV1".
 */
export interface DocsLookupArgsV1 {
  catalog_ref: CatalogRef;
  topic: Topic;
  version: Version2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "DraftCaseV1".
 */
export interface DraftCaseV1 {
  continuation_ref: ContinuationRef1;
  created_at: CreatedAt11;
  draft_id: DraftId;
  expires_at: ExpiresAt12;
  shop_url: ShopUrl6;
  state: State6;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "DriverV1".
 */
export interface DriverV1 {
  proven_runs: ProvenRuns;
  selectors: Selectors;
  steps: Steps;
}
export interface Selectors {
  [k: string]: string;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "DriverStep".
 */
export interface DriverStep {
  driver_step: DriverStep1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ApiStep".
 */
export interface ApiStep {
  api_step: ApiStep1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "MockStep".
 */
export interface MockStep {
  paypal_mock_response_code: PaypalMockResponseCode;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "EffectIntentV1".
 */
export interface EffectIntentV1 {
  action_group_id: ActionGroupId1;
  actor_id: ActorId3;
  approval_set_id: ApprovalSetId1;
  case_id: CaseId25;
  created_at: CreatedAt12;
  effect_class: EffectClass1;
  effect_id: EffectId1;
  environment_id: EnvironmentId2;
  expected_version: ExpectedVersion;
  generation: Generation13;
  operation: Operation3;
  plan_digest: PlanDigest2;
  provider_idempotency_ref: ProviderIdempotencyRef;
  provider_receipt_ref: ProviderReceiptRef;
  reconciliation_ref: ReconciliationRef;
  request_digest: RequestDigest;
  resource_epochs: ResourceEpochs1;
  resource_id: ResourceId3;
  run_id: RunId14;
  slot_id: SlotId2;
  state: State7;
}
export interface ResourceEpochs1 {
  /**
   * This interface was referenced by `ResourceEpochs1`'s JSON-Schema definition
   * via the `patternProperty` "^\S+$".
   */
  [k: string]: number;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "EffectSlotV1".
 */
export interface EffectSlotV1 {
  artifact_digest: ArtifactDigest2;
  cardinality: Cardinality1;
  config_digest: ConfigDigest2;
  depends_on: DependsOn1;
  effect_class: EffectClass2;
  expected_version_ref: ExpectedVersionRef1;
  operation: Operation4;
  recovery_branch_ref: RecoveryBranchRef1;
  required_authority_refs: RequiredAuthorityRefs1;
  required_controller_ids: RequiredControllerIds2;
  slot_id: SlotId3;
  state_plan_digest: StatePlanDigest2;
  target_key: TargetKey;
  trigger_digest: TriggerDigest1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "EvidenceReadArgsV1".
 */
export interface EvidenceReadArgsV1 {
  max_bytes: MaxBytes;
  ref: Ref1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "EvidenceSummaryArgsV1".
 */
export interface EvidenceSummaryArgsV1 {
  projection: Projection;
  run_ref: RunRef1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ExecutionProposalV1".
 */
export interface ExecutionProposalV1 {
  evidence_refs: EvidenceRefs17;
  expected_subject: ExpectedSubject1;
  operation: Operation5;
  recipe_ref: RecipeRef1;
  requested_output_schemas: RequestedOutputSchemas;
  scenario_ref: ScenarioRef;
  subject_ref: SubjectRef;
  task_id: TaskId2;
  variant: Variant2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ExecutionRequestArgsV1".
 */
export interface ExecutionRequestArgsV1 {
  proposal_ref: ProposalRef;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ExecutionStatusArgsV1".
 */
export interface ExecutionStatusArgsV1 {
  request_id: RequestId2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ExitCheckPlanV1".
 */
export interface ExitCheckPlanV1 {
  allowed_restart_count: AllowedRestartCount;
  authority_refs: AuthorityRefs3;
  budget_ref: BudgetRef1;
  case_id: CaseId26;
  criteria_refs: CriteriaRefs;
  deadline: Deadline1;
  evidence_read_authority_ref: EvidenceReadAuthorityRef;
  executor_identity_ref: ExecutorIdentityRef;
  exit_plan_id: ExitPlanId;
  failure_route_ref: FailureRouteRef;
  final_artifact_digest: FinalArtifactDigest1;
  final_config_digest: FinalConfigDigest1;
  generation: Generation14;
  plan_digest: PlanDigest3;
  private_evidence_destination_ref: PrivateEvidenceDestinationRef;
  recovery_plan_ref: RecoveryPlanRef1;
  reservation_ref: ReservationRef1;
  run_id: RunId15;
  state_digest: StateDigest;
  trusted_code_digest: TrustedCodeDigest;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ExitCheckResultV1".
 */
export interface ExitCheckResultV1 {
  case_id: CaseId27;
  evidence_read_authority_ref: EvidenceReadAuthorityRef1;
  executor_identity_ref: ExecutorIdentityRef1;
  exit_plan_digest: ExitPlanDigest;
  exit_plan_ref: ExitPlanRef2;
  final_artifact_digest: FinalArtifactDigest2;
  final_config_digest: FinalConfigDigest2;
  finished_at: FinishedAt;
  generation: Generation15;
  observations: Observations;
  ordinary_denials: OrdinaryDenials;
  outcome: Outcome5;
  policy_digest: PolicyDigest5;
  reservation_ref: ReservationRef2;
  resource_epochs: ResourceEpochs2;
  restart_count: RestartCount;
  result_digest: ResultDigest;
  result_id: ResultId;
  run_id: RunId16;
  scope_digest: ScopeDigest6;
  signature: SignatureMaterial;
  started_at: StartedAt;
  state_digest: StateDigest1;
  trusted_code_digest: TrustedCodeDigest1;
  work_package_digest: WorkPackageDigest4;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ExitCriterionObservation".
 */
export interface ExitCriterionObservation {
  criterion_ref: CriterionRef;
  evidence_ref: EvidenceRef;
  observed_at: ObservedAt;
  payload_digest: PayloadDigest2;
  state: State8;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CapabilityDenial".
 */
export interface CapabilityDenial {
  capability: Capability1;
  denied_at: DeniedAt;
  evidence_ref: EvidenceRef1;
  payload_digest: PayloadDigest3;
}
export interface ResourceEpochs2 {
  /**
   * This interface was referenced by `ResourceEpochs2`'s JSON-Schema definition
   * via the `patternProperty` "^\S+$".
   */
  [k: string]: number;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ExitEvidenceReconciliationV1".
 */
export interface ExitEvidenceReconciliationV1 {
  authenticity_ref: AuthenticityRef3;
  case_id: CaseId28;
  checked_at: CheckedAt10;
  evidence_read_receipt: ExitEvidenceReadReceipt;
  exit_manifest_digest: ExitManifestDigest;
  exit_manifest_ref: ExitManifestRef1;
  exit_plan_digest: ExitPlanDigest1;
  exit_plan_ref: ExitPlanRef3;
  exit_result_digest: ExitResultDigest;
  exit_result_ref: ExitResultRef;
  generation: Generation16;
  policy_digest: PolicyDigest6;
  resource_epochs: ResourceEpochs3;
  run_id: RunId17;
  scope_digest: ScopeDigest7;
  work_package_digest: WorkPackageDigest5;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ExitEvidenceReadReceipt".
 */
export interface ExitEvidenceReadReceipt {
  authority_ref: AuthorityRef2;
  disclosure_ref: DisclosureRef;
  read_at: ReadAt;
  read_digest: ReadDigest;
  read_evidence_ref: ReadEvidenceRef;
  revocation_digest: RevocationDigest;
  revocation_ref: RevocationRef;
  revoked_at: RevokedAt2;
}
export interface ResourceEpochs3 {
  /**
   * This interface was referenced by `ResourceEpochs3`'s JSON-Schema definition
   * via the `patternProperty` "^\S+$".
   */
  [k: string]: number;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ExitItemV1".
 */
export interface ExitItemV1 {
  evidence_refs: EvidenceRefs18;
  item_id: ItemId;
  owner: Owner;
  required_for_exit: RequiredForExit;
  state: State9;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ExitManifestV1".
 */
export interface ExitManifestV1 {
  case_id: CaseId29;
  cleanup_items: CleanupItems;
  exit_id: ExitId;
  legacy_obligations_ref: LegacyObligationsRef1;
  merchant_assets_ref: MerchantAssetsRef;
  outcome: Outcome6;
  persistent_runtime_evidence_refs: PersistentRuntimeEvidenceRefs;
  post_denial_observation_refs: PostDenialObservationRefs;
  run_id: RunId18;
  temporary_assets_ref: TemporaryAssetsRef;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ExitItem".
 */
export interface ExitItem {
  evidence_refs: EvidenceRefs19;
  item_id: ItemId1;
  owner: Owner1;
  required_for_exit: RequiredForExit1;
  state: State10;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "FinalisationPlanV1".
 */
export interface FinalisationPlanV1 {
  candidate_change_required: CandidateChangeRequired;
  case_id: CaseId30;
  dependency_check_refs: DependencyCheckRefs;
  desired_asset_manifest_ref: DesiredAssetManifestRef;
  final_candidate_ref: FinalCandidateRef;
  finalisation_id: FinalisationId;
  generation: Generation17;
  independence_criteria_refs: IndependenceCriteriaRefs;
  plan_digest: PlanDigest4;
  required_action_slot_ids: RequiredActionSlotIds;
  run_id: RunId19;
  validation_request_refs: ValidationRequestRefs;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "FinaliseUploadRequestV1".
 */
export interface FinaliseUploadRequestV1 {
  expected_manifest_digest: ExpectedManifestDigest1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "GuardEventV1".
 */
export interface GuardEventV1 {
  event: GuardEventKind;
  graft_id: GraftId8;
  latency_ms: LatencyMs;
  lib_version: LibVersion;
  money?: Money | null;
  order_ref: OrderRef1;
  path: Side;
  paypal_ids?: PayPalRefs | null;
  shop_id: ShopId3;
  signature?: Signature1;
  ts: Ts;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HandoffPackV1".
 */
export interface HandoffPackV1 {
  freeze_window_advice: FreezeWindowAdvice;
  records: Records;
  validation_summary: HandoffSummary;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HandoffRecord".
 */
export interface HandoffRecord {
  amount: Amount;
  currency: Currency1;
  customer_ref: CustomerRef;
  cycle: Cycle;
  id: Id7;
  next_billing: NextBilling;
  source: Source1;
  status: Status9;
  type: HandoffType;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HandoffSummary".
 */
export interface HandoffSummary {
  counts: Counts;
  duplicates: Duplicates;
  inactive: Inactive;
  totals_per_currency: TotalsPerCurrency;
}
export interface Counts {
  [k: string]: number;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HandoffRecordV1".
 */
export interface HandoffRecordV1 {
  amount: Amount1;
  currency: Currency2;
  customer_ref: CustomerRef1;
  cycle: Cycle1;
  id: Id8;
  next_billing: NextBilling1;
  source: Source2;
  status: Status10;
  type: HandoffType;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HealDecisionV1".
 */
export interface HealDecisionV1 {
  action: HealAction;
  from_stage_pct: FromStagePct;
  graft_id: GraftId9;
  hard_stop?: HardStop;
  reason: Reason;
  stats: HealStats;
  to_stage_pct: ToStagePct;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HealStats".
 */
export interface HealStats {
  n_new: NNew;
  n_old: NOld;
  prob_new_not_worse: ProbNewNotWorse;
  success_new: SuccessNew;
  success_old: SuccessOld;
  threshold: Threshold;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HealNoteV1".
 */
export interface HealNoteV1 {
  created_at: CreatedAt13;
  cutback_requested: CutbackRequested;
  evidence_refs: EvidenceRefs20;
  graft_id: GraftId10;
  id: Id9;
  pause_requested: PauseRequested;
  producer: Producer;
  stage_pct: StagePct;
  text: Text;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HeraldTextV1".
 */
export interface HeraldTextV1 {
  created_at: CreatedAt14;
  graft_id: GraftId11;
  id: Id10;
  kind: HeraldKind;
  numbers_used: NumbersUsed;
  producer: Producer;
  text: Text1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "LedgerNumber".
 */
export interface LedgerNumber {
  entry_hash: EntryHash;
  json_pointer: JsonPointer;
  value: Value;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "IssueV1".
 */
export interface IssueV1 {
  code: Code3;
  evidence_refs: EvidenceRefs21;
  input_ref: InputRef1;
  owner_role: OwnerRole1;
  recovery: Recovery1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "IssueApplyApprovalV1".
 */
export interface IssueApplyApprovalV1 {
  plan_digest: PlanDigest5;
  plan_ref: PlanRef;
  reviewed_bundle_digest: ReviewedBundleDigest1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "JobResultV1".
 */
export interface JobResultV1 {
  artifacts: Artifacts;
  error?: Error;
  finished: Finished;
  job_id: JobId;
  logs_ref: LogsRef;
  rate_limit_pauses: RateLimitPauses;
  raw_capture_refs: RawCaptureRefs;
  runner_identity: JobRunnerIdentity;
  started: Started;
  status: JobStatus;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "JobRunnerIdentity".
 */
export interface JobRunnerIdentity {
  run_id: RunId20;
  sha: Sha1;
  workflow: Workflow1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "JobSpecV1".
 */
export interface JobSpecV1 {
  graft_id: GraftId12;
  job_id: JobId1;
  kind: JobKind;
  mutant_ids: MutantIds;
  scenario_ids: ScenarioIds;
  secrets_ref: SecretsRef1;
  shop_pack_ref: ShopPackRef;
  signature: Signature2;
  stage: Stage;
  timeouts: JobTimeouts;
  variants: Variants;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "JobTimeouts".
 */
export interface JobTimeouts {
  build_s: BuildS;
  run_s: RunS;
  total_s: TotalS;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "LaneChangeV1".
 */
export interface LaneChangeV1 {
  created_at: CreatedAt15;
  graft_id: GraftId13;
  id: Id11;
  lane: Lane;
  producer: Producer;
  reason: Reason1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "LifecycleRunV1".
 */
export interface LifecycleRunV1 {
  active_effect_refs: ActiveEffectRefs1;
  attempt: Attempt3;
  case_id: CaseId31;
  evidence_refs: EvidenceRefs22;
  generation: Generation18;
  resource_graph_digest: ResourceGraphDigest3;
  run_id: RunId21;
  scope_digest: ScopeDigest8;
  stage: Stage2;
  updated_at: UpdatedAt3;
  work_id: WorkId3;
  work_package_digest: WorkPackageDigest6;
  work_package_ref: WorkPackageRef3;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "LifecycleWorkRequestV1".
 */
export interface LifecycleWorkRequestV1 {
  authority_binding_epochs: AuthorityBindingEpochs1;
  budget_ref: BudgetRef2;
  deadline: Deadline2;
  expected_output_schema: ExpectedOutputSchema;
  forbidden_effect_codes: ForbiddenEffectCodes;
  generation: Generation19;
  input_artifact_refs: InputArtifactRefs;
  operation_kind: OperationKind;
  package_digest: PackageDigest1;
  package_ref: PackageRef;
  policy_digest: PolicyDigest7;
  request_id: RequestId3;
  run_id: RunId22;
  runtime_profile_digest: RuntimeProfileDigest3;
}
export interface AuthorityBindingEpochs1 {
  /**
   * This interface was referenced by `AuthorityBindingEpochs1`'s JSON-Schema definition
   * via the `patternProperty` "^\S+$".
   */
  [k: string]: number;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "LifecycleWorkRequestReceiptV1".
 */
export interface LifecycleWorkRequestReceiptV1 {
  accepted_at: AcceptedAt1;
  generation: Generation20;
  request_digest: RequestDigest1;
  request_id: RequestId4;
  run_id: RunId23;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "LifecycleWorkResultV1".
 */
export interface LifecycleWorkResultV1 {
  authenticity_ref: AuthenticityRef4;
  completed_at: CompletedAt1;
  evidence_refs: EvidenceRefs23;
  generation: Generation21;
  inputs_digest: InputsDigest;
  limitation_codes: LimitationCodes;
  outcome: Outcome7;
  output_artifact_refs: OutputArtifactRefs;
  request_id: RequestId5;
  run_id: RunId24;
  source_unchanged: SourceUnchanged;
  worker_identity_ref: WorkerIdentityRef;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "LinksPackV1".
 */
export interface LinksPackV1 {
  buttons: Buttons;
  proofs: Proofs;
  untouched: Untouched;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "LinkButton".
 */
export interface LinkButton {
  hosted_button_id?: HostedButtonId;
  new_link_url: NewLinkUrl;
  old_form_fields?: OldFormFields;
  page: Page;
  snippet_html: SnippetHtml;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "LinkProof".
 */
export interface LinkProof {
  capture_id: CaptureId2;
  link: Link;
  order_id: OrderId2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "MappingRowV1".
 */
export interface MappingRowV1 {
  cmel_kind: Kind2;
  notes: Notes;
  signal_fields: SignalFields;
  source: Source3;
}
/**
 * Cumulative micro-USD accounting declaration, not a spend authorisation.
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ModelBudgetV1".
 */
export interface ModelBudgetV1 {
  budget_id: BudgetId;
  ceiling_micro_usd: CeilingMicroUsd;
  outstanding_micro_usd: OutstandingMicroUsd;
  pricing_ref: PricingRef;
  spent_micro_usd: SpentMicroUsd;
  target_micro_usd: TargetMicroUsd;
  unknown_micro_usd: UnknownMicroUsd;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ModelTurnRequestV1".
 */
export interface ModelTurnRequestV1 {
  allowed_tool_ids: AllowedToolIds1;
  budget_reservation_ref: BudgetReservationRef;
  context_digest: ContextDigest;
  context_ref: ContextRef;
  deadline: Deadline3;
  generation: Generation22;
  input_token_cap: InputTokenCap;
  lease_epoch: LeaseEpoch2;
  model_profile_ref: ModelProfileRef1;
  output_schema: OutputSchema;
  output_token_cap: OutputTokenCap;
  task_id: TaskId3;
  turn_id: TurnId;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ToolCall".
 */
export interface ToolCall {
  arguments_digest: ArgumentsDigest;
  arguments_ref: ArgumentsRef;
  call_id: CallId;
  tool: Tool;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ModelTurnStatusV1".
 */
export interface ModelTurnStatusV1 {
  checked_at: CheckedAt11;
  issue: Issue | null;
  result_ref: ResultRef;
  state: State11;
  task_id: TaskId5;
  turn_id: TurnId2;
  usage_receipt_ref: UsageReceiptRef1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "MoneyV1".
 */
export interface MoneyV1 {
  currency: Currency3;
  minor: Minor1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "MutantV1".
 */
export interface MutantV1 {
  equivalent_suspect: EquivalentSuspect;
  id: Id12;
  killed_by: KilledBy;
  location: FileLocation;
  op: MutantOp;
  patch: Patch;
  rule: Rule1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "FileLocation".
 */
export interface FileLocation {
  file: File;
  line: Line;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "MutantSetV1".
 */
export interface MutantSetV1 {
  created_at: CreatedAt16;
  graft_id: GraftId15;
  id: Id13;
  mutants: Mutants1;
  producer: Producer;
  unguarded_rule_ids: UnguardedRuleIds;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Mutant".
 */
export interface Mutant {
  equivalent_suspect: EquivalentSuspect1;
  id: Id14;
  killed_by: KilledBy1;
  location: FileLocation;
  op: MutantOp;
  patch: Patch1;
  rule: Rule2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "MutationOperatorV1".
 */
export interface MutationOperatorV1 {
  fault: Fault;
  op: MutantOp;
  rules_broken: RulesBroken;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "OmissionV1".
 */
export interface OmissionV1 {
  component_id: ComponentId;
  evidence_refs: EvidenceRefs24;
  path: Path;
  reason_code: ReasonCode2;
  required_for_scope: RequiredForScope;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "OmissionManifestV1".
 */
export interface OmissionManifestV1 {
  items: Items1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Omission".
 */
export interface Omission {
  component_id: ComponentId1;
  evidence_refs: EvidenceRefs25;
  path: Path1;
  reason_code: ReasonCode3;
  required_for_scope: RequiredForScope1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "P5ProblemV1".
 */
export interface P5ProblemV1 {
  code: Code4;
  detail: Detail;
  evidence_refs: EvidenceRefs26;
  instance: Instance;
  reason_code: ReasonCode4;
  recovery_action: RecoveryAction;
  request_id: RequestId6;
  retry: Retry;
  status: Status11;
  title: Title2;
  type: Type;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "PendingResultV1".
 */
export interface PendingResultV1 {
  checked_at: CheckedAt12;
  evidence_refs: EvidenceRefs27;
  request_id: RequestId7;
  state: State12;
}
/**
 * Untrusted seed/extension proposal; full dependency resolution requires admission.
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "PlanProposalV1".
 */
export interface PlanProposalV1 {
  case_id: CaseId32;
  generation: Generation23;
  parent_request_id: ParentRequestId;
  reason_refs: ReasonRefs;
  run_id: RunId25;
  tasks: Tasks;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "PredicateResultV1".
 */
export interface PredicateResultV1 {
  checked_at: CheckedAt13;
  evidence_refs: EvidenceRefs28;
  predicate: Predicate1;
  slot_id: SlotId4;
  status: Status12;
  subject_digest: SubjectDigest1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "PrivateReviewViewV1".
 */
export interface PrivateReviewViewV1 {
  approval_set: ApprovalSet | null;
  bundle: ReviewBundle;
  evidence_summary_refs: EvidenceSummaryRefs;
  missing: Missing;
  plan: ActionPlan;
  processing: ProcessingDisclosure;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ApprovalSet".
 */
export interface ApprovalSet {
  approval_refs: ApprovalRefs1;
  approval_set_id: ApprovalSetId2;
  authority_epochs: AuthorityEpochs1;
  case_id: CaseId33;
  checked_at: CheckedAt14;
  generation: Generation24;
  plan_digest: PlanDigest6;
  required_controller_ids: RequiredControllerIds3;
  run_id: RunId26;
  state: State13;
}
export interface AuthorityEpochs1 {
  /**
   * This interface was referenced by `AuthorityEpochs1`'s JSON-Schema definition
   * via the `patternProperty` "^\S+$".
   */
  [k: string]: number;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ReviewBundle".
 */
export interface ReviewBundle {
  artifact_digest: ArtifactDigest3;
  baseline_snapshot_refs: BaselineSnapshotRefs;
  bundle_digest: BundleDigest;
  bundle_id: BundleId;
  candidate_snapshot_refs: CandidateSnapshotRefs;
  case_id: CaseId34;
  created_at: CreatedAt17;
  domain_rule_result_refs: DomainRuleResultRefs;
  effective_config_digest: EffectiveConfigDigest;
  missing_evidence_refs: MissingEvidenceRefs;
  patch_digest: PatchDigest2;
  proposed_apply_plan_ref: ProposedApplyPlanRef;
  recovery_plan_ref: RecoveryPlanRef2;
  run_id: RunId27;
  scenario_result_refs: ScenarioResultRefs;
  security_result_refs: SecurityResultRefs;
  unsupported_paths: UnsupportedPaths;
  work_package_digest: WorkPackageDigest7;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ActionPlan".
 */
export interface ActionPlan {
  budget_ref: BudgetRef3;
  case_id: CaseId35;
  exit_plan_ref: ExitPlanRef4;
  expires_at: ExpiresAt13;
  finalisation_plan_ref: FinalisationPlanRef1;
  generation: Generation25;
  graph_digest: GraphDigest2;
  plan_digest: PlanDigest7;
  plan_id: PlanId1;
  policy_digest: PolicyDigest8;
  recovery_plan_ref: RecoveryPlanRef3;
  review_bundle_digest: ReviewBundleDigest2;
  run_id: RunId28;
  scope_digest: ScopeDigest9;
  slots: Slots1;
  state_plan_ref: StatePlanRef1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ProbeResultV1".
 */
export interface ProbeResultV1 {
  deadline_notes: DeadlineNotes;
  families_found: FamiliesFound;
  files_or_pages: FilesOrPages;
  next_step: NextStep;
  official_modern_module_available?: OfficialModernModuleAvailable;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ProcessingDisclosureV1".
 */
export interface ProcessingDisclosureV1 {
  checked_at: CheckedAt15;
  copy_scope: CopyScope1;
  limits: Limits1;
  policy_digest: PolicyDigest9;
  recipients: Recipients1;
  status: Status13;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ProcessingRecipientV1".
 */
export interface ProcessingRecipientV1 {
  name: Name4;
  purpose: Purpose6;
  region_text: RegionText1;
  retention_text: RetentionText1;
  terms_evidence_refs: TermsEvidenceRefs1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "PromotionDecisionV1".
 */
export interface PromotionDecisionV1 {
  action: Action;
  advice: HealDecision;
  advice_digest: AdviceDigest;
  case_id: CaseId36;
  checked_at: CheckedAt16;
  expires_at: ExpiresAt14;
  generation: Generation26;
  policy_digest: PolicyDigest10;
  proof_plan_digest: ProofPlanDigest1;
  proof_result_digest: ProofResultDigest1;
  proof_result_ref: ProofResultRef1;
  reason_code: ReasonCode5;
  resource_epochs: ResourceEpochs4;
  run_id: RunId29;
  scope_digest: ScopeDigest10;
  work_package_digest: WorkPackageDigest8;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "HealDecision".
 */
export interface HealDecision {
  action: HealAction;
  from_stage_pct: FromStagePct1;
  graft_id: GraftId16;
  hard_stop?: HardStop1;
  reason: Reason2;
  stats: HealStats;
  to_stage_pct: ToStagePct1;
}
export interface ResourceEpochs4 {
  /**
   * This interface was referenced by `ResourceEpochs4`'s JSON-Schema definition
   * via the `patternProperty` "^\S+$".
   */
  [k: string]: number;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ProofPlanV1".
 */
export interface ProofPlanV1 {
  case_id: CaseId37;
  checks: Checks2;
  created_at: CreatedAt18;
  exclusions: Exclusions;
  expires_at: ExpiresAt15;
  generation: Generation27;
  plan_digest: PlanDigest8;
  plan_id: PlanId2;
  policy_digest: PolicyDigest11;
  resource_epochs: ResourceEpochs5;
  run_id: RunId30;
  scope_digest: ScopeDigest11;
  work_package_digest: WorkPackageDigest9;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ProofCheck".
 */
export interface ProofCheck {
  check_id: CheckId2;
  critical: Critical;
  flow_id: FlowId;
  input_digest: InputDigest3;
  kind: Kind14;
  owner_role: OwnerRole2;
  required_evidence_class: RequiredEvidenceClass;
  required_schema: RequiredSchema;
  required_trust: RequiredTrust;
  rule_ids: RuleIds;
  subject_manifest_digest: SubjectManifestDigest1;
  subject_manifest_ref: SubjectManifestRef1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ProofExclusion".
 */
export interface ProofExclusion {
  approval_digest: ApprovalDigest;
  approval_ref: ApprovalRef;
  check_id: CheckId3;
  reason: Reason3;
}
export interface ResourceEpochs5 {
  /**
   * This interface was referenced by `ResourceEpochs5`'s JSON-Schema definition
   * via the `patternProperty` "^\S+$".
   */
  [k: string]: number;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ProofResultV1".
 */
export interface ProofResultV1 {
  case_id: CaseId38;
  checked_at: CheckedAt17;
  generation: Generation28;
  outcome: Outcome8;
  plan_digest: PlanDigest9;
  plan_ref: PlanRef1;
  policy_digest: PolicyDigest12;
  reason_codes: ReasonCodes1;
  resource_epochs: ResourceEpochs6;
  result_digest: ResultDigest1;
  result_id: ResultId1;
  results: Results;
  run_id: RunId31;
  scope_digest: ScopeDigest12;
  work_package_digest: WorkPackageDigest10;
}
export interface ResourceEpochs6 {
  /**
   * This interface was referenced by `ResourceEpochs6`'s JSON-Schema definition
   * via the `patternProperty` "^\S+$".
   */
  [k: string]: number;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ProofCheckResult".
 */
export interface ProofCheckResult {
  check_id: CheckId4;
  evidence_refs: EvidenceRefs29;
  reason_code: ReasonCode6;
  state: State14;
  subject_manifest_digest: SubjectManifestDigest2;
  subject_manifest_ref: SubjectManifestRef2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ProofStrengthV1".
 */
export interface ProofStrengthV1 {
  equivalent_dropped: EquivalentDropped1;
  killed: Killed2;
  score: Score1;
  total: Total;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ProviderIntentV1".
 */
export interface ProviderIntentV1 {
  case_id: CaseId39;
  continuation_ref: ContinuationRef2;
  expires_at: ExpiresAt16;
  intent_id: IntentId;
  provider_id: ProviderId3;
  purpose: Purpose7;
  redirect_url: RedirectUrl;
  resource_id: ResourceId4;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ProviderRefV1".
 */
export interface ProviderRefV1 {
  account_id: AccountId2;
  adapter_version: AdapterVersion1;
  provider_id: ProviderId4;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "PublicMetricV1".
 */
export interface PublicMetricV1 {
  evidence_ref: EvidenceRef2;
  name: Name5;
  value: Value1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "PublicProofViewV1".
 */
export interface PublicProofViewV1 {
  checked_at: CheckedAt18;
  evidence_class: EvidenceClass2;
  integrity: Integrity;
  limitations: Limitations1;
  public_id: PublicId;
  scope_text: ScopeText;
  summary_metrics: SummaryMetrics;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "PublicMetric".
 */
export interface PublicMetric {
  evidence_ref: EvidenceRef3;
  name: Name6;
  value: Value2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RawCaptureV1".
 */
export interface RawCaptureV1 {
  exchanges: Exchanges;
  graft_id: GraftId17;
  run_id: RunId32;
  scenario_id: ScenarioId1;
  variant: Variant1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "DbChange".
 */
export interface DbChange {
  after: After1;
  before: Before;
  key: Key;
  table: Table;
}
export interface Key {
  [k: string]: JsonValue;
}
export interface Headers {
  [k: string]: string;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RecipeV1".
 */
export interface RecipeV1 {
  confidence: Confidence;
  env?: RecipeEnv | null;
  fingerprint: Fingerprint;
  id: Id15;
  provenance: Provenance2;
  scenarios: Scenarios2;
  signature: Signature3;
  status: RecipeStatus;
  transform: Transform;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RecipeEnv".
 */
export interface RecipeEnv {
  compose: Compose;
  dockerfile: Dockerfile;
  driver_template: DriverTemplate;
  seed: Seed;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Fingerprint".
 */
export interface Fingerprint {
  ast_shape_hash: AstShapeHash;
  family: Family;
  framework: Framework;
  lang: Lang;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RecipeLookupArgsV1".
 */
export interface RecipeLookupArgsV1 {
  catalog_ref: CatalogRef1;
  fingerprint: Fingerprint1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RecipeStageArgsV1".
 */
export interface RecipeStageArgsV1 {
  detection_rule_ref: DetectionRuleRef;
  recipe_ref: RecipeRef2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RecoveryPlanV1".
 */
export interface RecoveryPlanV1 {
  affected_effect_refs: AffectedEffectRefs;
  baseline_refs: BaselineRefs;
  case_id: CaseId40;
  chosen_route: ChosenRoute;
  compensatable_effects: CompensatableEffects;
  irreversible_effects: IrreversibleEffects;
  original_transaction_routes_ref: OriginalTransactionRoutesRef;
  plan_digest: PlanDigest10;
  plan_id: PlanId3;
  required_current_authority: RequiredCurrentAuthority;
  restore_preconditions_ref: RestorePreconditionsRef;
  reversible_effects: ReversibleEffects;
  state_compatibility_ref: StateCompatibilityRef;
  unknown_effects: UnknownEffects;
  verification_case_refs: VerificationCaseRefs;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RequiredActionV1".
 */
export interface RequiredActionV1 {
  enabled: Enabled1;
  kind: Kind15;
  reason_code: ReasonCode7;
  resource_ids: ResourceIds3;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RequiredFlowV1".
 */
export interface RequiredFlowV1 {
  acceptance_rule_ids: AcceptanceRuleIds;
  flow_id: FlowId1;
  limitation: Limitation2;
  origin_routes: OriginRoutes;
  payment_family: PaymentFamily;
  required: Required3;
  scenario_refs: ScenarioRefs;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RequiredFlowManifestV1".
 */
export interface RequiredFlowManifestV1 {
  flows: Flows;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RequiredFlow".
 */
export interface RequiredFlow {
  acceptance_rule_ids: AcceptanceRuleIds1;
  flow_id: FlowId2;
  limitation: Limitation3;
  origin_routes: OriginRoutes1;
  payment_family: PaymentFamily1;
  required: Required4;
  scenario_refs: ScenarioRefs1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ResolvedDeliveryViewV1".
 */
export interface ResolvedDeliveryViewV1 {
  approvals: ApprovalSet | null;
  delivery_route: DeliveryRoute1;
  deployment: DeploymentObservation | null;
  exit_manifest: ExitManifest | null;
  exit_plan: ExitCheckPlan | null;
  final_assets: AssetManifest | null;
  lifecycle: LifecycleRun;
  plan: ActionPlan | null;
  predicate_results: PredicateResults;
  reservation: TargetReservation | null;
  review: ReviewBundle | null;
  snapshot: DeliverySnapshot;
  state_cutover: StateCutover | null;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "DeploymentObservation".
 */
export interface DeploymentObservation {
  case_id: CaseId41;
  checked_at: CheckedAt19;
  current_runtime_evidence_refs: CurrentRuntimeEvidenceRefs1;
  effect_id: EffectId2;
  environment_id: EnvironmentId3;
  observed_artifact_digest: ObservedArtifactDigest1;
  observed_config_digest: ObservedConfigDigest1;
  outcome: Outcome9;
  provider: Provider1;
  provider_deploy_id: ProviderDeployId1;
  provider_status: ProviderStatus1;
  resource_id: ResourceId5;
  submitted_artifact_digest: SubmittedArtifactDigest1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ExitManifest".
 */
export interface ExitManifest {
  case_id: CaseId42;
  cleanup_items: CleanupItems1;
  exit_id: ExitId1;
  legacy_obligations_ref: LegacyObligationsRef2;
  merchant_assets_ref: MerchantAssetsRef1;
  outcome: Outcome10;
  persistent_runtime_evidence_refs: PersistentRuntimeEvidenceRefs1;
  post_denial_observation_refs: PostDenialObservationRefs1;
  run_id: RunId33;
  temporary_assets_ref: TemporaryAssetsRef1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ExitCheckPlan".
 */
export interface ExitCheckPlan {
  allowed_restart_count: AllowedRestartCount1;
  authority_refs: AuthorityRefs4;
  budget_ref: BudgetRef4;
  case_id: CaseId43;
  criteria_refs: CriteriaRefs1;
  deadline: Deadline4;
  evidence_read_authority_ref: EvidenceReadAuthorityRef2;
  executor_identity_ref: ExecutorIdentityRef2;
  exit_plan_id: ExitPlanId1;
  failure_route_ref: FailureRouteRef1;
  final_artifact_digest: FinalArtifactDigest3;
  final_config_digest: FinalConfigDigest3;
  generation: Generation29;
  plan_digest: PlanDigest11;
  private_evidence_destination_ref: PrivateEvidenceDestinationRef1;
  recovery_plan_ref: RecoveryPlanRef4;
  reservation_ref: ReservationRef3;
  run_id: RunId34;
  state_digest: StateDigest2;
  trusted_code_digest: TrustedCodeDigest2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "AssetManifest".
 */
export interface AssetManifest {
  assets: Assets1;
  case_id: CaseId44;
  final_artifact_digest: FinalArtifactDigest4;
  final_config_digest: FinalConfigDigest4;
  legacy_obligations_ref: LegacyObligationsRef3;
  manifest_digest: ManifestDigest1;
  manifest_id: ManifestId1;
  run_id: RunId35;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "PredicateResult".
 */
export interface PredicateResult {
  checked_at: CheckedAt20;
  evidence_refs: EvidenceRefs30;
  predicate: Predicate2;
  slot_id: SlotId5;
  status: Status15;
  subject_digest: SubjectDigest2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "TargetReservation".
 */
export interface TargetReservation {
  action_plan_ref: ActionPlanRef1;
  case_id: CaseId45;
  expected_version_refs: ExpectedVersionRefs;
  lease_until: LeaseUntil1;
  reservation_id: ReservationId;
  resource_epochs: ResourceEpochs7;
  run_id: RunId36;
  state: State15;
  target_keys: TargetKeys;
  unresolved_effect_refs: UnresolvedEffectRefs;
}
export interface ResourceEpochs7 {
  /**
   * This interface was referenced by `ResourceEpochs7`'s JSON-Schema definition
   * via the `patternProperty` "^\S+$".
   */
  [k: string]: number;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "DeliverySnapshot".
 */
export interface DeliverySnapshot {
  action_plan_ref: ActionPlanRef2;
  approval_set_ref: ApprovalSetRef1;
  cancellation_ref: CancellationRef1;
  case_id: CaseId46;
  checked_at: CheckedAt21;
  current_evidence_refs: CurrentEvidenceRefs1;
  deployment_ref: DeploymentRef1;
  exit_manifest_ref: ExitManifestRef2;
  exit_plan_ref: ExitPlanRef5;
  final_asset_manifest_ref: FinalAssetManifestRef1;
  generation: Generation30;
  graph_ref: GraphRef3;
  issue: Issue | null;
  lifecycle_ref: LifecycleRef1;
  pending_effect_refs: PendingEffectRefs1;
  reservation_ref: ReservationRef4;
  review_ref: ReviewRef1;
  run_id: RunId37;
  state_cutover_ref: StateCutoverRef1;
  state_version: StateVersion4;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "StateCutover".
 */
export interface StateCutover {
  admission_ref: AdmissionRef;
  case_id: CaseId47;
  cutover_id: CutoverId;
  drain_evidence_refs: DrainEvidenceRefs;
  evidence_refs: EvidenceRefs31;
  export_manifest_ref: ExportManifestRef;
  fence_epochs: FenceEpochs;
  generation: Generation31;
  handler_inventory_ref: HandlerInventoryRef;
  high_water_ref: HighWaterRef;
  ingress_ref: IngressRef;
  origin_route_ref: OriginRouteRef;
  outcome: Outcome11;
  pending_external_effect_refs: PendingExternalEffectRefs;
  replay_manifest_ref: ReplayManifestRef;
  restore_manifest_ref: RestoreManifestRef;
  run_id: RunId38;
  schema_digest: SchemaDigest;
  state_digest: StateDigest3;
  writer_inventory_ref: WriterInventoryRef;
}
export interface FenceEpochs {
  /**
   * This interface was referenced by `FenceEpochs`'s JSON-Schema definition
   * via the `patternProperty` "^\S+$".
   */
  [k: string]: number;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ResourceBindingV1".
 */
export interface ResourceBindingV1 {
  approved_at: ApprovedAt;
  authority_basis: AuthorityBasis;
  authority_evidence_refs: AuthorityEvidenceRefs;
  binding_id: BindingId;
  case_id: CaseId48;
  checked_at: CheckedAt22;
  controller_id: ControllerId2;
  epoch: Epoch;
  granted_actions: GrantedActions;
  node_id: NodeId4;
  recipients: Recipients2;
  relation_digest: RelationDigest;
  requester_id: RequesterId3;
  revoked_at: RevokedAt3;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ResourceRecipient".
 */
export interface ResourceRecipient {
  principal_id: PrincipalId;
  role: Role1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ResourceEdgeV1".
 */
export interface ResourceEdgeV1 {
  edge_id: EdgeId;
  evidence_refs: EvidenceRefs32;
  from_node: FromNode;
  relation: Relation;
  required_for_scope: RequiredForScope2;
  to_node: ToNode;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ResourceGraphV1".
 */
export interface ResourceGraphV1 {
  case_id: CaseId49;
  edges: Edges;
  graph_digest: GraphDigest3;
  graph_id: GraphId;
  nodes: Nodes;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ResourceEdge".
 */
export interface ResourceEdge {
  edge_id: EdgeId1;
  evidence_refs: EvidenceRefs33;
  from_node: FromNode1;
  relation: Relation1;
  required_for_scope: RequiredForScope3;
  to_node: ToNode1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ResourceNode".
 */
export interface ResourceNode {
  binding_refs: BindingRefs2;
  environment_id: EnvironmentId4;
  evidence_refs: EvidenceRefs34;
  kind: Kind16;
  node_id: NodeId5;
  provider: ProviderRef;
  provider_resource_id: ProviderResourceId;
  required_for_scope: RequiredForScope4;
  revision: SourceRevision | null;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "SourceRevision".
 */
export interface SourceRevision {
  kind: Kind17;
  value: Value3;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ResourceNodeV1".
 */
export interface ResourceNodeV1 {
  binding_refs: BindingRefs3;
  environment_id: EnvironmentId5;
  evidence_refs: EvidenceRefs35;
  kind: Kind18;
  node_id: NodeId6;
  provider: ProviderRef;
  provider_resource_id: ProviderResourceId1;
  required_for_scope: RequiredForScope5;
  revision: SourceRevision | null;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ResourceRecipientV1".
 */
export interface ResourceRecipientV1 {
  principal_id: PrincipalId1;
  role: Role2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ResourceSummaryV1".
 */
export interface ResourceSummaryV1 {
  check_refs: CheckRefs1;
  controller_state: ControllerState1;
  environment: Environment1;
  label: Label1;
  node_id: NodeId7;
  permitted_actions: PermittedActions1;
  provider: ProviderRef;
  read_scope_text: ReadScopeText1;
  source_snapshot_ref: SourceSnapshotRef3;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ResumeRunRequestV1".
 */
export interface ResumeRunRequestV1 {
  expected_state_version: ExpectedStateVersion1;
  scope_digest: ScopeDigest13;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ReviewBundleV1".
 */
export interface ReviewBundleV1 {
  artifact_digest: ArtifactDigest4;
  baseline_snapshot_refs: BaselineSnapshotRefs1;
  bundle_digest: BundleDigest1;
  bundle_id: BundleId1;
  candidate_snapshot_refs: CandidateSnapshotRefs1;
  case_id: CaseId50;
  created_at: CreatedAt19;
  domain_rule_result_refs: DomainRuleResultRefs1;
  effective_config_digest: EffectiveConfigDigest1;
  missing_evidence_refs: MissingEvidenceRefs1;
  patch_digest: PatchDigest3;
  proposed_apply_plan_ref: ProposedApplyPlanRef1;
  recovery_plan_ref: RecoveryPlanRef5;
  run_id: RunId39;
  scenario_result_refs: ScenarioResultRefs1;
  security_result_refs: SecurityResultRefs1;
  unsupported_paths: UnsupportedPaths1;
  work_package_digest: WorkPackageDigest11;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RootMapV1".
 */
export interface RootMapV1 {
  lenses_run: LensesRun;
  money_flow: MoneyFlow;
  recall_evidence: RecallEvidence;
  shop_id: ShopId4;
  stack: Stack;
  touchpoints: Touchpoints;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "MoneyFlow".
 */
export interface MoneyFlow {
  approve: Approve;
  capture: Capture;
  create: Create;
  mark_paid: MarkPaid;
  notify: Notify;
  recurring: Recurring;
  refund: Refund;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "SiteLocation".
 */
export interface SiteLocation {
  selector: Selector;
  url: Url1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "AccountLocation".
 */
export interface AccountLocation {
  tcode: Tcode;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RecallEvidence".
 */
export interface RecallEvidence {
  matched_by_static: MatchedByStatic;
  misses: Misses;
  runtime_calls_total: RuntimeCallsTotal;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Stack".
 */
export interface Stack {
  db: Db;
  framework: Framework1;
  lang: Lang1;
  versions: Versions;
}
export interface Versions {
  [k: string]: string;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Touchpoint".
 */
export interface Touchpoint {
  confidence: Confidence1;
  family: Family;
  id: Id16;
  lenses: Lenses;
  live: Live;
  location: Location;
  money_30d?: Money | null;
  operation: Operation6;
  paypal_only: PaypalOnly;
  target: TouchpointTarget;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "TouchpointTarget".
 */
export interface TouchpointTarget {
  paypal_mapping_id: PaypalMappingId;
  rest_op: RestOp;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RuleV1".
 */
export interface RuleV1 {
  agreement: Agreement;
  correct_flow: CorrectFlow1;
  counter_examples: CounterExamples1;
  id: Id17;
  predicate: Predicate3;
  severity: Severity;
  sources: RuleSources;
  title: Title3;
  triangle: Triangle;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RunTaskSnapshotV1".
 */
export interface RunTaskSnapshotV1 {
  cancellation_ref: CancellationRef2;
  case_id: CaseId51;
  generation: Generation32;
  last_event_seq: LastEventSeq2;
  run_id: RunId40;
  state_version: StateVersion5;
  tasks: Tasks1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "AgentTask".
 */
export interface AgentTask {
  attempt: Attempt4;
  case_id: CaseId52;
  checkpoint_ref: CheckpointRef1;
  created_at: CreatedAt20;
  deadline: Deadline5;
  generation: Generation33;
  input_digest: InputDigest4;
  issue: Issue | null;
  lease_epoch: LeaseEpoch3;
  lease_owner: LeaseOwner1;
  lease_until: LeaseUntil2;
  model_profile_ref: ModelProfileRef2;
  next_wake_at: NextWakeAt2;
  output_refs: OutputRefs3;
  policy_digest: PolicyDigest13;
  policy_ref: PolicyRef1;
  prompt_digest: PromptDigest1;
  prompt_ref: PromptRef1;
  request_id: RequestId8;
  run_id: RunId41;
  state: State16;
  state_version: StateVersion6;
  task: TaskSpec;
  wake_condition_ref: WakeConditionRef1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RunnableShopV1".
 */
export interface RunnableShopV1 {
  base_url: BaseUrl;
  compose: Compose1;
  health: Health;
  image_digests: ImageDigests;
  seed: Seed1;
}
export interface Health {
  [k: string]: boolean;
}
export interface ImageDigests {
  [k: string]: string;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "SafetyRequestHoldArgsV1".
 */
export interface SafetyRequestHoldArgsV1 {
  evidence_refs: EvidenceRefs36;
  reason_code: ReasonCode8;
  run_ref: RunRef2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ScenarioV1".
 */
export interface ScenarioV1 {
  assured: Assured;
  cart: Cart;
  expect: Expect;
  family: ScenarioFamily;
  id: Id18;
  rules: Rules1;
  steps: Steps1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Assured".
 */
export interface Assured {
  flake_free_runs: FlakeFreeRuns;
  passes_on_old: PassesOnOld;
}
export interface Cart {
  [k: string]: JsonValue;
}
export interface Expect {
  [k: string]: JsonValue;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ScenarioSetV1".
 */
export interface ScenarioSetV1 {
  created_at: CreatedAt21;
  graft_id: GraftId18;
  id: Id19;
  producer: Producer;
  scenarios: Scenarios3;
  unguarded_rule_ids: UnguardedRuleIds1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "Scenario".
 */
export interface Scenario1 {
  assured: Assured;
  cart: Cart1;
  expect: Expect1;
  family: ScenarioFamily;
  id: Id20;
  rules: Rules2;
  steps: Steps2;
}
export interface Cart1 {
  [k: string]: JsonValue;
}
export interface Expect1 {
  [k: string]: JsonValue;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ScenarioStageArgsV1".
 */
export interface ScenarioStageArgsV1 {
  mutant_set_ref: MutantSetRef;
  scenario_set_ref: ScenarioSetRef;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ShopPackV1".
 */
export interface ShopPackV1 {
  answer_key: AnswerKey;
  buyer_script: BuyerScript;
  env_needed: EnvNeeded;
  framework: Framework2;
  health_url: HealthUrl;
  language: Language1;
  licence: Licence;
  name: Name7;
  port: Port;
  scenarios_supported: ScenariosSupported;
  shop_id: ShopId5;
  source: ShopSource;
  start: Start;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "AnswerKey".
 */
export interface AnswerKey {
  money_flow: MoneyFlow;
  touchpoints: Touchpoints1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ShopSource".
 */
export interface ShopSource {
  commit: Commit2;
  repo: Repo2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ComposeStart".
 */
export interface ComposeStart {
  compose_file: ComposeFile;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "CommandStart".
 */
export interface CommandStart {
  command: Command;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "SourceReadArgsV1".
 */
export interface SourceReadArgsV1 {
  max_bytes: MaxBytes1;
  path: Path2;
  snapshot_ref: SnapshotRef1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "SourceRevisionV1".
 */
export interface SourceRevisionV1 {
  kind: Kind19;
  value: Value4;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "SourceSnapshotV1".
 */
export interface SourceSnapshotV1 {
  authority_binding_refs: AuthorityBindingRefs;
  captured_at: CapturedAt;
  case_id: CaseId53;
  completeness: Completeness;
  file_count: FileCount;
  manifest_digest: ManifestDigest2;
  omission_manifest_ref: OmissionManifestRef;
  provenance_class: ProvenanceClass;
  provider: ProviderRef;
  revision: SourceRevision;
  snapshot_id: SnapshotId;
  source_kind: SourceKind;
  source_resource_id: SourceResourceId;
  total_bytes: TotalBytes;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "StageChangeV1".
 */
export interface StageChangeV1 {
  actor: StageActor;
  attempt: Attempt5;
  evidence_refs: EvidenceRefs37;
  from_stage: StageName | null;
  graft_id: GraftId19;
  reason: Reason4;
  to_stage: StageName;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "StageActor".
 */
export interface StageActor {
  kind: ProducerKind;
  name: Name8;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "StartWorkRequestV1".
 */
export interface StartWorkRequestV1 {
  action_id: ActionId2;
  readiness_digest: ReadinessDigest4;
  readiness_id: ReadinessId4;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "StateCutoverV1".
 */
export interface StateCutoverV1 {
  admission_ref: AdmissionRef1;
  case_id: CaseId54;
  cutover_id: CutoverId1;
  drain_evidence_refs: DrainEvidenceRefs1;
  evidence_refs: EvidenceRefs38;
  export_manifest_ref: ExportManifestRef1;
  fence_epochs: FenceEpochs1;
  generation: Generation34;
  handler_inventory_ref: HandlerInventoryRef1;
  high_water_ref: HighWaterRef1;
  ingress_ref: IngressRef1;
  origin_route_ref: OriginRouteRef1;
  outcome: Outcome12;
  pending_external_effect_refs: PendingExternalEffectRefs1;
  replay_manifest_ref: ReplayManifestRef1;
  restore_manifest_ref: RestoreManifestRef1;
  run_id: RunId42;
  schema_digest: SchemaDigest1;
  state_digest: StateDigest4;
  writer_inventory_ref: WriterInventoryRef1;
}
export interface FenceEpochs1 {
  /**
   * This interface was referenced by `FenceEpochs1`'s JSON-Schema definition
   * via the `patternProperty` "^\S+$".
   */
  [k: string]: number;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "StatusReadArgsV1".
 */
export interface StatusReadArgsV1 {
  run_ref: RunRef3;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "SubjectDerivationV1".
 */
export interface SubjectDerivationV1 {
  authenticity_ref: AuthenticityRef5;
  case_id: CaseId55;
  collector_identity_ref: CollectorIdentityRef1;
  derivation_id: DerivationId;
  generation: Generation35;
  operation: Operation7;
  output_refs: OutputRefs4;
  output_subject: OutputSubject;
  parent_refs: ParentRefs;
  parent_subject: ParentSubject;
  recipe_or_patch_digest: RecipeOrPatchDigest;
  run_id: RunId43;
  task_id: TaskId6;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "SubjectManifestV1".
 */
export interface SubjectManifestV1 {
  config_digest: ConfigDigest3;
  oci_manifest_digest: OciManifestDigest1;
  runtime_profile_digest: RuntimeProfileDigest4;
  scope_digest: ScopeDigest14;
  source_snapshot_refs: SourceSnapshotRefs3;
  source_tree_digest: SourceTreeDigest1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "SwitchConfigV1".
 */
export interface SwitchConfigV1 {
  expires_at: ExpiresAt17;
  graft_id: GraftId20;
  origin_rules: OriginRules;
  signature: Signature4;
  stage_pct: StagePct1;
  version: Version3;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "TargetKeyV1".
 */
export interface TargetKeyV1 {
  account_id: AccountId3;
  environment_id: EnvironmentId6;
  provider_id: ProviderId5;
  resource_id: ResourceId6;
  resource_kind: ResourceKind1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "TargetPlanV1".
 */
export interface TargetPlanV1 {
  deltas?: Deltas;
  handoff: Handoff;
  items: Items2;
  order: Order;
  origin_rules: OriginRules1;
  path: PlanPath;
  target_experience: TargetExperience;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "IntentDelta".
 */
export interface IntentDelta {
  description: Description;
  id: Id21;
  mapping_id: MappingId;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "PlanItem".
 */
export interface PlanItem {
  delta_ids: DeltaIds;
  mapping_id: MappingId1;
  paypal_only: PaypalOnly1;
  target_op: TargetOp;
  touchpoint: Touchpoint1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "TargetReservationV1".
 */
export interface TargetReservationV1 {
  action_plan_ref: ActionPlanRef3;
  case_id: CaseId56;
  expected_version_refs: ExpectedVersionRefs1;
  lease_until: LeaseUntil3;
  reservation_id: ReservationId1;
  resource_epochs: ResourceEpochs8;
  run_id: RunId44;
  state: State17;
  target_keys: TargetKeys1;
  unresolved_effect_refs: UnresolvedEffectRefs1;
}
export interface ResourceEpochs8 {
  /**
   * This interface was referenced by `ResourceEpochs8`'s JSON-Schema definition
   * via the `patternProperty` "^\S+$".
   */
  [k: string]: number;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "TaskCheckpointV1".
 */
export interface TaskCheckpointV1 {
  budget_reservation_refs: BudgetReservationRefs;
  committed_message_refs: CommittedMessageRefs;
  context_digest: ContextDigest1;
  created_at: CreatedAt22;
  generation: Generation36;
  invocation_refs: InvocationRefs;
  lease_epoch: LeaseEpoch4;
  next_step: NextStep1;
  policy_digest: PolicyDigest14;
  staged_output_refs: StagedOutputRefs;
  task_id: TaskId7;
  turn: Turn;
  wake_condition_ref: WakeConditionRef2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "TaskContextV1".
 */
export interface TaskContextV1 {
  allowed_tool_ids: AllowedToolIds2;
  budget_ref: BudgetRef5;
  case_id: CaseId57;
  checkpoint_ref: CheckpointRef2;
  deadline: Deadline6;
  expected_schemas: ExpectedSchemas1;
  expected_subject: ExpectedSubject2;
  generation: Generation37;
  input_refs: InputRefs4;
  lease_epoch: LeaseEpoch5;
  operation: Operation8;
  policy_ref: PolicyRef2;
  prompt_ref: PromptRef2;
  role: Role3;
  run_id: RunId45;
  task_ref: TaskRef;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "TaskEventV1".
 */
export interface TaskEventV1 {
  case_id: CaseId58;
  causation_id: CausationId;
  correlation_id: CorrelationId;
  event_id: EventId1;
  generation: Generation38;
  kind: Kind20;
  occurred_at: OccurredAt1;
  payload_digest: PayloadDigest4;
  payload_ref: PayloadRef1;
  run_id: RunId46;
  sequence: Sequence1;
  task_id: TaskId8;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "TaskLeaseV1".
 */
export interface TaskLeaseV1 {
  context_ref: ContextRef1;
  generation: Generation39;
  lease_epoch: LeaseEpoch6;
  lease_until: LeaseUntil4;
  run_id: RunId47;
  task_id: TaskId9;
  task_version: TaskVersion;
  worker_id: WorkerId;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "TaskSpecV1".
 */
export interface TaskSpecV1 {
  allowed_tool_ids: AllowedToolIds3;
  dependencies: Dependencies2;
  expected_schemas: ExpectedSchemas2;
  expected_subject: ExpectedSubject3;
  input_refs: InputRefs5;
  operation: Operation9;
  output_slot: OutputSlot1;
  output_subject_policy: OutputSubjectPolicy1;
  required: Required5;
  role: Role4;
  task_id: TaskId10;
  workspace_ref: WorkspaceRef2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ToolCallV1".
 */
export interface ToolCallV1 {
  arguments_digest: ArgumentsDigest1;
  arguments_ref: ArgumentsRef1;
  call_id: CallId1;
  tool: Tool1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "ToolInvocationV1".
 */
export interface ToolInvocationV1 {
  arguments_digest: ArgumentsDigest2;
  arguments_ref: ArgumentsRef2;
  budget_reservation_ref: BudgetReservationRef1;
  capability_ref: CapabilityRef;
  case_id: CaseId59;
  deadline: Deadline7;
  effect_ref: EffectRef;
  generation: Generation40;
  input_digest: InputDigest5;
  invocation_id: InvocationId;
  issue: Issue | null;
  lease_epoch: LeaseEpoch7;
  result_refs: ResultRefs;
  run_id: RunId48;
  state: State18;
  task_id: TaskId11;
  tool_id: ToolId;
}
/**
 * minimal v1, owner Aditya may extend
 *
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "TriangleRequestV1".
 */
export interface TriangleRequestV1 {
  created_at: CreatedAt23;
  graft_id: GraftId21;
  id: Id22;
  mutant_ids: MutantIds1;
  producer: Producer;
  reason: Reason5;
  rule_id: RuleId;
  scenario_ids: ScenarioIds1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "UnresolvedInputsV1".
 */
export interface UnresolvedInputsV1 {
  items: Items3;
}
export interface BindingEpochs3 {
  /**
   * This interface was referenced by `BindingEpochs3`'s JSON-Schema definition
   * via the `patternProperty` "^\S+$".
   */
  [k: string]: number;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "VerdictV1".
 */
export interface VerdictV1 {
  deltas_applied: DeltasApplied;
  grade: Grade;
  noise_masked: NoiseMasked;
  parity_diff: ParityDiff;
  rule_hits: RuleHits;
  scenario_id: ScenarioId2;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "RuleHit".
 */
export interface RuleHit {
  evidence: Evidence;
  rule: Rule3;
  side: Side;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "WakeConditionV1".
 */
export interface WakeConditionV1 {
  case_id: CaseId61;
  condition_id: ConditionId;
  due_at: DueAt;
  expected_digest: ExpectedDigest;
  expires_at: ExpiresAt19;
  generation: Generation41;
  kind: Kind21;
  minimum_version: MinimumVersion;
  owner: Owner2;
  run_id: RunId49;
  subject_ref: SubjectRef1;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "WorkAcceptanceV1".
 */
export interface WorkAcceptanceV1 {
  accepted_at: AcceptedAt2;
  action_id: ActionId3;
  case_id: CaseId62;
  readiness_digest: ReadinessDigest5;
  receipt_ref: ReceiptRef1;
  resource_graph_digest: ResourceGraphDigest4;
  scope_digest: ScopeDigest15;
  source_manifest_digest: SourceManifestDigest2;
  work_id: WorkId4;
  work_package_digest: WorkPackageDigest12;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "WorkCancellationV1".
 */
export interface WorkCancellationV1 {
  action_id: ActionId4;
  cancel_id: CancelId1;
  case_id: CaseId63;
  generation: Generation42;
  requested_at: RequestedAt;
  requested_by: RequestedBy;
  state: State21;
  termination_evidence_refs: TerminationEvidenceRefs;
  work_id: WorkId5;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "WorkPackageV1".
 */
export interface WorkPackageV1 {
  acquisition_expires_at: AcquisitionExpiresAt;
  baseline_manifest_digest: BaselineManifestDigest;
  case_id: CaseId64;
  completeness: Completeness1;
  components_ref: ComponentsRef;
  custody_policy_digest: CustodyPolicyDigest;
  delivery_feasibility_ref: DeliveryFeasibilityRef;
  external_dependencies_ref: ExternalDependenciesRef;
  fixture_profile_digest: FixtureProfileDigest2;
  omission_manifest_ref: OmissionManifestRef1;
  processing_policy_digest: ProcessingPolicyDigest2;
  required_flow_refs: RequiredFlowRefs;
  resource_graph_digest: ResourceGraphDigest5;
  resource_graph_ref: ResourceGraphRef;
  runtime_profile_digest: RuntimeProfileDigest5;
  scope_digest: ScopeDigest16;
  source_snapshot_refs: SourceSnapshotRefs4;
  state_recipe_refs: StateRecipeRefs;
  synthetic_seed_refs: SyntheticSeedRefs;
  unresolved_requirements_ref: UnresolvedRequirementsRef;
  work_package_id: WorkPackageId;
}
/**
 * This interface was referenced by `GoldGraftContracts`'s JSON-Schema
 * via the `definition` "WorkerOperationV1".
 */
export interface WorkerOperationV1 {
  assignment_digest: AssignmentDigest;
  authenticity_ref: AuthenticityRef6;
  evidence_refs: EvidenceRefs42;
  finished_at: FinishedAt1;
  generation: Generation44;
  kind: Kind22;
  observed_digest: ObservedDigest;
  operation_id: OperationId1;
  resource_graph_digest: ResourceGraphDigest6;
  result: Result;
  runtime_profile_digest: RuntimeProfileDigest6;
  scope_digest: ScopeDigest17;
  source_manifest_digest: SourceManifestDigest3;
  started_at: StartedAt1;
  work_id: WorkId7;
  work_package_digest: WorkPackageDigest13;
  worker_id: WorkerId1;
}
