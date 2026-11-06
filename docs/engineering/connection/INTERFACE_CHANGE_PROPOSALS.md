> Reviewed team baseline, 6 November 2026: this connection proposal is subject to the review addendum, implementation bridge and lifecycle atomic protocols linked from [engineering START](../START_HERE.md). Earlier programme status/owner restrictions in this frozen source are historical. No current API/implemented capability is created by this text.

# Versioned contract proposals — NOT CURRENT

Status: paper engineering specification, 6 November 2026. Nothing here is a deployed feature or current API unless explicitly labelled CURRENT. Proposed components/interfaces require later implementation and contract approval. Plan 1 ends at verified first sandbox operation; agent internals and Plans 2–6 remain outside scope.

## Current exact anchors
CURRENT `ShopCreate` has optional name/repo/site; `ConnectRequest` requires paypal_client_id/paypal_client_secret and optional webhook_id/nvp_user/nvp_password/nvp_signature. CURRENT Connection has shop_id, repo/site nullable, secrets_ref and rest_ok/nvp_ok/webhook_ok/version_match. CURRENT StartGraftRequest has optional note only. Existing POST /shops/{shop_id}/graft requires Idempotency-Key and returns Graft. Existing GET /grafts/{graft_id}/events has Last-Event-ID ledger replay. None provides case sessions/controller invitations/readiness receipt/cancellation/actual operation evidence. CURRENT Runner.run_job(JobSpec)->JobResult and JobResult.started/finished are not the receipt protocol below.

## Versioning and deployment
Proposal C-P1: additive connection-control API namespace `/v2/connection-cases` plus independent new registry formats `ConnectionCase/1`, `ControllerBinding/1`, `ConnectionReadiness/1`, `WorkAcceptance/1`, `WorkerOperation/1`, `WorkCancellation/1`; modify existing formats only with explicit next versions if needed. These names, fields and routes are design proposals ONLY. Old /shops/... routes remain compatibility-only; no live caller can bypass new security by calling v1. Deployment must put both behind the same current case/action authority or disable v1 external Start. Old fake connect booleans cannot be mapped to new readiness pass.

All objects forbid extra fields. IDs opaque nonempty strings, digest lowercase SHA-256 except explicitly named provider OCI/source IDs. Timestamps UTC with timezone; enums closed. Secret values never present in persisted/response formats. Versioning follows registry keys and exports, not an invented schema_version field in current payloads. Sensitive runtime/config fingerprints use keyed digest where low-entropy guessing is a risk.

## Earlier draft shapes — historical, superseded

The block below records the earlier draft only. **Use [CONNECTION_CONTROL_PROPOSAL.md](CONNECTION_CONTROL_PROPOSAL.md) for final proposed shapes.** That consolidation removes single-host assumptions, mandatory Git commits and premature worker generations, and separates immutable acceptance from current status. Do not implement the historical block.

