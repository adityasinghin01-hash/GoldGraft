# Lifecycle interfaces — proposed, never current

Status: Plan3 engineering on paper, 6 November 2026. No implementation, account change, deployment, live payment/model/worker job or agent-internal design. CURRENT means inspected existing contract; all new lifecycle states/interfaces/modules below are PROPOSED. Vendor/account/runtime qualification gates remain open.

## Reuse current support accurately
CURRENT: JobSpec/JobResult with job kind, variants, secrets_ref, timeouts, runner_identity and artifact refs; Runner.run_job/fetch_capture; RawCapture/CMEL/Contract/TargetPlan/Verdict/ProofStrength; SwitchConfig; Certificate and existing API routes. These shapes neither prove complete authority nor contain full new lifecycle/recovery/exit concepts. Current Certificate Git/workflow fields do not cover local source/E2B transparently. Current Stage/JobKind must not be silently widened.

New formats below are proposals for shared Python registry/API versioning under Singh, followed by schemas/OpenAPI/TS/examples/fixtures/fakes/compatibility tests together. No generated file changes or executable schemas are produced now. Use Plan1 typed IDs/digests/UTC/case-authorised refs; forbid unknown fields, strict integers, evidence content hashes checked at read; money remains integer minor units+currency. Ref maps to authenticated same-tenant/case artifact, not arbitrary URL/network path.

## Proposed required records
```text
LifecycleRun/1 = {run_id, case_id, work_id, generation:positive_int,
 work_package_ref, work_package_digest, resource_graph_digest, scope_digest,
 stage:BASELINE_VERIFY|BASELINE_RUN|CANDIDATE_READY|VALIDATING|REVIEW_READY|
 AWAITING_APPLY|PUBLISHING|MERGING|DEPLOY_PREPARED|DEPLOYING|OBSERVING|
 FINALISING|EXITING|COMPLETE|HELD|FAILED_SAFE|INCIDENT_UNKNOWN,
 attempt:positive_int, evidence_refs:Ref[], active_effect_refs:Ref[], updated_at:Utc}
LifecycleWorkRequest/1 = {request_id, run_id, generation, operation_kind,
 package_ref, package_digest, input_artifact_refs:Ref[], expected_output_schema,
 policy_digest, runtime_profile_digest, authority_binding_epochs:map[Id,int],
 budget_ref, deadline:Utc, forbidden_effect_codes:Id[]}
LifecycleWorkResult/1 = {request_id, run_id, generation, worker_identity_ref,
 inputs_digest, outcome:completed|failed|blocked|unknown,
 source_unchanged:bool, output_artifact_refs:Ref[], evidence_refs:Ref[],
 completed_at:Utc, limitation_codes:Id[], authenticity_ref}
```
`operation_kind` registry is approved external lifecycle task (build-baseline/run-baseline/validate-candidate etc), never model-supplied arbitrary code authority. Result schema reference must be allowlisted for request. Validation checks actual observed hashes and current scope; source_unchanged self-report is not proof. Attempts/jobs do not reset custody deadlines or revive grants.

```text
ReviewBundle/1 = {bundle_id, case_id, run_id, work_package_digest,
 baseline_snapshot_refs:Ref[], candidate_snapshot_refs:Ref[], patch_digest,
 artifact_digest, effective_config_digest, scenario_result_refs:Ref[],
 domain_rule_result_refs:Ref[], security_result_refs:Ref[],
 unsupported_paths:Id[], missing_evidence_refs:Ref[],
 recovery_plan_ref, proposed_apply_plan_ref, bundle_digest, created_at:Utc}
ApplyApproval/1 = {approval_id, case_id, controller_id, action_group_id,
 authority_binding_epochs:map[Id,int], graph_digest, scope_digest,
 reviewed_bundle_digest, baseline_digest, candidate_digest, patch_digest,
 artifact_digest, config_digest, delivery_route:git_protected|direct_artifact, source_snapshot_digests:Digest[],
 source_head:Id|null, source_base:Id|null, publication_destination_refs:Ref[],
 trigger_chain_digest,
 target_resources:Id[], allowed_actions:Id[], state_plan_digest,
 recovery_plan_digest, policy_digest, issued_at:Utc, expires_at:Utc,
 generation:int, action_plan_digest, authority_refs:Ref[], revoked_at:Utc|null}
EffectIntent/1 = {effect_id, action_group_id, case_id, run_id, generation,
 actor_id, operation, resource_id, environment_id, request_digest,
 approval_set_id, plan_digest, slot_id, resource_epochs:map[Id,int],
 expected_version, effect_class:E0|E1|E2|E3|EU,
 provider_idempotency_ref:Ref|null, created_at:Utc,
 state:intended|submitted|acknowledged|observed|failed|unknown|compensated,
 provider_receipt_ref:Ref|null, reconciliation_ref:Ref|null}
```
IDs/source heads/base/tree/provider artifact identities use provider validators; local source has snapshot revisions, no fabricated Git commit. Request payload/credentials are not leaked in idempotency_ref. `allowed_actions` fixed approved catalog, not client-created tool list. Approval compares canonical digests including declared state/trigger/preconditions; stale controller/expiry/revocation/generation/action mismatch denies. E3 monetary compensation needs separate explicit financial authority, not apply/rollback approval reused.

