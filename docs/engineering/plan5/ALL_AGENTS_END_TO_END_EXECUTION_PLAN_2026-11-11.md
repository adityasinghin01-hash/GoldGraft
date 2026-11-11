# All 13 agents, integrations and handoff — execution plan

11 November 2026. **Phase 0 is PASS for zero-cost implementation; new paid
dispatch remains held for actual-context sizing.** See the
[Phase 0 report](phase_evidence/PHASE_0_2026-11-11.md).
Aditya requested a report after every phase and issue reports when needed.

**Latest ownership clarification from Aditya:** Claude owns frontend only.
Codex owns all non-frontend implementation, integrations, tests, review,
commits/pushes and handoff. Do not wait for a separate driver or teammate to
complete those packages. Reuse their verified work and finish remaining gaps
in the appropriate component, keeping piece/contract boundaries intact.

**Workspace override from Aditya:** work and integrate directly on `main` in
`/Users/aditya/dev/GoldGraft-plan5-build`; do not create another integration
branch. The current main merge is prepared without commit. The two obsolete
integration branch names were deleted locally and on GitHub; their checkout
files and the original dirty checkout are preserved. See
[workspace migration evidence](phase_evidence/MAIN_WORKSPACE_CHANGE_2026-11-11.json).
The previous driver-source-integration blocker is cleared at the workspace
level. Codex now owns final checks, commit and push under the latest assignment.

> For agentic workers: use the executing-plans workflow, sequentially, with no
> sub-agents. Finish and record each phase gate before starting its dependent
> phase. Inside Phase 4, finish one role fully before the next. Codex owns review,
> commits and pushes on main. No stash, force push or destructive reset.

**Goal:** Complete every non-frontend part of GoldGraft: all 13 real-model agents,
their relevant sponsor/tool integrations, an actual connected code-upgrade
workflow, independent proof, qualified delivery/recovery/exit, rigorous retesting
and a reproducible operating handoff.

**Architecture:** Retain the Python guarded runtime and deterministic scheduler.
Connect agent, backend/runner/domain and proof components through the current
shared contracts, with composition in `integration/`. Models propose and explain;
trusted services own source collection, execution, money, authority and proof.

**Tech stack:** Python 3.12, current contracts/foundation, FastAPI, pytest/Ruff,
Anthropic API through the existing metered gateway; existing qualified domain
recipes, runner and provider adapters. Preserve current Node/PHP tooling where
required by actual domain tests. No new orchestration framework is planned.

## 1. What the user means and what completion means

Aditya clarified that “all” means **every agent plus integration**, not a request
for a third model. Current model families are Haiku and Sonnet; `haiku8` is a
Haiku turn-limit profile. Frontend implementation belongs to Claude. Everything
the frontend consumes—API, authentication/access boundaries, durable events,
safe projections, run states, evidence and integration documentation—is in scope.

The resulting service must accept authorised submitted code, inspect it, select
a supported recipe, establish baseline behaviour, produce an isolated upgrade,
build/test the exact candidate, obtain independent proof, expose truthful review
and perform separately authorised qualified delivery and exit. It must not be
hardcoded to the original sample repository.

“Any code” is an intake requirement, not a promise that every language, host or
payment product can safely be transformed. Every submitted input receives an
explicit admitted profile or an evidence-backed hold. The first qualified
upgrade profile is the existing licensed plain-PHP, one-time-payment path.
Additional frameworks, hosts, recurring products and source routes become
supported only after their own baseline/build/payment/state/delivery tests pass.
No universal compatibility or maximum intelligence claim is an exit criterion.

**Utmost ceiling** means the highest *measured* useful capability within the
approved runtime, model, source, cost and tool bounds. Every role's largest
passing input and first unsupported/failing boundary must be published. A budget
or provider limit cannot be silently raised to improve the score.

### Three distinct completion gates

| Gate | Required result |
|---|---|
| Agent and API ready | All 13 use the real model API through the service, actual downstream consumers accept their outputs, and full graph correctness/fault tests pass. |
| Tool and delivery ready | Required sponsor integrations have actual scoped evidence; actual runner/domain/proof/provider boundaries pass; qualified delivery/recovery/exit works for the declared profile. |
| Final handoff complete | Frozen revision reproduces results, operating/recovery/ownership records are accepted, and no required effect, evidence, cleanup or support gate remains unresolved. |

Passing the first gate does not complete the other two. If a required account,
authority, counterpart or budget is absent, record **BLOCKED** with its owner and
exact prerequisite. Do not call the whole plan complete. Frontend completion is
reported separately by Claude and is not claimed by this plan.

## 2. Starting evidence and constraints

| Existing evidence | Reuse and limitation |
|---|---|
| All 13 roles evaluated with real models | Preserve cards, prompts, cases, failures and receipts; tools in those evaluations were scripted counterparts. |
| Final evaluation regression: 886 passed | Dated affected-suite result, not the current whole-repository count. |
| Combined sample: 13/13 | Actual Surveyor→Herald handoff plus eleven independent jobs; not a connected thirteen-role delivery graph. |
| Model spend: $3.353287/$10 | Last audited close; $6.646713 remaining then. Re-read the ledger before planning paid work. Per-role envelopes still apply. |
| Gupta PR #11 / Singhal PR #10 merged | Audited main `aee298f31b13a6a6c76d28845b43763b948add7b`; local agent commit `c9f9ee9`. Do not assume the local branch contains all teammate changes. |
| Main CI and fixture signing passed | Independent plugtests: 177 passed, one local PHP skip. Payment script dry-run failed; simulated provider success and unauthenticated callback verification are known gaps. |

Detailed evidence: [evaluation close](FINAL_AGENTS_REPORT_2026-11-11.md),
[teammate audit](TEAM_GITHUB_AUDIT_2026-11-11.md),
[completion levels](../work/DONE_AND_TEST_MATRIX.md).

Global constraints:

- Work in `/Users/aditya/dev/GoldGraft-plan5-build`; preserve dirty docs and all
  existing evidence. Never modify the original checkout, frozen fixtures or keys.
- Codex owns every non-frontend package, including the existing GU backend/runner,
  SH proof and VJ domain groundwork. Inspect and preserve those contributions,
  including open PRs, then finish gaps in their proper components. Claude owns
  `pieces/web` only; no non-frontend review/commit dependency is assigned to him.
