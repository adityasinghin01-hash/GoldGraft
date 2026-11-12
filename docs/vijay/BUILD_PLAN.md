> **Current update — 7 November 2026:** Read [CURRENT_BASELINE.md](CURRENT_BASELINE.md) and [PHASE1_STATUS.md](PHASE1_STATUS.md) first. The refreshed Drive explicitly supersedes older build instructions/counts and delegates engineering to the reviewed team repository. Conflicting statements below are historical; the first plain-PHP reference and VJ01–VJ05 now govern. Docker is deliberately pending.

# PayPal + Shops work plan

Prepared 5 November 2026. This file is the detailed work inventory. Execution follows [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md), with uncertainties in [DECISIONS.md](DECISIONS.md) and current readiness in [PHASE0_STATUS.md](PHASE0_STATUS.md). Phase 0 preparation is complete locally; payment implementation and the checks below remain unperformed. Follow [AGENTS.md](../../AGENTS.md), including no push/upload without explicit instruction.

## Build order

1. Confirm shop-folder contract, sandbox seller/buyers and secret injection. Use the inspected team plug pack (see TEAM_REPO_ALIGNMENT.md); basic local shop work can proceed independently.
2. Freeze source commits, dependency versions and licences before tuning. Create the 11-shop register with unknown/blocked cases visible.
3. Boot the first PHP legacy shop and make its deterministic buyer pay in the sandbox. Supply the backend teammate a tiny runnable shop early so the runner can integrate.
4. Run legacy-payment feasibility tests early, especially NVP/WPS/IPN, notifications and legacy-capture refunds. Record failures and choose documented fallbacks.
5. Build/test the PHP switch and the Zen Cart official-module path; capture old, old-twin and new scenario evidence through the teammate capture interface.
6. Connect deterministic guard/controller results to sandbox Shadow, staged promotion and Cutback; drive simulated buyers and measure rollback.
7. Extend to Node and Python, static Buy Now links, the second Zen Cart for recipe evidence, then Ruby and the remaining specialised fixtures.
8. Finish all 16 test outcomes, switch validation and the complete shop set; prepare the short demo and four-arm evidence with teammates.

This order follows core-first guidance and PHP-first switch work. It is not permission to drop the remaining shops silently. Java/.NET runtime breadth follows the team scope; map/plan-only coverage cannot be described as tested payment execution.

## The 11 shops

Exact upstream revisions and current licences still need verification. Licence labels below are what the source plan reports, not a fresh legal/licence audit.

| # | Shop | Stack / legacy surface | Purpose |
| --- | --- | --- | --- |
| 1 | Zen Cart fork | PHP; WPS, EC-NVP, Direct Payment, IPN | Official modern PayPal module + switch + legacy refunds |
| 2 | Customised Zen Cart #2 | PHP; EC-NVP, custom observers | Independent recipe reuse and measured learning curve |
| 3 | Cutover legacy-php-shop | PHP; NVP EC, checkout.js v4, IPN; reported MIT | Rewrite path and baseline comparison |
| 4 | expressCart | Node; paypal-rest-sdk v1; reported MIT | REST v1 migration and comparison |
| 5 | django-oscar-paypal sandbox | Python; EC-NVP; reported BSD-3 | Python migration |
| 6 | better_spree_paypal_express | Ruby; EC-NVP; reported BSD-3 | Ruby migration |
| 7 | Licensed static Buy Now site | HTML; WPS buttons | No-code Payment Links path |
| 8 | Seeded hard shop | PHP; wrappers, config-built endpoints, templates, dead code | Survey ground truth and recall testing |
| 9 | Subscription shop | PHP; WPS Subscribe / recurring profiles | Legacy continuity, renewal events and PayPal handoff |
| 10 | Gauntlet shop | Node; hostile comments/README/HTML/install/dependency fixtures | Isolated security demonstration |
| 11 | Poisoner shop | PHP; deliberately misleading recipe example | Quarantine demonstration |

For each shop: agreed start command, deterministic buyer script, legacy inventory with file/operation locations, seed/reset steps, sandbox-only runtime configuration, health checks, pinned revision/dependencies, licence information and evidence output references. Use the team's existing folder schema; filenames and manifest fields are not fully defined in the Drive.

Freeze and hash/timestamp the set before tuning; report all outcomes, failures included. Gauntlet/Poisoner material is test data and only runs in the agreed isolated environment.

## All 16 feasibility tests

These are the team's original Step 6 tests. Image #1 assigns their result pack to PayPal + Shops. Some concern backend infrastructure or leader-owned accounts; Aditya coordinates those outcomes rather than assuming authority to create accounts, spend money or manage teammate credentials.

