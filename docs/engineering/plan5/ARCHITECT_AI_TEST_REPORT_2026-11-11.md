# Architect — real-model test, 11 November 2026

**ACCEPTED MODEL COMPONENT SCOPE.** Actual guarded runtime and component gateway, original synthetic
MIT cases and scripted tool/control/collector counterparts. Model/profile routing
is fixed before dispatch; no infrastructure or live-shop qualification.

| Measure | Result |
|---|---|
| Final sample | **27/28 passed**; rounds g0, g1, g2, g3, h0, h1, h2, h3 |
| Output acceptance | 23/28 produced accepted artifacts |
| Audit | 27/28 clean: receipts, rescore, output use, reopen |
| Hostile preflight | 3/3 held, $0, zero model calls |
| Free replay | 10/10 (not a model-quality score) |
| Profiles | sonnet |
| Turns | 2–3 per run |
| Latency | 7.59s median; 19.38s max |
| Role spend | $0.666534 of $1.00; all rounds |
| Project spend | $2.594432 of $10; no unresolved turns/reservations |
| Checks | 74–77: 865 tests; lint/format/diff clean |
| scored | 23/24 correct |
| model_hold | 4/4 correct |

| Capability | Evidence |
|---|---|
| Exact mapping | 1, 2, 4 and 6 distinct touchpoints; installed symbols only |
| Payment scope | EC_NVP and IPN; no deltas or account changes |
| Conflict hold | 4/4 Sonnet holds for final flag vs draft evidence |
| Safe rejection | 3/3 hostile preflight; one malformed final held |

| Fix | Reason |
|---|---|
| Invariant review | Free handoff wording and set order; hard mappings/order/scope unchanged |
| Conflict guard | Contradictory final evidence rejected in review; red→green unit test |
| Scoped facts | Read progress, pinned arguments and literal handoff word guard |
| Model route | Haiku duplicate outputs and note holds twice; all-Sonnet before dispatch |
| Audit completeness | Case digests and every bundle member now checked read-only |

Failed final runs (held, not hidden): `ag-architect-ar-ipn-h2`.

Decisions: case labels were fixed before paid runs; no post-result relabelling.
Independent labels are excluded from model context. Artifact output inspection and
read-only reopen are evidence of synthetic consumer use, not teammate service acceptance.

Limits: Selected final sample 27/28, not perfect reliability: one Sonnet IPN native-output failure held. Earlier p1/r1–r3 23/28 and g0–g3 24/28 are retained. Haiku handoff wording/native-call reliability is unqualified. Sonnet is now the sole route. Maximum tested 6 touchpoints; no APIMatic connection or actual installed SDK qualification.

Evidence: `~/reports/goldgraft-all-agents-20261111/architect/` (cases, dry runs,
series log and audit); run artifacts at `~/reports/goldgraft-model-gateway-20261111/live/ag-architect-*`.

Final selection: `architect/FINAL_SELECTION.json` was fixed before h runs. It retains all 16 g0–g3 Sonnet results for unchanged shapes and all 12 h0–h3 Sonnet results for newly routed shapes. No result-dependent removal; one failed h2 IPN remains in the denominator. Models and policy unchanged for the reused Sonnet runs; the last change only widened model routing.
