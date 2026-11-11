# SI01 exact bootstrap and compatibility plan

Specification only; no Python/generated contract/fixture/fake edited or generator run. New interfaces are proposals until one approved implementation includes models, registry/routes, exports, examples, meaningful fixtures/fakes and compatibility together. Keep current versions unchanged where semantics fit. No team consumer implements guessed fields ahead of this bootstrap.

## Sources and exact file changes

| Create/modify target during5.3.1 | Required contents / contract authority |
|---|---|
| `contracts/src/goldgraft_contracts/connector_adapters.py` | ProviderRef, SourceRevision, ResourceNode/Edge/Graph, Binding, capabilities/observation from canonical connection proposal |
| `.../work_package.py` | SourceSnapshot/1, UploadSession/1, manifest/chunk plus typed component/dependency/config/required-flow/omission/input records below; canonical WorkPackage/1 |
| `.../connection_control.py` | ConnectionCase, CheckResult/Readiness, ActionIntent, StartWorkRequest, WorkAcceptance/Status/Cancellation, WorkerOperation; typed provider/invitation/view shapes below |
| `.../lifecycle.py` | Existing proposed LifecycleRun/WorkRequest/WorkResult, ReviewBundle/ApplyApproval/EffectIntent/BaselineEvidence/DeploymentObservation/RecoveryPlan/ExitManifest; exact supplemental types below; DeliverySnapshot/ResolvedDeliveryView/Decision/receipts from delivery spec |
| `.../agent_runtime.py` | ArtifactDescriptor, SubjectManifest/1, SubjectDerivation/1, Issue, TaskSpec, PlanProposal, AgentTask/Lease/Checkpoint/Result, ExecutionProposal, WakeCondition, ModelTurnRequest/Result/Status, ToolInvocation, TaskEvent, RunTaskSnapshot and Protocols from communication spec; TaskContext below |
| `.../agents.py` | Add ChangeList/2; preserve existing ChangeList/1 and all other compatible13 artifact schemas. No silent old shape change |
| `.../registry.py`, `__init__.py` | Register exact `/1` new keys and ChangeList/2 while retaining `/1`; export named types and error unions. No duplicate key alias silently changes a model |
| `.../api_routes.py`, `.../api.py` | Add proposed v2 route definitions and strict request/response/error/projection unions; existing v1 remains explicit legacy |
| `.../interfaces.py`, `.../tools.py` | New Task/Model/Artifact/Tool/Delivery Protocols and closed guarded v2 tool catalog. Legacy AgentRunner/ToolCaller stay demo-compatible; no production v2 dispatch to old generic tools |
| `docs/FORMAT_CHANGES.md` | Append approved P5-C1 migration/version/legacy denial with exact source/export manifest. This stage does not amend the frozen authoring pack |
| `scripts/export_schemas.py`, `scripts/export_openapi.py`, `scripts/gen_ts.mjs` | Inspect reuse; adapt only actual registry/route gaps. Export from Python, never hand-edit derivative bytes |
| `contracts/examples/`, `fixtures/plan5/`, `fakes/src/goldgraft_fakes/` | Valid computed synthetic example for each new record; negatives indexed; persistent control, scripted model, guarded tools, lifecycle and frontend projection fakes sharing exact schemas |

Existing exporter/example directory conventions must first be read; current `contracts/examples` is the actual example location. Fixture v2 examples do not overwrite old v1 answer keys. Every new object forbids extra properties and validates referenced payloads after authorised lookup. Schema generation alone cannot establish relationship/ACL or byte integrity; validators and accepting services enforce those with negative tests.

## Typed referenced WorkPackage payloads

These settle required contents from CODE_AND_ENVIRONMENT_HANDOFF without an opaque unvalidated JSON bag. Add `ComponentManifest/1={components:Component[]}`, `DependencyManifest/1={dependencies:Dependency[]}`, `ConfigurationManifest/1={entries:ConfigurationEntry[]}`, `RequiredFlowManifest/1={flows:RequiredFlow[]}`, `OmissionManifest/1={items:Omission[]}`, `UnresolvedInputs/1={items:Issue[]}`. All inherit case identity through resolved artifact descriptor; refs still validate same case.

