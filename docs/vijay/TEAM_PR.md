# Vijay contribution — team integration entry point

This change adapts the published personal contribution at `adityavijay3659-sketch/goldgraft@4b231b2` to team main `c209bf6`. The team's root README, AGENTS, contracts, backend, proof and frontend are preserved. Personal history and planning documents are namespaced under `docs/vijay/`.

## What plugs in

- `pieces/shops/vijay-php-reference/recipe.py`: accepted shop-socket entry point; nine existing shared scenarios; unchanged licensed source. It admits only the explicitly reviewed operator fixture for unisolated host execution. Other agent candidates hold for protected execution.
- `pieces/shops/legacy-php-shop/candidate/`: durable USD PHP component, private stdio broker binding, callback-to-original-rail reconciliation and an explicitly offline browser harness. The compatibility fixture and durable candidate remain distinct.
- `lifecycle_recipes.py`: executable VJ03/VJ04/VJ05 domain checks against current shared records; these do not execute merchant state migration, deployment or exit.
- `pieces/switch-libs`: native PHP/Node/Python verification, caches and persistent-origin routing. The existing Node camelCase exports remain available; its default CI runner still works. New compatibility checks exercise all 207 shared cases through both APIs.
- `tools/sponsors`: typed APIMatic/SDK examples, local Newman assets and Kernel scenario preparation; no account/credit entitlement or remote integration is assumed.

## Team-repository adaptations

Tests now run through the team's existing `pytest` suite (`tests/`, `integration_tests/` added). New Python files follow team Ruff rules. Native PHP tests use the configured PHP on Unix or the explicit portable flags on Windows; an unavailable PHP/SQLite capability produces an explicit skip, not qualification.

The host checkers default to the current team checkout and current Python interpreter instead of requiring Vijay's separate D: checkout. External compatibility checkouts retain reviewed revision checks. The actual Git revision is recorded, not inferred as runtime or authority qualification. `prepare_local_contracts.py` restores exact unchanged contract blobs without CRLF drift.

Playwright 1.64.1 is added as a pinned development dependency for the buyer scripts; existing dependencies are retained. Node 22 remains required. The team's existing public Node switch API is preserved.

## Commands

```sh
uv sync --locked
uv run pytest -q tests integration_tests plugtests/test_shops.py plugtests/test_switch_libs.py
uv run python scripts/check_team_boundaries.py
uv run python scripts/check_shop_integration.py
node pieces/switch-libs/node/run_cases.mjs
node pieces/switch-libs/node/test_compat.mjs
```

Use PHP with curl, OpenSSL, Sodium and PDO SQLite configured for the relevant native checks. On Vijay's Windows machine, `VIJAY_PHP` selects the documented portable executable. Optional Playwright/browser checks need the browser binaries and the local runtime metadata described in [HANDOVER.md](HANDOVER.md). No ordinary check is permission to call a real provider/model or start a cloud job.

## Evidence and limits

The original personal-worktree results are recorded in [LOCAL_CHECK_RESULTS.json](LOCAL_CHECK_RESULTS.json): ten local groups passed, seventeen actual-counterpart tests passed, 27 fresh simulated-PayPal recordings, eight PASS/one PASS_FIXED scenario verdicts, and two executed mutations caught. That historical result is distinct from the team-base validation attached to this PR.

Connected proof deliberately retains 29 verified checks and ten holds: eight missing critical mutation guards plus genuine shop-payment/isolation evidence. Promotion and certificate remain held. Fourteen role-wide scenarios remain registered; nine socket cases do not replace that scope. No public callback listener, genuine payment, protected runtime, merchant deployment/state transfer or independent merchant exit is qualified by this PR.

No credentials, auth state, installed dependencies, databases or raw local recordings are included. This PR does not request a main-branch merge or a deployment automatically.
