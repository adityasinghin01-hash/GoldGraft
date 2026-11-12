# Local browser tooling

The PHP reference now has a working [portable runtime](../docs/vijay/PORTABLE_RUNTIME.md). `python scripts/portable_lab.py` runs its local PHP/HTTP/restart and Playwright checks. `check-reference-browser.mjs` is invoked by that helper with per-run local configuration; it blocks external requests and does not test PayPal payments.

From the personal repository root, run `npm ci --ignore-scripts`, then `npm run setup:browser`, then `npm run check:browser`. Browser downloads stay in ignored `.context/playwright-browsers/`.

`playwright.mjs` runs the installed Playwright CLI using that local browser cache. `check-browser.mjs` verifies Chromium launch, a local DOM interaction and cookie isolation between browser contexts. It performs no payment or sandbox test.

The first smoke used Node 24.13.1. The actual PHP/browser lab has now also passed using team Node 22.23.4 and Python 3.12; full service/isolation compatibility remains unqualified. See [portable runtime](../docs/vijay/PORTABLE_RUNTIME.md) for the D: installer and explicit --node command. Global PATH is unchanged.

## Private sandbox configuration

Follow [SANDBOX_SETUP.md](../docs/vijay/SANDBOX_SETUP.md), then double-click `configure-sandbox.cmd` or run `python scripts/sandbox_config.py --configure` in your own interactive terminal. Inputs are hidden and saved only to ignored `.secrets/sandbox.json`. `python scripts/sandbox_config.py` reports presence without printing values. No provider request runs during setup.

`live_sandbox_probe.py` accepts an explicit `--config .secrets/sandbox.json`; actual credential probes also require `--live` and a local `--authority-ref`. Correct sandbox authority must be established separately. They perform only OAuth/GetBalance, never checkout/payment proof. Ordinary unit tests are offline; 30 pass with Python 3.12.

## Current readiness report

`python scripts/phase1_status.py --config .secrets/sandbox.json` performs local inspection only. It records operator-reported credential success separately, checks source/current Node 22 component evidence and lists all fourteen payment scenarios as BLOCKED. Exit 2 and phase1_gate HOLD remain intentional until the qualified broker/runner/recorder/proof integration exists. See [counterpart handoff](../docs/vijay/PHASE1_HANDOFF.md). No payment, network call or teammate message is sent by this report.

## Phase 2 baseline characterization

`python scripts/phase2_baseline.py --node "D:\DevTools\GoldGraft\node-v22.23.4-win-x64\node.exe"` runs three offline OLD and three offline OLD_TWIN local component checks. It calls `portable_lab.py --characterize-store`, which exercises the original order store with synthetic records and records corruption behaviour in a separate disposable copy. Source bytes remain unchanged, no PayPal calls run, and local success cannot pass either full phase gate. See [Phase 2 status](../docs/vijay/PHASE2_STATUS.md). The expanded combined suite has 34 tests; the earlier Phase 1-only count was 30.