```text
Component={node_id:Id,purpose:Id,source_snapshot_ref:Ref|null,
 build_context_ref:Ref|null,runtime_profile_ref:Ref,
 dependency_manifest_ref:Ref,configuration_manifest_ref:Ref,
 correspondence_evidence_refs:Ref[],controller_binding_refs:Ref[]}
Dependency={dependency_id:Id,component_ids:Id[],purpose:Id,
 access_mode:fixture|sandbox_broker|read_evidence|unavailable,
 authority_ref:Ref|null,test_identity_ref:Ref|null,limitation:str}
ConfigurationEntry={name:Id,kind:public_value|secret_reference,
 value:str|null,secret_ref:Ref|null,required:bool,evidence_refs:Ref[]}
RequiredFlow={flow_id:Id,payment_family:Id,scenario_refs:Ref[],
 required:bool,origin_routes:Ref[],acceptance_rule_ids:Id[],
 limitation:str|null}
Omission={component_id:Id,path:str|null,reason_code:Id,
 required_for_scope:bool,evidence_refs:Ref[]}
```

Exactly one value/secret_ref according to kind; no raw credential allowed even in `public_value`. Sources/required flows/typed omitted records cannot mark an essential node optional to bypass scope. Safe configuration hashes for low-entropy/sensitive values are keyed and never leak guessed values. Profile/seed/state-recipe/dependency refs use trusted versioned catalog entries, not model executable script text. Chunk record is `{upload_id,file_path,offset:Count,length:Positive,sha256:Digest,blob_ref:Ref}`; receipt `{upload_id,file_path,offset,length,sha256,received_at:Utc}`. Streaming limits:200MiB/project,20,000 files,20MiB/file,4MiB/chunk initially; oversize holds named scope, no silent truncation. File ranges cover exactly once, duplicate identical chunks idempotent, symlink/absolute/parent/path-collision rejected.

## Supplemental lifecycle records: exact fields

Canonical connection/lifecycle records retain the full fields/validation in CONNECTION_CONTROL_PROPOSAL and LIFECYCLE_INTERFACE_PROPOSALS, with normative atomic semantics. The formerly abbreviated IR records become these strict objects:

