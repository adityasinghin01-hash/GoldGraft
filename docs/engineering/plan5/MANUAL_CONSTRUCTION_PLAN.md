# GoldGraft Phase5.3 manual construction implementation plan

> For agentic workers: execute the approved tasks in order with Aditya's guidance; use the applicable executing-plans workflow. This document is **not** an execution start. No implementation, installation, network/model/payment/worker/deploy job, commit or publication has run in Phase5.1/5.2.

**Goal:** Codex drives bounded agent-system and delivery construction in small explained steps under Aditya's direction; Antigravity builds the specified frontend. Aditya controls genuine decisions/access/approvals, rather than manually dispatching routine merchant-run tasks.

**Architecture:** Python3.12 policy/runtime over typed GU durable control/model/tool/delivery ports, independent SH evidence and VJ recipes. One control-state authority; no workflow platform or other-piece import. Offline persistent fakes prove own coordination only; real-model competence and real team/provider integration remain separately labelled checks.

**Tech stack:** existing uv/Python3.12/contracts/foundation/fakes, pytest/ruff; Node22/TypeScript5.9 tooling; supplied React18/Vite frontend stack. Exact dependencies/lockfiles inspected and approved at build preflight. No n8n/Redis/Temporal/LangGraph setup.

**Launch:** [Two-terminal workflow](TWO_TERMINAL_WORKFLOW.md) and its [Codex](CODEX_AGENTS_DELIVERY_START_PROMPT.txt)/[Antigravity](ANTIGRAVITY_FRONTEND_START_PROMPT.txt) prompts implement this plan's ownership/dependency order. Preparing prompts does not run B0 or create a worktree. When pasted, their explicit scoped start supersedes historical paper-only/deferred-internals wording without starting Plan6. Codex opens the existing repository first, creates the isolated build workspace, copies the reviewed local specs, completes/checks B1/B2 and emits frontend-ready before Antigravity starts. B3–B5 and AG1–AG6 may then proceed with disjoint writers and frozen shared inputs.

## Global constraints

- Explicit Phase5.3 start is required after this plan review. Plan6 remains separate.
- Preserve original dirty checkout, current team contributions, Desktop/personal/reference and secrets. No reset/clean/blanket stage/commit/push/merge.
- All piece imports are contracts/foundation plus own piece; no piece-to-piece imports. Dependency injection uses shared Protocols.
- Current Python owns actual wire; SI01 versions/fixtures/exports land together before new consumers.
- Ordinary tests are offline; no PayPal/GitHub/model/provider network. `live_` checks require named authority/data/cost scope; no billing assumed.
- Merchant same-site/host/accounts/data/required connections and no finishing homework; missing primitive holds before effects. No money undo/oldDB restore/unknown-effect retry.

## Construction map

```text
B0 preserve/preflight
  -> B1 SI01 models/routes/exports/examples
  -> B2 persistent task/model/tool/lifecycle stand-ins
  -> B3 bounded restart-safe agent vertical slice
  -> B4 thirteen role policies/prompts + graph collaboration/repair
  -> B5 delivery/recovery/exit coordinator
  -> B6 Antigravity frontend (can start after B1/B2 stable; terminal order stays B3→B5)
  -> B7 component/evaluation review and reproducible Plan5 handoff
  -> STOP. Plan6 only on explicit start.
```

## B0 — Preserve work and prepare an isolated build workspace

Files: read original AGENTS and all Plan5 specs; create future build-only workspace; no original-main modifications. Current observed remote main `da2b5f02d5559c510de6b3b9d81e58400bdf6c89`, proof branch `571393c563522dfd2e4d49afcfa080987e33b695`; these are dated pins, not commands to discard newer work.

- [ ] Read `git status --short --untracked-files=all`, `git worktree list`, `git ls-remote origin`; inspect actual new contribution sources. If refs changed, inspect relevant diff and update baseline before edits. Proof PR reuse is not automatic merge.
- [ ] Create verified byte backups/manifests for each intended edit and protected-file hashes. Read back and restore a fresh-path sample. Keep private audit outside publication paths.
- [ ] After explicit start, if the named branch/path is unused and the observed base is still accepted, create isolated checkout:

