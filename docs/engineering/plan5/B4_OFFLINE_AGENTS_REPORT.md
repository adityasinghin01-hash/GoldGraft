# B4 — thirteen supported offline role implementations

10 November 2026. Workspace: `/Users/aditya/dev/GoldGraft-plan5-build`.
This report separates executable offline construction from actual model, team,
provider and merchant qualification. **No model was trained or called.**

## Result and limits

All thirteen roles now have an exclusive prompt, bounded inputs, allowed typed
tools, schema/producer checks, guarded runtime path, positive and negative tests,
and an inspection consumer. Construction followed Surveyor → Herald → Sentinel →
Gardener → Builder → Explorer → Scribe → Architect → Grafter → Adversary → Healer →
Librarian → Orchard Analyst. Each role was checked and its output inspected before
starting the next. No sub-agents were spawned.

“Offline completion” means the supported deterministic/synthetic scope below. It
is **not B4 real-model acceptance**, a competence score, universal agent coverage,
real runner execution, independent money proof or merchant completion. The
ceiling of these agents has not been measured. Existing B3 mandatory guards remain
active independently of Sentinel. GU mechanisms, VJ domain recipes and SH proof
remain separate dependencies; this work does not implement them under new names.

Current check records and file hashes: `B4_OFFLINE_AGENTS_MANIFEST.json`.
Private commands, logs, SQLite state and run/inspection JSON:
`/Users/aditya/reports/goldgraft-b4-remaining-20261110/`.
Surveyor and Herald retain their earlier reports/manifests and evidence folders.

## Completed checklist, applied to every role

- [x] Purpose, allowed operation and trusted prerequisite defined in role input/admission code.
- [x] Exclusive prompt and policy hashes bound to the task; bounded context and final output.
- [x] Closed typed tool allowlist; no host shell, arbitrary network, publication or financial credentials.
- [x] Exact output schemas; authenticated role/output owner and case/run/generation/input/subject checks.
- [x] Actual role planner/renderer/reviewer executed in the existing guarded runtime.
- [x] Positive use and missing input; wrong case/run/subject/generation, denied tool and wrong owner/schema checks.
- [x] Role-specific failures below; unknown model turn keeps its original identity.
- [x] Actual accepted output read by its inspection view; core workflow also consumes predecessor artifacts.
- [x] Input/output refs, command logs, observed results and remaining gates recorded.

New component roles share eleven runtime guard cases each. Per-role counts below
include those common cases. These are **test results, not model quality scores**.
Individual test commands overlap the final suite; do not add their counts to it.

## Verification result

- **477 passed** in `pieces/agents/tests` (89.92s).
- **2,570 passed** in the full offline suite (101.83s); one existing Starlette/
  TestClient httpx deprecation warning.
- Whole-repository Ruff, TypeScript, generated parity and diff checks passed.
- The last lint pass found import/line formatting in the new subprocess recovery
  test. Those were fixed; its **7 tests passed again**. Product code did not change
  after the full-suite run. This recheck is not added to the suite total.
- Preservation: original **327 tracked file hashes**, original status/HEAD and
  **454 frontend frozen input hashes** unchanged; readiness remains revision2.
- Private run/inspect/resume commands produced twelve accepted core fixture tasks
  with no new dispatch on resume. The separate repair demonstration produced
  twenty-two tasks and three distinct candidate trees/images.

## Per-agent capabilities and deferred tools