- Pieces import only contracts/foundation across boundaries. Root composition
  may inject actual components; a piece must not import another piece to bypass
  its shared port. Do not build a second connector or scheduler.
- Current Python schemas and route registry own actual support. A missing shared
  shape requires `docs/FORMAT_CHANGES.md`, owner acceptance, a version bump where
  applicable, schemas/TS/OpenAPI, examples, fakes and compatibility tests together.
- Current outer runtime bounds: 12 turns, 24 tools, four reads per batch,
  32 tasks, four Scribe followups, two semantic repair rounds; stricter profile
  bounds win. Current model-admission ceilings are 24,000 input and 4,000 output
  tokens. This plan does not increase any cap.
- Never reset/edit/delete the cost ledger, replay an unknown request, release a
  hold, expand a grant or spend from the inactive $20 hard ceiling. Stop the
  affected lane on uncertainty; reconcile original identities through trusted
  observations. Keep money/state enforcement deterministic.
- Tests never call the network. Actual provider/model checks belong only to
  explicit `live_` scripts with bounded, scoped authority and cost accounting.
- Creating this plan makes no provider/payment/deploy/account/message action.
  Prior merchant/live-payment/publication prohibitions remain in force until
  the relevant exact operation is separately authorised. Prepare the complete
  reviewable artifact before that final approval step.

## 3. Phase order and phase record

Phase 0's initial BLOCKED finding is retained as dated evidence. Its scope and
zero-cost implementation gate now pass; a separate paid-dispatch gate remains
held until actual contexts can be sized. Exact paid costs depend on the Phase 1/2
adapters, so requiring them before building those adapters was circular.
This sequencing correction changes no cap, required case, denominator or label.
Existing qualifications above are inputs, not green checks for later gates.

| Phase | Deliverable and strict exit gate |
|---|---|
| 0 — Freeze scope | PASS for offline implementation: revisions, profiles, tools, corpus, limits and owners frozen; paid dispatch allowance remains zero until actual-context sizing passes. |
| 1 — Close counterpart gaps | Actual GU/VJ/SH inputs and accepted interfaces pass meaningful boundary tests; scripted paths cannot report actual success. |
| 2 — Connect API and models | Durable API-driven runtime with audited Haiku/Sonnet routing, terminal-failure escalation and no duplicate effects. |
| 3 — Qualify tool adapters | Every required non-frontend sponsor/tool path has verified scope, contract, real-use evidence and failure behaviour. |
| 4 — Finish all 13 roles | One role at a time: upgraded, offline-green, real-model repeated, actual output consumed, ceiling measured, audit/card complete. |
| 5 — Connect the whole graph | One submitted source subject flows through actual agent/backend/proof consumers; all 13 roles participate in their legitimate lifecycle branches. |
| 6 — Prove code-upgrade capability | Unseen admitted code upgrades correctly; baseline/candidate economics and unrelated behaviour pass independent checks. |
| 7 — Qualify delivery and exit | Exact approved artifact operates at the supported target; state/recovery, independence and cleanup evidence close. |
| 8 — Rerun acceptance | Full regression, fixed held-out corpus, fault/security/restart tests and actual sponsor paths pass on final bytes. |
| 9 — Freeze the handoff | API/client pack, operating instructions, limits, evidence, ownership and recovery drill independently reproduce. |
| 10 — Independent sign-off | Codex verifies frozen results with independent oracles/reproducible checks; no mandatory open gate, uncertain spend or hidden finishing task; Codex commits/pushes on main. |

After each phase create
`docs/engineering/plan5/phase_evidence/PHASE_<number>_2026-11-11.md` with
revision, scope, input/output subjects, checks and denominators, evidence paths,
cost, failures, owners and PASS/BLOCKED. Create `phase_evidence/` in Phase 0;
these report paths do not yet exist. Update BUILD_STATUS and private CODEX_OUT.
Do not change an expectation after seeing a result without disclosing the change
and retaining the original case/result. A changed dependency reopens its
downstream gates. Preparation in an independent lane may continue during a
blocker, but the dependent phase cannot be marked started or complete.

## 4. File and interface map

Paths marked **new** are proposed construction targets, not existing APIs.
Codex reconciles incoming teammate files on main; absence from the current local
branch is not proof they were never built. The named GU/SH/VJ specialists below
identify original package provenance; Codex is now the non-frontend delivery owner.

| Files | Responsibility / ownership |
|---|---|
| `contracts/src/goldgraft_contracts/{agent_runtime,connection_control,lifecycle,plan5_tools,api_routes}.py` | Existing shared records, protocols, allowed operations and routes; Singh owns accepted shared changes. |
| `pieces/agents/{ports,runtime,scheduler,graph,workflow,component,proof_gate,repair}.py` | Guarded execution, actual predecessor resolution, deterministic DAG/proof/repair policy; Codex. |
| `pieces/agents/component_agents/*.py`, `surveyor.py`, `herald.py`, `prompts/*.md`, `evals/*.py` | Role prompts, facts, bounded tools, independent scoring and role validation; Codex. |
| `pieces/backend/model_gateway/{component_port,broker,provider,profile,qualification,ledger}.py`; **new** `routing.py` | Existing trusted model path plus persistent route/escalation policy; Codex in model_gateway only. |
| **New** `integration/{agent_service,agent_ports,agent_artifacts,agent_tools,agent_models}.py` | Composition using actual GU ports, artifact/collector adapters, role-to-model binding and current API service views. No fake-backed production default. |
| **New** `pieces/agents/delivery.py`, `integration/delivery_service.py` | Pure delivery reducer plus external-port executor; consumes existing lifecycle contracts, not new deployment mechanisms. |
| `pieces/backend/connection/*`, `pieces/backend/lifecycle/*`, `pieces/backend/{app,payment_broker,callback_gateway,custody_broker,elastic_ingest,zapier_notifier}.py`, `providers/*`, `pieces/runner/*` | Gupta closes actual transport, durable control, isolation, execution, authority, delivery and state gaps. |
| `pieces/proof/*`; incoming `lifecycle_evidence.py`, `review_projection.py` | Singhal provides authenticated-input validation, independent proof/projection/certificate behaviour. |
| `pieces/shops/*`, `pieces/switch-libs/*`, licensed domain catalogs/recipes | Vijay supplies actual supported-domain build, scenario, callback, state and exit recipes. |
| `postman/GoldGraft_Collection.json`, environment template, `.github/workflows/ci.yml` | Shared reproducible API/fault checks and CI; no embedded secrets. |
| **New** `scripts/{check_agent_service,live_agent_service_eval,live_tool_qualification,live_delivery_qualification}.py` | Offline service check and separately scoped live model/tool/delivery qualification entry points. No live action by default. |
| **New** `pieces/agents/tests/{test_service_graph,test_model_escalation,test_delivery,test_service_faults}.py`, `plugtests/test_agent_service.py` | Actual counterpart composition, graph, routing, authority and fault tests; no network. |
| **New** `docs/engineering/plan5/{AGENT_SERVICE_HANDOFF,AGENT_CAPABILITY_CEILINGS,TOOL_QUALIFICATION_REGISTER,FINAL_SERVICE_ACCEPTANCE}_2026-11-11.md` | Operating handoff, measured limits, tools and final evidence; not yet generated. |