```sh
git worktree add -b plan5-build-20261106 /Users/aditya/dev/GoldGraft-plan5-build da2b5f02d5559c510de6b3b9d81e58400bdf6c89
```

- [ ] Copy only the reviewed `docs/engineering/plan5` pack and specifically reconciled entry docs into that checkout after content comparison; old tracked dirty files are not blanket copied or staged. If worktree/branch already exists, inspect it; do not delete/reset it.
- [ ] Inspect versions/lockfiles using `uv --version`, `python3.12 --version`, `node --version`, `npm --version` and existing manifests. Python must be3.12 and Node22. Missing tools/dependencies is an explicit setup action at this future step, not permission to upgrade accounts or use broad system installs.
- [ ] Only after dependency scope approval if needed, resolve exact lockfiles with existing uv/npm conventions. Keep no-network tests independent of provider account setup.

Expected result: isolated checkout, explicit baseline/team-diff decision and protected original hashes unchanged. Debug: missing Git object→read-only approved fetch; architecture/tool error→correct interpreter/tool path, never reset source. Safe stop: before any install/change; no accepted job exists.

## B1 — Implement SI01 as one coherent boundary change

Files: exact list in SHARED_BOOTSTRAP_PLAN. Tests: `contracts/tests/test_plan5_contracts.py`, `test_plan5_routes.py`, `test_plan5_compatibility.py`; examples under `contracts/examples`; generated files only through exporters.

- [ ] Implement strict primitives and typed records in dependency order: adapters/package → connection → lifecycle atomic records → agent runtime → projections/route registry. Add ChangeList/2 without altering /1. Resolve references via accepting service, not model-provided objects.
- [ ] Implement context-aware validators: same tenant/case/run/subject; output producer; exact plan/resource epochs/slots; version/digest semantics; valid DAG/uniqueness; optional-field conditions; no required-flow bypass. Implement closed Problem/retry/error enum.
- [ ] Create computed synthetic positive and negative examples before dependent consumers. Each negative has a precise expected error. Register all versions and update FORMAT_CHANGES in the same change.
- [ ] Inspect actual exporters. Generate derivatives and check them:

```sh
uv run --locked python scripts/export_schemas.py
node scripts/gen_ts.mjs
uv run --locked python scripts/export_openapi.py
npx --no-install openapi-typescript contracts/api/openapi.json -o contracts/ts/goldgraft-api.d.ts --silent
npm run check:types
uv run --locked pytest -q contracts/tests/test_plan5_contracts.py contracts/tests/test_plan5_routes.py contracts/tests/test_plan5_compatibility.py
sh scripts/check_generated.sh
```

Expected: schema/TS/OpenAPI/example version manifest agrees; negatives reject; legacy examples still validate; v2 cannot bypass through old Start/tools/lanes. Debug: a derivative mismatch is fixed in Python/registry/exporter, not by editing generated bytes; missing current fields do not become fake defaults. Safe stop: do not create new consumers until boundary checks pass.

## B2 — Build and inspect labelled counterpart stand-ins

Create `fakes/src/goldgraft_fakes/{task_control,model_broker,guarded_tools,lifecycle_control,case_views}.py`, shared `fixtures/plan5/index.json` and subdirectories. Add `fakes/tests/test_plan5_{task_control,brokers,lifecycle,views}.py`. Reuse existing fixture loader/ledger where correct; explicit version-aware example resolution replaces hardcoded `.1` lookup for new consumers, while legacy helper behaviour remains unchanged.