```text
BaselineEvidence/1 = {run_id, package_digest, variant:OLD|OLD_TWIN,
 immutable_source_digest, runtime_digest, dependency_digest, seed_digest,
 scenario_results_ref, observed_defects_ref, actual_provider_evidence_ref,
 skipped_required:Id[], outcome:reproduced|reproduced_with_defects|failed|unknown}
DeploymentObservation/1 = {effect_id, case_id, provider, resource_id, environment_id,
 submitted_artifact_digest, observed_artifact_digest:null|Digest,
 observed_config_digest:null|Digest, provider_deploy_id,
 provider_status, current_runtime_evidence_refs:Ref[], checked_at:Utc,
 outcome:pending|verified|failed|unknown}
RecoveryPlan/1 = {plan_id, case_id, baseline_refs:Ref[], affected_effect_refs:Ref[],
 state_compatibility_ref, original_transaction_routes_ref,
 required_current_authority:Id[], reversible_effects:Id[],
 compensatable_effects:Id[], irreversible_effects:Id[], unknown_effects:Id[],
 chosen_route:code_cutback|config_cutback|forward_repair|safe_hold,
 restore_preconditions_ref, verification_case_refs:Ref[], plan_digest}
ExitManifest/1 = {exit_id, case_id, run_id,
 merchant_assets_ref, temporary_assets_ref, legacy_obligations_ref,
 persistent_runtime_evidence_refs:Ref[], post_denial_observation_refs:Ref[],
 cleanup_items:[{item_id, owner, required_for_exit:bool,
 state:preserved|local_denied|termination_pending|revocation_pending|
 deleted_active|backup_pending|held|exported_unrecallable|confirmed|unknown,
 evidence_refs:Ref[]}], outcome:complete|pending|failed_safe|unknown}
```
Asset/effect inventories and actual authority metadata are private, typed and resolved by authorised services. Full required cleanup can stay pending alongside a live-upgrade observation, but overall exit isn't complete. Long-tail merchant operational assets/credential references are preserved, not classified temporary because a job created them.

## Proposed service interfaces and durable ownership
Lifecycle.submit(request)->request_receipt (current scope and budget); Evidence.accept(result)->validated artifact refs (auth/fence/schema/content); Review.evaluate(bundle)->ready/partial/hold reasons (deterministic proof+scoped human review); Approval.issue(exact result/actions)->ApplyApproval (current controllers); Effect.prepare/execute/reconcile(effect_id)->EffectIntent state (trusted broker); Deployment.observe(effect_id)->DeploymentObservation; Recovery.plan(current effects)->RecoveryPlan; Exit.reconcile(exit_id)->ExitManifest.

Suggested additive service routes under /v2/connection-cases/{case_id}: /lifecycle-runs, /review-bundles, /apply-approvals, /effects/{effect_id}, /recovery-plans, /exit-manifests. These are proposed namespace responsibilities, not existing endpoints. Mutations use current Idempotency-Key convention; events use committed cursor and authorised projection. Browser cannot submit verified worker/provider receipts or arbitrary effects. Actual route/model signatures are delivered together in later contract bootstrap, not improvised by each piece.

Durable tables extend Plan1 with lifecycle_runs/requests/results, review_bundles, apply_approvals, effect_intents/observations, recovery_plans, deployment_observations, asset_ownership, legacy_obligations and exit_items. Tenant/case foreign keys and unique request/effect identities; one current generation per run; action-group lock orders cancellation/approval/effect prepare. Commit intent before external effect, record provider receipt separately, outbox reconciliation after crash. Never mutate or delete existing financial ledger facts to simulate rollback.

## Compatibility and migration
New Artifact registry formats can reuse current money/proof payloads where semantics fit; proposed new versions only where fields fundamentally change (e.g. private review/non-Git certificate). Do not forge GitHub workflow identity for E2B. Existing public certificate endpoint requires strict public projection; no public raw captures/provider transaction IDs/keys. Shared contract/bootstrap is Singh; Gupta consumes lifecycle mechanism contracts, Vijay shop/domain fixtures, Singhal proof result/projection semantics. No cross-piece imports.

## Route-specific publication consistency
Git source/destination requires current head/base/PR/protection and exact merge-tree checks. DirectArtifact requires merchant-owned private registry/source-bundle destination and separately authorised write/pull/config policy evidence; Git fields null and no merge stage. Neither source snapshot absence nor arbitrary null may bypass graph/authority/trigger/provenance checks. Stage graph is route-aware: direct_artifact goes from approved destination publishing to deploy_prepared, not a fake MERGING state. Registry/object webhook effects are included before first write. This extends proposed shared schemas only; no current fields changed.

## Plan4 material-correction authority
[ATOMIC_DELIVERY_PROTOCOLS.md](ATOMIC_DELIVERY_PROTOCOLS.md) is normative for bootstrap state transfer BEFORE first destructive prerequisite change, cross-case target reservations/shared-asset cleanup, exact deployable-image build/test/private publish, IPN unverified receipt→acknowledgement→validation ordering, independent per-resource apply authority/approval-set/per-effect-slot consumption and merchant-owned post-denial exit executor. It supersedes ambiguous earlier single-controller/global consumed_at/per-run-only-lock/post-revoke-self-restart wording. All mechanisms remain paper proposals; actual qualification is open.
