# Same-site delivery and merchant-owned exit

PROPOSED coordinator construction specification. Actual provider/state/payment/exit conformance remains open. Normative IR01–IR05/IR07 in [atomic protocols](../lifecycle/ATOMIC_DELIVERY_PROTOCOLS.md) controls every step; this document supplies Singh's coordinating policy and precise pending states, not a second deployment/state engine.

## Admitted outcome and first profile

Leave the same website URL/domain/hosting/accounts under merchant ownership, with necessary approved PayPal changes already operating. Preserve unrelated functions, current business/economic state, credentials/apps/listeners and pending/historical obligations. Merchant receives operating/recovery records and private source/artifacts as ownership evidence, without technical finishing homework. Full delivery is not available just because code can be scanned or sandbox tests pass.

First construction reference: licensed pinned plain-PHP one-time-payment lab, qualified single-platform linux/amd64 image, synthetic/sandbox state, image-backed Render adapter only where it matches the existing target. This is a **fixture/profile target**, not a supported live migration. Source routes may be Git or stable non-Git capture. Direct artifact does not create fictitious Git fields. Existing Git-backed service conversion is a separately qualified config/state/trigger change; never assume image-backed support applies automatically. Other hosts/languages/payments/subscriptions require their own qualified profiles.

Before Start, read-only feasibility records complete required source/components, current running-shop correspondence, controllers, prospective delivery route and missing primitives. Before apply, refresh every identity/authority/policy and verify actual continuity primitives. Pre-Start checks neither run source/models/payments nor obtain initial write authority.

## Exact entry/success predicates

`can_review`: required baseline and candidate flows evidenced; unchanged baseline defects explicitly distinguished; exact source/tree/dependency/recipe/OCI-manifest/config subject; missing/unsupported required evidence empty; independent proof ready; scoped expert review available. High scores/signatures/health pages cannot substitute.

`can_prepare_apply`: can_review plus current resource graph/controllers, all trigger chains known, exact immutable ActionPlan/state/recovery/finalisation/exit plans; merchant private source/registry/persistent pull path; safe export/fence/handler route; independent exit executor readiness. A planned future setup mutation must appear as an approved effect slot, not be pretended already complete.

`can_submit_slot`: current complete ApprovalSet covers that exact slot and its dependencies; authority/current role/epochs/expiry match; target reservations/fences/expected provider versions match; no unresolved overlapping effect; artifact/config/state/trigger/plan digests unchanged; budget/time constraints valid. GU mechanism checks atomically at use; coordinator prechecks are for truthful planning, never the sole enforcement.

`upgrade_verified`: actual same target URL/account, exact active image/config, current-state/replay and required handler/payment/origin evidence meet approved scope under production-safe observation authority. No real live payment test is implied. `exit_complete`: upgrade_verified plus independent Q0–Q4 evidence, required temporary termination/revocation/cleanup confirmed or explicitly policy-approved retention disposition, merchant required assets accessible and no finishing tasks. A pending required deletion/ack/executor blocks completed exit. Upgrade and cleanup status remain separate facts.

## Coordinator interface

`advance_delivery(view:ResolvedDeliveryView)->DeliveryDecision` is deterministic and side-effect free. `DeliveryPort.snapshot` returns a current authorised coherent projection from GU/SH/VJ; Singh's `resolve_delivery(snapshot, ArtifactPort)` verifies/materializes the records before calling the reducer. A snapshot contains refs, digests/versions and no secrets. A decision has exactly one of request/wait/hold/incident/complete; executor commits the chosen request identity before a port call.

```text
DeliverySnapshot/1 = {case_id, run_id, generation:Positive,
 state_version:Positive, lifecycle_ref:Ref, graph_ref:Ref,
 review_ref:Ref|null, action_plan_ref:Ref|null,
 approval_set_ref:Ref|null, reservation_ref:Ref|null,
 state_cutover_ref:Ref|null, deployment_ref:Ref|null,
 final_asset_manifest_ref:Ref|null, exit_plan_ref:Ref|null,
 exit_manifest_ref:Ref|null, current_evidence_refs:Ref[],
 pending_effect_refs:Ref[], cancellation_ref:Ref|null,
 issue:Issue|null, checked_at:Utc}
DeliveryDecision/1 = {case_id,run_id,generation:Positive,
 expected_state_version:Positive,
 kind:request|wait|hold|incident|complete,
 operation:review_evaluate|plan_apply|reserve_targets|preserve_state|
           publish_artifact|publish_source|merge_protected|
           apply_configuration|deploy_exact|reconcile_effect|
           observe_target|finalise|prepare_exit|run_exit|read_exit_evidence|
           revoke_exit_evidence|reconcile_cleanup|null,
 input_refs:Ref[], existing_effect_ref:Ref|null,
 slot_id:Id|null, reason_code:Id, next_wake_at:Utc|null}
```