Current interface anchors, which implementations must satisfy:

```python
ModelPort.turn(request: ModelTurnRequest) -> ModelTurnResult
ModelPort.reconcile(turn_id: Id) -> ModelTurnStatus
ToolPort.invoke(invocation: ToolInvocation) -> ToolInvocation
ToolPort.reconcile(invocation_id: Id) -> ToolInvocation
ArtifactPort.resolve(ref: Ref, task_context: Ref) -> ArtifactDescriptor
ArtifactPort.stage(task_id: Id, schema: Id, payload_ref: Ref, subject: Digest) -> Ref
DeliveryPort.snapshot(run_ref: Ref) -> DeliverySnapshot
DeliveryPort.submit(decision: DeliveryDecision, request_id: Id) -> LifecycleWorkRequestReceipt
DeliveryPort.status(request_id: Id) -> LifecycleWorkResult | PendingResult
```

TaskControl uses its existing seed/extend/claim/load/renew/checkpoint/begin_tool/
observe_tool/finish/wait/snapshot/cancel protocol. RuntimeArtifacts adds trusted
admission/context/authenticity/authorisation support; production adapters must
implement those extensions, not merely the narrower ArtifactPort.

The new pure agent delivery function is planned as:
`advance_delivery(view: ResolvedDeliveryView) -> DeliveryDecision`.
The composition factory is planned as:
`build_agent_ports(*, control, artifacts, model, tools, clock) -> RuntimePorts`.
Injected objects must implement the existing runtime protocols. No new public
HTTP route or field is invented by these internal function names.

## Phase 0 — Freeze the executable scope

- [x] Record local/remote SHAs, dirty paths and prior reports. Under Aditya's
  later instruction, work directly on main and prepare the reviewed current-main
  merge without losing agent changes or documentation. Codex owns the final
  commit/push; no stash or temporary integration branches.
- [ ] Build a code-to-contract map for every selected route, tool and role. Mark
  each implementation `scripted`, `actual offline component` or `qualified
  external`. Seeded demo data must be explicitly demo-only.
- [ ] Freeze the first supported recipe and source/profile matrix: Git source
  and validated uploaded source, plain PHP one-time EC_NVP/IPN reference; declare
  required OLD/OLD_TWIN/NEW, refund, pending, return and callback obligations.
  Both source routes require actual collector provenance; neither is invented.
- [ ] Freeze a 20-case independent final service corpus, three repeats each:
  eight supported source/upgrade variations, four named model/repair paths,
  four authority/subject/privacy negatives and four restart/unknown/tool-fault
  paths. Specify expected outcomes before tuning. Model holds and infra holds
  have separate denominators. Retain original broader acceptance cases and
  report any unmapped case as open; this new corpus does not silently replace it.
- [ ] Freeze sponsor requirements using Section 7: eight targeted partners,
  two conditional assessments, plus core PayPal/E2B/custody/storage/source tools.
  AG/Bryntum UI implementation is Claude's; non-frontend producers are ours.
- [x] Re-read the cost ledger and envelopes; freeze zero-cost implementation
  allowance and record historical stress forecasts. Exact paid batch, ceiling
  probe and provider sizing is a mandatory gate before the first new paid run.
  Allocate within existing remaining authority. Record
  external quotas/credits/cost separately. If required evidence cannot fit,
  prepare an exact costed blocked request; never reduce a denominator secretly
  or treat this plan as a cap increase.

**Gate G0:** scope/registers/corpus, limits, ownership and zero-cost implementation
authority are frozen; each requirement has a precise acceptance assertion.
Existing receipts are preserved. Paid dispatch is a separately held lane until
actual-context feasibility and qualification pass; missing external authority
remains a visible blocked lane. This does not block building offline adapters.

## Phase 1 — Close and verify the actual counterpart boundaries

- [ ] Codex replaces fabricated verified/LIVE/build/publish responses with
  actual adapter results or explicit unqualified holds. Fix the broken payment
  script, upload bounds and callback authentication before any real exercise.
- [ ] Codex completes persistent case/controller/readiness/Start/Stop/lease/
  checkpoint/effect/reconciliation adapters; duplicate same-body writes return
  the same receipt, changed-body keys conflict, and restart retains state.
- [ ] Codex completes actual isolated source execution, pinned dependencies,
  runnable baseline/candidate/driver, independent captures and exact OCI/config
  provenance. A local content hash is not an observed container image.
- [ ] Codex completes normative domain fixtures, scenario/mutation coverage,
  origin/pending/refund handling and state/exit compatibility recipes. Unknown
  provider operations cannot be retried as a new financial action.
- [ ] Codex completes actual RawCapture→CMEL→verdict integration, exact-subject
  lifecycle review, recipient-safe views and certificate verifier inputs.
  Fixture-only evidence is ineligible for merchant certification.
- [ ] Run counterpart compatibility negatives: wrong case/run/generation,
  mixed tree/image/config, expired authority, stale fence, duplicate receipt,
  replayed callback, unknown effect, failed persistence and substituted evidence.
  Reproduce the audit's false-verification/false-LIVE cases as failing tests,
  then demonstrate corrected behaviour without network in ordinary tests.

