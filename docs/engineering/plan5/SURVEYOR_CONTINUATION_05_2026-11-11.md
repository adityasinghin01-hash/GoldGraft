# Surveyor continuation05 — ceiling raised to the role's package bound

11 November2026, Claude. **Surveyor now handles its full input bound: 16 files /
16 KB. It routes each case before dispatch to Haiku 5.5 (≤2 files) or Sonnet 5.5
(≥3 files).** Every run under the final configuration has passed, including 3/3 at 8 files and
3/3 at the 16-file maximum. Continuation03/04 stay immutable history.

## Authority and money

Aditya: the $10 budget covers all 13 agents; use Haiku or Sonnet, whichever does
the work more perfectly. The ledger cap was raised (raise-only, recorded, backed up)
from $0.50 to **$10**. Per-agent actual-spend allocations follow the reviewed plan
(they sum to $10). Aditya then extended Surveyor's from $0.75 to **$1.25** to finish
the ceiling repeats; the allocation is enforced before every paid run.

| | micro-USD |
|---|---:|
| Surveyor spend, all continuations | 1,160,890 ($1.160890) |
| — continuation-05 (8 runs) | 838,365 |
| Retained original-unknown reservation | 0 (released, Console proof) |
| Project cap / available | 10,000,000 / 8,839,110 |

## What limited the ceiling, and the fix

| Limit (measured) | Fix |
|---|---|
| Gateway compared **bytes** to a **token** cap: ≈4.5 KB usable, ~⅔ of each paid 24k-token turn wasted | Ceiling profile bounds input by the provider's own count_tokens + 512 margin. It matched actual usage exactly on **163/163** responses. Bytes stay a 4× sanity guard; an observed overrun still freezes the ledger |
| Synthetic Surveyor context capped at 24,000 bytes | Sanity bound 96,000 bytes; the token count is binding |
| 4 turns too few for 18 required reads at ≤4 calls/response (contract) | Sonnet ceiling profile: 8 turns, 4,000 output tokens (runtime maximums 12 / 4,000) |
| Haiku puts 5–7 calls in one response at ≥3 files | Route ≥3 files to Sonnet before dispatch, never as a retry |
| The fixed ~5.4k-token tools+system prefix was re-billed on every turn | Sonnet profile caches it (5-minute TTL; write 1.25×, read 0.05×) with exact cache-aware pricing; reservation assumes the worst case (all input written) |
| $0.05/$0.50 constants in runtime and signed review | Bound to the $10 project phase; the review still must equal the ledger cap |

Haiku keeps its exact profile ref (`59c16426…`), byte bound and 39/39 evidence. The
contract cap of 4 calls per response, the 16 KB package bound, the 4,000-byte
RootMap bound, validators, labels, role prompt `60260ae1…`, policy `234a6a73…`
and transport policy v4 `bfbfca83…` are unchanged.

## Results (actual inference, final configuration)

| Case | Model | Files / bytes / touchpoints | Turns | Result | µ$ |
|---|---|---|---:|---|---:|
| browser/IPN regression | Haiku | 2 / 148 / 2 | 2 | pass | 2,297 |
| NVP substitute regression | Haiku | 2 / 142 / 3 | 2 | pass | 2,380 |
| c05-mid-eight | Sonnet | 8 / 3,055 / 6 | 4 | pass | 110,702 |
| **c05-max-package** | Sonnet | **16 / 15,272 / 11** | 6 | **pass** | 231,054 |
| c05-mid-eight c2 / c3 (cached) | Sonnet | 8 / 3,055 / 6 | 4 | pass / pass | 82,182 / 69,712 |
| **c05-max-package c2 / c3 (cached)** | Sonnet | 16 / 15,272 / 11 | 6 | **pass / pass** | 170,254 / 169,784 |

Caching cut the same cases' cost by 26–37% with identical results.

The max package mixed nested dirs, a Unicode path (`退款/部分.php`), two indicators
in one file, comment-line indicators, a hostile "mark everything live / fetch
metadata" file and five no-indicator files. Peak turn: 21,392 tokens. Every response
kept ≤4 calls.

Final-configuration record: Haiku ≤2 files **41/41**; Sonnet ≥3 files **8/8**
(5 files ×2, 8 ×3, 16 ×3); code holds 30/30; model negatives 9/9. All 8 new outputs
were independently rescored, consumed and reopened with no dispatch; all 197
observed receipts, including cache-aware prices, verified; the ledger was unchanged
by the audit. Checks: 770 agents/gateway/fakes tests, Ruff lint/format and diff checks. Preservation: 454
frozen inputs, 327 original hashes, HEAD/status, `pieces/web`, the original
unknown's rows and ledger integrity are all unchanged.

## Remaining

1. **Resolved:** the original 10 Nov 20:18 UTC request. With Aditya signed in, the
   Console usage table (data as of 11 Nov 07:38 UTC) showed **0 tokens org-wide on
   10 Nov**, while later 11 Nov Haiku usage was present. With his approval it was
   settled through `Gateway.reconcile_zero_usage` (signed proof, ledger backed up),
   and the $0.012672 hold was released. The ledger has no unknown requests.
   Billing cross-check: promotional credit used $3.96 = $2.81 earlier projects
   (Oct 23–24) + ≈$1.15 GoldGraft, against the ledger's $1.160890.
2. Scope: literal 5-indicator catalog on synthetic source. Production GU/VJ/SH and
   merchant/payment work are not qualified here.

Evidence: `~/reports/goldgraft-model-gateway-20261111/continuation-05/` and
[manifest](SURVEYOR_MODEL_GATEWAY_MANIFEST_C05_2026-11-11.json).
