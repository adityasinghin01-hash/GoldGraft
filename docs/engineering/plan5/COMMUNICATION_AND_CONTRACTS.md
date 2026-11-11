# Typed collaboration, task control and worked runs

Proposed wire/port specification. Python implementation and generated exports do not exist yet. Common primitives below reuse the canonical connection proposal: `Id/Ref` nonempty opaque identifiers, `Digest` lowercase SHA256, `Utc` timezone-aware UTC, strict `Count`≥0 and `Positive`≥1. A Ref resolves only through authorised same-tenant/case lookup. Provider Git/OCI identities retain their provider formats. Unknown fields/enums, non-finite numbers, bool-as-int, oversized lists and cross-case refs are rejected. Caps are policy limits, never a mechanism to truncate required evidence into a pass.

## New shared records for SI01

Names ending `/1` are proposed registry keys, not a new arbitrary `version` property on old payloads. All enums are closed. `Role` is exactly the thirteen canonical strings in AGENT_ROLES. `Operation` is a server-owned catalog key. Inputs and outputs are immutable, content-verified descriptors.

```text
ArtifactDescriptor/1 = {
 ref:Ref, case_id:Id, run_id:Id, generation:Positive,
 schema:Id, payload_digest:Digest, byte_count:Count,
 subject_digest:Digest, input_digest:Digest, derivation_ref:Ref|null,
 producer_identity_ref:Ref,
 trust:model_proposal|collector_observed|deterministic_result,
 evidence_class:scripted|component_offline|real_model|real_provider|
                real_payment|isolation_qualified|merchant_exit,
 created_at:Utc, expires_at:Utc|null
}
Issue = {code:Id, input_ref:Ref|null, owner_role:Id,
         recovery:retry_read|reconnect|supply_input|review_scope|reapprove|
                  await_counterpart|reconcile|unsupported,
         evidence_refs:Ref[]}
TaskSpec = {task_id:Id, role:Role, operation:Operation,
 dependencies:Id[], input_refs:Ref[], expected_schemas:Id[],
 output_slot:Id, workspace_ref:Ref|null, expected_subject:Digest,
 allowed_tool_ids:Id[], required:bool,
 output_subject_policy:same_subject|candidate_child|build_from_source|derived_evidence}
PlanProposal/1 = {case_id:Id, run_id:Id, generation:Positive,
 parent_request_id:Id, tasks:TaskSpec[], reason_refs:Ref[]}
AgentTask/1 = {task:TaskSpec, case_id:Id, run_id:Id, generation:Positive,
 request_id:Id, input_digest:Digest, policy_ref:Ref, policy_digest:Digest,
 prompt_ref:Ref, prompt_digest:Digest, model_profile_ref:Ref|null,
 state:pending|ready|leased|running|waiting|retry_due|succeeded|
       held|unknown|failed|cancelled,
 state_version:Positive, attempt:Positive, created_at:Utc, deadline:Utc,
 next_wake_at:Utc|null, wake_condition_ref:Ref|null,
 lease_owner:Id|null, lease_epoch:Count,
 lease_until:Utc|null, checkpoint_ref:Ref|null,
 output_refs:Ref[], issue:Issue|null}
TaskLease/1 = {task_id:Id, run_id:Id, generation:Positive,
 worker_id:Id, lease_epoch:Positive, task_version:Positive,
 lease_until:Utc, context_ref:Ref}
TaskCheckpoint/1 = {task_id:Id, generation:Positive, lease_epoch:Positive,
 turn:Count, committed_message_refs:Ref[], invocation_refs:Ref[],
 staged_output_refs:Ref[], context_digest:Digest, policy_digest:Digest,
 budget_reservation_refs:Ref[], wake_condition_ref:Ref|null,
 next_step:model_turn|await_tool|validate_output,
 created_at:Utc}
AgentResult/1 = {task_id:Id, request_id:Id, case_id:Id, run_id:Id,
 generation:Positive, lease_epoch:Positive, input_digest:Digest,
 outcome:completed|blocked|failed|unknown, output_refs:Ref[],
 evidence_refs:Ref[], issue:Issue|null, completed_at:Utc,
 authenticity_ref:Ref}
ExecutionProposal/1 = {task_id:Id,
 operation:build_baseline|build_candidate|validate_driver|run_scenario|
           run_mutant|selfcheck_recipe,
 subject_ref:Ref, recipe_ref:Ref, scenario_ref:Ref|null,
 variant:OLD|OLD_TWIN|NEW|null, requested_output_schemas:Id[],
 expected_subject:Digest, evidence_refs:Ref[]}
```