**Gate G1:** actual offline components are compatible through accepted contracts;
all audit defects affecting the admitted path are fixed or that path is blocked.
Live external qualification belongs to Phase 3/7; no scripted result is labelled
external. Implement missing mechanisms in backend/runner/proof/domain components,
not inside the agent piece. External credentials/authority may block a qualified
path; the historical package author is not a reason to stop Codex's implementation.

## Phase 2 — Connect API-driven agents and Haiku/Sonnet policy

- [ ] Construct the new integration modules from the actual ports. Separate
  fixture mode from service mode; service mode refuses fake/scripted mandatory
  runtime dependencies. Do not change the old fixture run's evidence class.
- [ ] Wire the current case/source/readiness/Start/cancel/resume/status/review
  routes from `api_routes.py`, authenticated run/artifact access and durable SSE
  replay. Pre-Start read-only intake cannot execute submitted code, call models
  or run payments. Start is accepted durably before worker execution.
- [ ] Bind each admitted task to its scoped real ModelPort, ArtifactPort,
  ToolPort and TaskControl, retaining the distinct Surveyor/Herald adapters.
  Resolve role facts from trusted artifacts; facts never include the answer.
- [ ] Persist prompts/policies/models/SDK/profile versions, scoped routing and
  attempt lineage. Consume previous committed artifacts rather than sample()
  role inputs or synthetic expected outputs.
- [ ] Implement and test the escalation policy below; do not claim the existing
  pre-dispatch `route()` hooks already provide full runtime fallback.
- [ ] Exercise API start→first task→saved output→status→cancel/resume through
  actual storage, with killed workers, duplicate requests and expired leases.

### Exact model escalation policy

1. Preserve existing validated shape routes: complex Surveyor inputs, Gardener
   larger graphs, Architect, guard-generation Adversary and other documented
   routes may start on Sonnet. Other qualified shapes start on Haiku/haiku8.
2. A **named model failure** is a scored groundedness/reasoning/output failure
   after a terminal, attributable model response. Permit the existing single
   malformed correction within profile bounds. Persist the failure and input
   subject; never repeatedly reset an attempt until it passes.
3. After two terminal Haiku failures on the same named capability/shape, select
   the qualified Sonnet profile for the next bounded attempt. Already-established
   two-failure evidence may justify starting that shape on Sonnet. Obtain its
   signed grant/reservation before dispatch; tool/authority ceilings stay equal.
4. A denied tool, stale subject, revoked grant, unsupported recipe, real proof
   failure, missing data, budget exhaustion or unknown request is **not** a reason
   to evade the gate using Sonnet. Transport faults follow the existing bounded
   retry/reconciliation policy. Unknown model/tool effects halt dispatch.
5. Escalation retains the same logical task/input lineage, valid completed reads
   and existing effect identities. It never repeats a patch, charge, notification
   or deploy because the model changed. Record both models' costs and failures.
6. Stop each tuning line after two failed variants. If qualified Sonnet cannot
   complete the shape within bounds, publish its limit and hold safely. Do not
   add an unqualified third model or increase turns/context/budget implicitly.

Offline routing tests must cover Haiku success; first/second named failure;
Sonnet success; Sonnet failure; already-qualified Sonnet route; budget denied;
unknown turn; revoked authority; Stop during escalation; restart before/after
route commit; and no duplicate completed tool operation.

**Gate G2:** every role can be admitted through the service, routing decisions
are reproducible and budgeted, and model failure cannot bypass deterministic
checks. Full role quality and tool-equipped ceilings are closed in Phase 4.

## Phase 3 — Qualify the shared sponsor and other tool adapters

- [ ] Inventory already configured access through approved secret references;
  never print/copy/hash keys or webhook URLs. An installed plugin is not proof
  of account scope, credits, licence or permission to send private data.
- [ ] For every Section 7 entry record version, purpose, owner, permitted data,
  account/resource scope, licence, quota/cost, expiry/retention, exact tool mapping,
  outputs, failure behaviour and evidence class in TOOL_QUALIFICATION_REGISTER.
- [ ] Add adapter contract/failure tests with deterministic replay responses.
  Closed tool arguments and returned refs must preserve subject/access checks;
  remote text stays untrusted input. Never grant raw provider credentials to
  a model or let it choose arbitrary URLs/commands.
- [ ] Prepare exact bounded real-use scripts; execute only within existing
  explicit authority. Missing scope or credentials means a named blocked gate,
  not signup, hidden mocks or an unsolicited key request.
- [ ] Verify actual positive use, permission denial/revocation, timeout/quota,
  stale result, wrong subject and restart/reconciliation. Fetch the created
  artifact independently and consume it in its actual downstream role/service.
- [ ] Prove optional connector outage does not weaken proof, money or safety
  enforcement. Preserve termination and unknown outcomes as unknown until seen.

**Gate G3:** required non-frontend adapters are actually qualified; display-only
producer contracts are tested for Claude. Conditional sponsors have a precise
adopted/held/not-justified decision. A targeted required sponsor that is blocked
prevents a claim that all sponsor integration work is complete.

## Phase 4 — Upgrade and finish all 13 roles, sequentially

For **each** role, complete every step before the next:

1. Read actual role/consumer/tool contracts. Write red tests for a real gap, fix
   it, then run affected offline tests. Keep invariant review independent.
2. Attach only relevant Phase 3 qualified tools using allowlisted ports. Adjust
   role prompts/facts, tool schemas and provenance without giving expected answers.
3. Freeze at least five distinct paid development positive/judgment cases,
   three hostile pre-dispatch $0 cases, role-specific tool/subject failures and
   at least one separate held-out source/input. Do not tune on the held-out
   result; evaluate it only after selecting the fixed configuration. Preserve
   larger historical samples.
4. Run regression/lint/format/diff; refresh qualification after every code/case
   change; free dry run must match every case's expected outcome before paid work.
5. Run one paid pilot per development case, Haiku first except qualified shape
   routes; apply the explicit two-failure Sonnet rule. Then run three fresh
   repeats per development case on the selected fixed configuration and evaluate
   the separate held-out case three times without tuning. Report all misses and
   model/infra holds separately; a held-out failure opens a new disclosed revision
   and requires fresh independent held-out evidence.
6. Exercise the actual downstream consumer and reopen after process restart.
   A schema-valid output that is unused or rejected downstream is not complete.