| Build order / agent | Supported offline behavior and output | Specific checks passed | Typed tools used or allowed; later connections |
|---|---|---|---|
| 1 Surveyor | Reads pinned bounded source, finds five literal indicators across three families, discovers missing includes, records omissions and emits RootMap/1. Source-only confidence/coverage remains limited. | 79 source/role checks; 4/4 independently labelled inventory artifacts | source.read, analysis.matches, evidence.read. Later: GU source/custody scopes; VJ detection coverage; authorised Elastic/site/account lenses if adopted. |
| 2 Herald | Closed evidence-bound status prose, ledger-checked numbers, private/public projections, deterministic fallback and opt-in notification preview. HeraldText/1. | 80; actual Surveyor→Herald advancement and restart | status.read, evidence.summary. Later: opt-in destination and Zapier delivery/dedupe connector. No notification sent. |
| 3 Sentinel | Reviews consecutive scoped audit events, emits Alert/1, requests a hold for grounded critical anomalies. Reports termination pending, never fabricated halt success. | 17 | audit.summary, safety.request_hold. Later: GU audit/fencing/termination observations; optional Elastic. |
| 4 Gardener | Advises one bounded next known-input stage through PlanProposal/1; checks required tasks, roles, acyclicity and subject/ref scope. Cannot dispatch tasks. | 19 | status.read. Later: GU durable task service; Bryntum is optional frontend visualisation, not scheduling authority. |
| 5 Builder | Proposes baseline/candidate builds and driver validation. Checks pinned recipe fixture, installed symbols, exact source and synthetic manifest digest. Emits ExecutionProposal/1. | 20 | recipe.lookup, dependency.inspect, evidence.read, execution.request/status. Later: VJ qualified recipes, GU isolated runner/collector; APIMatic catalog access if used. |
| 6 Explorer | Requests exact OLD/OLD_TWIN/NEW scenario variants. Baseline discovery needs no prior Contract; NEW needs final Contract. Incomplete/unknown captures never become verified proof. ExecutionProposal/1. | 23 | execution.request/status, evidence.read. Later: Kernel/Postman if adopted, guarded sandbox credentials, real recorder and SH mapper. |
| 7 Scribe | Preserves normative predicates, severity, correct flows and counterexamples. Distinguishes CODE_ONLY from BOTH; emits bounded TriangleRequest/1 followups and distinct draft/final Contract/1. OLD defects do not waive requirements. | 22 | source.read, evidence.read. Later: trusted VJ rule catalog and authenticated SH mapped events; optional authorised evidence search. |
| 8 Architect | Grounds each supported payment touchpoint in exact catalog mapping and installed symbol; rejects unrelated work, invented APIs and unapproved deltas. TargetPlan/1. | 21 | recipe.lookup, docs.lookup, evidence.read. Later: pinned APIMatic/docs/version/symbol qualification. Current fixture support covers EC_NVP/IPN, not arbitrary recurring/account migration. |
| 9 Grafter | Sole isolated candidate writer with expected-tree CAS, approved paths, immutable baseline and collector-bound child subject. Snapshot ChangeList/2 contains no invented branch/commit. Requires fresh independent build/proof. | 23 | source.read, dependency.inspect, candidate.patch. Later: real GU exclusive candidate lease/CAS/custody and VJ installed dependencies. No merchant source or Git write. |
| 10 Adversary | Derives scenario/mutant drafts from Contract, records unguarded rules, stages quarantine proposals and requests separate disposable-fork runs. ScenarioSet/1, MutantSet/1 or ExecutionProposal/1. | 22 | source.read, scenario.stage, execution.request/status, evidence.read. Later: GU forks, VJ qualified mutation catalog, independent SH kill/equivalence results; Kernel/Postman and rights-cleared Channel3 only if approved. Current synthetic operator is one M1 fixture, not all twelve qualified operators. |
| 11 Healer | Diagnoses bounded synthetic operational anomalies; requests a hold. HealNote/1 cannot claim recovery, restore old DB state, cut back traffic or compensate money. | 20 | status.read, evidence.read, safety.request_hold. Later: authorised operational observations, optional Elastic; GU/VJ current-state-compatible recovery evidence. |
| 12 Librarian | Requires synthetic consent/rights/completion/de-identification evidence. Produces unsigned QUARANTINE Recipe/1 and DetectionRule/1 proposals; separate non-origin selfcheck through ExecutionProposal/1. Never ACTIVE promotion. | 24 | recipe.stage, execution.request/status. Later: explicit learning rights/purpose/consent, independent fixture and separate budget/promotion review. Current transform is one approved synthetic template. Optional learning never blocks delivery. |
| 13 Orchard Analyst | Closed tenant/purpose aggregate query, minimum cohort, approved metrics/group/filter keys. DashboardSpec/1 with projection refs. No raw rows, SQL, exports or merchant dispatch. | 22 | aggregate.read. Later: authorised fleet aggregate service and AG Grid/optional Studio connection. Frontend remains Antigravity-owned. |

The sponsor names above are integration destinations and constraints, **not a
claim that accounts, SDKs or services are connected**. Render/E2B/storage/custody
are shared GU service dependencies. Astropods/Channel3 remain conditional. More
ambient tools would not increase legitimate authority. Full tool power means
using each qualified capability within its role, purpose and budget.