```text
TargetKey={provider_id,account_id,environment_id,resource_kind,resource_id:Id}
TargetReservation/1={reservation_id,case_id,run_id,action_plan_ref:Ref,
 target_keys:TargetKey[],resource_epochs:map[Id,Positive],
 lease_until:Utc,expected_version_refs:Ref[],unresolved_effect_refs:Ref[],
 state:held|reconciling|releasable|released}
EffectSlot={slot_id,operation:Id,target_key:TargetKey,
 effect_class:E0|E1|E2|E3,depends_on:Id[],
 artifact_digest:Digest|null,config_digest:Digest|null,state_plan_digest:Digest|null,
 trigger_digest:Digest,required_authority_refs:Ref[],required_controller_ids:Id[],
 expected_version_ref:Ref,cardinality:Positive,recovery_branch_ref:Ref|null}
ActionPlan/1={plan_id,case_id,run_id,generation:Positive,
 graph_digest,scope_digest,review_bundle_digest,policy_digest:Digest,
 slots:EffectSlot[],recovery_plan_ref:Ref,state_plan_ref:Ref,
 finalisation_plan_ref:Ref,exit_plan_ref:Ref,
 budget_ref:Ref,expires_at:Utc,plan_digest:Digest}
ApplyAuthority/1={authority_id,controller_id,delegate_id:Id|null,
 target_key:TargetKey,actions:Id[],role_evidence_refs:Ref[],
 grant_epoch:Positive,issued_at:Utc,expires_at:Utc,revoked_at:Utc|null}
ApprovalSet/1={approval_set_id,case_id,run_id,generation:Positive,
 plan_digest:Digest,required_controller_ids:Id[],approval_refs:Ref[],
 authority_epochs:map[Id,Positive],checked_at:Utc,
 state:complete|missing|stale|revoked}
StateCutover/1={cutover_id,case_id,run_id,generation:Positive,
 writer_inventory_ref:Ref,handler_inventory_ref:Ref,
 ingress_ref:Ref,origin_route_ref:Ref,admission_ref:Ref,
 drain_evidence_refs:Ref[],fence_epochs:map[Id,Positive],
 high_water_ref:Ref,export_manifest_ref:Ref,restore_manifest_ref:Ref,
 replay_manifest_ref:Ref,state_digest:Digest,schema_digest:Digest,
 pending_external_effect_refs:Ref[],evidence_refs:Ref[],
 outcome:prepared|fenced|exported|restored|replayed|verified|held|unknown}
ArtifactBuild/1={build_id,case_id,run_id,generation:Positive,
 source_snapshot_refs:Ref[],source_tree_digest:Digest,recipe_digest:Digest,
 dependency_digest:Digest,build_config_digest:Digest,
 platform:linux/amd64,oci_manifest_digest:str,export_tar_digest:Digest,
 layer_digests:str[],runtime_profile_digest:Digest,
 exact_image_test_refs:Ref[],leak_scan_refs:Ref[],provenance_ref:Ref,
 collector_identity_ref:Ref,authenticity_ref:Ref,
 outcome:built|tested|held|failed|unknown}
Asset={asset_id,kind:source|image|registry|runtime|config|state|credential|
       callback|origin_handler|grant|worker|copy|record|exit_executor,
 ownership:merchant|shared_service|exclusive_run,
 target_key:TargetKey,required_for_operation:bool,
 active_reference_refs:Ref[],desired:keep|deny_revoke|delete|retain_policy,
 authority_refs:Ref[],evidence_refs:Ref[]}
AssetManifest/1={manifest_id,case_id,run_id,assets:Asset[],
 final_artifact_digest:str,final_config_digest:Digest,
 legacy_obligations_ref:Ref,manifest_digest:Digest}
FinalisationPlan/1={finalisation_id,case_id,run_id,generation:Positive,
 desired_asset_manifest_ref:Ref,dependency_check_refs:Ref[],
 candidate_change_required:bool,final_candidate_ref:Ref|null,
 validation_request_refs:Ref[],required_action_slot_ids:Id[],
 independence_criteria_refs:Ref[],plan_digest:Digest}
ExitCheckPlan/1={exit_plan_id,case_id,run_id,generation:Positive,
 reservation_ref:Ref,executor_identity_ref:Ref,trusted_code_digest:Digest,
 final_artifact_digest:str,final_config_digest:Digest,state_digest:Digest,
 criteria_refs:Ref[],allowed_restart_count:Positive,
 recovery_plan_ref:Ref,budget_ref:Ref,deadline:Utc,
 private_evidence_destination_ref:Ref,evidence_read_authority_ref:Ref,
 failure_route_ref:Ref,authority_refs:Ref[],plan_digest:Digest}
```

Grouped bare names are Id unless otherwise typed on that line; this notation is specification shorthand, not executable schema. `TargetKey` fields all required/nonempty; `account/environment` use approved explicit canonical logical identity where provider has no such level, never wildcard. Target-key encoding is canonical structured serialization, not delimiter concatenation. Epoch maps key validated canonical target IDs; same physical target across cases resolves identically. Source/OCI digests are not interchangeable: OCI digest validates algorithm:`sha256` plus64hex; export digest plain SHA256. `ArtifactBuild.oci_manifest_digest` and Asset/Exit final artifact use the same OCI validator. EffectSlot.cardinality is exactly1 and ExitCheckPlan.allowed_restart_count exactly1 in first profile; other values deny despite Positive transport type. Every ref above resolves and validates schema/authority/current subject, not just shape. Slot DAG acyclic/unique/dependencies exist; reservation cannot release with unresolved effects. Export/restore/replay inventories include counts/offsets/invariants/H per qualified VJ recipe; a digest alone is insufficient. FinalisationPlan final_candidate_ref is required when change_required; pending preparation cannot authorize an apply. ActionPlan's finalisation_plan_ref resolves this type; exact exit plan refers the currently approved final candidate, and changes require a replacement plan/approval set.

`ChangeList/2={id,graft_id,producer:Producer,created_at:Utc,provenance:git|snapshot,branch:str|null,baseline_snapshot_ref:Ref,candidate_snapshot_ref:Ref,patch_digest:Digest,changes:[{plan_item_ids:Id[],summary:str,commit:str|null}],open_item_ids:Id[]}`. Git requires real branch and provider-validated commits; snapshot requires branch/commits null and collector-bound snapshots. Do not force fabricated commit strings into ChangeList/1.