7. Run the bounded ceiling ladder below; freeze the accepted supported ceiling.
   Audit ledger, receipt provenance, output use, privilege denial and cost.
8. Write a revised role card, capability-ceiling row, sponsor-use result and
   phase progress. Any required-case failure blocks that role gate until fixed
   and retested or the requested capability is explicitly revised; never silently
   remove a case or describe a historical miss as a universal reliability claim.

Development order below remains distinct from runtime dependencies:

| Order / role | Required actual work, tool upgrade and downstream gate |
|---|---|
| 1 Surveyor | Authorised varied source→exact locations/flows/RootMap. Qualified source/custody first; pinned APIMatic context only where relevant. Builder and graph consume real refs. Test computed/missing indicators, secret/path injection and source overflow. |
| 2 Herald | Committed run facts→grounded private/public text and optional permitted Zapier notification. Counts remain exact; missing/unknown stays visible. Delivery failure cannot mark the run complete. |
| 3 Sentinel | Actual scoped audit events→grounded Alert/hold request, optionally exact-subject Elastic retrieval. Deterministic fence/termination acts without the model. Never report termination from a hold request. |
| 4 Gardener | Current task/subject/dependency facts→admitted bounded DAG. GU scheduler owns dispatch. Bryntum consumes safe graph/events outside the role; no scheduling authority granted to display tools. |
| 5 Builder | Actual recipe/dependency/API context→baseline/candidate requests and independently observed image/driver provenance. APIMatic grounding plus qualified runner/E2B. Source, image and config must match. |
| 6 Explorer | Actual OLD/OLD_TWIN/NEW scenario requests→trusted recorder captures. Kernel browser evidence and Postman API checks complement independent payment evidence. No fabricated buyer approval or direct financial key. |
| 7 Scribe | Actual source/mapped observations/normative catalog→grounded Contract and bounded followups. Elastic may locate exact evidence; it cannot turn source-only into BOTH or waive money rules. |
| 8 Architect | Actual inventory/Contract→qualified SDK/API change plan. Pinned APIMatic symbols/examples must compile against the installed version. Existing Sonnet route retained. Unknown symbol/profile holds. |
| 9 Grafter | TargetPlan→actual isolated CAS patch and new source snapshot, rebuilt and independently checked. Use qualified symbols/catalog; no publishing. Explicitly resolve or retain the failed four-file ceiling; multi-task partitioning must prove final assembled-subject correctness. |
| 10 Adversary | Actual Contract/final candidate→independent scenario/mutation bundle in disposable forks. Kernel/Postman and rights-cleared Channel3 only when adopted. SH computes kill/equivalence; no editing required guards to improve scores. |
| 11 Healer | Actual scoped runtime/state/effect observations→diagnosis or review-required hold. Elastic diagnostics may help. GU performs any separately authorised recovery; Sonnet cannot authorise compensation or stale database rollback. |
| 12 Librarian | Explicit consent/rights→deidentified quarantine recipe and independent non-origin selfcheck. Qualified catalog/storage/signature checks; no automatic activation, customer-data transfer or learning budget use. Missing consent must hold. |
| 13 Orchard Analyst | Authorised safe aggregates→grounded aggregate explanation. Actual ACL/minimum-disclosure service and SH public projection; Claude's AG views consume it. No fleet raw SQL, row export or invented financial impact. |

### Capability ceiling protocol

Measure the current ordinary case, current known boundary, and successively
larger permitted inputs until the first failure or approved ceiling. Examples:
Surveyor files/touchpoints (including prior 16-file bound), Gardener nodes/edges
(at most 32 tasks), Scribe rules/trace/followups (at most four followups), Grafter
changed files/bytes/CAS conflicts (including the previously failed four-file
shape), Adversary guards/mutants and multi-output completeness, and all roles'
context/tool-call/output limits. Count limits remain contractual, not targets
to exceed. No arbitrary raw-source truncation or lost required guard is permitted.

At each rung record input size, model/profile, expected outcome, accepted output,
downstream correctness, latency, turns/tools/tokens, cost and failure reason.
Repeat the largest passing rung three times on the fixed configuration, including
one fresh input at that rung. Reopen and consume outputs. Stress invalid/overflow
inputs must safely hold without paid dispatch where admission can decide it.
Publish largest passing and first failing/unqualified rung; report if the budget
prevented further measurement. A new decomposition strategy is a new named
capability requiring full-subject tests, not a retroactive pass for old failures.

**Gate G4:** thirteen complete revised role records, real API evidence and actual
output-use evidence; all mandatory role cases pass on the fixed supported
configuration; historical failures and measured limits remain visible.

## 7. Sponsor and other-tool acceptance matrix

This implements the existing [sponsor ownership register](../work/SPONSOR_UTILISATION_AND_OWNERSHIP.md)
without treating every vendor as every agent's direct tool. Sponsor access adds
useful capability, never another authority/state/proof engine. A logo, formatter,
signup or mocked request does not count as actual integration.

