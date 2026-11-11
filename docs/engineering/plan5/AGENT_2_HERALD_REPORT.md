# Agent 2 — Herald: supported offline implementation completed

10 November 2026. This completes the supported offline implementation and checks,
not real-model, GU service or notification integration. No sub-agents, external
messages, Git staging/commit/push/merge, deployment, account changes or paid calls.

## Capabilities and tools

- **status.read** and **evidence.summary** consume one authorised committed run/
  projection. No raw source/capture, arbitrary URL/SQL, credential, payment, host,
  candidate-write or publication capability is granted.
- An exclusive versioned prompt/policy allows explain_status and HeraldText/1.
  The code registers Surveyor and Herald; the remaining 11 roles are not built.
  Mandatory enforcement does not depend on Sentinel.
- A closed claim catalog covers queued, working, inventory-ready, input wait,
  held, unknown, cancellation pending/confirmed, review, delivery wait and
  explicitly synthetic completion. Unknown stays unknown; a PR/signature/score
  without complete exact-subject proof cannot produce review readiness.
- Approved reasons name the next responsible owner/action: source controller,
  GU authority/reconciliation/termination, SH proof, budget review or independent
  exit. Contradictory status/reason pairs hold before a Herald turn.
- GRAFT_CARD, PR_BODY, HANDOFF and VERDICT_EXPLAIN drafts have concise/detailed
  deterministic templates. These are drafts, not created PRs or sent messages.
  Templates remain usable without a real model or while optional model work holds.
- Quoted counts carry the exact scoped numeric-journal hash and JSON pointer.
  The counterpart derives the number from actually committed Surveyor bytes.
  Runtime, staging and acceptance resolve and validate it. Missing/forged refs,
  wrong pointers, unsigned counts and even float 5.0 in place of integer 5 fail.
- Retained/removed/pending asset labels remain separate and bounded. Conflicting
  dispositions hold. Public inspection excludes private IDs, entry hashes and
  evidence refs. Herald's context excludes raw source excerpts and captures.
  The inspection view independently rechecks numbers, identity, kind and claims.
- A pure opt-in notification preview provides minimal text and a stable logical
  event key shared across draft formats. It **sends nothing**, records no consent
  and grants no authority. **Zapier is the planned future GU delivery connector;
  it is not connected here.** Elastic, AG Grid and Bryntum remain team-side
  upstream/display integrations, not ambient tools given directly to Herald.

Herald prose changes no authoritative status, proof, approval, money, recovery or
exit state. An unknown optional turn retains its identity/reservation and cannot
be completed through fallback; the pure fallback renderer remains available to
an authorised caller without erasing or overriding that unknown work.

## Actual results

| Check | Observed result |
|---|---|
| Herald runtime/claims/privacy/graph/restart checks | **80/80 passed** |
| Full offline regression | **2,320 passed**, one existing TestClient/httpx warning |
| Ruff/shared TypeScript | Passed |
| Generated examples/views/schema/API/TS parity | Passed: 177 schemas, 15 modes, 46 paths |
| Separate-process run,inspect,resume | Private and public-safe examples passed |
| Real model calls / API spend / notifications sent | **0 / $0 / 0** |
| Real-model competence or safety rate | **NOT EVALUATED**; no invented score |

One command ran the actual B4 Surveyor then B4 Herald, committing two results
with five scripted turns and eight read-tool dispatches. These are not provider
calls. Herald copied the actual source indicator count 5; another source-driven
case copied 0. Separate-process inspection/resume added no dispatches.

Actual public-safe text:

> The source inventory is accepted for further analysis. Inventory contains 5 source indicators. Source-only offline evidence; runtime, payment and live-site outcomes remain unverified.

Private evidence: `/Users/aditya/reports/goldgraft-b4-herald-20261110/`.
Accepted command/cwd/status/duration/log-hash records are checks/16-accepted-herald.json,
17-accepted-full.json,18-accepted-lint.json,12-final-types.json,13-final-generated.json.
The demo directory records actual private/public run,inspect,resume outputs and
an explicitly unsent notification preview. Failed red tests for initial missing
integration, float counts, contradictory reasons, inspection and event identity
are retained. Final per-file/check hashes are in AGENT_2_HERALD_MANIFEST.json.

Six real subprocess crashes bypass cleanup before/after model, before/after tool,
and before/after acceptance. Fresh processes preserve original dispatch identities
with count≤1. An incomplete intent without qualified fence rebinding holds.
A seventh crash between Surveyor commit and Herald admission proves automatic
recovery and incremental advancement. Duplicate/reordered events do not repeat
an accepted explanation. Stop and wrong case/run/generation/tool/owner/subject
fail closed; the accepted predecessor result survives optional text failure.

## Architecture and shared revision2

Own graph policy resolves the committed Surveyor descriptor before appending
Herald through TaskControl.extend with run-version CAS. It never guesses a future
ref or mutates the predecessor. Herald is optional, consumes the exact accepted
output and is an observability branch. It does not redefine the specified main
Surveyor→Builder→Explorer→Scribe→Architect→Grafter→candidate/proof graph or add a scheduler.

Own modules: herald.py,prompts/herald.md,graph.py,tests/test_herald.py plus existing
role/runtime/CLI/scheduler hooks. Fakes supply persistent task/tool/projection
counterparts and invoke the actual own renderer through deferred composition.
The immutable projection journal is a **synthetic GU ledger counterpart**, not
the foundation ledger, real GU identity/durability, signing or proof authority.

HeraldText/1 already required ledger context for numbers. The pure shared
validate_artifact helper now accepts optional trusted validation_context from
the accepting service; model JSON cannot supply it. Absent context still rejects
referenced numbers. No wire fields, versions or routes changed; FORMAT_CHANGES
records the accepting-adapter correction.

All 454 revision 1 inputs matched before editing. `pieces/web` contained only `.gitkeep`
and no worker status existed. FRONTEND_READY was marked updating first, then
revision 2 publishes fresh source hashes and actual check records atomically.
Existing generated schema/API/TS and fixture bytes remain unchanged. No frontend
file was edited. Historical manifests retain their dated implementation snapshots.

## Reproduce and limits

From the isolated root, inspect the saved matching state:

```sh
uv run --locked --no-sync python -m pieces.agents.cli inspect --mode offline --fixture surveyor_herald --projection public_safe --state-file /Users/aditya/reports/goldgraft-b4-herald-20261110/demo/public_safe.sqlite
```

Use run with a new explicitly named state file for another synthetic programme.
Do not delete unknown state or change a persisted profile/projection to force retry.
The claim catalog and asset labels are deliberately bounded; free prose is not
accepted by this initial profile. Public rendering is a developer inspection
consumer, not a newly implemented production API or frontend.

Real reasoning quality, GU projections/ledger/authority, SH proof, notifications
and the remaining 11 roles stay open. Model evaluation still needs the selected
Anthropic Python SDK behind a qualified GU model/processing/budget boundary.
No key was needed here; never paste one in chat. Every agent and every paid
calibration/retry/evaluation/regression/demo share the user's total $20 ceiling,
starting at the cumulative $5 checkpoint. Paid checks remain NOT RUN.

Next construction role: **Sentinel**. Mandatory guards are already active.