| # | Test | Decision / evidence needed |
| --- | --- | --- |
| 1 | NVP sandbox credentials + Express Checkout end to end | Legacy rail available; complete approval/capture IDs |
| 2 | WPS purchase + IPN delivered to tunnel URL | Baseline button payment and notification evidence |
| 3 | IPN simulator | Available events, verification and handling results; distinguish simulation from a purchase |
| 4 | Modern Orders/Payments refund route for NVP-era transaction | Whether a legacy capture can use a modern refund path; retain legacy routing unless proved |
| 5 | Transaction Search permission, T-codes and lag | Observed family classification and evidence delay; do not assume T0006 identifies API generation |
| 6 | Button Manager in sandbox | Hosted-button read support; otherwise use available form fields |
| 7 | Webhook simulator including subscription/recurring events | Exact supported events; simulated renewals do not prove real renewal timing |
| 8 | Payment Links API | Available sandbox creation + buyer payment + amount/currency check |
| 9 | Vault v3 and second purchase | Sandbox eligibility/configuration and observed repeat-purchase behaviour |
| 10 | Pay Later messages render | Eligible account/region/rendering evidence; unsupported states recorded |
| 11 | Agent Ready / UCP sandbox route | Whether actual sandbox execution exists; otherwise prerequisites only, UNVERIFIED execution |
| 12 | Sandbox rate limits and runner IP behaviour | Observe bounded legitimate traffic/429 behaviour; throttling is backend-owned; do not assume each runner has a unique IP |
| 13 | cloudflared tunnel from a GitHub runner | Public callback/return URL and delivery evidence with backend |
| 14 | KERNEL headful browser completes v6 popup | Repeatable sandbox buyer; local Playwright fallback if unavailable |
| 15 | AG Studio trial / Agent Framework availability | Coordinate leader's account/access and trial duration; no claim that you own frontend |
| 16 | Claude API spending cap and development Actions authentication | Coordinate leader/backend account configuration; no secrets in output and no spend merely to complete this review |

For every test record: test ID, date, environment and dependency versions, steps, expected/observed outcome, PASS/FAIL/BLOCKED/UNVERIFIED, redacted evidence refs, PayPal IDs where applicable, limitation, owner and fallback. No results have been produced in this repository.

## Switch and rollout acceptance

- [ ] Consistent session split for valid signed config; 0 and 100 percent boundaries tested.
- [ ] Invalid signature/expired config chooses the documented safe rail; cached-valid fetch-failure behaviour tested.
- [ ] Configuration updates preserve in-flight OLD and NEW sessions.
- [ ] Legacy captures/refunds/renewals use proven origin routing.
- [ ] Forged and duplicate IPN/webhooks cannot cause a second state change or a paid state.
- [ ] Buffered guard events and frozen promotion work during outages; controller hard stop is exercised.
- [ ] Shadow uses sandbox-only NEW payments with cart data and no buyer PII; a mismatch prevents promotion.
- [ ] Controller consumes proof results and approved statistical rules; low traffic waits.
- [ ] Fault injection produces a measured Cutback and no stranded payment.
- [ ] Cleanup leaves required legacy handlers until the agreed refund/renewal window is safe.
- [ ] Tests run for each delivered language; unimplemented languages are listed explicitly.

## Payment scenario evidence

Coordinate the proof teammate's scenario IDs: happy, cancel, decline, payer action, double click/two tabs, lost response/retry, tampered amount/currency, pending capture, refund and second refund, forged/duplicate notifications, restart mid-payment, renewal simulation and currency edges.

Run OLD and OLD_TWIN on reset state where applicable, then NEW; retain raw redacted capture and PayPal evidence. Unknown account eligibility, failed ledger reads and unrun cases remain explicit gaps. Use integer minor units plus ISO currency in shared evidence. Proof verdicts are supplied by the deterministic Judge, not invented in these fixtures.

## Demo delivery

Prepare sandbox buyers and recordings for old/new purchases, a named planted bug, fault-triggered Cutback, recipe reuse and the team's security/certificate demos. Only show a real old-shop bug if found. Capture measured costs/times, not estimates. Role 4 runs/records scenarios; everyone reviews the README/video.

The source proposes a video under 3 minutes and an 8 November team feature freeze. Reconfirm scheduling with the leader. The manual comparison arm should be the teammate least familiar with that shop. All simulated rollout shots say **PayPal sandbox · simulated buyers**.

## Team repository review — 5 November 2026

See [team repository alignment](TEAM_REPO_ALIGNMENT.md) for the pinned source, exact Aditya Vijay ownership, phases 0–6, executable contract details and unresolved integration gates. This review adds context; it does not mark payment implementation complete.
