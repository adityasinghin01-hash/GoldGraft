# Adversary — real-model test, 11 November 2026

**ACCEPTED MODEL COMPONENT SCOPE.** Actual guarded runtime and component gateway, original synthetic
MIT cases and scripted tool/control/collector counterparts. Model/profile routing
is fixed before dispatch; no infrastructure or live-shop qualification.

| Measure | Result |
|---|---|
| Final sample | **28/28 passed**; rounds g0, g1, g2, g3, h0, h1, h2, h3 |
| Output acceptance | 16/28 produced accepted artifacts |
| Audit | 28/28 clean: receipts, rescore, output use, reopen |
| Hostile preflight | 3/3 held, $0, zero model calls |
| Free replay | 10/10 (not a model-quality score) |
| Profiles | haiku8, sonnet |
| Turns | 3–3 per run |
| Latency | 6.81s median; 13.79s max |
| Role spend | $0.454404 of $1.20; all rounds |
| Project spend | $3.145659 of $10; no unresolved turns/reservations |
| Checks | 117–120: full regression and lint/format/diff |
| scored | 16/16 correct |
| model_hold | 12/12 correct |

| Capability | Evidence |
|---|---|
| Guard coverage | Supported pending-capture operator; unsupported rule ids explicitly unguarded |
| Staged bundle | ScenarioSet/1 and MutantSet/1 bound to staged payloads |
| Fork request | RawCapture/1 requested only from separately owned disposable fork |
| Receipt holds | Incomplete, unknown and candidate-mutated receipts require model hold |

| Fix | Reason |
|---|---|
| Invariant review | Model labels/unique ids accepted, substantive guard fields and stage-to-final binding exact |
| Operator bound | Unrelated predicate cannot silently get a pending-capture mutant |
| Inline staging | scenario.stage gets typed inline scenarios and mutants; execution.request reused |
| Scoped facts | Metadata ids, explicit request-before-status sequence; no proof verdicts supplied |
| Replay correctness | Inline draft producer labels match reference metadata; explicit rule-prefix derivations recognized |
| Guard route | Repeated Haiku invented guards and malformed staged calls; all guard derivation now Sonnet, fork requests Haiku8 |

Decisions: case labels were fixed before paid runs; no post-result relabelling.
Independent labels are excluded from model context. Artifact output inspection and
read-only reopen are evidence of synthetic consumer use, not teammate service acceptance.

Limits: Only one synthetic pending-capture mutation operator, not general guard synthesis. Unsupported rules remain unguarded. Tool/control/collector/fork effects are stand-ins; SH owns actual kills/equivalence. No Kernel/Postman connection. Initial p1 2/7 passed: fork status-before-request fixed; two-rule inline-validation failure (729 output tokens, not output-cap exhaustion); its exact malformed field was not retained. Source reads, staging and output review are real own-runtime checks, not proof of container isolation. Labels unchanged; unsafe output never accepted. Baseline g0–g3 22/28 retained. Final selection fixed before h runs: all 20 unchanged-route runs plus all 8 new Sonnet guard/empty-operator runs, no result-dependent exclusions; only routing changed for reused runs.

Evidence: `~/reports/goldgraft-all-agents-20261111/adversary/` (cases, dry runs,
series log and audit); run artifacts at `~/reports/goldgraft-model-gateway-20261111/live/ag-adversary-*`.
