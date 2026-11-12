# GoldGraft agents — handoff (12 Nov 2026)

## Latest (evening): three pieces connected, Vijay socket, live checks

Codex ran out at 15:27; Claude finished the rest and owns all work (see AGENTS.md).
Sections below are earlier history where they differ.

| Piece | State on main |
|---|---|
| SI01 formats | ProofPlan/1, ProofResult/1, PromotionDecision/1, Certificate/2, CertificateVerification/1, ExitCheckResult/1, ExitEvidenceReconciliation/1 (`5b81e1e`) |
| Gupta | `feat/gupta-live-completion` merged; its five unsupported claims corrected (`525c22d`): E2B refuses without a real integration, scratch-copy runner reports `isolation_verified=False`, custody env fallback only for one named sandbox ref, PayPal re-fetch is read-only and uncached, live script uses real buyer approval and invents nothing |
| Connected run | `integration/connected_run.py`: WorkControl case→start→claim→authenticated BASELINE_READ → recipe executes the agents' candidate under the work id → Singhal judge + mutant re-judging → SI01 plan/result/promotion → Certificate/2 attempt. API `GET /grafts/{id}/connected` re-validates records (503 on edits); Proof screen shows it |
| Vijay socket | `integration/shop_socket.py` + `pieces/shops/README.md`: one folder per shop, existing formats only, `conformance()`; the vendored legacy PHP shop is wired through it as `reference_stand_in` |

Live results (all real, 12 Nov):

- PayPal sandbox via the broker: order `4JN01011WL703525P` → capture `4HP47932H07497904` →
  refund `89784014675460948`, each COMPLETED and re-fetched from PayPal (GoldGraft's own sandbox
  app, buyer-approved in a browser; not a merchant shop). Evidence in `~/reports/goldgraft-live-20261112/`.
- `r9-final-connected`: 13/13 agents on real models, $0.475004. Connected run on its AI-written
  code: 29/39 verified (9/9 scenarios, 2/2 planted bugs), 10 held, certificate held at EVIDENCE_HOLD.
- Its ProofResult signed by `.github/workflows/sign-proof.yml` (run 43215822128): Rekor log index
  3832106644; changed copy rejected; hash and workflow identity re-checked by `scripts/live_verify_rekor.py`.

Holds, by design: 8 critical rules without an executed mutation guard (R02 R04 R05 R06 R08 R11 R12 R17),
the shop's own checkout on real PayPal, isolation (no Docker/E2B), exact OCI image, real buyer
traffic for promotion, Vijay's state/finalisation/exit recipes, PayPal webhooks (no public listener),
Render deploy, merchant exit, real login, PostgreSQL.