Each nullable field is conditional: request requires operation and required current refs; consequential operations require exact approved slot ID and resolved plan; reconciliation requires existing effect ref and cannot allocate a new slot. Other kinds have operation/slot null except incident may request reconciliation through a subsequent committed request decision. Snapshot validator resolves trusted records and current state; model-supplied booleans cannot satisfy predicates. `complete` requires exact exit-complete predicate. A model cannot directly call this executor or supply its approval inputs.

`DeliveryPort.submit(decision,request_id)->LifecycleWorkRequestReceipt`; `DeliveryPort.status(request_id)->LifecycleWorkResult|PendingResult`; `DeliveryPort.snapshot(run_ref)->DeliverySnapshot`. These service-only Protocols in shared lifecycle definitions have Gupta implementations. `PendingResult={request_id,state:queued|running|waiting|unknown,evidence_refs:Ref[],checked_at:Utc}`. `LifecycleWorkRequestReceipt/1={request_id,run_id,generation:Positive,accepted_at:Utc,request_digest:Digest}`. Requests use `(run,generation,state_version,operation,slot)` unique logical key; stale snapshot rejection causes refetch, not new effect. Retries/query preserve identity. UI has no arbitrary-effect endpoint.

`ResolvedDeliveryView/1={snapshot:DeliverySnapshot,lifecycle:LifecycleRun,delivery_route:git_protected|direct_artifact,review:ReviewBundle|null,plan:ActionPlan|null,approvals:ApprovalSet|null,reservation:TargetReservation|null,state_cutover:StateCutover|null,deployment:DeploymentObservation|null,final_assets:AssetManifest|null,exit_plan:ExitCheckPlan|null,exit_manifest:ExitManifest|null,predicate_results:PredicateResult[]}`. `PredicateResult={predicate:can_review|can_prepare_apply|can_submit_slot|upgrade_verified|exit_complete,slot_id:Id|null,status:pass|missing|stale|failed|unknown,evidence_refs:Ref[],subject_digest:Digest,checked_at:Utc}`. `can_submit_slot` requires the exact nonnull slot_id and matching evidence subject; other predicates require slot_id=null; absence is denial. Resolver checks schema/digests/tenant/run/generation/current evidence and populates trusted predicates; untrusted caller cannot send booleans. The pure reducer never performs hidden IO and rejects missing/mixed-version resolved data.

## Sequence and safe branch predicates

