# Librarian — real-model test, 11 November 2026

**ACCEPTED MODEL COMPONENT SCOPE.** Actual guarded runtime and component gateway, original synthetic
MIT cases and scripted tool/control/collector counterparts. Model/profile routing
is fixed before dispatch; no infrastructure or live-shop qualification.

| Measure | Result |
|---|---|
| Final sample | **23/24 passed**; rounds p1, r1, r2, r3 |
| Output acceptance | 11/24 produced accepted artifacts |
| Audit | 23/24 clean: receipts, rescore, output use, reopen |
| Hostile preflight | 3/3 held, $0, zero model calls |
| Free replay | 9/9 (not a model-quality score) |
| Profiles | haiku8 |
| Turns | 1–3 per run |
| Latency | 5.90s median; 6.74s max |
| Role spend | $0.050198 of $0.40; all rounds |
| Project spend | $3.244314 of $10; no unresolved turns/reservations |
| Checks | 129–132: full regression, lint/format/diff |
| scored | 11/12 correct |
| model_hold | 12/12 correct |

| Capability | Evidence |
|---|---|
| Quarantine only | Closed deidentified pending-capture template and detection pattern |
| Rights checks | Consent, rights and non-origin selfcheck required |
| Staged bundle | Recipe/1 and DetectionRule/1 match observed staged drafts |
| Selfcheck holds | Failed, wrong-fixture and unknown receipts held |

| Fix | Reason |
|---|---|
| Invariant review | Honest model metadata accepted while recipe content and staged output binding remain exact |
| Inline staging | Typed recipe.stage inputs; existing ExecutionProposal staging reused |
| Scoped facts | Pinned template identifiers/digest and provenance refs; no model-generated hash or signature |
| Call order | Explicit request then status then proposal-or-hold sequence |

Failed final runs (held, not hidden): `ag-librarian-li-quarantine-r3`.

Decisions: case labels were fixed before paid runs; no post-result relabelling.
Independent labels are excluded from model context. Artifact output inspection and
read-only reopen are evidence of synthetic consumer use, not teammate service acceptance.

Limits: One closed synthetic template, not general learning or source reuse. Recipe signature field is an explicit UNSIGNED_SYNTHETIC_QUARANTINE label, not a cryptographic success claim. No ACTIVE promotion, external storage, actual independent corpus, merchant source, sponsor connection or production recipe qualification. Rights, consent and non-origin checks enforced deterministically. Labels unchanged. One of 24 final runs failed inline native validation before recipe.stage; retained as a model failure, no raw/promotion artifact accepted. All12 bad-selfcheck receipts were held.

Evidence: `~/reports/goldgraft-all-agents-20261111/librarian/` (cases, dry runs,
series log and audit); run artifacts at `~/reports/goldgraft-model-gateway-20261111/live/ag-librarian-*`.
