# Scribe (agent 7) — real-model close-out, 11 November 2026

**ACCEPTED MODEL COMPONENT SCOPE.**
Model for existing final rounds: **Claude Haiku 5.5**, `haiku8` profile.
Actual runtime/gateway; synthetic source, evidence and tool/control counterparts.

| Measure | Result |
|---|---|
| Final series | **28/28 passed**; 7 cases × 4 |
| Audit | 28/28 clean: ledger, receipts, rescore, output use, reopen |
| Hostile preflight | 4/4 held, zero model calls, $0 |
| Offline regression | 862 passed; one existing Pydantic warning |
| Lint / format / diff | Checks 62 / 63 / 65 passed |
| Free dry run | 11/11; largest wire 12,268/22,976 bytes |
| Scribe spend | $0.124970 of $1.00, including interrupted batch cost $0.000626 |
| Project spend | $1.927898 of $10; zero uncertain turns/reservations |

| Capability | Completed evidence |
|---|---|
| Normative preservation | Predicates, severity, flows and code basis retained |
| Evidence grading | CODE_ONLY/BOTH; mapped OLD and OLD_TWIN refs |
| Followup requests | Missing trace basis; multiple rules |
| Injection refusal | Source instructions do not waive predicates |
| Grounded output | Contract/1 and TriangleRequest/1 resolved, inspected and reopened |

Fixes inherited from the handoff: exact-output review became normative invariants;
opt-in unread read progress avoids re-reading; read pairing permits independent
reads in any order while retaining write positions; the followup reason policy
states the literal waiver/proof word guard. Earlier handoff results were p1/r1–r3
25/28 and f0–f3 27/28. This session changed no implementation or case labels.

Decisions: g2r's `sc-three-rules` replaces the interrupted g2 case in the final
28-run denominator. The interrupted batch is excluded from quality scoring but
its $0.000626 actual remains included in spend. Aditya approved clearance of the
never-submitted turn; Claude used the existing `abort_intended`/close path.
`scribe/USER_APPROVAL_CLEAR_INTENDED_G2.json` records the approval. The original
batch identity was never replayed. This session completed only the nine missing
runs, then audited all 28 completed runs. No labels changed.

Limits: no Elastic connection, live shop, independent payment proof or production
qualification. Four hostile cases exercise deterministic preflight refusal, not
paid-model resistance. The finite synthetic sample does not establish universal reliability.

Evidence: `~/reports/goldgraft-all-agents-20261111/scribe/`:
`AUDIT_g0-g1-g2-g2r-g3.json`, `DRYRUN_haiku8.json`, the dated `CODEX_LEDGER_BLOCKER.json`, clearance record, cases
and existing series log. Checks: `61-full-regression-scribe3`, `62-lint-scribe3`,
`63-format-scribe3`, `65-diff-scribe-closeout`. Qualification records refreshed for all
three profiles; qualified for synthetic component evaluation only.