| Step / state | Coordinator request and responsible mechanism | Evidence before next step / failure |
|---|---|---|
|1 REVIEW_READY | SH evaluate exact bundle, scoped reviewer sees limitations | Required evidence ready; otherwise isolated bounded repair/held, no publication |
|2 AWAITING_APPLY | GU builds immutable plan/effect DAG; independent controllers approve source/registry/host/data/callback scope | Exact complete set and current authorities. Missing/rejected/expired consent waits; no merchant deployment instruction |
|3 reservation | GU04 canonical provider/account/environment/resource keys, all dependencies, atomic sorted acquisition | Cross-case conflict holds. Expiry fences old executor; unknown effects retain ownership |
|4 pre-first-prerequisite state safety | GU05 with VJ03 existing ingress/handler/export/fence recipes | All writers/returns/refunds/tasks inventoried; merchant-owned durable UNVERIFIED ingress and origin handler or genuinely complete approved drain; H, fence, consistent export and disposable restore/replay verified BEFORE destructive disk/config/redeploy prerequisite |
|5 publish private exact outputs | GU04 trusted image/source publisher; build guest has no push scope | Exact tested OCI manifest/layers, provenance/leak scan, private merchant source/registry ownership and persistent pull. Unknown upload reconciles same effect |
|6 protected Git, if chosen | GU04 merge exact reviewed head/base under protections | Result tree/input/image derivation matches approval, or rebuild/reprove/reapprove. DirectArtifact skips this state |
|7 DEPLOY_PREPARED | GU04/05 apply approved persistent image/config/state prerequisites in effect-DAG order | State preserved before any restart; merchant pull/operational credentials and original callbacks intact. No one-off override mistaken for persistent config |
|8 DEPLOYING | GU04 exact target/config/image request, intent first | Accepted/queued response is not live. No-ID202 remains original pending/unknown effect; unique provider/runtime reconciliation required; never retry merely to get an ID |
|9 OBSERVING | GU target/state reads, VJ domain observations, SH completeness | Actual active image/config/URL, current state/replay backlog, callbacks, pending/refund/history and unrelated required functions. No unapproved live payment probe |
|10 FINALISING | GU05/VJ04 final candidate removes temporary rollout reliance under approved slot | New image/config revalidated/reapproved; preserve merchant legacy routes/credentials/registry. Expiry cannot revive unsupported old code |
|11 EXITING Q0–Q4 | Independent merchant executor and GU05 mechanism below | GoldGraft ordinary authority denied/revoked, independent restart/private observations, temporary evidence-read revoked, required cleanup disposition known |
|12 COMPLETE | Coordinator verifies current exit manifest and projects private result | Operating upgraded same-site service with retained assets and no hidden technical tasks. Otherwise upgrade-observed/exit-pending, FAILED_SAFE or INCIDENT_UNKNOWN |

State preservation and publication ordering follows the approved effect DAG. Safe private publication may precede a live drain where independent; **no destructive prerequisite** may precede verified current export/fence/handler continuity. An all-drained option includes every long-tail obligation; a timeout holds, not a forced cutover.

Finalisation has an explicit sub-DAG: prepare final candidate without rollout dependency → build/test exact final OCI/config against required flows and current-state/origin semantics → independent proof/private review → new ActionPlan/ApprovalSet for final publication/config/deploy slots → retain/acquire current reservations → apply final exact image/config under approved state plan → observe final target → Q0. If no bytes/config change is needed, record evidence that the existing approved subject already satisfies independence. Any changed final subject invalidates old dependent proof/approval; `run_exit` is denied until new final subject is independently approved and observed. No shortcut from “remove old code” to EXITING.

The first construction profile prepares a merchant-independent final candidate before initial apply, without adopting historical percentage-rollout stages. FINALISING normally verifies that existing approved bytes/config need no change. If qualified later recipes require a changed final candidate, the explicit sub-DAG above applies and ExitCheckPlan is reissued for that final exact subject. Executor capability/readiness can be known before its final restart plan is approved; never pretend tentative final-artifact evidence is observed.

## Payment/state rules consumed from domain owners

No raw production database enters model context. Original store remains authoritative until explicit all-writer fence and durable H. Every checkout/capture/return/refund/admin/task/notification writer is included. Stop-new-checkout alone is insufficient. Pre-H effects are committed consistently; post-H inputs durably queue under original identities and apply only through the designated writer. Unknown processor outcomes reconcile before additional economic actions. Do not restore an old snapshot over newer economic history.

IPN: bounded ingress persists encrypted original UNVERIFIED bytes/listener/environment → acknowledges receipt → async exact validation → merchant/order/status/amount/currency/origin checks → idempotent local business effect. Failed persistence must not acknowledge accepted receipt. Duplicate transport is different from a legitimate later status. REST webhooks use their own app/raw-body/transmission validation, not IPN logic. Account identity alone does not transfer another app's events; original required IPN/app/listeners and legacy routes remain until obligations are demonstrably discharged.

Financial compensation requires separate explicit authority and plan. Neither Stop, rollback nor apply authorises refund/capture/new-charge requests. Externally settled money cannot be undone by code/state rollback. Code cutback is allowed only when current schema/economic/origin/credential compatibility is proved; otherwise forward repair or safe hold.

These are GoldGraft policy requirements, not claims that PayPal stores our receipts or provides exactly-once delivery. Source facts and limits are in the private delivery study and [existing payment study](../lifecycle/research/PAYMENT_CONSTRAINTS.md).

## Asset ownership and keep/remove plan

