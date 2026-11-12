# Phase 2 — independent baseline characterization

Current local continuation: [LOCAL_PHASE_DELIVERY.md](LOCAL_PHASE_DELIVERY.md) adds a separate NEW candidate domain and scripted browser harness. The original six-run baseline results below are unchanged. A candidate is now implemented locally; no NEW genuine payment or protected runtime is qualified.

Started locally on 8 November 2026 at the user's request. **Full Phase 1 and Phase 2 qualification remain HOLD.** This slice advances the independent VJ01 baseline preparation allowed by current requirements; it does not bypass GU02/GU03 or authorize a new shared contract, payment, deployment or push.

## Sources and scope

The current Drive guide and team main were rechecked before this work. Guide modification remains 6 November 2026 09:29:50 UTC; main remains `da2b5f02d5559c510de6b3b9d81e58400bdf6c89`. Scope is still the pinned MIT plain-PHP reference, not the superseded Zen Cart/eleven-shop programme. See [CURRENT_BASELINE.md](CURRENT_BASELINE.md).

Documented requirements come from [VJ01](https://github.com/adityasinghin01-hash/GoldGraft/blob/da2b5f02d5559c510de6b3b9d81e58400bdf6c89/docs/START_Aditya_Vijay_paypal_shops.md) and [baseline reproduction](https://github.com/adityasinghin01-hash/GoldGraft/blob/da2b5f02d5559c510de6b3b9d81e58400bdf6c89/docs/engineering/lifecycle/BASELINE_REPRODUCTION.md): unchanged source, independent OLD/OLD_TWIN state, actual observed behaviour and baseline defects separated from correctness. The specific local helper and six-run sequence are implementation proposals, not new shared wire formats or a claim that the documents prescribe this exact test.

## Implemented slice

- `lab/order_store_check.php` calls the unchanged original `orders_save`, `orders_get` and `orders_all`. It seeds two unmistakably synthetic records, updates one without losing the other, and verifies them after an actual server process restart. It refuses to seed or corrupt a preexisting order file.
- A separate disposable source/state copy exercises malformed JSON. The normal seeded run store is preserved. No vendor source is edited.
- `portable_lab.py --characterize-store --variant OLD|OLD_TWIN` adds actual order-store component observations to the existing protected local HTTP/cart/restart checks. All PayPal functions/requests remain disabled; no credentials are passed to PHP.
- `phase2_baseline.py` runs three independent checks per baseline label, records unique run/storage/source identities and rejects incomplete, duplicated-state or drifted-source results. It does not produce JobResult/RawCapture or invent GitHub runner identity.
- Four meaningful negative tests check duplicate run/state, missing repetition, source drift, health-only results and improper runtime/payment qualification claims. The combined offline suite passes 34 tests on Python 3.12.

## Execute and inspect

Run in CMD from the repository root using the existing portable installations:

```cmd
python scripts/phase2_baseline.py --node "D:\DevTools\GoldGraft\node-v22.23.4-win-x64\node.exe"
```

Use Python 3.12 for the team-aligned run. Reports remain ignored at `.context/phase2/baseline-result.json`; individual source copies, synthetic state, screenshots and local keys stay under each distinct D: run directory. No provider transaction is created, reset or erased. The command returns 0 only for its local component checks, with `phase2_gate: HOLD`, `qualified_purchases: 0` and `runtime_qualified: false` still explicit.

## Observed baseline defect

Actual execution completed: all six component runs passed, three OLD and three OLD_TWIN, with six distinct run/state directories and identical unchanged source hashes. First run `20261108T130829004809Z`; last run `20261108T130914437592Z`. Each passed Node 22 browser/cart/access checks and actual unchanged-order-store persistence across restart. Corruption behaviour was reproduced in all six separate corruption copies, whose invalid input bytes remained preserved. There were zero provider requests from these runs and zero qualified purchases. Detailed local evidence is in the ignored report described above.

The unchanged order store returns an empty array for malformed `orders.json`, with no explicit corruption error. This was reproduced using only synthetic invalid JSON in separate disposable copies. Treating unreadable financial state as an empty shop could conceal existing obligations; this is a characterized baseline defect, not a passing money rule or a production-loss incident. A candidate fix needs its own approved implementation and tests; the baseline remains unchanged for comparison.

Synthetic record persistence is narrower than payment/order correspondence, concurrent-writer safety, backup migration or callback durability. Three cart checks per label are not three paid purchases. No NEW candidate has been implemented or certified by this slice.

## Remaining gates

Qualified protected source/image/runtime, GU02 broker, GU03 actual recorder/callback gateway, approved shared formats where needed, genuine scenario executions and proof-owner verdicts remain required. [TEAM_INPUTS_NEEDED.md](TEAM_INPUTS_NEEDED.md) lists the current team inputs. No switch, state migration, finalisation or exit claim is introduced here. Nothing was pushed during this phase start.
