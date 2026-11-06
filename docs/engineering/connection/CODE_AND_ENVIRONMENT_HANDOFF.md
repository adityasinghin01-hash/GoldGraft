> Reviewed team baseline, 6 November 2026: this connection proposal is subject to the review addendum, implementation bridge and lifecycle atomic protocols linked from [engineering START](../START_HERE.md). Earlier programme status/owner restrictions in this frozen source are historical. No current API/implemented capability is created by this text.

# Code and environment package — concrete Plan1 handoff

Status: proposed engineering interface, no code acquired/built/executed. Defines external inputs/outputs and lifecycle gates, not internal agent planning/tools/prompts.

## What “get the code” actually produces
After identity, permission and custody disclosure, acquire enough authorised material to reproduce the supported shop scope, not just whichever folder was easiest to upload. Build a RequiredComponentGraph with:
- Frontend source/served assets, backend API/payment/order/notification handlers and scheduled jobs involved in the requested flows.
- Their repository/folder roots and immutable source snapshot IDs; multiple repos and providers permitted with separate grants/recipient approvals.
- Build recipes and pinned runtime/dependency/lockfile versions; private packages and generated assets accounted for without ungranted recursive fetch.
- Runtime configuration names/types and nonsecret values; secret references resolved only by qualified brokers, never pasted into source/model context.
- Database/storage schema and migration versions, API contracts, queues and state dependencies; synthetic seed/test identities rather than production customer/payment data copied blindly.
- Domain/routing, backend endpoints, callbacks/IPN/webhooks, external services and account/environment dependencies; each classified as reproducible fixture, authorised sandbox service, qualified broker or unavailable.
- Required supported user/payment flows, declared exclusions and completeness evidence. “Whole” means all dependencies needed for the agreed outcome, not every unrelated file or third party's proprietary source.

Discovery method: parse imports/manifests/build configs/routes/SDK usage statically, combine host read deployment/routing inventory and controller declarations, compare expected versus acquired dependency graph, then flag unresolved source/config/private dependency/generated content. Static discovery is bounded/incomplete by nature; post-Start execution can find further requirements and must hold before changes if essential context is missing. Never advertise mathematically certain complete source from a successful directory listing.

## Acquisition by location
Git adapter pins each repository revision and trusted archive manifest. Local-folder adapter produces stable capture manifest via authorised browser read/chunk upload, double validation and interruption recovery. Cloud files require actual narrow read grants, complete revision-set acquisition and download rights; otherwise use controller-selected local copies. Host export requires a qualified nonmutating exporter with bounded custody. No original remote source is modified; no service deployment/environment changes during acquisition. Public website crawling cannot recover private backend/source/secrets. Unknown controller remains an honest dependency in the same case.

## Match source to website before attributing results
For each required component establish source snapshot → approved build inputs/provenance → actual artifact → current host deployment → domain/backend/callback/environment relation. Non-Git capture digest replaces commit, not this evidence chain. On Render use the actual live deployment, not latest attempted build or service settings alone. Record provider-reported, observed and controller-attested evidence separately. Missing image/build/source/config linkage, stale upload or unrelated backend means Match not verified; do not run changes as though this were the user's deployed system.

## Proposed WorkPackage/1 — NOT CURRENT
```text
work_package_id: opaque ID
case_id / resource_graph_digest / scope_digest: bound identities
source_snapshots: SourceSnapshot/1 references, one per required source
components: [{node_id, purpose, source_snapshot_ref|null, build_context_ref|null,
 runtime_profile_ref, dependency_manifest_ref, configuration_manifest_ref,
 correspondence_evidence_refs, controller_binding_refs}]
external_dependencies: [{dependency_id, component_ids, purpose,
 access_mode: fixture|sandbox_broker|read_evidence|unavailable,
 authority_ref|null, test_identity_ref|null, limitation}]
state_recipe_refs / synthetic_seed_refs / required_flow_refs: typed references
processing_policy_digest / custody_policy_digest / runtime_profile_digest
baseline_manifest_digest / omission_manifest_ref / acquisition_expiry
completeness: sufficient_for_declared_static_scope|incomplete|unknown
unresolved_requirements: [{requirement_id, component_id, reason,
 responsible_controller_id|null, safe_next_action}]
delivery_feasibility_ref: pre-Start constraints, NOT publication authority
```
No raw credentials/customer data or executable model-invented scripts are smuggled through JSON bags. Validate exact proposed formats/versioning through shared Python contracts during later implementation. Each broker still rechecks current authority at actual use.