| Tool / owner | Required non-frontend integration and acceptance evidence |
|---|---|
| Render / Gupta | Actual scoped metadata reads and exact approved image/config deployment observation; queued response is not LIVE. Verify persistent configuration, restart, target correspondence, state compatibility and independent exit. |
| Kernel / Vijay + Gupta | Authorised reference-shop browser scenarios with scoped sessions, case/run/scenario identity, replay plus independent recorder evidence, domain egress restrictions, Stop/cleanup observations. Review current vendor security/retention profile before private sessions. |
| APIMatic / Vijay + Codex | Pinned SDK/spec/document grounding feeding Builder/Architect/Grafter; exact operation-to-symbol mapping and compiling actual adapter/example, plus invalid/absent-symbol negatives. Generated docs alone are insufficient. |
| Postman / Gupta + Vijay + Singhal | Repository collections exercise actual case/start/stop/lease/review/access/effect and payment/callback boundaries, with empty-secret environment templates. Separate replay results from actual authorised sandbox/provider runs. |
| Elastic / Singhal + Gupta | Redacted index and authenticated exact-subject search→canonical artifact; verify ingestion, stale index, cross-case access, revoked access and safe public projection. Search is derived, never proof authority. |
| Zapier / Gupta + Codex | Opt-in minimal committed-event notifications, exactly one logical delivery, retries/deduplication, opt-out, quota/failure handling and truthful status. No real message without explicit destination/send authority. Historical receipt is not a current expanded-path qualification. |
| AG Grid / Studio / Claude + Singhal | Ours: schema-stable safe scenario/evidence/aggregate APIs with denominators, pagination/filtering and server-side access control. Claude: actual grid/UI and any licensed optional Studio use. API completion does not claim the frontend sponsor feature is complete. |
| Bryntum / Claude + Gupta | Ours: coherent read-only dependency/timing/blocker/event projection with resume, duplicates and unknown intervals. Claude: licensed display integration. Neither display nor model may reschedule backend tasks. |
| Astropods / Gupta + Codex, conditional | Assess a concrete model/cost/capability benefit; only adopt with exact model/processing/retention/usage/budget/reconciliation parity. Otherwise record not justified. Do not replace direct Claude merely to count a sponsor. |
| Channel3 / Vijay + Singhal, conditional | Demonstrate an uncovered line-item identity defect and actual dataset rights first; if adopted, pin a bounded lawful snapshot for OLD/OLD_TWIN/NEW. No rights or no material gap means not justified, with existing licensed fixtures retained. |
| PayPal / Gupta + Vijay + Singhal | Actual scoped sandbox transport and account/app binding, original callback authentication, money/origin/idempotency witnesses and independent proof/re-fetch. No production payments under this plan's current authority. |
| E2B / Gupta + Vijay | Actual isolated source execution, immutable template/runtime profile, process/egress/credential boundaries, timeouts, revocation, termination and independently retrieved captures. Kernel is not a substitute for source execution isolation. |
| GitHub/source/archive/registry/storage/custody / Gupta | Authorised read-only initial source collection, safe uploads/archive extraction, stable snapshots and provenance; scoped durable artifacts and secret references. Later PR/registry/config writes need exact separate authority. |
| Domain driver, mutation, recipe and aggregate tools / Vijay + Singhal + Gupta | Installed/pinned recipes and symbols, actual scenario execution and mutation forks, independent scorer, recipe quarantine/consent and aggregate ACLs. No raw shell/SQL or model-minted observed records. |

