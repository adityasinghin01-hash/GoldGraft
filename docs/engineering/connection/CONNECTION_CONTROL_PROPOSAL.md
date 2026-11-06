> Reviewed team baseline, 6 November 2026: this connection proposal is subject to the review addendum, implementation bridge and lifecycle atomic protocols linked from [engineering START](../START_HERE.md). Earlier programme status/owner restrictions in this frozen source are historical. No current API/implemented capability is created by this text.

# Canonical connection-control proposal — paper only

This is the consolidated Plan1 proposal, not current API/models/generated types. It supersedes conflicting early single-host, mandatory-Git-commit and mandatory-worker-generation draft fields in INTERFACE_CHANGE_PROPOSALS.md. Current contracts remain unchanged. New registry formats and v2 routes still require approved versioning, fixtures/fakes, generation and implementation acceptance.

## Common types and validation
Id and Ref are opaque nonempty strings. Ref resolves through authenticated tenant/case-scoped service lookup, not an arbitrary supplied URL. Digest is lowercase 64-hex SHA-256; use keyed digest for sensitive low-entropy configuration. Utc is a timezone-aware UTC timestamp. Count is a strict nonnegative integer, Positive is strict positive integer. No booleans/floats accepted as integers; monetary values retain current integer minor-unit contracts. Lists/maps have documented caps at intake; unknown fields and enum values rejected. Provider commit/OCI identifiers use their named provider validators, not fictitious SHA-256 coercion. Each artifact belongs to one case; embedded references must resolve to that case/tenant. Secret values never enter persisted responses, work packages or evidence.

## Adapter/resource graph types (all proposed)
```text
ProviderRef = {provider_id: Id, adapter_version: Id, account_id: Id|null}
SourceRevision = {kind: git_commit|provider_revision_set|capture, value: Id}
ResourceNode = {node_id: Id, provider: ProviderRef,
 kind: source|frontend|backend|datastore|callback|scheduled_job|external_service|artifact,
 provider_resource_id: Id|null, environment_id: Id|null,
 revision: SourceRevision|null, required_for_scope: bool,
 binding_refs: Ref[], evidence_refs: Ref[]}
ResourceEdge = {edge_id: Id, from_node: Id, to_node: Id,
 relation: builds_from|routes_to|stores_state_in|receives_callback_from|depends_on,
 required_for_scope: bool, evidence_refs: Ref[]}
ResourceGraph = {graph_id: Id, case_id: Id, nodes: ResourceNode[],
 edges: ResourceEdge[], graph_digest: Digest}
ResourceBinding = {binding_id: Id, case_id: Id, node_id: Id,
 controller_id: Id, requester_id: Id,
 recipients: [{principal_id: Id, role: requester|controller|reviewer}],
 granted_actions: [view|connect|start|review], relation_digest: Digest,
 authority_basis: provider_verified|controller_attested,
 authority_evidence_refs: Ref[], checked_at: Utc, epoch: Positive,
 approved_at: Utc, revoked_at: Utc|null}
AdapterCapabilities = {provider: ProviderRef,
 operations: [source_read|deployment_read|artifact_identity|route_read|
 config_evidence|controller_role|revocation_observation],
 qualification: proposed|implemented|account_tested|correspondence_qualified|e2e_tested,
 limitations: str[], qualification_refs: Ref[]}
AdapterObservation = {observation_id: Id, case_id: Id, node_id: Id,
 capability: Id, status: available|changed|revoked|unsupported|unknown,
 basis: observed|provider_reported|controller_attested,
 evidence_refs: Ref[], checked_at: Utc, expires_at: Utc|null}
```
Validate unique node/edge/binding IDs, edge endpoints exist, required dependencies represented, requester/recipients approved per resource, and graph digest computed from canonical stable contents. Do not reject all graph cycles: real callback relationships can cycle; dependency resolution must terminate with bounded visited-node traversal and report missing edges. Client cannot mark a required node optional to bypass agreed scope. Provider registry is server-owned: github/render first-reference descriptors; local_folder capture descriptor added only with its qualified uploader. Additional adapters remain unavailable until registered/qualified. Source-data access and rights assertions retain their evidence class: local possession/attestation is not provider-verified ownership.