## Two isolated copies; explicit timing
Pre-Start: acquire/disclose/quarantine/static-check; compute immutable source/baseline manifest and readiness/constraints. No repository execution/model calls/payment tests.

After durable Start: worker verifies the pinned package (Plan1 actual first-operation evidence), then Plan3 materialises a read-only BASELINE copy and separately writable WORKING copy in qualified isolated execution, with per-run data/credentials separated. Baseline source hashes cannot change. Agent's “local environment” means isolated service worker storage, not merchant laptop or live hosting filesystem. Neither copy gets live mutation credentials. Writing WORKING cannot push a source branch or auto-deploy remotely. Later publication is separately authorised and checked for triggers.

Then Plan3 runs unchanged baseline first using a controlled disposable runtime/synthetic state and genuine required sandbox authentication. Evidence: build/dependency result, page/backend health, complete required flow coverage, persisted outcomes and notification verification, existing bugs and unsupported/unknown paths. If baseline fails, service investigates within scope, obtains missing authorised inputs or holds; it does not start rewriting and claim all differences are upgrade improvements. These are external lifecycle requirements only, not agent algorithm design.

After baseline qualification, apply proposed upgrade to WORKING and run controlled before/after/regression/security checks. Passing these demonstrates the tested copy under named conditions; it still does not independently prove source-to-production correspondence or live deployment success. Those require their own evidence.

## Readiness/operation labels
“Code received” != “Required components available” != “Matched to running website” != “Ready for sandbox work” != “Baseline read completed” != “Unchanged site reproduced” != “Upgrade validated” != “Live upgrade verified”. UI and event contracts must preserve these distinctions. First operation in Plan1 is not a successful build or working website. Every required missing component is attached to existing case with next action/owner, no dead-end generic error.

## Delivery admission before promising the house keys
Pre-Start service inspects, read-only, whether a supported publication/deploy/continuity route exists and who must later approve it. Require declared persistent-state handling and merchant ownership. Do not collect write authority early; record dependencies and get exact revision-bound authorisation later. If required pipeline/permission/state-safe cutover is unavailable, full end-to-end promise remains unverified/blocked or a different clearly named scope must be chosen. Plan3 must complete this gate with fresh actual evidence before apply.

## Proposed code/test targets and responsibility
contracts/src/goldgraft_contracts/work_package.py (versioned proposed package); pieces/connector/component_inventory.py (static dependency closure); work_package.py (assembly/validation); existing acquisition/correspondence/readiness modules consume package digests. fixtures/connection_control/work_packages/ defines multi-repo/missing-backend/private-package/flat-file-state cases; plugtests/test_connection_work_package.py checks exact boundaries. These are future implementation paths, not files built now. Singh integration; Singhal may review evidence/fixtures; no additional Gupta/Vijay tasks. Full lifecycle implementation slices belong to Plan3 planning, not this amendment.

## Closure consolidation
The canonical typed WorkPackage/SourceSnapshot/resource graph and immutable acceptance/status/cancel definitions are in [CONNECTION_CONTROL_PROPOSAL.md](CONNECTION_CONTROL_PROPOSAL.md). Components/external-dependencies/unresolved-input records in this document define the required validated referenced contents. Baseline reproduction remains Plan3 after Start; Plan1 closes at its specified first-operation handoff, not an executed working-site claim.