- [ ] TaskControl fake uses a local SQLite file, not only RAM. Implement shared seed/extend/claim/renew/checkpoint/tool/finish/wait/snapshot/cancel Protocols with real transaction/CAS/unique-key semantics and deterministic injected clock. State persists across constructing a new fake/runtime process.
- [ ] Scripted ModelPort emits known tool/final/blocked results and staged untrusted JSON; has persisted turn status/unknown usage scenarios. It never calls an SDK/network or pretends model competence.
- [ ] Guarded ToolPort validates the exact role/tool/arguments/current generation and produces labelled deterministic source/evidence/runtime results. Include submitted/unknown/stale observation paths, not just success.
- [ ] Lifecycle fake exposes DeliverySnapshot and authenticated synthetic artifact/approval/effect/state/exit records. Track requested operation counts and identities. It must never implement the Singh coordinator being tested.
- [ ] Case-view fake shares exact generated types/fixture IDs with frontend; model/provider “real” modes unavailable by default. Fake signatures are labelled as fake and cannot verify as real evidence.

```sh
uv run --locked pytest -q fakes/tests/test_plan5_task_control.py fakes/tests/test_plan5_brokers.py fakes/tests/test_plan5_lifecycle.py fakes/tests/test_plan5_views.py
```

Expected: process restart retains original task/turn/effect identity; repeated changed-body keys conflict; no-network tripwire passes; fake outputs validate same schemas. Debug: lost data→check file path/transaction commit, not create a new run; stale lease→refetch current generation. Safe stop: after fixture validation, no product worker/service runs.

## B3 — One autonomous task and restart-safe next step

Create `pieces/agents/{__init__,ports,context,tools,runtime,scheduler,cli}.py`, `pieces/agents/policies/offline.yaml`, `pieces/agents/tests/{test_context,test_tools,test_runtime,test_scheduler,test_restart}.py`.

Exact own interfaces:

```text
context.build_context(task:AgentTask,lease:TaskLease,artifacts:ArtifactPort)->TaskContext
tools.validate_invocation(task:AgentTask,invocation:ToolInvocation)->None|ControlError
runtime.run_task(lease:TaskLease,control:TaskControl,artifacts:ArtifactPort,
                 model:ModelPort,tools:ToolPort)->AgentResult
scheduler.tick(run_ref:Ref,now:Utc,ports:RuntimePorts)->SchedulerReport
RuntimePorts={control:TaskControl,artifacts:ArtifactPort,model:ModelPort,tools:ToolPort}
SchedulerReport={claimed:Count,completed:Count,waiting:Count,rejected:Count,run_version:Positive}
```

- [ ] Implement context bounding/provenance and guarded turn loop exactly from architecture. Stage model JSON untrusted; validate before descriptor creation. No raw provider SDK or merchant secrets in runtime.
- [ ] Implement deterministic readiness/claim policy; first two-task graph is synthetic Surveyor read→Herald status explanation. Start acceptance/BASELINE_READ are synthetic boundary preconditions, explicitly not generated by the agent.
- [ ] Implement CLI `status`, `run`, `cancel`, `resume` and `doctor` with `--mode offline` required/default and closed mode enum. CLI is developer assembly/diagnosis, not routine per-agent dispatch. Service mode refuses until an approved actual port profile is supplied.
- [ ] Persist task/turn/invocation IDs, checkpoints and results at exact port boundaries. Crash hooks are test-only; no production environment variable may secretly activate fixture responses.

Future commands from isolated root:

```sh
uv run --locked python -m pieces.agents.cli doctor --mode offline
uv run --locked python -m pieces.agents.cli run --mode offline --fixture two_task_read --state-file /private/tmp/goldgraft-plan5-demo.sqlite
uv run --locked python -m pieces.agents.cli status --mode offline --state-file /private/tmp/goldgraft-plan5-demo.sqlite
uv run --locked pytest -q pieces/agents/tests/test_context.py pieces/agents/tests/test_tools.py pieces/agents/tests/test_runtime.py pieces/agents/tests/test_scheduler.py pieces/agents/tests/test_restart.py
```

Expected: one command advances two tasks without human dispatch; new process recovers the same run/status; fake artifacts remain scripted. Unknown tool/model state holds and is inspectable; stale writer cannot complete. Debug: `held` displays exact reason/owner/input; `unknown` inspects original invocation/turn, not retries a fresh ID; no-progress checks due wake/lease/version. Safe stop: CLI cancel records intent/awaits fake termination, then status confirms; no effect on merchant resources.