Vendor capabilities/SDKs/licences must be rechecked against current official docs
at execution. Public sources are not account qualification. Relevant checked
references: [Anthropic tool-call handling](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls),
[APIMatic SDK validation/generation](https://docs.apimatic.io/generate-sdks/overview-sdks/),
[Kernel browser-session API](https://www.kernel.sh/docs/api-reference/browsers/list-browser-sessions),
[Kernel security incident notice](https://dev.kernel.sh/blog/public-notice-of-security-incident-nov-4-2026).
These support the required explicit tool/session/schema qualification; they do
not establish this project's integrations or entitlements.

## Phase 5 — Connect the complete thirteen-role lifecycle

- [ ] Remove sample-derived predecessor inputs from the actual service path in
  workflow/graph composition. Preserve labelled fixture programs for tests.
- [ ] Implement trusted artifact resolution and exact subject derivation for
  every edge; only committed accepted outputs wake dependencies. Enforce writer
  leases, current generation and current recipe/input digests at each handoff.
- [ ] Run the following actual connected core, with bounded followup/repair:

```text
authorised intake + durable Start
  → Surveyor → Gardener/admission → Builder OLD
  → Explorer OLD + OLD_TWIN → independent SH mapping
  → Scribe draft → bounded Explorer followups → Scribe final
  → Architect → Grafter → Builder NEW → Explorer NEW
  → Adversary guards + disposable mutations → independent SH proof
  → review or bounded Grafter repair/rebuild/reproof → delivery gate
```

- [ ] Attach Herald to committed progress/results, Sentinel to actual audit
  events and Healer to actual operational observations. An ordinary successful
  run need not invent an incident: the integrated qualification suite includes
  a controlled isolated fault branch proving Healer participation.
- [ ] Attach Librarian only to an explicitly consented synthetic/rights-cleared
  result, with quarantine/non-origin selfcheck. Attach Orchard Analyst to an
  authorised derived aggregate view. Do not fabricate consent or cross-case
  scope merely to make all 13 appear in a trace.
- [ ] Exercise each role with the real model through the same API-backed
  service, shared case/run lineage and actual consuming artifacts. Produce
  per-edge input/output ref and source/tree/image/config/mapping evidence.
- [ ] Restart at stage boundaries, resume the same accepted run and prove no
  completed model/tool/economic effect is dispatched again. Stop blocks new
  work; unknowns preserve ownership and original request identities.

**Gate G5:** all 13 have actual integrated participation evidence across the
legitimate lifecycle branches. One connected core uses independently collected
baseline/candidate/proof records. Thirteen separately invoked samples do not pass.

## Phase 6 — Prove useful code upgrades, not sample replay

- [ ] Exercise the Phase 0 supported variations on submitted code not embedded
  in role samples: different names/layouts, repeated touchpoints, refunds,
  pending states, return/IPN paths, multiple files and changed dependencies.
- [ ] Verify safe acquisition: archive traversal/symlink/bomb/oversize rejection,
  immutable snapshot, missing source/backend detection, ownership/read-only
  scope and correspondence between submitted source and inspected runtime.
- [ ] Build/execute unchanged OLD and OLD_TWIN before accepting a rule baseline.
  Preserve baseline defects explicitly; normative money/state rules cannot be
  weakened because OLD is broken.
- [ ] Apply actual isolated patches to the exact baseline, build exact candidate,
  run required NEW scenarios and independent mutation guards, and inspect actual
  semantic changes. Compilation, a PR or model self-review alone cannot pass.
- [ ] Check order/customer history, integer money/currency, duplicate/late events,
  pending/refund/origin obligations, unrelated site functions and no added
  external/host/data authority. An unchanged required flaw remains a failure.
- [ ] Test repair on a named planted defect. Each candidate change invalidates
  affected build/scenario/proof/approval refs; at most two semantic repairs.
  Repeat identical failure or unsupported scope holds without editing the oracle.
- [ ] Export private updated source, patch, manifests, reproducible build/test
  instructions, exact image/config and limitations. Direct-artifact source
  provenance must not invent Git commit/workflow certificate fields.

**Gate G6:** unseen admitted inputs produce real independently verified upgrades;
unsupported inputs yield correct holds with the original untouched. The supported
matrix and measured ceilings describe what works, not “all code works.”

## Phase 7 — Delivery, state, recovery and merchant-independent exit

Codex integrates the deterministic reducer/executor using existing
`DeliverySnapshot`, `ResolvedDeliveryView`, `DeliveryDecision` and `DeliveryPort`.
Codex completes the backend/domain mechanisms and deterministic proof verifier,
preserving their independent evidence boundaries and original groundwork.
Follow [delivery and exit](DELIVERY_AND_EXIT_SPEC.md) and the normative
[atomic protocols](../lifecycle/ATOMIC_DELIVERY_PROTOCOLS.md).

- [ ] Evaluate can_review from actual complete baseline/candidate/domain/proof
  evidence. Materialise an exact ActionPlan/effect DAG, private merchant assets,
  state/recovery/finalisation/ExitCheckPlan and scoped ApprovalSet.
- [ ] Prepare the complete reviewable staging transaction. Before actual writes,
  obtain the required exact target/provider/publication/deploy/data/test authority;
  existing instructions do not authorise live merchant operations. Record missing
  authority as BLOCKED, never silently drop this phase from “complete.”
- [ ] Acquire actual target reservations/fences. Preserve consistent current
  state, all-writer fencing, ingress/handler/origin continuity and verified
  export/restore/replay before any destructive prerequisite.
- [ ] Publish the tested exact image/private source and use the selected
  protected-Git or direct-artifact route. Protect branches/triggers and refresh
  identity/grants/versions immediately before each effect slot.
- [ ] Observe actual persistent deployment/config/image/URL, required business
  functions, callbacks, current state and long-tail obligations. A queued deploy,
  guessed URL or healthy home page is insufficient.
- [ ] Test process crash before/after intent, provider timeout/no returned ID,
  Stop after submission, approval expiry, concurrent target claim, drift,
  registry pull failure and database incompatibility. Reconcile the original
  effect; do not send a second request to obtain a convenient ID.
- [ ] Test compatible current-state recovery and forward repair; prohibit old
  database restoration over newer economic history. Compensation requires
  separate authority and is not an automatic repair action.
- [ ] Close finalisation and Q0–Q4: merchant-owned independent executor ready;
  ordinary GoldGraft authority fenced/revoked; independent pull/restart and
  state/callback/origin observations; bounded evidence read; final capability
  revoked and cleanup/retention dispositions verified.

**Gate G7:** supported target operates with the exact approved upgrade and its
required state/handlers/assets, independently of ordinary GoldGraft authority;
no required unknown effect, cleanup or finishing task remains. If only staging
is authorised, qualify staging explicitly and leave live release BLOCKED.

Provider facts that constrain this gate: Render distinguishes deploy submission
from the persistent configured image reference; a one-off image override does
not change later settings. See [Render image deployment](https://render.com/docs/deploying-an-image)
and [deploy API](https://api-docs.render.com/reference/create-deploy).
PayPal webhook verification needs actual authentication using the original
message/app context; IPN requires the exact postback protocol, not trusting a
request parameter. See [webhook integration](https://developer.paypal.com/api/rest/webhooks/rest/)
and [IPN introduction](https://developer.paypal.com/api/nvp-soap/ipn/IPNIntro).

## Phase 8 — Retest everything after the upgrades

- [ ] Freeze final code/prompt/tool/model/recipe versions, then refresh signed
  qualifications. Any fix after this point reopens affected tests and fresh
  model/tool evidence; previous green results remain dated snapshots.
- [ ] Run whole-repository offline Python checks and required Node/PHP/domain
  suites, schema/TS/OpenAPI parity, actual counterpart integration, owned-file
  lint/format and diff checks. Restore PHP availability for acceptance; a required
  skipped test is a failed gate, not a completed check.
- [ ] Run the fixed 20-case × three-repeat service corpus, 60/60 expected outcomes,
  including disclosed correct holds; additionally report successful supported
  upgrades separately. Real model/provider calls occur only in live harnesses,
  never pytest. Retain every failed/unknown/cancelled identity in accounting.
- [ ] Cover the full 46 connection AC and 39 lifecycle LC applicability map,
  plus PAY-P01–P14 and REN-R01–R18 profile cases. Each applicable requirement has
  an actual test and evidence class. A non-applicable case requires an explicit
  profile reason; an unimplemented required case remains BLOCKED. Do not count
  old abstract/fake checks as provider evidence.
- [ ] Re-test required sponsor connections after role/graph upgrades, including
  outage, quota, revoked access, stale result and redaction. Confirm each result
  is consumed and cannot bypass canonical state/proof.
- [ ] Run a complete service restart and bounded concurrent-caller test: duplicate
  Start, conflicting idempotency body, stale lease, cross-case artifacts,
  simultaneous candidate writers, expired deadline and SSE reconnect. Verify
  no cross-case leak, double effects or fabricated progress.
- [ ] Run prompt/source/docs injection, dependency substitution, filesystem and
  metadata/private-network access denial, callback tampering/replay and malicious
  archive tests. Deterministic guards remain effective with the model absent.
- [ ] Record runtime, p50/p95 latency, model/tool calls, costs, budget exhaustion,
  largest passing source/graph/patch and resource cleanup observations on pinned
  hardware/profile. Never infer an untested throughput or reliability guarantee.
- [ ] Independently reopen every final evidence bundle, verify chain/signature/
  subject/access, and reconcile provider receipts with spend/reservations.

**Gate G8:** all mandatory expectations pass on final bytes; 60-run denominators,
per-role model/tool results, applicable AC/LC coverage, limitations and costs are
published. Required tests have no unexplained skips. Historical failures remain
in development totals. New unresolved model/provider operations prevent sign-off.

### Check commands and evidence environment

Use the pinned evaluation Python for real-model harnesses:

```sh
V=/Users/aditya/reports/goldgraft-model-gateway-20261111/venv/bin/python
```

It lacks PyYAML at audit time; the existing repo `.venv` passed plugtests. Phase 0
must pin a single reproducible full-check environment from the lockfile and
separately retain the qualified pinned model SDK environment. Do not silently
install/change the model environment during a paid series. Record interpreter
and module locations before tests when multiple checkouts exist.

Existing offline commands (run from the selected integrated checkout):

```sh
env GOLDGRAFT_PROOF=pieces.proof.proof:Proof GOLDGRAFT_API_APP=integration.app:create_app .venv/bin/python -B -m pytest -q
.venv/bin/python -B -m pieces.agents.workflow_cli --help
bash scripts/check_generated.sh
.venv/bin/ruff check pieces/agents pieces/backend/model_gateway pieces/backend/notifications
.venv/bin/ruff format --check pieces/agents pieces/backend/model_gateway pieces/backend/notifications
git diff --check
```

The existing `integration.app` command checks the fixture composition, not the
new actual agent service. Add separate actual-service test selection in the
same accepted route/port framework and record it explicitly. Node/PHP commands
come from the integrated CI at the pinned revision; do not replace unavailable
executables with passing stand-ins.

For changes affecting model qualification, use the existing reports-side
`run_check.py` four-check sequence and `make_qualification.py` with unique names,
the exact changed owned-file list and current source/case hashes. Never format
`test_source_references.py`. Retain prior qualifications as history.
All new check/live scripts named in Section 4 must include `--help`, explicit
offline/default behaviour, exact scope and bounded run IDs before use; their
commands are not presented as currently executable tools.

## Phase 9 — Produce and independently rehearse the handoff

- [ ] Write AGENT_SERVICE_HANDOFF with exact commit/lockfiles, model/profile
  versions, service entry points, environment variable names only, private secret
  setup references, source admission rules and start/cancel/resume/read commands.
- [ ] Export OpenAPI/schema/TS types and current example/error/SSE records for
  Claude. Document every state including waiting, rejected, held, unknown,
  stopping, proof failed, delivery pending, cleanup pending and complete. No
  frontend implementation or untested UI completion claim is required here.
- [ ] Provide the thirteen revised cards and AGENT_CAPABILITY_CEILINGS; actual
  per-role tools/models, fallback behaviour, largest passing inputs, historical
  misses, unsupported profiles and exact test denominators remain explicit.
- [ ] Provide TOOL_QUALIFICATION_REGISTER, provider/SDK/licence/expiry/retention
  records, actual evidence links, conditional dispositions and failure runbooks.
- [ ] Provide private source/patch/build/image/config/state/origin/approval/proof/
  exit manifests for the qualified profile; safe redacted public summary separate
  from private merchant data. Include ownership and fresh independent retrieval.
- [ ] Document incident response for unknown inference/effect, worker death,
  expired/revoked grants, provider outage, callback backlog, state drift, model
  failure, budget exhaustion and incompatible recovery. Give the exact same-ID
  reconcile procedure and named owner; never “clear ledger and retry.”
- [ ] Rehearse from a fresh local state using the actual service: submit a new
  supported source, observe the real workflow, inspect updated output/proof,
  stop/resume and replay saved evidence without additional effects. Rehearse the
  qualified external path only under its existing exact authority.
- [ ] Reconcile total/per-role/model/tool spend, no reservations/unknowns; record
  deletion/retention/credential separation and explain any retained required asset.
  Keep credentials and private evidence out of the distributable handoff.

**Gate G9:** another authorised operator can reproduce the admitted path and
recovery from the pack, with no hidden notebook, manual code edits, fabricated
receipt or merchant technical finishing task. Claude receives the API pack;
the user receives the concise completion/limit/operating record.

## Phase 10 — Independent review, final report and close

- [ ] Codex reviews contract/authority/money/state/provenance against independent
  frozen oracles and reruns reproducible checks on the final revision. Record
  findings/fixes; any fix reopens affected gates. No force push or stash.
- [ ] Produce FINAL_SERVICE_ACCEPTANCE with a row for each G0–G9, all thirteen
  role rows, source/profile coverage, sponsor dispositions, model routes, costs,
  checks, remaining limitations and actual handoff/exit evidence.
- [ ] Check the six user requirements against the matrix below and reconcile
  the original programme requirements. Every required item is PASS; any missing
  mandatory external action is BLOCKED, so the whole plan is not yet complete.
- [ ] Codex commits/pushes the checked code/docs on main and
  records the final SHA and CI result. No deployment is implied by Git publication.
- [ ] Update engineering/build START/status/handoff records, role/tool registers,
  private STATUS/CODEX_PROGRESS/CODEX_OUT with exact files, results, spend and
  evidence locations. Keep dated evaluation snapshots intact.

**Gate G10 / final done:** all mandatory non-frontend functionality and accepted
profile gates are green, final result is independently reproducible, no uncertain
request/reservation or required cleanup remains, and the operating handoff has
been verified. Do not close on “only the live part is left” while claiming full
delivery readiness. If live release is not authorised, state that separate gate
plainly and keep its status open.

## User-requirement coverage and execution rule

| User requirement | Phase and proof of completion |
|---|---|
| All 13 agents work with the API | G2/G4/G5: real model calls through actual service, all-role output use, actual connected lifecycle. |
| Agents plus every non-frontend integration work end to end | G1/G5/G6/G7: actual counterpart chain, unseen supported code upgrade, independent proof and qualified delivery/exit. |
| Haiku failures escalate to Sonnet | G2/G4/G8: named two-failure policy, persisted lineage/budget, actual successful escalation and failure/unknown negatives. |
| Upgrade agents with sponsor and other tools | G3/G4: every relevant role uses qualified tools; eight targeted partners and two conditional decisions tracked; Claude owns the UI portions. |
| Test again and reach measured ceiling | G4/G8: per-role boundary ladders and repeats, 60-run corpus, applicable AC/LC/provider/domain/security/restart results, full final regression. |
| Complete the handoff | G9/G10: fresh-operator replay, API/tool/operating/limits pack, independent acceptance and final revision. |

No routine progress requires Aditya to choose implementation details. Work
sequentially, record decisions and continue within the accepted scope. Ask only
when a real authority/budget/account decision cannot be supplied from existing
approval. A missing unavoidable external action remains a concrete owner-bound
blocker, never a guessed capability or false completion statement.

**Current next action:** close the actual-context cost prerequisites recorded
in the Phase 0 report. Workspace source integration is now prepared on main.
Preserve dirty documentation;
do not advance a dependent phase or dispatch a new paid job through an open gate.