### Historical block
```text
ResourceRef = {provider: registered_provider_id, account_id: str, resource_id: str,
               environment_id: str|null, revision: str|null}
Recipient = {principal_id: str, role: requester|controller|reviewer}
ControllerBinding/1 = {binding_id, case_id, controller_id, resource: ResourceRef,
 requester_id, recipients: Recipient[], granted_actions: [view|connect|start|review],
 relation_digest, provider_actor_id, provider_role, authority_evidence_refs: str[],
 authority_checked_at, epoch: positive_int, approved_at, revoked_at: timestamp|null}
ConnectionCase/1 = {case_id, tenant_id, requester_id, shop_url, created_at,
 status: draft|waiting_controller|checking|setup_needed|ready|accepted|closed,
 binding_ids: str[], source_ref: ResourceRef|null, host_ref: ResourceRef|null}
CheckResult = {check_id, status: pass|missing|unsupported|failed|stale|unknown,
 evidence_refs: str[], checked_at, expires_at, recovery_code: str|null}
ConnectionReadiness/1 = {readiness_id, case_id, actor_id, source_manifest_digest,
 source_commit, host_resource_id, environment_id, correspondence_digest,
 binding_epochs: map[str,int], scope_digest, processing_policy_digest,
 runtime_profile_digest, fixture_profile_digest, checks: CheckResult[],
 issued_at, expires_at, readiness_digest}
StartWorkRequest = {readiness_id, readiness_digest, action_id}
WorkAcceptance/1 = {action_id, case_id, work_id, accepted_at,
 readiness_digest, scope_digest, source_commit, generation: positive_int,
 receipt_ref, state: accepted|queued|provisioning|operation_started|held|unknown|
 cancellation_pending|cancelled|stopped|failed}
WorkerOperation/1 = {operation_id, work_id, generation, worker_id,
 kind: BASELINE_READ, assignment_digest, source_manifest_digest, scope_digest,
 observed_digest, runtime_profile_digest, started_at, finished_at,
 result: verified|failed, evidence_refs: str[], authenticity_ref}
WorkCancellation/1 = {cancel_id, case_id, action_id, requested_by, requested_at,
 state: intent_recorded|fenced|termination_pending|confirmed|unknown,
 generation: positive_int, termination_evidence_refs: str[]}
```
Types omitted on simple IDs/digests above mean nonempty strings under named validation rules; implementers must encode exact Python types in proposed model modules. `authenticity_ref` is a verified trusted receipt reference, not a self-supplied signature string accepted without checking. No source/credential blob fields.

## Proposed routes and responses
| Route | Producer/consumer, authority and result |
|---|---|
| POST /v2/connection-cases | BFF → case service; browser draft secret, CSRF, bounded shop_url; returns private draft; no ownership inference. |
| GET /v2/connection-cases/{case_id} | Case member only; role-filtered snapshot, checks and receipt; generic 404 for unauthorised enumeration. |
| POST .../{case_id}/invitations | Requester; contribution/expiry; returns once-only invite URL; no message sent by service in first scope. |
| POST .../{case_id}/bindings | Controller; validated provider authority evidence + displayed relation digest; atomic binding, no attachment on rejection. |
| POST .../{case_id}/source-intents and /host-intents | Authenticated controller; server creates one-use provider-specific return state. Host Render path produces setup guidance, not fictional OAuth. |
| POST .../{case_id}/host-credential | Controller + bound intent; once-only Render scoped key transported straight to vault, returns opaque handle; never echoes key. Scope qualification and role binding required before private evidence attaches. |
| GET .../{case_id}/readiness | Authorised actor; current proposed ConnectionReadiness or explicit missing/stale checks; no green synthesis from booleans. |
| POST .../{case_id}/actions | Current start delegate; Idempotency-Key + StartWorkRequest; returns 202 WorkAcceptance ONLY after durable acceptance. Stable retry same receipt; conflict 409, stale scope 412, prerequisite 422, provider unavailable 503, unauthorised generic 404/403 policy. |
| GET .../{case_id}/actions/{action_id} | Authorised member; original durable receipt/status including cancellation, never creates work. |
| POST .../{case_id}/actions/{action_id}/cancellation | Start delegate/controller; idempotent cancellation intent even before acceptance; returns pending/confirmed state accurately. |
| GET .../{case_id}/events | Authorised role projection, monotonic committed cursor, replay; stale cursor returns explicit resync requirement. |
| POST /v2/worker-operations | Service-only authenticated supervisor; verifies assignment/current fence/evidence digest; never browser writable. |

Identity callback endpoints are separate allowlisted BFF/provider handlers, bound to one-use state and internal destinations; no proposed path pretends to be a current route. Errors preserve existing RFC7807 problem+json convention with proposed extension `recovery_code` and safe correlation_id only, never raw provider secrets.

## Service interfaces / data boundary

The acquisition signature below is the historical Git-first example. Final generic source input is authorised ResourceBinding + SourceRevision + custody policy, producing SourceSnapshot/1; Host.inspect returns per-node AdapterObservations, not a single-host universal result. Readiness and worker boundaries bind WorkPackage and full resource-graph digests from the canonical proposal.