## B4 — Complete role policies and bounded collaboration

Create `pieces/agents/{roles,graph,review,supervision}.py`, `pieces/agents/prompts/{gardener,surveyor,builder,explorer,scribe,architect,grafter,adversary,healer,librarian,herald,orchard_analyst,sentinel}.md`, service policy template with no secrets and tests `test_roles.py`, `test_graph.py`, `test_collaboration.py`, `test_repair_stop.py`.

- [ ] `roles.ROLE_POLICIES` maps exact13 names to exclusive output schemas, tools, prompt refs and task-operation catalog. Prompt text is advisory; code enforces same catalog. Retain old fake compatibility through explicit legacy adapter, never broaden v2 tools.
- [ ] `graph.admit_plan(proposal,current_snapshot)->ValidatedPlan` checks current scope, DAG/count≤32, producers/subjects and one writer. Start graph `verify_package→survey→build_baseline→explore_baseline→scribe_draft`.
- [ ] Validate TriangleRequests; append at most4 bounded Explorer trace follow-ups and distinct `scribe_final`, then append the stages `architect→grafter→build_candidate→candidate_tests+adversary_guards→independent_proof→review_projection` incrementally, each only after its producer commits the exact input refs/subject. Do not prepopulate future tree/image digests. Core actual proof remains injected SH port; no imports of pieces/proof. OLD baseline has no circular Contract prerequisite. Librarian/Orchard are separate opt-in jobs, not merchant completion dependencies.
- [ ] `review.validate_result` checks schema/producer/content/subject/current generation and required evidence. `supervision.classify` yields safe-read retry, persisted wait, bounded repair, unknown reconciliation or terminal hold. Two repairs create new candidate attempts/affected downstream tasks; unchanged repeated failure halts. No plan-test weakening.
- [ ] Test each role against wrong-case/tool/output and its named charter case; test all-role registration and partial/collaborative path with persistent ports. A shared fixture cannot precompute the coordinator's final answer.

```sh
uv run --locked pytest -q pieces/agents/tests/test_roles.py pieces/agents/tests/test_graph.py pieces/agents/tests/test_collaboration.py pieces/agents/tests/test_repair_stop.py
uv run --locked python -m pieces.agents.cli run --mode offline --fixture full_sandbox_graph --state-file /private/tmp/goldgraft-plan5-graph.sqlite
```

Expected: valid DAG advances autonomously to review-ready; missing proof holds; repair changes invalidate prior evidence; role overlap/Stop/stale output fail closed. Debug: first unresolved dependency is named; no manual task dispatch needed to bypass wait. Safe stop: no new ready work after durable cancel, pending outcomes tracked.

## B5 — Build delivery coordination through teammate contracts

Create `pieces/agents/delivery/{__init__,resolve,coordinator,dispatch,report}.py`; tests `test_delivery_admission.py`, `test_delivery_sequence.py`, `test_delivery_unknown.py`, `test_delivery_state_exit.py`. Gupta owns actual mechanisms; this step never reconstructs provider SDKs, state migration, approval issuance or PayPal validation internals.

- [ ] `resolve.resolve_delivery(snapshot,artifacts)->ResolvedDeliveryView` validates exact trusted records/current subject and predicate evidence. No IO hidden inside reducer.
- [ ] `coordinator.advance_delivery(view)->DeliveryDecision` implements the route-aware sequence, state/bootstrap preconditions, finalisation sub-DAG and Q0–Q4. It produces only one allowed next request/wait/hold/incident/complete.
- [ ] `dispatch.execute_decision(decision,control,delivery_port)->receipt_or_wait` commits unique request/slot identity before submission; status/reconcile original identity after unknown, never issues replacement effect. GU rechecks authority atomically.
- [ ] `report.project_result` copies verified outcome and keep/remove/pending data; Herald cannot set outcome. Ordinary GoldGraft key use after Q1 must be absent; Q3 evidence read uses only disclosed temporary capability.
- [ ] Exercise fake successful Git and DirectArtifact paths, missing primitives, no-ID202, Stop after dispatch, changed final artifact, split approvals/shared reservations and independent-executor failure. Assert actual coordinator request counts/order and denied transitions.

