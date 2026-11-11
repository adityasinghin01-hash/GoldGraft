# Explorer (agent 6) — real-model test, 11 November 2026

Model: **Haiku 5.5** (`haiku8` profile). Explorer requests one exact scenario capture
(variant OLD / OLD_TWIN / NEW) and accepts only an exact, complete recorder capture.

## Result

| Measure | Value |
|---|---|
| 9 cases × 4 runs (p1, r1–r3) | **35/36** |
| Bad captures held by the model (wrong variant, wrong flow, partial, stale image, unknown) | 19/20 |
| System safety (nothing wrong accepted) | 36/36 |
| Hostile inputs (NEW without Contract, invalid driver, unqualified recipe) | 3/3 held, $0 |
| Explorer spend | $0.066002 of $1.00 |
| Cost per run | ~$0.0018 (3 turns) |
| Project spend now | $1.802928 of $10 |

## What it can do

| Capability | Shown by |
|---|---|
| Exact variant | OLD, OLD_TWIN, NEW |
| Flow binding | capture, refund |
| Capture checking | 4 mismatch kinds held |
| No proof claims | partial capture held |

## Notes

- Reuses Builder's inline staging and execution facts; review compares the normalized proposal.
- The one miss: a response mixing `execution.status` with a repeated `execution.request`; the runtime denies mixed read/write batches (fail-safe).
- Kernel/Postman (optional sponsors) deferred; recorder and captures are scripted stand-ins.

Evidence: `~/reports/goldgraft-all-agents-20261111/explorer/`; runs `ag-explorer-*`. Checks 45–48 (853 passed).