## Actual combined construction evidence

`workflow.py` incrementally extends the existing `scheduler.tick` policy over
TaskControl; it is not a replacement scheduler or an agent framework. It admits
only committed predecessor refs, authenticates descriptors, and binds composite
inputs to an exact manifest. Future candidate/image refs are never guessed.
The persisted synthetic core programme is:

1. Builder baseline with supplied synthetic inventory/recipe prerequisites.
2. Explorer OLD and OLD_TWIN.
3. Scribe draft → bounded Explorer followup → distinct Scribe final.
4. Architect → exclusive Grafter → exact candidate Builder.
5. Candidate Explorer plus independent Adversary guard/fork requests.
6. Own review prerequisite gate demands an injected independent SH proof summary.

The main programme has twelve tasks; two repair rounds produce twenty-two total,
below the thirty-two-node cap. Construction order does not redefine this graph.
The earlier **actual Surveyor→Herald** programme remains separately exercised.
This core fixture begins with supplied inventory; it does not claim a single real
end-to-end source/runner/payment/proof service integration.

Actual checks cover acyclic incremental extension, at most four followups,
separate-process restart without dispatch growth, interrupted input materialisation
recovery, altered predecessor subject rejection, and process death after candidate
CAS, before finish and after finish. The latter recover one patch and at most one
dispatch per identity. Two repairs rebuild/retest a changed child tree/image,
reject stale proof, refuse repeated unchanged failures and hold a third repair.
Missing flow, wrong source/image/refs, unguarded rule, required failure or incomplete
independent proof block the own gate even with score 1.0. No merchant review/apply
authority is created by this offline gate.

## Important scope decisions

Model outputs remain proposals. New Builder/Explorer runs accept
ExecutionProposal/1 plus scoped **synthetic counterpart receipts**; they do not
manufacture real RunnableShop/Driver/ArtifactBuild/RawCapture evidence. Candidate
CAS uses private synthetic snapshot bytes and shared SubjectManifest/
SubjectDerivation validation, not a real source custody service. The mapping and
proof ports are explicit injected SH counterparts. Reproducibility, real capture
bytes, genuine mapper/proof behavior and authenticated team services remain open.

Deterministic renderers deliberately cover the bounded fixtures above; no
unqualified “general coding agent,” all-stack migration or perfect security claim
follows from green tests. Replacing the scripted ModelPort with paid inference
still requires named evaluation, including all hard negatives and repair/resume
cases. Synthetic learning consent and certification do not approve merchant reuse.

## Deferred manual actions and engineering gates

See [MANUAL_CONNECTIONS_AND_GATES.md](MANUAL_CONNECTIONS_AND_GATES.md) for the
per-agent connection register. None were executed. The inspected environment has
no ANTHROPIC_API_KEY and no installed Anthropic client. No key is needed for the
construction completed here. Configure a key **locally** or in the approved secret
store later; never paste it into chat. Presence-only check:

```sh
uv run --locked --no-sync python -c 'import os; print("PRESENT" if os.getenv("ANTHROPIC_API_KEY") else "ABSENT")'
```

Use the selected **Anthropic Python client SDK behind the qualified GU ModelPort**.
A key alone does not qualify GU broker custody, durable control, processing terms,
model/version/pricing/tokenizer, SDK adapter, or atomic budget reservations and
reconciliation. Those are engineering dependencies, not merely user connections.
Paid checks remain **NOT RUN** until those conditions and explicit evaluation
spend authority exist. No provider/model upgrade or alternate framework is implied.

The entire project shares **$20 maximum**, covering all thirteen agents and every
paid calibration, retry, evaluation, regression and demo. Initial cumulative
checkpoint is $5, with separately reviewed $10/$15/$20 increases and a $15 target.
Spent + outstanding + unknown reservations all count; unknown charges never release
budget. This construction made zero model API calls and spent **$0**. No training
job is planned or authorised.

B5 delivery, B6 frontend and B7/real-model qualification are not closed here.
No Plan6, external publication, deployment, payment/provider/merchant job, private
source transfer, account/billing change or teammate message occurred. Original
source and frontend frozen inputs were checked separately in preservation.json.