TaskSpec can only reduce the current capability/role catalog, never expand it. Task IDs unique per run; ≤32 nodes, ≤32 dependencies/node, no cycles, no self-dependency, every dependency exists. Required tasks cannot become optional by model choice. A waiting task must have a persisted wake condition/owner; no busy polling inside model loops. `succeeded` requires nonempty expected validated outputs and no blocking issue; optional tasks may be omitted from the admitted DAG but are never silently skipped after becoming required.

`expected_subject` identifies the canonical manifest of the task's **known accepted inputs**, not a guessed future candidate/image digest. Admit each stage only after its producer has committed the exact refs/subject; do not fill placeholders or mutate TaskSpec after claim. Parallel tasks may share a known pinned candidate. Grafter and Builder may produce new subjects only under the fixed output_subject_policy and authenticated derivation below; equality with the old subject is not required for a transform. Content identity and parent-input lineage are both checked.

`SubjectDerivation/1={derivation_id:Id,case_id:Id,run_id:Id,generation:Positive,task_id:Id,parent_refs:Ref[],parent_subject:Digest,operation:candidate_patch|artifact_build|evidence_derivation,recipe_or_patch_digest:Digest,output_refs:Ref[],output_subject:Digest,collector_identity_ref:Ref,authenticity_ref:Ref}`. Parent refs/input digest must equal the accepted task inputs. Collector observes output bytes/source-tree/build/image/config manifest and computes output subject; model cannot assert it. Same-subject output requires derivation_ref=null and equal subject; transforms require exact valid derivation_ref/operation/producer. SubjectDigest is SHA256 of canonical secret-free `SubjectManifest/1={source_snapshot_refs:Ref[],source_tree_digest:Digest|null,oci_manifest_digest:str|null,config_digest:Digest|null,runtime_profile_digest:Digest,scope_digest:Digest}`; OCI field uses provider OCI validation rather than raw Digest coercion. Manifest ref/bytes are persisted and checked, not a naked hash label.

Lease owner/epoch/time all null/zero before claim; positive epoch after claim. Authoritative server clocks define expiry. Result completion compares current generation/lease epoch/state version, exact input digest, allowlisted output schemas/producer/subject and resolved bytes. A missing authenticity reference or forged self-report cannot create an observed record. `blocked/failed/unknown` requires Issue; `completed` forbids blocking Issue. Request/operation IDs are persisted before dispatch. Source-unchanged evidence is collector-observed, not a model boolean.

## Model turn and tool protocol

```text
ModelTurnRequest/1 = {turn_id:Id, task_id:Id, generation:Positive,
 lease_epoch:Positive, model_profile_ref:Ref, context_ref:Ref,
 context_digest:Digest, allowed_tool_ids:Id[], output_schema:Id,
 input_token_cap:Positive, output_token_cap:Positive,
 budget_reservation_ref:Ref, deadline:Utc}
ToolCall = {call_id:Id, tool:Id, arguments_ref:Ref, arguments_digest:Digest}
ModelTurnResult/1 = {turn_id:Id, task_id:Id,
 kind:tool_calls|final|blocked,
 calls:ToolCall[], final_artifact_ref:Ref|null, issue:Issue|null,
 usage_receipt_ref:Ref, provider_receipt_ref:Ref|null}
ToolInvocation/1 = {invocation_id:Id, task_id:Id, case_id:Id, run_id:Id,
 generation:Positive, lease_epoch:Positive, tool_id:Id,
 arguments_ref:Ref, arguments_digest:Digest, input_digest:Digest,
 capability_ref:Ref, budget_reservation_ref:Ref, deadline:Utc,
 state:intended|submitted|observed|denied|failed|unknown,
 result_refs:Ref[], effect_ref:Ref|null, issue:Issue|null}
TaskEvent/1 = {event_id:Id, case_id:Id, run_id:Id,
 generation:Positive, task_id:Id|null, sequence:Positive,
 kind:task_ready|task_changed|tool_observed|approval_changed|
      cancellation_changed|timer_due|evidence_changed,
 payload_ref:Ref, payload_digest:Digest, causation_id:Id,
 correlation_id:Id, occurred_at:Utc}
```

