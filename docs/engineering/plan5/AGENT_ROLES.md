# Thirteen exclusive role charters

Proposed charters, not implemented agents. Exact names verified in `contracts/.../tools.py:AGENTS`, `interfaces.py`, old design06 and fake OUTPUTS. Keep name compatibility, but **do not treat the old tool allowlist or producer fields as current service authority**. Simon/Nessie are unverified, unused transcriptions. No thirteenth/fourteenth identity is inferred.

Every role receives the same validated TaskContext: case/run/task/generation, role and prompt versions, immutable input refs/digests, current operation, permitted outputs/tools, policy/budget/deadline and prior checkpoint. Context lookup and all tools pass through the guarded ports. Every role returns AgentResult/1 referencing validated artifacts or a typed hold/unknown/failure. The backend authenticates producer attribution; payload text cannot choose another role's identity. Model proposals and collector-observed records are distinguishable.

Common denial: no grant minting, private cross-case reads, production credential values, arbitrary network/control-plane shell, direct PayPal/host/source publication, signing, unapproved financial request or cleanup. Stop on revoked/stale authority, missing mandatory input, policy/custody/budget expiry or unknown effects. Do not dilute required flows to obtain a pass. Common role tests include wrong-case ref, denied tool, wrong output owner and stale generation. Named additional cases below are planned in the [test pack](COMPONENT_TEST_PLAN.md).

## 1. Gardener — plan adviser

- Exclusive job: propose bounded task decomposition/order for the admitted sandbox programme and explain a hold; deterministic scheduler makes all assignments and transitions.
- Inputs/context: WorkPackage scope, role/operation catalog, committed task/proof summaries, dependency and budget status. No unrestricted raw source by default.
- Output/ownership: PlanProposal/1; optional explanation. `Assignment/1`/`LaneChange/1` survive only as legacy demo projections; no NO-CODE/NO-RUNTIME path may yield full completion.
- Tools: scoped task/status/artifact-summary reads. No task insertion, stage change or other role's tools.
- Dependencies: current acceptance + authenticated baseline verification before sandbox graph. Completion: validated acyclic allowed graph within32 nodes, or specific blocked requirement. Repair: one plan correction; invalid repeat holds.
- Test: `test_plan_cannot_add_deploy_or_cycle`; scheduler must progress without asking Gardener or a human to approve each next task.

## 2. Surveyor — source/payment inventory

- Exclusive job: identify supported PayPal touchpoints and required component/flow gaps in the pinned authorised source. This is deeper post-Start analysis; pre-Start static readiness belongs GU acquisition/readiness.
- Inputs: package manifests, redacted source slices, qualified public-site/account evidence where already authorised, snapshot/provenance.
- Output: RootMap/1 draft plus issue/evidence refs; trusted collector binds its source subject. Coverage omissions remain explicit.
- Tools: `source.read`, `analysis.matches`, qualified `evidence.read`. A source lens cannot itself crawl arbitrary URLs or call transaction APIs.
- Dependencies: acceptance/first-operation. Completion: each required lens observed or marked missing; required missing lens blocks downstream completeness. No mutation.
- Test: `test_survey_injection_cannot_fetch_metadata`; wrong-source snapshot and missing backend cannot produce complete inventory.

## 3. Builder — reproducible runtime and driver plan

- Exclusive job: propose the pinned build/runtime/driver recipe and diagnose reproducibility failures. It does not execute scenario economics or manufacture build evidence.
- Inputs: RootMap, VJ01 qualified recipe/catalog, dependency/config manifests, baseline or exact candidate snapshot.
- Output: ExecutionProposal/1 for `build_baseline`/`build_candidate` and driver validation. Collector/runner supply observed RunnableShop/1, Driver/1 and ArtifactBuild/1 refs; model cannot invent an image digest.
- Tools: recipe/dependency catalog read and bounded `execution.request`/`execution.status`. Guest executable commands are fixed recipe inputs validated by runner; no host Docker socket, registry write or arbitrary tunnel.
- Dependencies: Surveyor; candidate build also requires Grafter snapshot. Completion: observed reproducible runtime and driver checks on exact subject, or diagnosable hold. Three fixture runs do not prove all flows.
- Test: `test_builder_cannot_publish_or_select_unqualified_recipe`; candidate source-tested but different-image result is rejected.

## 4. Explorer — scenario execution planner

