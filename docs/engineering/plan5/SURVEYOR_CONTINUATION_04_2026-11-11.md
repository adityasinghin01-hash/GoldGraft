# Surveyor continuation04 — final-policy repeat series, negatives, limits

11 November2026, Claude (complete handover from Codex). **Selected scope
qualified: synthetic source-only literal inventory on Claude Haiku 5.5 under the
final transport policy, ≤2 source files / ≈4.5 KB observations.** The reviewed
20-case × 3-repeat design ran with one documented substitution. Haiku fails
cases that need ≥3 files; a Sonnet 5.5 comparison passed those 2/2. The original
unknown request is still unattributed and its reservation is retained.
Continuation03 stays immutable dated evidence.

## Authority and money

Aditya: “Complete the model run. You can increase the model to Sonnet if it's not
working correctly.” Asked for a cap, he chose **raise to $0.50** (Surveyor outer
ceiling). Applied by a new raise-only, authority-bound ledger method; spend,
reservations and the unknown row were byte-checked unchanged; backup kept.

| Item | micro-USD |
|---|---:|
| Usage-priced spend, all time | 322,525 ($0.322525) |
| — continuation-04 (68 batches) | 295,862 (Haiku 144,566; Sonnet 151,296) |
| Retained original reservation (unknown 3,168 + outstanding 9,504) | 12,672 |
| Active cap / available | 500,000 / 164,803 |

Inference attempts all time: **166** = 163 observed responses + 2 proven terminal
400 + 1 original unknown. Tokens observed all time: 1,344,144 in / 88,612 out.
All 163 receipts and per-turn prices verified by a read-only audit (ledger unchanged).

## What was wrong and what changed

| Problem (verified) | Fix | Evidence |
|---|---|---|
| Available $0.010665 < $0.012672 batch | User-chosen raise-only cap $0.50 (`Ledger.raise_active_cap`) | CAP_RAISE.json |
| Signed one-case review hardcoded $0.05 cap | Binds the ledger's actual cap, ≤ $0.50 outer ceiling | test_independent_review |
| Runtime hardcoded $0.05 ticket ceiling (first run DENIED, $0) | `REAL_MODEL_CEILING_MICRO_USD = 500000` | s4-…-r1 kept; new test |
| Qualification stale (herald.py changed) | Requalified each change; checks 104–107 | manifest |
| Repeat reads on single-file cases (a1: 2 TURN_LIMIT, 4-turn runs) | `tool_progress.unread_paths` + `ready_to_submit` | n1 5/5 in 2 turns |
| Model never told the 4-calls/response bound | v3 text, then v4 `next_calls` | **both failed** → line stopped |
| Rejections undiagnosable | Closed `rejection` label + `tool_use_blocks` count in signed audit | `tool_call_count`, 7 calls |

No validator, expected label, required read, role prompt (`60260ae1…`) or role
policy (`234a6a73…`) was weakened. Final transport policy v4
`bfbfca834a9d9b068c9cd726cfbed55f782bc5949ce74e8c7de2c0e4be184af2`.

## Results (actual inference unless marked)

| Series | Policy | Runs | Accepted | µ$ |
|---|---|---:|---:|---:|
| a1 before | c03 final | 14 | 11 | 38,609 |
| n1 | v2 | 6 | 5 | 11,774 |
| n2 / n3 / s1 size probe | v2 / v3 / v4 | 3 | 0 | 3,511 |
| **f1–f3 final** | v4 | 42 | **39** | 90,672 |
| Sonnet size probe | v4 | 2 | **2** | 151,296 |

Final-policy Haiku, 13 in-scope cases × 3: **39/39**, 38 in two turns, one in
three; mean $0.002232/run, median 6.1 s. Size probe Haiku: 0/8 across policies.

**Reviewed 20×3 mapping:** 10 inventory cases × 3 = **30/30** accepted (inventory-nvp
replaced by separately authored `c04-nvp-substitute` — the original unknown is never
replayed); 10 required-hold cases × 3 = **30/30** held with zero model calls through
the actual runtime/gateway (code enforcement, not model behavior). Extra model
negatives × 3: tool-escalation instructions 3/3, false live/money/REST claims 3/3,
comment-line duplicate indicators 3/3. A correct hold is not counted as task success.

## Output use

All **57** accepted continuation-04 outputs were independently rescored (exact
file/line/family/operation/rule ID, every money-flow location, no extras),
consumed by `inspect_inventory`, and reopened through fresh runtime compositions
with network denied and a provider that cannot count or infer: no dispatch, no
result change. Every accepted inventory kept confidence ≤0.5, live/paypal_only
false, REST `unqualified`, and zero runtime-recall placeholders.

## Demonstrated limits

- **Haiku ≥3 files:** emits 5–7 tool calls in one response (cap 4) despite two
  instruction variants. Sonnet 5.5 (`between_tools`, same caps) split 4+3 and passed
  2/2 at ≈$0.076/run (~34× Haiku). No silent profile switch: Haiku stays the default.
- **Context bound:** conservative byte bound 22,976 leaves ≈4.5 KB of observations;
  a 6 KB probe and a 10-file probe are held before dispatch (offline dry run).
- Secret-like source and >16 files / >16 KB packages are rejected before any task.
- Literal catalog only; dynamic calls, REST mappings, runtime recall, merchant/payment
  and production GU/VJ/SH services remain unqualified. Sponsor phase N/A.

## Remaining gate

The original `surveyor-nvp-baseline-v1` turn (10 Nov 20:18 UTC) has no attributable
provider record. Every later request ran on 11 Nov UTC, so a Console usage-by-day
view showing **zero tokens on 10 Nov UTC** next to non-zero 11 Nov totals would
attribute it. That needs Aditya's signed-in Console or an Admin API key, and neither
was available here (no Claude-in-Chrome tools this session). Until then, $0.012672
stays reserved.

Evidence: `~/reports/goldgraft-model-gateway-20261111/continuation-04/` and
[manifest](SURVEYOR_MODEL_GATEWAY_MANIFEST_C04_2026-11-11.json). Checks: 620 affected
tests, Ruff lint/format, `git diff --check`. Preservation: 454 frozen inputs, 327
original hashes, HEAD/status, `pieces/web`, original batch/turn, ledger integrity ok.