`tool_calls`:1–4 calls, final/issue null; `final`:calls empty, final ref required, issue null; `blocked`:calls empty, final null, issue required. Argument refs resolve to catalog-specific strict objects and are never arbitrary shell instructions. A duplicate call ID must have the same tool/arguments/input fingerprint or conflict. A prior unknown invocation cannot be replaced by a new call ID to repeat the effect. Runtime chooses invocation ID from the durable `(task,attempt,turn,call)` identity, not model randomness. Usage receipt is broker-produced; tool selection from the model is untrusted.

## Port signatures and durable commit boundary

All signatures are Python-facing Protocol targets in `contracts/.../agent_runtime.py`; implementations remain separately owned. IO may be async, but logical arguments/results must match generated contracts. Errors are closed `ControlError(code, retry_class, evidence_refs)` with `retry_class=none|safe_read|reconcile|reauthorise`; no raw exception/secret text in user responses.

```text
TaskControl.seed(run_ref:Ref, proposal:PlanProposal, key:Id)->list[AgentTask]
TaskControl.extend(run_ref:Ref, expected_run_version:Positive,
                   proposal:PlanProposal, key:Id)->list[AgentTask]
TaskControl.claim(worker_id:Id, now:Utc)->TaskLease|null
TaskControl.load(lease:TaskLease)->AgentTask
TaskControl.renew(lease:TaskLease, now:Utc)->TaskLease
TaskControl.checkpoint(lease:TaskLease, value:TaskCheckpoint)->Ref
TaskControl.begin_tool(lease:TaskLease, value:ToolInvocation)->ToolInvocation
TaskControl.observe_tool(lease:TaskLease, invocation_id:Id, result_ref:Ref)->ToolInvocation
TaskControl.finish(lease:TaskLease, result:AgentResult)->AgentTask
TaskControl.wait(lease:TaskLease, issue:Issue, condition:WakeCondition)->AgentTask
TaskControl.snapshot(run_ref:Ref)->RunTaskSnapshot
TaskControl.cancel(run_ref:Ref, cancellation_ref:Ref)->RunTaskSnapshot
ArtifactPort.resolve(ref:Ref, task_context:Ref)->ArtifactDescriptor
ArtifactPort.stage(task_id:Id, schema:Id, payload_ref:Ref, subject:Digest)->Ref
ModelPort.turn(request:ModelTurnRequest)->ModelTurnResult
ModelPort.reconcile(turn_id:Id)->ModelTurnStatus
ToolPort.invoke(invocation:ToolInvocation)->ToolInvocation
ToolPort.reconcile(invocation_id:Id)->ToolInvocation
```

`RunTaskSnapshot={case_id,run_id,generation,state_version:Positive,tasks:AgentTask[],last_event_seq:Count,cancellation_ref:Ref|null}`. `finish` is one GU transaction: revalidate lease/current authority/result; insert immutable unique result and accepted output bindings; mark succeeded or terminal hold; mark newly satisfied dependency nodes READY; append outbox/task events. Result-before-event-loss therefore survives. No accepted result if cancellation wins the same lock. Cancellation never erases prior effects/results. `observe_tool` may retain authenticated stale-result evidence privately but cannot accept it as current task output; old leases cannot advance tasks.

`WakeCondition/1={condition_id,case_id,run_id,generation:Positive,kind:timer|task_result|authority|approval|counterpart|tool_reconcile,subject_ref:Ref,expected_digest:Digest|null,minimum_version:Count,owner:Id,due_at:Utc|null,expires_at:Utc}`. Persist before releasing a waiting lease. Approval wake binds exact ActionPlan digest; task/counterpart wake binds exact expected schema/subject via its referenced request; timer/reconcile requires due_at. On any wake, current authority, input and deadline still revalidate; an event merely prompts evaluation. No permanent wait with neither observable subject nor due timer. Expiry produces held with a named owner.

`ModelTurnStatus/1={turn_id,task_id,state:intended|submitted|observed|failed|unknown,result_ref:Ref|null,usage_receipt_ref:Ref|null,checked_at:Utc,issue:Issue|null}`. GU02 persists the turn identity and budget reservation before provider dispatch. On ambiguous timeout, reconcile the same ID and usage; if provider cannot determine completion, retain unknown and hold. No new call/turn is automatically issued to replace an unknown billed call. Only a separately explicit bounded reattempt policy with renewed budget may supersede a known failed call.