`TaskContext/1={task_ref:Ref,case_id,run_id,generation:Positive,lease_epoch:Positive,role:Role,operation:Operation,input_refs:Ref[],expected_subject:Digest,policy_ref:Ref,prompt_ref:Ref,allowed_tool_ids:Id[],expected_schemas:Id[],budget_ref:Ref,deadline:Utc,checkpoint_ref:Ref|null}`. No new raw source/key/customer data in TaskContext. Task/Model/Tool declarations from communication spec and delivery records are incorporated exactly, not duplicated with different fields.

## Browser projections and request contracts

`ActionStatusView/1={status:WorkStatus,acceptance_ref:Ref|null}`. Acceptance_ref nonnull only for real committed acceptance, immutable on replay.

`ResourceSummary={node_id,label,provider,environment:Id,controller_state:unbound|waiting|approved|revoked|unknown,read_scope_text:str,source_snapshot_ref:Ref|null,check_refs:Ref[],permitted_actions:Id[]}`. Server projection must be recipient-authorised; no source/repo findings before that boundary. Display label is escaped text.

`ProcessingDisclosure/1={policy_digest:Digest,recipients:[{name:str,purpose:str,region_text:str,retention_text:str,terms_evidence_refs:Ref[]}],copy_scope:str,limits:str[],checked_at:Utc,status:qualified|missing|stale}`. Only qualified actual config yields Start; labels are not invented promises.

`CaseView/1={case:ConnectionCase,state_version:Positive,last_event_seq:Count,resources:ResourceSummary[],processing:ProcessingDisclosure|null,readiness:ConnectionReadiness|null,pending_action_id:Id|null,action:ActionStatusView|null,lifecycle:LifecycleRun|null,delivery_ref:Ref|null,required_actions:[{kind:Id,resource_ids:Id[],enabled:bool,reason_code:Id|null}],evidence_class:Id,checked_at:Utc}`. Coherent backend projection, current ACL and strict evidence-class enum from ArtifactDescriptor. Required actions are hints, not permission tokens. CaseList/1 contains `{items:[{case_id,shop_url,status:ConnectionCase.status,updated_at:Utc}],next_cursor:Id|null}`; limit1–50, opaque cursor bound actor/filter.

`DraftCase/1={draft_id:Id,shop_url:str,created_at:Utc,expires_at:Utc,continuation_ref:Ref,state:unclaimed|claimed|expired}`. Anonymous draft has no requester/private findings/provider grants. Server issues a random HttpOnly/Secure scoped draft-capability cookie, CSRF protection and bounded rate/size/TTL; URL/ID possession alone cannot claim it. After official sign-in, one atomic ClaimDraft requires current authenticated session plus draft capability and bound continuation. It assigns requester and returns ConnectionCase/1 with stable case_id equal to draft_id; repeats by same identity return same case, other identity without authorised claim is denied. No source/model/execution/payment work occurs in draft. Expired or lost capability returns only bounded restart/claim recovery, never private findings. This settles AC02 without putting fake requester IDs in ConnectionCase.

`ProviderIntent/1={intent_id,case_id,provider_id,resource_id:Id|null,purpose:read_connect|apply_connect,continuation_ref:Ref,redirect_url:str,expires_at:Utc}`; redirect must be qualified provider allowlist/backend-constructed, return bound state/nonce/PKCE as provider requires. `ControllerInvitation/1={invitation_id,case_id,resource_ids:Id[],requester_id,recipient_hint:str|null,copy_url:str,expires_at:Utc,status:pending|approved|denied|expired}`; no automatic email/message.

`CaseEvent/1={event_id,case_id,sequence:Positive,state_version:Positive,kind:case_changed|readiness_changed|work_changed|lifecycle_changed|delivery_changed|access_changed,payload_ref:Ref,payload_digest:Digest,occurred_at:Utc}`. Event payload is authorised safe projection or notification to refetch; never arbitrary full ledger payload sent to browser. Replay cursor is not identity/authority.