Acquisition.acquire(case_id,binding_epoch,repo_id,commit,policy_digest)->manifest_ref; Host.inspect(case_id,host_binding_epoch,service_id)->correspondence_inputs; Readiness.evaluate(case_id,actor_id)->ConnectionReadiness; Acceptance.accept(case_id,actor_id,key,StartWorkRequest)->WorkAcceptance; Cancellation.request(case_id,actor_id,action_id,key)->WorkCancellation; Supervisor.record(WorkerOperation)->verified status. All require authenticated service context; signatures above omit transport credentials deliberately, never authority.

Persistent tables: cases, memberships, controller_bindings, provider_handles, callback_nonces, manifests, correspondence, policies, readiness, action_identities, work_acceptances, cancel_intents, outbox, worker_assignments, operations, case_events. Foreign keys include tenant/case; unique `(tenant_id,case_id,actor_id,operation,idempotency_key)`, `(case_id,action_id)`, `(work_id,generation,operation_id)`. Serializable or explicit row locks enforce transaction invariants; retry serialization failure safely. Durable metadata encrypted/backed up separately from deletable raw code.

## Compatibility/migration acceptance
Future change entry in docs/FORMAT_CHANGES.md owned by Singh; new Python models in contracts, registry additions, schema/OpenAPI/TS generation, examples, new fixtures/fakes and plugtests updated in the same authorised implementation change. Preserve money integer-minor-unit rules. No field added here exists until that change lands. Test older clients against explicit compatibility policy and deny security bypass on legacy routes. No piece imports another piece; connector composes backend through a proposed authenticated HTTP adapter, never imports backend/runner code. Acceptance records may exist before a legacy graft_id is allocated; link later via idempotent dispatch. Existing Graft API becomes downstream execution projection, not acceptance authority.

## Extensibility amendment — proposed, not current
`registered_provider_id` is a nonempty identifier accepted only when present in the server-owned, versioned adapter registry; it is not an arbitrary URL or self-registered client plugin. Initial registry entries remain github/render. `ConnectionCase/1` must use `resource_nodes: ResourceNode[]`, `resource_edges: ResourceEdge[]` and `resource_bindings: ResourceBinding[]` for multiple providers/components rather than relying on singular source_ref/host_ref. Any retained singular fields are display projections only and cannot drive readiness. Readiness binds `resource_evidence_digests: map[node_id,digest]` plus a full `resource_graph_digest`; singular host_resource_id/environment_id represent the first reference only. Start binds the entire graph digest. AdapterCapabilities/ResourceNode/ResourceEdge/ResourceBinding/AdapterObservation shapes and method responsibilities are specified in CONNECTOR_EXTENSIBILITY_SPEC.md; qualification and schema generation remain future work. Never present this amendment as current wire support.

## Non-Git source proposal — supersedes mandatory source_commit
Add proposed SourceSnapshot/1 in FIXED_JOURNEY_AND_SOURCE_ROUTES.md. Resource revision is typed Git commit/provider revision set/capture, never a fabricated commit. ConnectionReadiness, WorkAcceptance and WorkerOperation bind source_snapshot_ref, source_manifest_digest and resource_graph_digest. Retain source_commit only as nullable Git-specific projection; no common code assumes it exists. Proposed UploadSession/1 binds case/contributor/binding epochs, expected relative-path/hash/byte manifest, permitted chunk IDs, received set, TTL and finalised snapshot ref, never browser filesystem credentials. Draft route POST .../{case_id}/source-uploads creates that scope; authenticated chunk/finalise/status/cancel operations are idempotent and refuse disclosure/finalisation without current authority. No current API/generated format changes occur here.

## Complete-work-package proposal
Add proposed WorkPackage/1, component inventory/completeness and DeliveryFeasibility references defined in CODE_AND_ENVIRONMENT_HANDOFF.md. SourceSnapshot and ResourceGraph compose multiple required source/service/data/callback nodes, without secrets or production customer data in model inputs. Readiness binds package/graph/scope/policy digests; post-Start external results distinguish BASELINE_READ, BASELINE_REPRODUCED, UPGRADE_VALIDATED and LIVE_VERIFIED (new proposal, never reinterpret current enums). Plan3 must define later result/delivery evidence; this change does not implement them or grant publication/deploy rights.
