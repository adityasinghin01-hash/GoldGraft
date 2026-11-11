# Pushed-work integration verification

11 November 2026. Scope is the seven current GitHub branch heads recorded in SOURCE_PINS.json and their fixture-backed supported behavior.

- Full suite selecting the actual proof and composed backend: **1,502 passed, zero failures, zero skips**. Includes real PHP execution of all twelve planted checkout mutants.
- Standalone backend → submitted runner → independent proof → ledger → API → restart: **PASS**, nine scenarios, 208 CMEL events, 272 ledger entries, intact ledger chain. Restart performs no new execution.
- Nine verdicts: five PASS, one PASS_FIXED, two PROBLEM, one UNVERIFIED. These are preserved expected fixture outcomes.
- Node switch: **207 cases passed**.
- All five revised Postman requests and their checked-in assertions passed against the composed backend using an offline Node VM implementation of the response/environment/expect API subset used by this collection. This is a local assertion replay, not a Postman cloud run.
- Whole-repository Ruff, specification coverage (193 field paths, 108 enum values), generated parity (42 schemas and 24 OpenAPI paths), TypeScript and staged/unstaged whitespace checks passed.
- Concurrent start, conflicting replay, atomic failure, missing run, archive-only reads and tampered ledger/input blobs are covered by the integration tests.

No external provider/model/payment/signing/deployment call or notification was made. Elastic use here is document formatting, Zapier remains disabled, and the unsupported callbacks are held. These limits describe the published code's implemented scope rather than unfinished future work being included in this task.

Source preservation: all 1,016 files from the earlier broader local integration were moved to a report archive before rebuilding this branch from the pushed merge tree. Original and Claude worktrees were not edited. The branch contains no unpublished Plan5 bootstrap/runtime/model-gateway work. Private state and runtime artifacts remain excluded from Git.

Detailed logs and saved end-to-end evidence: `~/reports/goldgraft-pushed-integration-20261111/`. Git publication status is recorded by the final task handoff after verification.