`PrivateReviewView/1={bundle:ReviewBundle,plan:ActionPlan,approval_set:ApprovalSet|null,evidence_summary_refs:Ref[],processing:ProcessingDisclosure,missing:Issue[]}`; same-case scoped reviewer/controller only. `PublicProofView/1={public_id,scope_text:str,evidence_class:Id,summary_metrics:[{name:str,value:str,evidence_ref:Ref}],integrity:verified|unverified|invalid|unknown,limitations:str[],checked_at:Utc}`; all refs public-projection identifiers only, no private resolvable artifact refs. Integrity status cannot set merchant lifecycle.

New request definitions: CreateDraft/CreateCase `{shop_url:str}`; ClaimDraft `{continuation_ref:Ref}`; CreateProviderIntent `{provider_id:Id,resource_id:Id|null,purpose:read_connect|apply_connect}`; CreateInvitation `{resource_ids:Id[],recipient_hint:str|null}`; CreateActionIntent `{readiness_id:Id,readiness_digest:Digest}`; StartWorkRequest canonical; CancelWorkRequest `{cancel_id:Id}` (server derives requester); ResumeRunRequest `{expected_state_version:Positive,scope_digest:Digest}`; IssueApplyApproval `{plan_ref:Ref,plan_digest:Digest,reviewed_bundle_digest:Digest}` (server derives controller/actions). CreateUploadRequest `{manifest:ManifestEntry[],expected_manifest_digest:Digest,expected_total_bytes:Count,binding_epochs:map[Id,Positive]}`; FinaliseUploadRequest `{expected_manifest_digest:Digest}`; CancelUploadRequest `{}`. ChunkUploadRequest is multipart/form-data with metadata `{file_path:str,offset:Count,length:Positive,sha256:Digest}` and one bounded binary data part whose length/digest match. Server derives upload_id from the scoped path and stores blob_ref after durable reception; the browser cannot submit a blob_ref or server filepath. Every request rejects extra fields.

## Proposed v2 routes and errors

The exact proposed methods/paths below are SI01 generator inputs; FRONTEND_SPEC uses abbreviated paths for readability only. All case-scoped IDs are bound to current actor/case. Service-only WorkerOperation endpoint stays `/v2/worker-operations`; Task/Model/Tool/Delivery are service Protocols, not browser authority endpoints. Backend provider callback/credential custody endpoints are GU adapter implementation surfaces and remain provider-qualified; no route guess grants access.

| Method and exact proposed path | Request → response |
|---|---|
| POST `/v2/connection-drafts` | CreateDraft → DraftCase/1; anonymous draft capability/CSRF/rate-limit exception, no private findings |
| POST `/v2/connection-drafts/{draft_id}/claim` | ClaimDraft → ConnectionCase/1; session + capability + continuation |
| POST `/v2/connection-cases` | CreateCase → ConnectionCase/1; already authenticated new-case path |
| GET `/v2/connection-cases` | cursor/limit → CaseList/1 |
| GET `/v2/connection-cases/{case_id}` | none → ConnectionCase/1 |
| GET `/v2/connection-cases/{case_id}/view` | none → CaseView/1 |
| POST `/v2/connection-cases/{case_id}/provider-intents` | CreateProviderIntent → ProviderIntent/1 |
| POST `/v2/connection-cases/{case_id}/invitations` | CreateInvitation → ControllerInvitation/1 |
| POST `/v2/connection-cases/{case_id}/source-uploads` | CreateUploadRequest → UploadSession/1 |
| GET `/v2/connection-cases/{case_id}/source-uploads/{upload_id}` | none → UploadSession/1 |
| POST `/v2/connection-cases/{case_id}/source-uploads/{upload_id}/chunks` | ChunkUploadRequest → ChunkReceipt/1 |
| POST `/v2/connection-cases/{case_id}/source-uploads/{upload_id}/finalise` | FinaliseUploadRequest → UploadSession/1 with final snapshot ref |
| POST `/v2/connection-cases/{case_id}/source-uploads/{upload_id}/cancel` | CancelUploadRequest → UploadSession/1 |
| POST `/v2/connection-cases/{case_id}/action-intents` | CreateActionIntent → ActionIntent/1 |
| POST `/v2/connection-cases/{case_id}/actions` | StartWorkRequest → WorkAcceptance/1 or typed cancellation/problem outcome |
| GET `/v2/connection-cases/{case_id}/actions/{action_id}` | none → ActionStatusView/1 |
| POST `/v2/connection-cases/{case_id}/actions/{action_id}/cancellation` | CancelWorkRequest → WorkCancellation/1 |
| POST `/v2/connection-cases/{case_id}/lifecycle-runs/{run_id}/resume` | ResumeRunRequest → LifecycleRun/1 |
| GET `/v2/connection-cases/{case_id}/review-bundles/{bundle_id}` | none → PrivateReviewView/1 |
| POST `/v2/connection-cases/{case_id}/apply-approvals` | IssueApplyApproval → ApplyApproval/1 |
| GET `/v2/connection-cases/{case_id}/events` | optional after:Count + Last-Event-ID → CaseEvent/1 SSE |
| GET `/v2/public-proof/{public_id}` | none → PublicProofView/1; Check is refetch only |
| POST `/v2/worker-operations` | WorkerOperation/1 → collector acceptance; service identity only |