- Exclusive job: request and inspect required OLD/OLD_TWIN/NEW scenario runs, identify unreachable edges and seek missing trace evidence.
- Inputs: baseline runs consume the required-flow/scenario inventory and approved Driver, pinned runtime/seed identities and prior captures. Candidate runs additionally consume the final Scribe Contract. A baseline Contract is not a prerequisite to discovering baseline observations.
- Output: ExecutionProposal/1 for `run_scenario`; validated capture refs in AgentResult. RawCapture is trusted recorder output; CMEL/1 mapping belongs Singhal's mapper. Explorer can reference these, never rewrite observed money.
- Tools: `execution.request`, `execution.status`, `evidence.read`. PayPal calls occur only through qualified runner/payment broker; no direct financial API credentials.
- Dependencies: Builder baseline; candidate requires rebuilt exact artifact. Completion: required runs evidenced or marked unavailable; unavailable required flow holds proof. Bounded sandbox actions need scope, not live permission.
- Test: `test_explorer_missing_capture_stays_unverified`; duplicate request retains identity and unknown capture cannot cause a second charge.

## 5. Scribe — business-rule synthesis

- Exclusive job: relate code-grounded behaviour and observed OLD/OLD_TWIN events to the rule contract, preserving normative rule precedence and existing-defect distinctions.
- Inputs: source excerpts, RootMap, authenticated mapped events, immutable rule catalog and declared scope.
- Output: Contract/1 draft and TriangleRequest/1 for missing scenario/mutant support, with evidence provenance in the enclosing artifact descriptor.
- Tools: `source.read`, `evidence.read`, rule catalog read. No candidate/scenario edits or money-event rewriting.
- Dependencies: Explorer baseline. Completion: each rule has identified basis or explicit unverified evidence; source-only assertion cannot become BOTH by consensus. Normative failures cannot be waived.
- Test: `test_scribe_cannot_relax_normative_rule`; a defect in OLD is not automatically an accepted regression in NEW.

## 6. Architect — grounded change plan

- Exclusive job: select necessary payment-upgrade changes and allowed deltas; separate required payment work from unrelated rewrites.
- Inputs: RootMap, Contract, qualified API/SDK/docs versions, applicable VJ recipe metadata and missing-scope report.
- Output: TargetPlan/1 draft with exact touchpoint→change/evidence/verification links. No apply plan authority.
- Tools: `docs.lookup` through pinned trusted fetch/catalog, `recipe.lookup`, dependency/API symbol evidence. Returned docs remain untrusted data.
- Dependencies: Scribe. Completion: every required touchpoint grounded or explicit hold; no invented SDK operation or silent account migration.
- Test: `test_architect_unknown_api_holds`; changing unrelated checkout/hosting scope requires explicit replan, not broadened tool access.

## 7. Grafter — sole candidate source writer

- Exclusive job: implement TargetPlan in isolated WORKING source and bounded repairs grounded in failing evidence.
- Inputs: immutable baseline, current candidate snapshot, TargetPlan, real installed API-symbol/dependency evidence, independent failure refs.
- Output: ChangeList/2 draft + collector-observed candidate snapshot/patch descriptor. Version2 explicitly distinguishes Git and snapshot provenance; version1 still requires branch/commit and is legacy/Git-only. Non-Git never invents branch/commit fields. Exact version2 is in SHARED_BOOTSTRAP_PLAN.
- Tools: scoped `source.read`, `candidate.patch`, qualified dependency/symbol lookup. Patch CAS binds expected tree and lease; only approved relative paths. No test expectation/normative-rule editing, remote push, host/deploy/payment scope.
- Dependencies: Architect and exclusive candidate-writer lease. Completion: exact patch/snapshot ready for independent build/test, not self-approved success. At most2 semantic repair rounds; repeated identical failure holds.
- Test: `test_grafter_only_writer_and_cas`; concurrent patch or path escape denied, every changed tree invalidates downstream approval.

## 8. Adversary — independent guards

- Exclusive job: derive scenario and mutation guards from Contract/required flows, independently of Grafter's self-report.
- Inputs: Contract/TargetPlan, immutable NEW snapshot, rule/mutation catalog, baseline defects, verified recorder observations.
- Output: ScenarioSet/1, MutantSet/1 and unguarded rule IDs. Each mutant executes in a separately owned disposable fork; no candidate edits.
- Tools: `source.read`, bounded scenario draft staging, `execution.request` for allowlisted scenario/mutation operations, mutation catalog read.
- Dependencies: Scribe; exact candidate for execution. Completion: every required rule guarded or explicitly unguarded; Singhal computes kill/equivalence verdicts. Agent cannot declare its mutation equivalent to remove a failing denominator.
- Test: `test_adversary_cannot_mutate_candidate_or_drop_required_guard`; wrong mutant subject does not earn coverage.

## 9. Healer — operational diagnosis adviser

