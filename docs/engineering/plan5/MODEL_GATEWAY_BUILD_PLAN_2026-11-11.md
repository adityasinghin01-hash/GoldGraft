# Scoped model gateway and Surveyor evaluation implementation plan

**Current,11 November2026 continuation03:** Surveyor's tiny actual-model
pilot works: **seven accepted outputs across four distinct synthetic cases**,
including all five literal indicators, an injection sample and empty inventory.
Final transport-policy refund and browser/IPN checks passed2/2. Three earlier
quality/limit runs were blocked, including one of three original refund repeats;
those failures remain in the denominator. **595 affected offline tests passed**,
Ruff lint/format passed, and all accepted outputs were consumed/reopened without
new dispatch. The400 speed-field rejection, repeated reads, source-only claim
limits and catalog-ID confusion were corrected without relaxing validation.

Conservative priced usage **$0.026663**, retained original reservation
**$0.012672**, available **$0.010665** under the unchanged$0.05 cumulative cap.
Another full$0.012672 batch cannot fit. Original unknown request was never
replayed or cleared. User-authorized signed case/batch exceptions retained it;
two separate attributable HTTP400 rejections were proven terminal/unbilled.
Console authentication succeeded but did not attribute the original request.

**Tiny pilot/correction round complete; full Surveyor model acceptance HELD.**
The reviewed20×3 design was not run or silently narrowed. Broader model negatives
and repeats still need a reviewed affordable design/budget; original usage still
requires attributable provider evidence to release its reserve. Herald has not
advanced and its model grant remains unqualified. Sponsor phase N/A; production
GU/VJ/SH, merchant/payment work and universal reliability remain unqualified.
No money reset or automatic Codex restart is scheduled. Current evidence, exact
counts, hashes, phase decisions and limits: [continuation03](SURVEYOR_CONTINUATION_03_2026-11-11.md) and the current manifest.

## Historical snapshots and original plan

The dated statements below describe their recorded state; the current block above
and continuation03 supersede older sign-in, zero-output and no-new-call statements.

11 November2026. Aditya explicitly authorized building the missing test gateway,
testing Surveyor through the API and improving it, following the earlier estimate.
This supersedes the earlier prohibition on implementing this missing model/cost
boundary **for this scoped synthetic test gateway only**. No other GU service,
other agent, frontend, merchant/payment/proof service or Plan6 work is added.

> Execute sequentially using executing-plans/TDD/verification guidance. No
> sub-agents, Git mutations or framework/scheduler replacement. Record observed
> outcomes; do not claim an absolute ceiling or perfection.

**Goal:** A reusable local Anthropic ModelPort with durable project accounting,
guarded scope/secret handling, stable reconciliation and actual measured Surveyor
component results within the initial$0.05 cumulative pilot and$20 total ceiling.

**Architecture:** New `pieces/backend/model_gateway/` implements the now-authorized
local test boundary behind existing shared ModelPort contracts. Scripts compose
it with the existing Python agent runtime and explicit persistent synthetic
TaskControl/artifact/tool counterparts. Backend imports contracts only; agents
never import backend. New own admission hooks fail closed by default and accept
only this scoped gateway's authenticated, current grants. Existing offline modes
and all frozen interfaces remain unchanged.

**Stack:** Python3.12, SQLite transactions/HMAC/private local files, pinned
Anthropic Python client in an isolated evaluation environment, existing pytest/
Ruff and typed contracts. No HTTP server/external hosting is needed for the local
in-process port. No production distributed custody/control claim follows.

## Constraints and evidence limits

- One fixed private project ledger across all agents/processes; hard ceiling
  20,000,000 micro-USD, initial active cumulative checkpoint50,000 micro-USD.
  No cap increase without reviewed approval; no per-case ledger reset.
- Reserve worst-case batch/turn usage before dispatch. Unknown/submitted/intended
  outcomes retain reservation; no replacement identity or automatic retry.
- Only original synthetic MIT case bytes, no merchant/private code or personal
  data, fake financial/provider tools, no live payments/deployments/messages.
- Provider origin fixed to Anthropic, explicit API model/SDK/pricing/profile,
  SDK retries0, bounded timeout/output, no hosted tools/caching/fast/batch charges.
- Credentials stay in the approved private local file and provider transport;
  no value/hash in repo, diagnostics, contexts, logs, URLs or fixtures.
- Shared schemas/types/fixtures/fakes/frontend inputs stay frozen. Task/authority/
  artifact/tool counterparts remain labelled synthetic even with real inference.
- Standard commercial synthetic-data processing is the scoped purpose; do not
  assert account ZDR/residency/credits or alter account/billing/privacy settings.

## Execution status — 11 November2026

| Phase | Result |
|---|---|
| A | PASS for the pinned local synthetic candidate/profile; account entitlement not established by a successful inference receipt |
| B | PASS: persistent fixed project ledger; concurrency, subprocess death, unknown/Stop and overrun checks |
| C | PASS for the local scoped component; diagnostics strengthened after the pilot; production GU still unqualified |
| D | PASS offline against controlled provider and labelled synthetic tools/control; full affected-suite evidence in the gateway report |
| E | ATTEMPTED / HELD: one SDK inference request attempted on `inventory-nvp`; no accepted output/usage receipt; original reservation retained |
| F | PARTIAL / HELD: durable sanitized provider diagnostics added and tested; model-quality comparison cannot proceed until the original request's usage is reconciled |

