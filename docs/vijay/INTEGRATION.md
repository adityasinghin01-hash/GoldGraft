> **Current update — 7 November 2026:** Read [CURRENT_BASELINE.md](CURRENT_BASELINE.md) and [PHASE1_STATUS.md](PHASE1_STATUS.md) first. The refreshed Drive explicitly supersedes older build instructions/counts and delegates engineering to the reviewed team repository. Conflicting statements below are historical; the first plain-PHP reference and VJ01–VJ05 now govern. Docker is deliberately pending.

# PayPal + Shops integration handoff

Use the [phased plan](IMPLEMENTATION_PLAN.md) and [decision register](DECISIONS.md). Shared-contract alignment is the Phase 3 gate. Follow [AGENTS.md](../../AGENTS.md); local work and phase completion never authorize a push or remote workflow. See [Phase 0 readiness](PHASE0_STATUS.md) for observed prerequisites.

## Work independently, integrate through shared formats

Image #1 permits this role to build locally with Docker and PayPal sandbox without waiting for other components. The team still needs one agreed shop-folder format and the P12 data contract. The plug pack has now been inspected at team commit 05b5b3b; see [team repository alignment](TEAM_REPO_ALIGNMENT.md).

Supply a tiny runnable shop early for the backend runner. The leader consumes your payment/rollout evidence for screens and agents. The proof teammate consumes your traffic for deterministic CMEL mapping and verdicts.

## Inputs and outputs

| Your component | Consumes | Produces / hands off |
| --- | --- | --- |
| Shop folder | Pinned licensed source, seed data, sandbox runtime config | Start command, health/reset procedure, buyer script, legacy inventory |
| Sandbox checks | Seller/buyer accounts, REST/NVP access, callback endpoint | 16 result records with evidence and fallbacks |
| Buyer/capture run | Shop revision, scenario IDs, runner/capture settings | Raw redacted traffic, payment IDs, OLD/OLD_TWIN/NEW run references |
| Switch library | Signed SwitchConfig, stable session ID, object origin | Rail decision, guard payment events and application timestamps |
| Shadow/rollout | Cart-only events, controller config, proof verdicts | Sandbox NEW-shadow run, traffic/guard state and Cutback evidence |
| No-code lane | Static form fields or available hosted-button details | LinksPack, replacement snippets and sandbox proofs |
| Handoff | Legacy recurring-profile/billing-agreement fixture data | Validated JSON/CSV data for PayPal-only steps |

The backend owns capture machinery and transport; the proof teammate owns event normalisation/Judge; you supply runnable shops, complete buyer flows and authentic recordings. Do not make integration conditional on rebuilding either teammate's service.

## Relevant planned control-plane endpoints

| Endpoint | Role in your work |
| --- | --- |
| GET /switch/config/{graft} | Retrieve signed config for language libraries |
| POST /guard/event | Non-blocking money events from shop libraries |
| POST /pp/webhook/{graft} | PayPal notification relay/control-plane delivery; separate from shop-specific handlers |
| GET /heal/{id} (SSE) | Rollout state for team integration and evidence |
| POST /heal/{id}/inject-fault | Demo-only fault mechanism, coordinated with proof/backend |
| POST /shops/{id}/connect | Connection checks through Key Guard; never copy credentials into evidence |

P12 gives planned routes, not a verified API implementation. Exact request/response/error schemas, auth, idempotency, retries and event replay semantics come from the plug pack/backend owner.

## Shared data

P12 SwitchConfig fields: graft_id, stage_pct (0/1/10/50/100), version, expires_at, origin_rules, ed25519 signature. Invalid/expired config defaults to OLD in the sandbox design. Confirm canonical signing bytes, verification key distribution, expiry/clock behaviour and hashing test vectors with the backend before writing libraries.

P12 MoneyEvent includes graft/run/scenario IDs, variant, sequence/time, source, event kind, shop order reference, PayPal object/debug IDs, integer minor-unit amount/currency, normalised status, raw evidence reference and noise fields. The proof team owns the mapping. Capture the original source evidence so this mapping is auditable.