Model broker normalizes bounded provider inline argument/final JSON into **untrusted staging blobs**, then returns arguments_ref/final_artifact_ref. Models cannot mint storage refs or trusted descriptors. Runtime resolves the blob, checks tool-specific/output schema and source constraints, and only then stages an ArtifactDescriptor with trust=model_proposal; collector-observed/deterministic trust is issued solely by those authenticated services. Reject model-supplied arbitrary refs, trust claims and provider response URLs. No circular requirement to possess an accepted artifact before validation.

`extend` atomically appends new immutable task specs only; it cannot mutate existing dependencies, required flags or ownership. Compare expected run version, current authority and whole accumulated DAG/count≤32. Initially admit through `scribe-draft`. Validate its TriangleRequests; append at most4 follow-up Explorer trace tasks depending on the draft, then a distinct `scribe-final` depending on those results, then Architect only after the final synthesis commits. Adversary guard work starts after the exact candidate exists. No Scribe→Explorer→same-Scribe cycle. An additional missing essential trace after final synthesis holds rather than unbounded graph growth. Repairs append new candidate-attempt tasks and invalidate downstream subject-dependent results; they do not edit past tasks. See manual task graph for exact node order.

GU03 owns these durable mechanisms, not Singh's runtime. SI01 supplies records and a **persistent offline fake** with contractual uniqueness/CAS/lease/outbox semantics; it must be clearly labelled and use synthetic refs. The fake's local SQLite database demonstrates runtime restart against persisted boundary state, not production/Postgres/provider conformance. The existing foundation ledger can record refs; it is not a second independently writable task-state owner.

## Guarded tool catalog

Every argument object has `additionalProperties=false`; numeric caps strict. Resolve all refs/paths and validate role/current capability before dispatch. Return refs+Issue/outcome, not uncontrolled guest stdout. Tools may use backend catalogued recipes, never model-provided effect URLs.

| Tool | Exact argument fields | Result / roles |
|---|---|---|
| `status.read` | `run_ref:Ref` | RunTaskSnapshot/private status refs; Gardener/Healer/Herald |
| `source.read` | `snapshot_ref:Ref,path:str,max_bytes:Positive≤32768` | Redacted excerpt descriptor; Surveyor/Scribe/Grafter/Adversary |
| `analysis.matches` | `snapshot_ref:Ref,rule_ref:Ref,max_matches:Positive≤500` | Match-list descriptor; Surveyor |
| `evidence.read` | `ref:Ref,max_bytes:Positive≤32768` | Bounded authorised descriptor/excerpt; Surveyor/Builder/Explorer/Scribe/Architect/Adversary/Healer |
| `evidence.summary` | `run_ref:Ref,projection:private_status|public_safe` | Approved summary descriptor; Herald |
| `recipe.lookup` | `catalog_ref:Ref,fingerprint:Id` | Qualified recipe refs or unavailable; Builder/Architect/Grafter |
| `docs.lookup` | `catalog_ref:Ref,topic:Id,version:Id` | Pinned documentation refs; Architect/Grafter |
| `dependency.inspect` | `recipe_ref:Ref,package:Id,version:Id` | Allowlist/licence/installed-symbol refs; Builder/Grafter |
| `execution.request` | `proposal_ref:Ref` | Durable LifecycleWorkRequest receipt ref; Builder/Explorer/Adversary/Librarian with exact operation restrictions |
| `execution.status` | `request_id:Id` | Authenticated result/evidence refs or pending/unknown; same requester scope |
| `candidate.patch` | `workspace_ref:Ref,expected_tree:Digest,patch_ref:Ref` | CAS new snapshot descriptor; Grafter only; branch write/push is not this tool |
| `scenario.stage` | `scenario_set_ref:Ref,mutant_set_ref:Ref` | Schema-validated draft refs; Adversary only |
| `recipe.stage` | `recipe_ref:Ref,detection_rule_ref:Ref|null` | Quarantine ref; Librarian only |
| `aggregate.read` | `query_ref:Ref,projection_ref:Ref` | Bounded authorised aggregate ref; Orchard Analyst |
| `audit.summary` | `run_ref:Ref,after_seq:Count` | Redacted policy audit refs; Sentinel |
| `safety.request_hold` | `run_ref:Ref,reason_code:Id,evidence_refs:Ref[]` | Hold-request receipt; Healer/Sentinel, actual fence/termination separately observed |

