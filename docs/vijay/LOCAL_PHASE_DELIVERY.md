# Local phase delivery — 12 November 2026

**Superseded by the later continuation:** [FINAL_LOCAL_STATUS.md](FINAL_LOCAL_STATUS.md) records actual PHP/broker/callback integration, current SI01 lifecycle models, an accepted recipe and connected proof. The missing local bridge/recipe statements below describe the earlier slice and are now historical.

This is the current implementation report. The user deferred real-time payment checks and authorized continued local work. Component completion and full phase qualification remain distinct.

## Published scope

Phase 0 preparation was already published in `60f6ab2`/`e5c25ad`. The user's new Phase 0-only publication is verified on personal `main` at [9144ab274a6bb575e83d0da1332a32b63bdb3ab1](https://github.com/adityavijay3659-sketch/goldgraft/commit/9144ab274a6bb575e83d0da1332a32b63bdb3ab1), adding only `docs/PHASE0_COMPLETE.md`. No later local implementation was included. Leader repository remains unchanged by us.

## Refreshed engineering context

The Drive guide still has the 10 November amendment (modified `2026-11-10T08:46:08.891Z`). Team main advanced to [525c22de61b504f67ea633e5aac95b8bed0fda64](https://github.com/adityasinghin01-hash/GoldGraft/commit/525c22de61b504f67ea633e5aac95b8bed0fda64). The earlier `25e2159` review is a dated snapshot.

Source inspection now finds actual sandbox POST/GET broker operations and durable request identities, plus real IPN postback/webhook verifier components and a callback inbox. This supersedes the older statement that only header checks exist. It does **not** establish qualified end-to-end callback application. `CallbackGateway` explicitly leaves merchant business effects unapplied; its actual wiring, custody and authority must be verified at the boundary.

The current runner still labels `run_job` fixture replay. Its optional host-process scratch copy explicitly reports `isolation_verified=False`; the E2B placeholder refuses execution. Custody remains in memory, with process-environment credentials available only to one explicit operator-named reference. These source findings are not a real service test. Proof PR1 remains merged and its fixture adapter is available.

## Phase assessment

| Phase | Local delivery | Remaining gate |
| --- | --- | --- |
| 0 | **Complete and published:** instructions, plan, source/role map, dependency/register inspection | None for the preparation gate |
| 1 | Scenario inventory, safe credential tools, operator-reported credential probes, source/runtime review | Fourteen genuine sandbox scenarios and qualified captures/callbacks; deferred by user |
| 2 | Frozen source, offline OLD/OLD_TWIN shop and buyer, six independent baseline cart/store/restart runs; NEW candidate domain and browser harness added | Protected exact runtime/image and real baseline/candidate payment correspondence |
| 3 | PHP/Node/Python switch libraries and verified caches; persistent NEW origins/operation IDs; private typed-broker adapter and negative boundary tests | Qualified PHP/backend transport binding, callback/business effect integration, actual counterpart checks |
| 4 | Current-model decision consumer plus actual PHP switch/candidate tests through 0/1/10/50/100, Cutback and expiry with in-flight capture/refund preserved | Shadow evidence, authenticated decisions/config/events, operational apply and measured end-to-end Cutback |
| 5 | State/finalisation/exit domain recipes, read-only original-state inspector; new consistent SQLite inspection and separate-process continuity without temporary transport | GU05 fence/export/bootstrap/replay, merchant-owned runtime and independent authorized exit executor |
| 6 | Runnable checks, source pins, scenario/component coverage and integration handoff | Real counterpart/proof/evidence/demo qualification and final agreed delivery |

All seven full phase gates are **not** complete. The new code closes the previously missing independent candidate-domain slice. State/apply/exit infrastructure belongs to the other owners; their recipes are not relabelled as operating mechanisms.

## New changed files and actual checks

The separate implementation is under `pieces/shops/legacy-php-shop/candidate/`. Its README describes all files and the exact current protocol. No original vendor file was edited. `scripts/check_candidate.py`, `check_candidate_browser.py`, `candidate_lab.py`, `candidate_buyer.mjs` and `check-candidate.cmd` provide repeatable local execution. `scripts/check_all_local.py` now includes both candidate groups. `tests/test_candidate_adapter.py` adds native Python boundary checks.

- Native PHP suite: **108 checks passed** with scripted provider-shaped data; zero provider calls. Hardening also rejects an unrelated/empty existing SQLite file, stored-origin tampering and a capture without a corresponding local operation.
- Independent second PHP process: three persisted order/origin records survive, with zero transport calls on duplicate operations.
- Read-only SQLite snapshots: integrity/resource/origin/operation bindings inspected; unknown refund remains visible. A deliberately tampered synthetic origin is rejected. No merchant migration is attempted.
- Actual PHP + Playwright browser harness: ten actions, four private-route checks, anonymous access denied, repeated capture/refund creates no extra operation, cancellation cannot capture, clean server/state cleanup. All output is explicitly `OFFLINE_SCRIPTED`.
- Python unit suite after adding the adapter: **55 tests passed**. The full aggregate's **ten groups passed**, including 768 switch checks, twelve synthetic rollout checks, 27 cart checks, manifest/sponsor checks, both candidate groups and the original shop/buyer/state checks. Reports preserve their actual run results; later targeted hardening checks are recorded separately.

Evidence files remain ignored under `.context/candidate-tests/result.json`, `.context/candidate-browser/result.json` and `.context/local-profile/result.json`. These are local engineering evidence, not RawCapture/1, proof-owner verdicts, genuine purchases or exit certificates.

## Fourteen-scenario coverage

| Scenario | Local candidate coverage | Still required externally |
| --- | --- | --- |
| S01 create/approve/capture/return | Create/capture/resource/money state; scripted browser lifecycle | Actual buyer approval, return and recorded payment |
| S02 cancel | Browser signal stays nonfinancial; capture denied after cancellation | Actual sandbox cancellation |
| S03 decline | No fulfillment/new dispatch for scripted declined capture | Provider-supported observed decline |
| S04 pending/completed | Pending not paid; fresh GET completion; regression rejected | Actual pending and later verified completion |
| S05 payer action | Action-required state remains unpaid | Product/account support and actual payer action |
| S06 duplicate/two tabs | Persisted reservation before dispatch; reentrant second connection held | Real concurrent browser/provider boundary |
| S07 lost response/restart/retry | Unknown held, no new key; known resource GET recovery | Actual uncertain provider exchange/reconciliation |
| S08 refund/repeated refund | Exact original NEW capture, one intent, pending/minimal read-back | Actual refund and ledger correspondence |
| S09 IPN authenticity/business | Existing inventory and original-rail preservation recipe | Qualified gateway plus original merchant business handler |
| S10 IPN ordering/dedupe | Candidate rejects stale capture/refund regression; this is not IPN execution | Actual raw IPN/authentication/dedupe/effect sequence |
| S11 webhook authenticity | No callback body or caller-supplied verification flag accepted by candidate | Current gateway wiring and trusted business handoff |
| S12 outage/reconciliation | GET-only recovery and unavailable read-back holds | Genuine callback outage and recorded recovery |
| S13 persistence/restart | SQLite journal/origins and actual separate PHP process checked | Qualified persistent runtime/recovery |
| S14 tampering | Trusted catalogue; wrong amount/currency/order/reference/merchant rejected | Actual sandbox tamper boundary/evidence |

No row is marked a genuine payment PASS. The ShopPack's declared payment scenario list remains empty until actual qualified scenarios exist.

## Integration handoff and next steps

No credential re-entry is needed. Run `scripts\check-candidate.cmd` for the new slice or `scripts\check-all-local.cmd` for the implemented local profile. Neither command pushes or calls PayPal.

The private Python adapter maps the existing REST vocabulary to `execute_orders_v2` actions `create`, `capture`, `refund`, `get_order`, `get_capture`, `get_refund`. Backend references and evidence mode are bound at construction. It rejects ambient auth headers, unknown routes, wrong methods/currency and mode changes. Tests use a scripted counterpart; the real PHP/Python bridge and complete backend response/evidence boundary are still to be qualified. Minimal current-broker responses are handled by mandatory resource read-back.

Next integration work uses the actual approved backend/proof revisions: bind the PHP port, exercise the counterpart boundary offline, wire durable verified callback business effects, and then perform the separately scoped protected runtime/payment/state/apply/exit checks when the user resumes those. No new public API, signing schema or infrastructure substitute was invented to make the status green. Further publication requires an explicit request for those later changes.
