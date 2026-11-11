# Builder (agent 5) — real-model test, 11 November 2026

Model: **Haiku 5.5** on a new additive 8-turn Haiku profile (`haiku8`; same model and
prices; existing Haiku/Sonnet refs unchanged). Builder proposes builds; the scripted
runner returns receipts; Builder must accept only exact, observed receipts.

## Result

| Measure | Value |
|---|---|
| 9 cases × 4 runs (p1, r1–r3) | **35/36** model-correct |
| System safety (nothing wrong accepted) | 36/36 |
| Bad receipts held by the model (failed, unknown, source drift, invalid driver) | 15/16 |
| Forged image digest (model can't hash) | 4/4 held by Builder's review |
| Hostile inputs (unqualified recipe, missing symbol, candidate mismatch) | 3/3 held, $0 |
| Builder spend | $0.102616 of $0.90 |
| Cost per run | ~$0.0029 (4 turns) |
| Project spend now | $1.736926 of $10 |

## What it can do

| Capability | Shown by |
|---|---|
| Recipe binding | exact recipe + subject refs |
| Three operations | baseline, candidate, driver |
| Staged proposal | inline content, gateway-staged |
| Receipt checking | 4 failure kinds held |
| No self-written results | never alters receipts |

## Fixes found (free dry runs, before paying)

| Found | Fix |
|---|---|
| Tools take staged refs (`proposal_ref`) a model cannot mint | gateway inline staging: model sends the proposal, gateway validates it against ExecutionProposal/1 and stages it task-scoped; raw refs refused |
| 5 calls need 4 turns at best = Haiku's whole cap | additive `haiku8` profile; Builder routes to it |
| Review compared raw dicts | compare after contract normalization |
| Request id not visible | shared execution `facts` (ids, outputs, receipt rule) |

## Limits

- Runner, recipes and images are scripted stand-ins (GU/VJ infrastructure not qualified).
- One model miss in 16 bad-receipt runs (source digest compare); the review still held it.
- APIMatic (optional sponsor) deferred.

Evidence: `~/reports/goldgraft-all-agents-20261111/builder/`; runs `ag-builder-*`. Checks 41–44 (853 passed).
