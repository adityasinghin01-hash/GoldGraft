# Sentinel (agent 3) — real-model test, 11 November 2026

Model: **Claude Haiku 5.5** (Sonnet not needed). Synthetic audit windows only.
Path: actual runtime + shared component gateway (S0) + scripted tool counterparts.

## Result

| Measure | Value |
|---|---|
| Final code, 8 cases × 4 runs | **32/32 passed** |
| Hostile cases (gap, cross-case, old generation) | 3/3 held, $0, zero model calls |
| Audit (ledger, receipts, rescore, output use, reopen) | 32/32 clean |
| Sentinel spend (all rounds) | $0.152931 of $0.40 |
| Cost per run (final) | ~$0.0015 (2–3 turns) |
| Project spend now | $1.313821 of $10 |

## What it can do

| Capability | Shown by |
|---|---|
| Kind detection | all 4 kinds, mixed, up to 32 events |
| Severity choice | CRITICAL / MAJOR / MINOR correct 32/32 |
| Hold request | only on breach; 0 false holds (final) |
| Honest wording | never claims safe or terminated |
| Grounded refs | input refs + returned hold receipt only |
| Window refusal | gap / cross-case / stale generation |

## Fixes found by real runs (none visible to the free replay)

| Round | Found | Fix |
|---|---|---|
| p1 0/8 | model can't see the exact `run_ref` / hold code | shared `call_facts` (refs, closed codes, call policy) for every agent; dry run now flags any argument value the model cannot see |
| p2 3/8 | review demanded exact text: hold receipt in refs, `Z` timestamp | review → invariants: grounded refs, same instant |
| p2 | model used event fingerprints as refs (real error) | still rejected; policy says fingerprints are not refs |
| r3, f0 | empty window: literal "is safe" (negated); one false hold | guard kept unchanged; policy states the literal guard and "empty window = MINOR" (2nd and last variant) |

History by round (same audit): p1 0/8 · p2 3/8 · p3 8/8 · r1–r3 23/24 · f0–f3 31/32 · **g0–g3 32/32**.

## Limits

- Scripted tool counterparts; real audit/fence/termination stay GU evidence.
- Elastic (optional sponsor) deferred; not connected.
- Wire size: largest case uses 21,211 of 22,976 bytes on Haiku; longer policies need the Sonnet count bound.

Evidence: `~/reports/goldgraft-all-agents-20261111/sentinel/` (cases, `SERIES_LOG.jsonl`,
`DRYRUN_haiku.json`, `AUDIT_*.json`); runs in `~/reports/goldgraft-model-gateway-20261111/live/ag-sentinel-*`.
Checks: `~/reports/goldgraft-all-agents-20261111/checks/17–20` (832 passed, lint/format/diff clean).