The current source of truth is [the gateway report](SURVEYOR_MODEL_GATEWAY_REPORT_2026-11-11.md).
No second paid attempt, budget increase or next-agent progression occurred.
An unchecked paid-output/comparison item below is an explicit remaining gate,
not a successful phase. Local code completion does not establish model competence.

## Phase A — Pin scope, dependency and trial profile

Files: this plan, isolated private evaluation dependency lock/profile/evidence.
- [x] Verify actual official SDK release/model ID/rates/token-count/tool API and
  processing documentation; inspect installed SDK symbols after resolving pins.
- [x] Install only the scoped SDK/evaluation dependencies in a private venv;
  preserve root/frontend lockfiles. Capture resolved versions without secrets.
- [x] Pin one synthetic profile: candidate Haiku5.5, no fallback; capped input,
  output, turns/deadline and an independently calculated reservation under$0.05.
  If provider entitlement/version is unavailable, hold rather than switch silently.

## Phase B — Shared durable money/identity boundary

Files: create `pieces/backend/model_gateway/{__init__,ledger}.py`, tests under
`pieces/backend/model_gateway/tests/`.
Interfaces: Ledger.reserve(batch_id,fingerprint,ceiling), begin_turn/submit/
observe/unknown/close, snapshot and stop. Monetary fields are strict integers.
- [x] Write failing concurrent reservation, exact cap, changed-ID/fingerprint,
  restart, unknown, stop, late response and unused-reservation release tests.
- [x] Implement one SQLite BEGIN IMMEDIATE authority; retain submitted/unknown
  identities across restart. Unknown usage must never release its allowance.
- [x] Exercise subprocess/concurrent access and crash/reopen, not only mocks.

## Phase C — Guarded actual ModelPort and custody

Files: create `pieces/backend/model_gateway/{profile,secrets,broker,provider}.py`
and focused tests. Exact shared records remain unchanged.
- [x] Write negative checks for forged/stale/wrong-scope grants, context digest,
  unauthorized tools, malformed output, secret disclosure, expiry and Stop.
- [x] Build per-task signed grants binding source/input/prompt/policy/profile,
  actual local authority check and budget reservation. Verify again at dispatch.
- [x] Load the key only inside provider boundary with owner/0600/no-symlink/size
  checks; pin origin, timeout and retries0. Never print raw SDK exceptions.
- [x] Map native typed provider tools to allowlisted tools and final/blocked
  proposal staging. Actual provider usage/request IDs and signed scoped receipts
  reconcile against reservation; unknown transport outcomes hold original ID.
- [x] Qualify token bound/counting and record actual usage separately from the
  conservative monetary accounting amount; no UTF-8-as-measured-token claim.

## Phase D — Existing runtime integration and offline qualification

Files: modify own `pieces/agents/{ports,context,runtime}.py`; create separate
`scripts/live_surveyor_model_eval.py` composition and agent adapter tests.
- [x] Add explicit optional model policy/admission hooks, with existing offline
  behavior unchanged. A self-declared flag/key/nonzero budget cannot admit calls.
- [x] Use existing scheduler/run_task/validators/tool limits; no second loop.
  Mixed evidence is explicit: actual model gateway, synthetic tool/control/source
  collector. Actual model receipts bind the accepted proposal bytes.
- [x] Offline mocked-provider tests exercise the real new gateway and own runtime;
  all network denied. Check restart/unknown/Stop, staged output and output use.
- [x] Run affected gateway+agent checks, lint and frozen/original preservation
  before enabling an opt-in live script. Service/merchant mode remains separate.

## Phase E — Tiny Surveyor API pilot

Named question: can the pinned model read allowed source/matches/omissions and
produce a grounded RootMap on `inventory-nvp`? A missing-input negative must hold
before inference. Sponsor phase remains N/A. User authorization is this explicit
build/test request within the existing$0.05 active checkpoint.
- [x] Present exact final model/SDK/profile/token/turn caps, reserve arithmetic,
  named case and stop criteria after pins/tests qualify; do not exceed$0.05.
- [ ] Run approved synthetic token counting/calibration and one stable pilot
  identity. Inspect actual SDK response, scoped receipts, output checker and
  downstream accepted inventory. Record usage/cost/latency and limitations.
- [x] On invalid credentials, unavailable model, API uncertainty or safety failure,
  retain appropriate reservation and hold; never fabricate a successful test.

## Phase F — Measured Surveyor improvement and completion report

Files: own Surveyor prompt/context/checker changes only as justified by actual
results; new versioned results/report/manifest and BUILD_STATUS update.
- [ ] Diagnose the actual first failure/weakness. Make one justified improvement,
  check offline regressions first, compare on a distinct tiny licensed case and
  retain baseline vs changed results. Additional paid batches must fit the same
  active cumulative$0.05 authority and be concretely presented before dispatch.
- [ ] Reconcile ledger, retain unknowns, run affected final tests and inspect
  actual accepted output use. Capture pinned hashes and preservation evidence.
- [ ] Close each phase as passed/held/N/A with actual evidence. Do not advance
  Herald or claim perfection. If access/budget blocks completion, report the exact
  remaining gate and measured results rather than silently broaden scope/cap.

The broader20-case/three-repeat cross-agent acceptance design remains separate;
a tiny Surveyor pilot does not become full production or13-agent acceptance.