Artifacts you need to understand: Connection, RunnableShop, Driver, CMEL, Scenario, Verdict, TargetPlan/origin_rules, SwitchConfig, LinksPack and PayPal handoff data. The full app's LedgerEntry, Recipe and Certificate are downstream consumers, not new frontend/agent responsibilities for this role.

## Contract gaps to resolve

- Exact shop-folder schema/start/reset command, buyer arguments and expected output file.
- Raw traffic file format, redaction and capture coverage (HTTP, PayPal calls, DB state, notifications).
- Evidence storage and retention, scenario/run naming and returned payment/debug IDs.
- Currency exponent table and safe amount conversion shared with proof.
- P12 CMEL variants list OLD/OLD_TWIN/NEW, but Shadow uses NEW_SHADOW elsewhere. Agree the schema extension/representation rather than silently changing it.
- Notification dedupe IDs: raw CMEL examples do not fully define webhook event-id storage. Agree explicit IDs before testing duplicates.
- Switch hash algorithm/session persistence, origin metadata, signature payload/key and compatibility vectors across languages.
- Signed-config publication and guard/controller responsibility: backend serves/persists, proof supplies authoritative verdicts/maths, you implement shop-side routing and rollout integration.
- Versioned canonical shop/PayPal object links: a heuristic ID shape alone is not proof of origin.
- Recipe activation wording conflicts: some traces imply the second shop is enough; other text requires two independent shops. The leader/proof owner must settle activation before a recipe is claimed ACTIVE.

## Zen Cart path

Source notes describe legacy modules paypal.php (WPS), paypalwpp.php plus paypal_curl.php (EC-NVP), paypaldp.php (Direct Payment), and ipn_main_handler.php. They identify an official PayPalRestful v2.1.1 plugin (paypalr) in the studied revision. Verify the actual selected revision/plugin and licence during implementation.

Boot PHP + MySQL, seed demo products and enable the legacy sandbox module. The buyer goes product → cart → Express Checkout → sandbox approval → return → order confirmation.

Prefer enabling the official modern module for NEW checkouts and porting required custom observers over a blanket rewrite. A notifier-based switch chooses modules per session. Admin/report/refund readers must understand both generations. Keep paypalwpp installed but hidden for legacy refunds/voids, and keep IPN handling for late legacy notifications. Card-field support depends on account eligibility; report it separately.

The second customised Zen Cart shop supplies independent recipe-use evidence. Do not pre-edit it to make a learned recipe appear successful.

## No-code and recurring paths

For static WPS buttons, preserve form fields (item, amount, currency and hosted-button reference). Read hosted details only if Button Manager works; otherwise form-only fallback. The plan proposes Payment Links and a sandbox payment per replacement. Keep Donate/Subscribe outside the Buy Now/Add-to-Cart retirement replacement scope unless the team adopts another explicit plan.

Old recurring profiles keep their original path; new subscriptions may use the modern API. Existing live billing-agreement/profile conversion is PayPal-only. Handoff fields: type, ID, customer reference, amount/currency, cycle, next billing, status and source, plus validation counts/totals/duplicates/inactive records. Simulator events prove handler behaviour, not genuine renewal timing.

## Boundaries and honest status

Secrets belong in runtime/vault configuration and must be redacted from captures, repositories, prompts and logs. Production keys, real payments, upstream changes, account subscriptions and spending are not part of this context-update task. Hostile fixtures require the agreed isolated environment.

No schema, library, sandbox run or deployment is implemented by these documents. Current API routes, SDK behaviour, eligibility, quotas and licences still require verification when implementation begins.

## Team repository review — 5 November 2026

See [team repository alignment](TEAM_REPO_ALIGNMENT.md) for the pinned source, exact Aditya Vijay ownership, phases 0–6, executable contract details and unresolved integration gates. This review adds context; it does not mark payment implementation complete.