## Source and complete context
```text
SourceSnapshot/1 = {snapshot_id: Id, case_id: Id,
 source_kind: git|local_folder|cloud_files|host_export, provider: ProviderRef,
 source_resource_id: Id|null, revision: SourceRevision,
 manifest_digest: Digest, file_count: Count, total_bytes: Count,
 captured_at: Utc, omission_manifest_ref: Ref,
 authority_binding_refs: Ref[],
 provenance_class: provider_reported|controller_attested|verified_build_link,
 completeness: complete_for_declared_scope|incomplete|unknown}
ManifestEntry = {relative_path: str, file_type: file|directory,
 bytes: Count, sha256: Digest|null}
UploadSession/1 = {upload_id: Id, case_id: Id, contributor_id: Id,
 binding_epochs: map[Id,Positive], expected_manifest_ref: Ref,
 expected_manifest_digest: Digest, expected_total_bytes: Count,
 received_chunk_refs: Ref[], state: pending|receiving|finalised|cancelled|expired,
 created_at: Utc, expires_at: Utc, finalised_snapshot_ref: Ref|null}
WorkPackage/1 = {work_package_id: Id, case_id: Id,
 resource_graph_ref: Ref, resource_graph_digest: Digest, scope_digest: Digest,
 source_snapshot_refs: Ref[], components_ref: Ref, external_dependencies_ref: Ref,
 state_recipe_refs: Ref[], synthetic_seed_refs: Ref[], required_flow_refs: Ref[],
 processing_policy_digest: Digest, custody_policy_digest: Digest,
 runtime_profile_digest: Digest, fixture_profile_digest: Digest,
 baseline_manifest_digest: Digest, omission_manifest_ref: Ref,
 acquisition_expires_at: Utc,
 completeness: sufficient_for_declared_static_scope|incomplete|unknown,
 unresolved_requirements_ref: Ref, delivery_feasibility_ref: Ref}
```
The typed referenced component/dependency/required-input records are specified in CODE_AND_ENVIRONMENT_HANDOFF.md and must be validated at resolution, not treated as an opaque unvalidated blob. Reject absolute/parent/link/path-collision entries and apply limits streaming. Chunk records bind upload/file-relative-path/offset/length/digest; ranges must cover each file once without gaps/conflicting overlaps at finalisation. Duplicate identical chunk is idempotent; changed digest/expired grant requires new validation. Server, not client, computes/validates final snapshot and graph digests. No raw credential or production dataset in these objects. Git commit is a route-specific revision value; local source has capture identity instead.

