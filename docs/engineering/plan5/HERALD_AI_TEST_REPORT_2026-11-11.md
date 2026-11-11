# Herald (agent 2) — real-model test, 11 November 2026

Model: **Claude Haiku 5.5**. Surveyor runs first (deterministic); Herald's own runtime
task then runs through the shared component gateway. Validators unchanged: only exact
closed-catalog text and exact ledger numbers are accepted.

## Result

| Measure | Value |
|---|---|
| Final code, 8 cases × 4 runs | **32/32 passed** |
| Hostile facts (status/reason conflict, asset conflict, review without proof) | 3/3 held, $0, zero model calls |
| Audit (ledger, receipts, rescore, no side effects, reopen) | 32/32 clean |
| Herald spend (all rounds) | $0.062770 of $0.25 |
| Cost per run | ~$0.0014 (2 turns) |
| Project spend now | $1.376591 of $10 |

## What it can do

| Capability | Shown by |
|---|---|
| Catalog choice | 7 statuses, 6 reason codes |
| Exact numbers | count only when inventory is ready |
| Number omission | no count in 7 other cases |
| Asset lists | retained / removed / pending kept apart |
| Draft kinds | card, PR body, handoff, verdict |
| Public-safe | no IDs or refs in text |
| No side effects | status unchanged, 0 sends |

## Fix found by real runs

| Round | Found | Fix |
|---|---|---|
| p1 4/8 | Herald observations carry a `kind`, not a tool name, so `tool_progress` read `[null, null]`; the model re-read until the 4-turn limit | gateway `tool_progress` hook; Herald maps kinds to `status.read` / `evidence.summary`; policy: "never read again once both are listed"; dry run now flags any null progress |

History: p1 4/8 · **p2 + r1–r3 32/32**.

## Limits

- Closed catalog: Herald cannot write free prose (by design in this profile).
- Facts come from the scripted Surveyor→Herald projection, not live GU status.
- Zapier delivery was proven earlier (real send + dedupe); not re-run here.

Evidence: `~/reports/goldgraft-all-agents-20261111/herald/`; runs in
`~/reports/goldgraft-model-gateway-20261111/live/ag-herald-*`. Checks 25–28 (841 passed).