Commands (this Mac's `uv` is an Intel build whose child `git` breaks; call `.venv/bin/python` directly):

```sh
.venv/bin/python -m integration.connected_run <run dir> --state-dir <run dir>/connected-run \
  [--sandbox-capture <paypal recording>]
.venv/bin/python -m integration.shop_socket --agent-run <run dir> --workdir <new folder>
.venv/bin/python -m scripts.live_paypal_sandbox_payment --authorize-sandbox-payment   # needs a US sandbox buyer
gh workflow run sign-proof.yml -f payload_path=docs/engineering/plan5/signing/<file>.json
.venv/bin/python scripts/live_verify_rekor.py <file> <bundle> --identity <workflow identity>
```

## Step 2 local PHP execution and proof

The morning snapshot below is historical where this update differs. Codex completed the
bounded local plain-PHP check: this is **not** provider/isolation/merchant-delivery qualification.

- Native ARM64 PHP 8.4.27 is installed at `~/.local/bin/php` without Homebrew.
- Architect declares the pinned Orders-library comparison mappings; Scribe's capture rule
  is bound to `R01`. Unknown mappings and unrelated money changes remain rejected.
- Fresh real-model run `r8b-proof-legacy`: all 13 roles completed, $0.474566, with one
  recorded Scribe retry. Earlier `r8a-proof-legacy` held at Explorer's prohibited mixed
  tool batch ($0.148880); its failed evidence is retained. Runtime guards are unchanged.
- Actual PHP execution, using local simulated PayPal: eight PASS and one PASS_FIXED.
  The pending repair preserves the OLD R01/R07 findings and its exact repair diff.
  PARITY_EXTRA now checks the actual unchanged order-listing endpoint.
- Two mutations of the AI-written candidate were executed and caught by independent proof.
  These two are separate from the twelve executable fixture mutations, which also pass.
  No claim of complete critical-rule mutation coverage is made.
- `/grafts/{run}/scenarios` and `/cmel` replay digest-bound actual local recordings;
  the progress card for this run reports 9/9 accepted, zero unresolved problems.
  A successful retry clears the active problem while both paid attempts remain in the ledger.
- The qualified certificate is **not issued**. Eight critical rules remain unguarded by
  executed candidate mutations; authenticated sandbox/payment, signing/transparency and
  the merchant certificate binding remain separate prerequisites. The run stays PROVING.
- The checkout.js v4 browser item is still explicit and open; it is outside this PHP profile.

Evidence on this Mac:
`~/reports/goldgraft-agents-integration-20261112/runs/r8b-proof-legacy/local-proof/REPORT.json`.
It includes the captured inputs' digests, verdicts, actual mutation diffs/recordings,
coverage gaps and certificate hold reasons. Local digests do not authenticate a provider.

Repeat on a **new output directory** after an admitted model run:

```bash
.venv/bin/python -m scripts.live_local_shop_proof --execute-local \
  --run-dir ~/reports/goldgraft-agents-integration-20261112/runs/RUN_ID \
  --output-dir ~/reports/goldgraft-agents-integration-20261112/runs/RUN_ID/local-proof
```

This explicitly executes the reviewed MIT sample on the host against loopback services;
it is not an isolated runner and never contacts PayPal or a model. No budget cap was raised.

## Historical morning snapshot

Owner of this work: Aditya (built by Claude overnight; Codex built the API layer `integration/agents_app.py`).
Local main: `a290a56` → merge `dc6aeff` (frontend `aditya/web` merged into main) → this handoff. See `git log`.

**On GitHub this work is on branch `integration/agents-12-nov`, not on `main`.** GitHub `main` got Gupta's
PR #13 (live providers and recovery, 12 Nov 02:31) overnight. Merging it into this work conflicts in 4 backend
files that Singhal's proof commits also changed (`4925491`, `952cbcc`, `b25ce0a`, already in local main):
`pieces/backend/connection/upload_sessions.py`, `pieces/backend/lifecycle/effects.py`,
`plugtests/test_connection_and_providers.py`, `scripts/live_paypal_sandbox_payment.py` (10 conflict blocks;
Singhal stores uploads durably in SQLite, Gupta adds size limits and filename checks in memory). That is a
design choice between two owners, so it was not resolved overnight. Next: Gupta and Singhal merge
`origin/main` into `integration/agents-12-nov` (keep both: durable store + limits/sanitising), run the full
regression, then open the PR to `main`. None of the agent or frontend files conflict.

## What works now

| Piece | State |
|---|---|
| All 13 agents in one connected run | Gardener → Surveyor → Herald → Builder → Explorer ×4 → Scribe ×2 → Architect → Grafter → Builder → Explorer → Adversary ×2, plus Healer, Sentinel, Librarian, Orchard Analyst on the same run. Every edge carries the previous agent's committed output (`EDGES.json` per run). |
| Real AI calls | Every agent turn goes through the budget gateway (ledger, receipts, caps). Haiku for simple tasks, Sonnet for complex ones (Surveyor on ≥3 files, Architect, Adversary guard design, Grafter writing code, Gardener >5 nodes). Two scored Haiku failures on a task shape move it to Sonnet automatically (`ROUTING.json`; Healer and Librarian moved this way overnight). |
| Real code fixing | The Surveyor maps the submitted shop's real files; the Architect plans from that map; the Grafter (Sonnet) **writes the new PHP itself** for the shop's real payment files against the GoldGraft Orders v2 library (`fixtures/switch-libs/php/`). A deterministic review refuses old NVP/IPN calls left behind, missing planned operations, a missing library include, secrets, or marking an order paid on a non-COMPLETED capture; a real PHP parser (`tools/php-lint`) checks every candidate file. |
| Bounded retries | Survey: up to 2 re-attempts on incomplete reading or a refused answer. Chain stages: one retry (`<stage>-retry1`) when the model's answer was refused or the model ran but evidence was missing. Deterministic refusals (DENIED) are never retried. |
| Frontend | Live mode shows real runs: Progress (real stages and per-agent AI cost, live while a run is running), Old pieces (the Surveyor's real map), **Code changes** (line diff of the AI-written code + PHP check), My upgrades → **Real agent runs**. Starting an upgrade for a repo containing `legacy-php-shop` or `eval-nvp` starts a real run (one at a time, ≤3 per server start). |
| Tests | Full offline regression on merged main: **2972 passed, 18 skipped** (no network). New: `pieces/agents/tests/test_integrated.py` (22), `plugtests/test_agents_app.py` (13). |

## Results (real runs, see `INTEGRATED_RESULTS_2026-11-12.md`)

| Check | Result |
|---|---|
| Final run on the final code (`r4-final-legacy`) | **completed, 13 of 13 agents, 19 of 19 steps, $0.450**; Grafter rewrote 4 PHP files, all 5 files parse; checkout.js v4 button left as an open item |
| Runs since the Grafter fixes (7) | 6 completed with all 13 agents (`r2-realcode-7`, `r3-legacy-1`, `r3-legacy-2`, `r3-eval-nvp-1`, the UI-started `web-legacy-php-shop-20261112-001347`, `r4-final-legacy`); 1 held (UI-started eval-nvp, Explorer missing evidence) → fixed by the model-ran retry (`1957631`), verified by r4 |
| Typical cost | legacy-php-shop ≈ $0.38–0.45 per full run; eval-nvp ≈ $0.21 |
| Ledger (read 12 Nov ~06:10 IST) | $8.092648 spent in total, 0 reserved, 0 unknown, $1.91 left under the $10 active cap (hard cap $20, approved by Aditya; active cap not raised). Tonight's runs: $4.739 |

## Run it (on this Mac)

```bash
# 1. agents API (real runs; --live lets the frontend start new real runs)
cd ~/dev/GoldGraft-plan5-build
PATH=/Library/Developer/CommandLineTools/usr/bin:$PATH .venv/bin/python -m integration.agents_app --port 8710 --live

# 2. frontend in live mode
cd ~/dev/GoldGraft-web/pieces/web        # (same code is now in main: pieces/web)
VITE_API_BASE=http://127.0.0.1:8710 VITE_DEMO_TOOLS=true npx vite --port 8782
#    open http://127.0.0.1:8782/my  → Real agent runs → pick a run → Progress / Old pieces / Code changes
#    or  /connect with repo https://github.com/goldgraft/legacy-php-shop → Start → watch a real run (~4–5 min, ≈$0.40)

# 3. one real run from the command line (≈$0.40, cap with --max-usd)
PATH=/Library/Developer/CommandLineTools/usr/bin:$PATH \
  ~/reports/goldgraft-model-gateway-20261111/venv/bin/python -m scripts.live_integrated_run \
  --live --run-id my-run-1 --shop legacy-php-shop --max-usd 0.95
#    evidence: ~/reports/goldgraft-agents-integration-20261112/runs/my-run-1/{RESULT,OUTPUTS,EDGES,CHANGES}.json

# 4. results table from all run evidence (offline)
python3 -m scripts.integrated_results > docs/engineering/plan5/INTEGRATED_RESULTS_2026-11-12.md
```

Fresh clone (rehearsed 12 Nov ~06:30 from GitHub branch `integration/agents-12-nov`): `uv sync`, then
`cd pieces/web && npm ci && npx vite build`, then tests offline. On an Apple-silicon Mac whose `uv` is the
Intel (Rosetta) Homebrew build, `uv sync` tries to compile `cryptography` from source and fails; pass a
native Python: `uv sync --python ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none/bin/python3.12`.

Model keys and the gateway signing key live in `~/.config/goldgraft/` (never in the repo). Port 8700 is the old stand-in API.
With $1.91 left under the active cap, about 4 more full legacy runs fit before the cap must be raised (Aditya's call).

## API pack (agents API, `integration/agents_app.py`)

Shapes are the existing v1 contract types (`contracts/`, TS types in `pieces/web/src/api/types.ts`); errors are
problem+json. Every other path falls through to the offline stand-in app.

| Request | Answer |
|---|---|
| `GET /runs` | Every run on disk, newest first: `run_id`, `shop`, `status` (`running`, `completed`, `failed`), `roles_passed`, `roles_participated`, `spent_usd`, `finished_at` |
| `GET /grafts/{run}` | `Graft` (stage, card: old pieces, upgraded, AI cost, time) |
| `GET /grafts/{run}/rootmap` | `RootMap/1` from the Surveyor (404 until committed) |
| `GET /grafts/{run}/changes` | `CHANGES.json`: per file `path`, `author` (`model` or `library`), `before`, `after`; `lint` per file; `open_items` (404 until the Grafter commits) |
| `GET /grafts/{run}/events` | Server-sent events. Browser (`Accept: text/event-stream`): live while running (polls every 1.5 s, `: still running` keep-alive), then `event: end`. Plain GET: the ledger so far, once. `Last-Event-ID` resumes |
| `GET /grafts/{run}/scenarios` | `{"graft_id": …, "scenarios": []}` (payment scenarios are recorded, not served yet); `cmel`, `proof` → 404 |
| `POST /shops` then `POST /shops/{id}/graft` (with `Idempotency-Key`) | Starts a real run when the repo contains `legacy-php-shop` or `eval-nvp` and the server runs with `--live`; one at a time (409), at most 3 per server start (429) |

```
id: 12
event: ledger
data: {"seq":12,"graft_id":"r4-final-legacy","type":"COST","schema":"BudgetRecord/1","payload":{...},...}

event: end
data: {}
```

## What is real and what is not (say this in the demo)

| Real | Not real yet (labelled in the app) |
|---|---|
| All agent reasoning and outputs (real Haiku/Sonnet calls, ledgered) | Builds and payment scenario runs use recorded runner counterparts ("scripted runner"): no Docker/PHP on this Mac |
| The shop's real source, the Surveyor's real map, the Architect's real plan, the Grafter's real code | No independent SH proof/certificate on the AI-written candidate yet (the app stops at "Proving every payment") |
| PHP syntax check of the AI-written files | The new code has not been run against PayPal's sandbox |
| Budget, receipts, two-strike Sonnet escalation, bounded retries | Librarian learns from its qualified de-identified template (consent recorded as an assumption for the MIT sample shop) |
| | One code-fixing profile: plain PHP with Express Checkout NVP + IPN (`legacy-php-shop`, `eval-nvp`) |
| | Progress "last step" time for a finished run is when the API server last rebuilt its view (the foundation ledger stamps entries when written); runs watched live show real times |

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