Define ChunkReceipt/1 with the receipt fields above. Create receives the bounded inline manifest, validates paths/count/bytes/digest/epochs, stages it in private custody and commits UploadSession with its server-issued expected_manifest_ref. It does not need a pre-existing browser-minted ref or fetch a user URL. Chunk request produces the internal Chunk record only after validated durable data receipt. Finalise rechecks full coverage/current grants and computes the SourceSnapshot; no arbitrary blob-reference trust boundary.

Success codes: case/draft/intents/upload creation201; claim/status/view200; Start202 only after immutable acceptance commit; cancellation202 intent with current WorkCancellation; resume202 accepted request/current LifecycleRun; apply approval201. Chunk/finalise return200 on same-content replay. Mutations require Idempotency-Key and CSRF/current session where browser-facing, except bounded anonymous draft uses its own capability/CSRF protections. Same key/different body or stale CAS version409; stale readiness/scope412 (preserves reviewed connection semantics); expired410 where nonenumerating policy permits; unsupported422; unauthorised401/403 or generic unavailable404; rate limited429 with bounded retry hint; service unavailable503. Unknown submitted mutation is queried/reconciled by original ID, never returned as certain rejection. `P5Problem/1` extends the current RFC7807 Problem fields `{type:str,title:str,status:strict_int400..599,detail:str|null,instance:str|null}` with `{code:Id,request_id:Id,reason_code:Id,retry:never|status_only|safe_read|reauthorise,recovery_action:Id|null,evidence_refs:Ref[]}`. It is a new strict shape, not silent widening of the legacy class. HTTP status equals payload status; details/instance/evidence cannot disclose private or secret data. ProblemBanner reads core fields and optional Plan5 extensions through a typed adapter.

## Fixture and migration matrix

Fixtures under `fixtures/plan5/{connection,agents,delivery,frontend}/` and `index.json` include each record example and negative variant. Compute all content hashes/digests from synthetic payloads during fixture construction; mark fake authenticity/provenance explicitly. Examples with64 zeroes must never be interpreted as validated evidence. No raw live source or secret values. Fixture catalogs list scenario, owner, expected contract error/state, input refs and evidence class.

Retain legacy v1 tests/examples unchanged except verified fixes. New service mode denies legacy Start/connect/old tool/catalog/lane paths from entering v2 lifecycle; legacy demo responses remain labelled. Existing `/1` certificate Git/workflow shape stays legacy actual-Git; non-Git/private review uses new exact projections, no fabricated workflow identity. `Stage/1`/`JobKind/1` are not widened to new lifecycle enums. Compatible current money/proof payloads remain reused within bound descriptors.

SI01 construction checks (future): strict validation/relationship negatives, registry/export parity, TS type checks, OpenAPI routes/idempotency/SSE/security distinctions, fake conformance, current legacy regressions and denied bypasses. Run Python exporters→TS/OpenAPI generator→`npm run check:types`→`sh scripts/check_generated.sh` only in authorised build workspace after dependencies approved. Preserve generated references elsewhere. No schema/export generation or product tests have run now.
