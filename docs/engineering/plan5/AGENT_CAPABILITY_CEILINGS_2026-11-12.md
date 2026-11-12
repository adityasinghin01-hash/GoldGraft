# Agent capability limits and tool register (12 Nov 2026)

Sources: the 11 Nov one-agent-at-a-time AI tests (`FINAL_AGENTS_REPORT_2026-11-11.md`) and the 12 Nov
connected runs (`INTEGRATED_RESULTS_2026-11-12.md`, evidence in
`~/reports/goldgraft-agents-integration-20261112/runs/`). "Largest passing" is the largest input
measured to pass. "First failing" is the smallest measured input that failed; "not measured" means no
larger input was tried. The agents were not upgraded overnight (Phase 4 not started).

## Per agent

| Agent | Model in connected runs | Largest passing input (measured) | First failing / limit (measured) |
|---|---|---|---|
| Gardener | Haiku | 9-node plans (11 Nov); 1-node survey admission in every connected run (22/22) | 2 format failures kept on 11 Nov (54/56); plans over 5 nodes route to Sonnet. Not measured above 9 nodes |
| Surveyor | Sonnet for ≥3 files; Haiku for the 2-file eval-nvp shop | 16 files (11 Nov ceiling); 11-file legacy shop with 8 touchpoints in connected runs | Incomplete reads on the 11-file shop in 3 of 22 attempts (MISSING_EVIDENCE), 1 refused answer; covered by 2 bounded re-attempts. Not measured above 16 files |
| Herald | Haiku | Summary of an 8-touchpoint inventory (18/18) | Not measured |
| Builder | Haiku (8 turns) | Baseline and candidate build requests for both shops (30/30) | Builds run on a recorded runner, not a real PHP/Docker build |
| Explorer | Haiku (8 turns) | OLD, OLD-twin, follow-up and NEW captures (63/65) | 1 refused answer, 1 missing evidence after the model ran (now retried once). Captures are recorded, not live |
| Scribe | Haiku (8 turns) | Draft and final money rules for both shops (32/33) | 1 deterministic refusal (variance) |
| Architect | Sonnet | 7-item plan from 8 real touchpoints (legacy); 3-item plan (eval-nvp) (15/15) | checkout.js v4 (browser button) is left as an open item by design |
| Grafter | Sonnet (writes code) | **Writes the code itself for 4 PHP files** (legacy) and 2 (eval-nvp); every file parses (12/15) | 3 refused final answers while the output format was being fixed; 11 Nov replacement mode failed at 4 files on both models. Not measured above 4 files |
| Adversary | Sonnet (guards) + Haiku (planted bug) | Guard bundle + one planted pending-capture bug on the real candidate (24/24) | One mutation kind only |
| Healer | Sonnet (moved after 2 Haiku misses) | Diagnosis of one controlled go-live fault with a pause request (10/12) | 2 Haiku refusals → two-strike rule moved it to Sonnet |
| Sentinel | Haiku | Flags the hostile "secret attempt" event and requests a hold (12/12) | Advisory only; cannot certify safety |
| Librarian | Sonnet (moved after 2 Haiku misses) | Quarantined recipe + detection rule from the de-identified template (8/13) | 3 deterministic refusals (no consent / bound references: correct), 2 Haiku refusals |
| Orchard Analyst | Haiku (8 turns) | Fleet view over all test runs with small groups hidden (6/8) | 2 refusals on a small cohort (correct: minimum-disclosure rule) |

## What every result still depends on

| Real | Recorded / not yet real |
|---|---|
| Every agent's reasoning, every AI call, the ledger | Builds, payment captures and go-live signals (recorded runner) |
| The shop's source, the Surveyor's map, the Architect's plan, the Grafter's code | No SH proof/certificate on the AI-written code; not run against PayPal sandbox |
| PHP syntax check of every written file | One code profile only: plain PHP, Express Checkout NVP + IPN |

## Tool register (checked 12 Nov ~06:20 IST, names only, no secrets read)

| Tool | State | Missing prerequisite |
|---|---|---|
| Anthropic models (Haiku, Sonnet) | **Configured and used** through the budget gateway | — |
| Zapier | Proof from earlier (11 Nov, `zapier.env` present); not rerun in connected runs | A connected-run step that needs it |
| Render | CLI installed; not used by agents | Backend deploy decision (local only by default) |
| E2B (remote runner) | Not configured | Account + key → would replace the recorded runner for Builder/Explorer |
| Postman, APIMatic, Kernel, Elastic, Channel3, Bryntum | Not configured | Account + key each |
| Docker, PHP runtime on this Mac | Not installed | Needed for real local builds (Gupta's runner work) |

## Cost reconciliation (connected runs, 12 Nov)

22 runs, 289 agent steps, $4.739361 in total. Run totals = sum of step costs = the ledger's change over
these runs (exact to the micro-dollar). By model: Sonnet $4.301 (91%, 66 steps), Haiku 8-turn $0.358
(167 steps), Haiku $0.080 (56 steps). By agent: see `INTEGRATED_RESULTS_2026-11-12.md`. The Surveyor
is the largest single cost ($2.115), then Grafter ($0.991).
