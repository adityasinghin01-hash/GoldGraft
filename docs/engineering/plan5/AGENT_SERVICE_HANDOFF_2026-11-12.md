# GoldGraft agents — handoff (12 Nov 2026, morning)

Owner of this work: Aditya (built by Claude overnight, Codex built the API layer).
Main branch commits: `a290a56` → `3a8082e` (see `git log`); frontend on `aditya/web` (`be49723`+).

## What works now

| Piece | State |
|---|---|
| All 13 agents in one connected run | Gardener → Surveyor → Herald → Builder → Explorer ×4 → Scribe ×2 → Architect → Grafter → Builder → Explorer → Adversary ×2, plus Healer, Sentinel, Librarian, Orchard Analyst on the same run. Every edge carries the previous agent's committed output (`EDGES.json` per run). |
| Real AI calls | Every agent turn goes through the budget gateway (ledger, receipts, caps). Haiku for simple tasks, Sonnet for complex ones (Surveyor on ≥3 files, Architect, Adversary guard design, Grafter writing code, Gardener >5 nodes). Two scored Haiku failures on a task shape move it to Sonnet automatically (`ROUTING.json`). |
| Real code fixing | The Surveyor maps the submitted shop's real files; the Architect plans from that map; the Grafter (Sonnet) **writes the new PHP itself** for the shop's real payment files against the GoldGraft Orders v2 library; deterministic review refuses old NVP/IPN calls left behind, missing planned operations, a missing library include, secrets, or marking an order paid on a non-COMPLETED capture; a real PHP parser checks every candidate file. |
| Frontend | Live mode shows real runs: Progress (real stages and per-agent AI cost), Old pieces (the Surveyor's real map), **Code changes** (line diff of the AI-written code), My upgrades → **Real agent runs**. Starting an upgrade for a repo containing `legacy-php-shop` or `eval-nvp` starts a real run. |
| Tests | Offline (no network): agents + gateway + fakes suites green; `pieces/agents/tests/test_integrated.py` (19), `plugtests/test_agents_app.py` (13). |

## Run it (on this Mac)

```bash
# 1. agents API (real runs; --live lets the frontend start new real runs)
cd ~/dev/GoldGraft-plan5-build
PATH=/Library/Developer/CommandLineTools/usr/bin:$PATH .venv/bin/python -m integration.agents_app --port 8710 --live

# 2. frontend in live mode
cd ~/dev/GoldGraft-web/pieces/web
VITE_API_BASE=http://127.0.0.1:8710 VITE_DEMO_TOOLS=true npx vite --port 8782
#    open http://127.0.0.1:8782/my  → Real agent runs → pick a run → Progress / Old pieces / Code changes
#    or  /connect with repo https://github.com/goldgraft/legacy-php-shop → Start → watch a real run (~4 min, ≈$0.35)

# 3. one real run from the command line (≈$0.35, cap with --max-usd)
PATH=/Library/Developer/CommandLineTools/usr/bin:$PATH \
  ~/reports/goldgraft-model-gateway-20261111/venv/bin/python -m scripts.live_integrated_run \
  --live --run-id my-run-1 --shop legacy-php-shop --max-usd 0.95
#    evidence: ~/reports/goldgraft-agents-integration-20261112/runs/my-run-1/{RESULT,OUTPUTS,EDGES,CHANGES}.json
```

Model keys and the gateway signing key live in `~/.config/goldgraft/` (never in the repo). Port 8700 is the old stand-in API.

## What is real and what is not (say this in the demo)

| Real | Not real yet (labelled in the app) |
|---|---|
| All agent reasoning and outputs (real Haiku/Sonnet calls, ledgered) | Builds and payment scenario runs use recorded runner counterparts ("scripted runner"): no Docker/PHP on this Mac |
| The shop's real source, the Surveyor's real map, the Architect's real plan, the Grafter's real code | No independent SH proof/certificate on the AI-written candidate yet (the app stops at "Proving every payment") |
| PHP syntax check of the AI-written files | The new code has not been run against PayPal's sandbox |
| Budget, receipts, two-strike Sonnet escalation, bounded survey re-attempts | Librarian learns from its qualified de-identified template (consent recorded as an assumption for the MIT sample shop) |

## Results

See `ROUND1_RESULTS.md` next to this file for per-run and per-agent numbers, and
`~/reports/goldgraft-agents-integration-20261112/PROGRESS.md` for the overnight log.

## For the team today

| Who | Most useful next step |
|---|---|
| Gupta (backend/runner) | Run the candidate tree (`CHANGES.json`) in a real PHP container (Builder/Explorer NEW) instead of the recorded runner |
| Singhal (proof) | Point the SH proof at the AI-written candidate and issue a certificate for a real run |
| Vijay (shops/recipes) | A second real shop (different code style) in `scripts/live_integrated_run.py` `SHOPS` |
| Frontend | Test live mode screen by screen; Code changes is new |

## Rules that still hold

No ledger edits or resets; no cap raise without Aditya; tests never call the network; any edit to a file listed in
`~/reports/goldgraft-all-agents-20261111/make_qualification.py` FILES needs the four checks (`run_check.py`) and
`make_qualification.py`, or live runs refuse with `QUALIFICATION_STALE`.