## Case/readiness/action evidence
```text
ConnectionCase/1 = {case_id: Id, tenant_id: Id, requester_id: Id,
 shop_url: str, created_at: Utc, graph_ref: Ref|null, binding_refs: Ref[],
 status: draft|waiting_controller|checking|setup_needed|ready|accepted|closed}
CheckResult = {check_id: Id, status: pass|missing|unsupported|failed|stale|unknown,
 evidence_refs: Ref[], checked_at: Utc, expires_at: Utc|null,
 recovery_code: Id|null}
ConnectionReadiness/1 = {readiness_id: Id, case_id: Id, actor_id: Id,
 work_package_ref: Ref, work_package_digest: Digest,
 resource_graph_digest: Digest, source_snapshot_refs: Ref[],
 source_manifest_digest: Digest, resource_evidence_digests: map[Id,Digest],
 binding_epochs: map[Id,Positive], scope_digest: Digest,
 processing_policy_digest: Digest, runtime_profile_digest: Digest,
 fixture_profile_digest: Digest, checks: CheckResult[],
 issued_at: Utc, expires_at: Utc, readiness_digest: Digest}
ActionIntent/1 = {action_id: Id, case_id: Id, actor_id: Id,
 readiness_id: Id, readiness_digest: Digest, created_at: Utc, expires_at: Utc}
StartWorkRequest = {action_id: Id, readiness_id: Id, readiness_digest: Digest}
WorkAcceptance/1 = {action_id: Id, case_id: Id, work_id: Id,
 accepted_at: Utc, readiness_digest: Digest, work_package_digest: Digest,
 resource_graph_digest: Digest, scope_digest: Digest,
 source_manifest_digest: Digest, receipt_ref: Ref}
WorkStatus/1 = {action_id: Id, case_id: Id, work_id: Id|null,
 state: submitting|accepted|queued|provisioning|operation_started|held|unknown|
 cancellation_pending|cancelled|stopped|failed,
 generation: Positive|null, last_event_seq: Count, checked_at: Utc,
 evidence_refs: Ref[]}
WorkerOperation/1 = {operation_id: Id, work_id: Id, generation: Positive,
 worker_id: Id, kind: BASELINE_READ, assignment_digest: Digest,
 work_package_digest: Digest, resource_graph_digest: Digest,
 source_manifest_digest: Digest, scope_digest: Digest,
 observed_digest: Digest, runtime_profile_digest: Digest,
 started_at: Utc, finished_at: Utc, result: verified|failed,
 evidence_refs: Ref[], authenticity_ref: Ref}
WorkCancellation/1 = {cancel_id: Id, case_id: Id, action_id: Id,
 requested_by: Id, requested_at: Utc,
 state: intent_recorded|fenced|termination_pending|confirmed|unknown,
 work_id: Id|null, generation: Positive|null,
 termination_evidence_refs: Ref[]}
```
ActionIntent is persisted before Start/cancel and scoped to authenticated actor/case/reviewed readiness. Cancellation before accepted work legitimately has null work_id/generation. Atomic ordering on the action identity decides whether Start is rejected cancelled or accepted then fenced. No invented worker generation before assignment. Cancellation response is not false proof process terminated.

WorkAcceptance is immutable historical acceptance; current WorkStatus is separate. Idempotent Start retry yields the same acceptance identity/payload, current state is read through status. Acceptance replay cannot relaunch a stopped/revoked job. If cancellation wins before acceptance, return current cancelled action outcome, not an acceptance record for non-existent work. Status derives from committed facts; browser action pending is not service acceptance. Only valid current BASELINE_READ may produce operation_started; claimed/provisioned and unverified stdout cannot. This type proves neither model inference nor successful site reproduction. Future Plan3 baseline/upgrade/live outcome formats are reserved work, not added current events or part of this first-operation enum.

## Route consolidation and compatibility
New proposed namespace remains /v2/connection-cases. Existing proposal routes for case, invitations, bindings, provider intents/credential, readiness, actions, cancellation and events remain; add POST .../{case_id}/action-intents (review-authorised actor, persistent intent) and proposed source-upload create/chunk/finalise/status/cancel routes. Status route GET .../{case_id}/actions/{action_id} returns WorkStatus plus immutable receipt ref when accepted. POST actions returns 202 immutable WorkAcceptance only after accepted transaction; precise rejection/unknown/cancelled semantics follow START_AND_OPERATION_EVIDENCE.md. No route provides private state solely from action/case ID. Upload bearer capabilities permit only bounded chunks, never case membership or reads. POST /v2/worker-operations is service-only through trusted collector, not browser/guest ambient signing rights.

All existing route methods/fields/idempotency/SSE semantics remain CURRENT as described in INTERFACE_CHANGE_PROPOSALS.md. Proposed exports cannot be imported as though implemented. New formats, typed referenced records, generated schemas/OpenAPI/TS/examples, fixture indexes/fakes and compatibility/legacy-Start denial tests must land together in a later authorised change. No generated/reference files were edited to close this paper plan.
