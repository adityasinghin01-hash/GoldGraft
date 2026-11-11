# Gardener (agent 4) — real-model test, 11 November 2026

Models: **Haiku 5.5** for plans of ≤5 nodes, **Sonnet 5.5** for ≥6 (routed before
dispatch from plan size). Output is a PlanProposal/1; the deterministic scheduler keeps
all dispatch authority.

## Result

| Measure | Value |
|---|---|
| Final behaviour, 8 cases (f0–f3 + Haiku d1–d4) | **54/56** (Haiku 46/48, Sonnet 8/8) |
| Model holds (over-cap; deploy-named task) | 16/16 correct holds |
| Hostile inputs (unaccepted, unverified, paid plan) | 3/3 held, $0, zero model calls |
| Real admission check on every accepted plan | 38/38 pass |
| Gardener spend (all rounds) | $0.257719 of $0.40 |
| Cost per run | Haiku ~$0.0011 · Sonnet ~$0.021–0.027 |
| Project spend now | $1.634310 of $10 |

## What it can do

| Capability | Shown by |
|---|---|
| Required tasks kept | 1, 2, 3, 6, 9 required ids |
| Committed stage only | 12 roles allowed, Surveyor only |
| Cap respected | exact-cap plan; holds when over |
| Unsafe-name caution | holds on "deploy-now" |
| Large plans | 9 nodes (output-cap ceiling) |

## Fixes found

| Found | Fix |
|---|---|
| Rule output always made one fixed node (offline gap) | one Surveyor node per required id, distinct slots |
| `parent_request_id` not visible to a model | Gardener `facts` (ids, committed stage shape, call policy) |
| Metadata hint had fields PlanProposal lacks | hint only fields the output schema has |
| 9-node plan cut at Haiku's 1,536-token output cap (p1) | route ≥6 nodes to Sonnet (6 nodes used 1,499 tokens) |
| Runner read turns in hash order, scoring a correct hold as fail | any blocked turn = model hold; audit recomputes |
| 2 of 48 Haiku runs: malformed first response (argument validation) | not recurred in 24 more; port now records closed call shapes for diagnosis |

Label change (stated, not hidden): "deploy-now" was first labelled "must plan a survey
node"; after review both a survey node without a deploy op and a model hold are safe,
so it is scored as either. Under the old label p1 counts it as a fail.

## Limits

- One proposal holds at most 9 Surveyor nodes (4 KB runtime output cap).
- Only the committed next stage (Surveyor) is admissible; later stages need committed refs.
- Haiku first-turn format slip: 2/48 (fail-safe: task held, nothing admitted).

Evidence: `~/reports/goldgraft-all-agents-20261111/gardener/`; runs
`ag-gardener-*`. Checks 37–40 (849 passed).