```sh
uv run --locked pytest -q pieces/agents/tests/test_delivery_admission.py pieces/agents/tests/test_delivery_sequence.py pieces/agents/tests/test_delivery_unknown.py pieces/agents/tests/test_delivery_state_exit.py
uv run --locked python -m pieces.agents.cli run --mode offline --fixture delivery_unknown_no_id --state-file /private/tmp/goldgraft-plan5-delivery.sqlite
```

Expected: known current synthetic success reaches visibly synthetic completion; missing/unknown paths never do. Original effect/reservation persists; no source/host/payment SDK appears in Singh code. Safe stop: reconcile any fake submitted action, retain trace; real effects cannot exist in offline mode.

## B6 — Frontend in Antigravity

Files and exact step prompts: FRONTEND_SPEC and ANTIGRAVITY_HANDOFF. Start only after SI01+fixtures stable and explicit frontend build scope. Antigravity writes `pieces/web` using React18/Vite and generated versions, not Desktop/reference.

- [ ] Execute AG1–AG6 with per-step browser/state checks, preserving safe copy and deferring styling decision.
- [ ] Package scripts required: `typecheck`→`tsc --noEmit`, `test`→`vitest run`, `build`→`vite build`, `test:e2e`→`playwright test`, `dev`→`vite --host 127.0.0.1`. Dependencies/version lock created at build preflight, approved downloads if absent. Test/browser tools are not installed by this plan.
- [ ] Expected future commands:

```sh
npm --prefix pieces/web run typecheck
npm --prefix pieces/web run test
npm --prefix pieces/web run build
npm --prefix pieces/web run test:e2e
```

Expected: actual component/browser behavior against labelled fixtures, keyboard/focus and truthful state/copy verified. Debug: generated type mismatch→stop dependent screen and fix shared version first, no cast-to-any/guessed endpoint. Safe stop: local frontend only, no deploy/public link/account grant.

## B7 — Own component completion, evaluations and handoff

Codex owns BUILD_STATUS/FRONTEND_READY and the combined AS_BUILT_HANDOFF. Antigravity owns pieces/web and its FRONTEND_BUILD_REPORT. Before combined checks, Codex verifies that the frontend report and generated/fixture hashes match the current ready revision. Frontend outstanding or version mismatch is a precise pending dependency, not full Phase5.3 completion. Neither terminal edits the other piece or changes shared frozen inputs outside the documented pause/revision protocol.

- [ ] Run the exact relevant test groups from COMPONENT_TEST_PLAN, current legacy plugtests and generated checks in the isolated workspace; inspect all results. No repeated full suites after no further code changes unless unresolved failures justify it.
- [ ] Run bounded real-model component evaluation only under explicit model/source/cost profile approval. Actual agent competence cannot be marked passed from scripted turns; absent permission/profile leaves that evidence gate open, with offline control behavior reported separately.
- [ ] Inspect diffs/imports/secrets/protected hashes, redacted traces, pending jobs/effects and reproducibility instructions. Record actual source/contract/prompt/model/fixture hashes, results, limitations and any current teammate revisions.
- [ ] Prepare `docs/engineering/plan5/AS_BUILT_HANDOFF.md` during implementation only: exact setup/operating/debug commands, actual check results, missing counterpart/provider/model evidence and Plan6 replacement map. Do not create an as-built claim during this paper phase.
- [ ] Stop after reviewable own components/handoff. Ask no automatic permission to deploy/publish; Plan6 starts only when Aditya explicitly requests it.

No step ends with a commit/push or merchant setup chore. A dependency hold names what is missing and its owner; it is not permission to build a teammate's internals, relax safety or call external services.