No role receives generic provider HTTP, grant issuance, remote Git write, registry push, deploy, switch-write, financial compensation or arbitrary host shell. Legacy tools stay only in explicit legacy demo fixtures; new admitted tasks cannot route to that catalog. Backend broker rechecks independently even if the agent adapter was bypassed.

## Routing, ordering and wake conditions

No direct agent chat is authoritative. A Scribe-draft TriangleRequest may cause bounded Explorer trace followups; validated refs satisfy the distinct scribe-final task. Adversary guard work starts only after the final Contract and exact candidate exist. No task can wake another by writing a forged event. Backend committed outbox is delivered at least once. Inbox dedupe key is event_id; run sequence/state version detects gaps; stale-generation events cannot advance state. Acknowledgement occurs after inbox+state commit. Reordered events trigger current snapshot reconciliation; they do not require global ordering across unrelated cases.

Waiting reasons: authority/input/counterpart → authenticated relevant committed change; provider/tool unknown → reconciliation timer/observation; rate limit → bounded due timer; budget/custody expiry → hold, no automatic reset; controller approval → exact current plan approval event. After a backend restart scans due tasks/outbox and lease expiry; scheduler automatically resumes eligible work. Unknown external effects retain reservations even if their local lease expired.

## Worked successful synthetic run

Synthetic IDs below are explanatory, not valid production signatures/digests. Fixtures supply computed SHA256 fields and authenticated **fake** evidence during SI01; no invented hashes are presented as proof.

1. Backend accepts action `a-demo-01` once, returns immutable WorkAcceptance for `w-demo-01`. Lost-response query returns that same receipt/current status. Controller scope permits synthetic sandbox work only.
2. Trusted verifier supplies BASELINE_READ receipt; WorkStatus becomes operation_started. Scheduler seeds run `r-demo-01`, generation1; package verification and Surveyor task are unique.
3. Surveyor reads pinned `snapshot-demo-old`, returns RootMap draft. Collector binds input digest; finish transaction marks Surveyor succeeded and Builder ready.
4. Builder requests VJ recipe baseline build. Explorer requests required OLD/OLD_TWIN scenarios. Recorder/mapper produce observed refs; required missing flow would hold here.
5. Scribe Contract and Architect TargetPlan are validated. Grafter patches WORKING by expected-tree CAS; collector seals `snapshot-demo-new-1`. Builder tests the exact candidate artifact; Explorer/Adversary use that artifact and separate data/forks.
6. Deterministic proof rejects or issues scoped evidence-ready result. Synthetic fully evidenced result yields REVIEW_READY only. Herald/UI explain required controller review and remaining live qualification. No model can skip this stage.
7. In a component-only delivery test, fake current approvals/effects/state/exit observations exercise coordinator requests to final `complete`. UI still displays “Mock mode: showing saved sample data, not a live system.” No real merchant complete claim follows.

## Crash, retry, Stop and repair trace

- Task t7 owns candidate version3/lease epoch2. It commits invocation i7 then worker dies after runner dispatch. New worker claims epoch3. It reads i7 as submitted/unknown and calls reconcile; it does not issue i8 to repeat the build/payment scenario. Unknown result holds; known observed result may be rebound only after current subject/scope checks.
- Old worker eventually returns result for epoch2. Collector may retain it as stale evidence; TaskControl.finish rejects advancement. Cancellation ordered before output commit also wins even if model text says “success.”
- If task result commits but ready event is lost, restart outbox redelivery finds unique completed result/next task. No second accepted result or writer exists.
- A failed NEW guard generates repair round1 targeted to Grafter, preserving original normative tests. New tree invalidates old image/test/proof/review/approval; rebuild/retest. Round2 exhaustion or repeated unchanged failure fingerprint produces held `REPAIR_EXHAUSTED`.
- Stop after an external deploy submission is not task cancellation proof. Delivery enters `INCIDENT_UNKNOWN`, asks GU reconcile original effect/target and shows pending truth. New mutation needs current approved recovery authority; no old grant resurrection.