| Asset | Keep / remove and final owner | Completion evidence |
|---|---|---|
| URL/domain/TLS/host account/site/unrelated functions | Keep merchant ownership and required function | Current target correspondence/observations |
| Upgraded editable source/build inputs/manifests | Keep in private merchant-accessible destination | Authorised retrieval and provenance, not manual deployment homework |
| Exact image, configured reference and registry pull identity | Keep merchant ownership/access; maintain image availability | Fresh independent pull/restart matches approved final digest/config |
| Operational PayPal account/app/credential refs/validation roots | Keep required merchant custody; rotate only via explicit compatible plan | Callback/origin/history continuity after GoldGraft ordinary grant denial |
| Current database, intent/idempotency/origin ledger/H/replay and pending obligations | Keep merchant durable state | Counts/digests/offsets/domain invariants, private evidence |
| Durable callback ingress/queues/return bridges/legacy handlers | Keep merchant-owned while required | No service-only relay, expiring tunnel or GoldGraft secret dependency |
| Exit executor/evidence/recovery destination | Merchant-owned fixed trusted code and bounded authority | Q0 ready plus Q2 independent evidence; no workflow-write permission inferred |
| Temporary GoldGraft grants/capabilities | Fence locally, revoke/expire remotely per grant and shared-use inventory | Per-provider acknowledgement; shared installation not blindly removed |
| Exclusive sandbox/worker/temporary tunnel | Fence/terminate, reconcile external sandbox effects, remove within approved scope | Actual trusted child/process/resource observations, timeout not proof |
| Temporary source/prompts/captures/uploads/copies | Per-store disclosed active deletion/version sweep/retention/holds | Active/backup/held/exported-unrecallable/unknown differentiated |
| Minimal case and private operating/recovery record | Retain under disclosed scoped policy | No public source/customer/payment IDs, no automatic public merchant status |

## Independent exit Q0–Q4

Q0: qualified merchant executor exists **before** disruptive verification. Approve exact ExitCheckPlan: target reservation, final image/config/state, fixed trusted code/identity, one restart, bounded compatible recovery, deadline/budget, private evidence destination and failure route. It cannot be an untrusted shop workflow or new privileged workflow silently installed by Publisher.

Q1: GU fences ordinary GoldGraft acquisition/model/mutation/worker authority, confirms termination, revokes ordinary grants after shared-use checks. Pending revoke acknowledgement is recorded honestly. Required merchant operational credentials are separate and preserved.

Q2: merchant-owned executor independently performs the approved restart/current-state/callback/origin checks and any approved bounded compatible recovery. GoldGraft cannot use revoked ordinary keys. Insufficient recovery scope yields approved safe hold, not unapproved money/state repair.

Q3: explicitly disclosed temporary read-only EXIT-EVIDENCE capability reads signed redacted results from the merchant destination; it is not host/source authority. SH verifies identity/subject/evidence completeness. Q4: revoke/expire and confirm that last evidence capability separately; retain authorised public or merchant operating observation. Required unresolved cleanup means exit pending.

## Failure map and visible state

| Condition | Required coordinator result / visible words |
|---|---|
| Missing safe primitive, source, controller or required flow | HELD; “Setup needed” plus exact item/owner; original preserved |
| Proof failure before effects | Bounded isolated repair or FAILED_SAFE; no live-upgrade claim |
| Approval expires after publication | Await exact remaining current approvals; published fact retained, new deploy denied |
| Publication/deploy timeout or no attributable ID | INCIDENT_UNKNOWN/pending; “Checking delivery status”; same effect reconciliation, no second request |
| Stop after dispatch | Fence remaining slots; reconcile; “Stopping work. Delivery status is being checked.” |
| Restore/replay/current state incompatible | No admission reopening; approved forward repair/compatible cutback/safe hold |
| Source/config/controller drift | Invalidate dependent review/approval; observe fresh input before replan |
| Independent executor absent | “Upgrade observed; independent-operation check pending” only if live evidence supports first clause |
| Remote revocation/delete unavailable | Item-specific pending/held; “Upgrade verified; cleanup pending” only when upgrade evidence valid |

Every consequential operation has a current authority, exact effect slot, evidence-before-next-step and safe pending/unknown path. Models explain these states; they do not own the state machine. Actual acceptance criteria and fault assertions are in the component-test plan; no tests ran in this specification phase.