- Exclusive job: explain observed operational anomalies and request a hold or a current-state recovery review. Deterministic guards can act without waiting for the model.
- Inputs: redacted live/state/callback evidence, deterministic HealDecision where compatible, exact effect/legacy/origin state.
- Output: HealNote/1 with evidence refs and recovery suggestion only. A request is not performed recovery.
- Tools: `status.read`, `evidence.read`, `safety.request_hold`. No route write, percent bump, money compensation, old-DB restore or direct cutback.
- Dependencies: qualified observation stage; disabled in an offline run except synthetic checks. Completion: bounded diagnosis/hold record; incident continues under GU supervisor if model absent.
- Test: `test_healer_no_blind_legacy_cutback`; incompatible current state remains held even if old code is available.

## 10. Librarian — optional quarantined learning

- Exclusive job: distil a reusable recipe/detection proposal after consented completed evidence; excluded from merchant success prerequisites.
- Inputs: private-source policy-approved, de-identified certified diff/guard metadata. No merchant raw code reuse without rights/processing approval.
- Output: Recipe/1 in QUARANTINE and DetectionRule/1 proposals, never ACTIVE promotion. No change to current run or its accepted tests.
- Tools: policy-filtered evidence read, `recipe.stage`, self-check request against independent non-origin fixture under separate budget.
- Dependencies: explicit learning permission and completion evidence; otherwise not scheduled and no hold of delivery. Completion: quarantined proposal or rejection; promotion is separate reviewed policy.
- Test: `test_librarian_no_cross_tenant_source_or_self_promotion`.

## 11. Herald — evidence-bound explanation

- Exclusive job: render concise private progress/review/result text from committed structured facts; deterministic fallback templates always exist.
- Inputs: authorised projection only, status/reason codes, approved numbers with ledger refs, retained/removed/pending asset summary.
- Output: HeraldText/1 draft. Code checks referenced numbers and allowed claim/status catalog. Current numeric validator alone cannot verify all prose claims.
- Tools: `status.read`, `evidence.summary`; no raw captures, state mutation or arbitrary publication. UI never derives authoritative status from Herald prose.
- Dependencies: any committed progress/result; optional model never blocks core operation. Completion: supported text or template fallback. Unknown remains unknown.
- Test: `test_herald_no_done_from_pr_or_unsigned_number`; public text excludes private IDs even if input draft includes them.

## 12. Orchard Analyst — optional authorised analytics

- Exclusive job: answer an authorised fleet aggregate question, outside per-merchant upgrade dispatch.
- Inputs: tenant/purpose-scoped aggregate projection with minimum disclosure controls; never arbitrary cross-tenant rows.
- Output: DashboardSpec/1 with evidence refs and approved metrics/grouping/filter keys. No computed improvement claims without data.
- Tools: `aggregate.read` with server-enforced ACL and bounded query catalog. No raw SQL, model-created data export or AG Studio agent with ambient fleet access.
- Dependencies: separate question/budget/profile; disabled in merchant critical path. Completion: grounded answer or explicitly unavailable data.
- Test: `test_orchard_cross_case_aggregate_denied`; invalid filter cannot widen scope.

## 13. Sentinel — audit adviser around mandatory code enforcement

- Exclusive job: review redacted audit anomalies, explain policy breaches and request a halt. Mandatory checks run before dispatch in code regardless of this role.
- Inputs: own authorised audit summaries, rejected tool/output fingerprints, redacted security events and current generation.
- Output: Alert/1 and safety hold request. Actual fencing/termination evidence comes from GU03/runner, never LLM `agent.halt` success text.
- Tools: `audit.summary`, `safety.request_hold`; no inspecting raw secrets/prompts across tenants or stopping unrelated targets.
- Dependencies: independent of candidate-writer context; optional reasoning, deterministic guard always on. Completion: bounded alert; code enforces no new effects immediately on valid Stop/revocation.
- Test: `test_sentinel_absence_does_not_disable_guards`; halt timeout remains termination-pending.

## Artifact namespace and duplication rule

`source/baseline` is collector-owned and immutable. `source/candidate` has one Grafter writer. `runtime/driver` is Builder plan plus trusted observation. `captures` is recorder-owned. `money-events` and `proof` are Singhal-owned. `rules` is Scribe draft plus normative validation. `scenarios/mutants` is Adversary draft plus disposable execution. `plan` is Architect/Gardener in distinct typed namespaces. `review/effects/exit` is trusted lifecycle service-owned. `text`, `learning-quarantine`, `aggregate-proposal`, `audit-alert` are exclusive Herald/Librarian/Orchard/Sentinel outputs.

No role finishes another role's task by producing that role's output schema. TaskControl checks the output-slot producer and exact input dependencies atomically. Failed role output is quarantined for scoped diagnostics; it never silently becomes trusted evidence or a successful lifecycle transition.
