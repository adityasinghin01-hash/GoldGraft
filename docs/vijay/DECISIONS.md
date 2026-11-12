> **Current update — 7 November 2026:** Read [CURRENT_BASELINE.md](CURRENT_BASELINE.md) and [PHASE1_STATUS.md](PHASE1_STATUS.md) first. The refreshed Drive explicitly supersedes older build instructions/counts and delegates engineering to the reviewed team repository. Conflicting statements below are historical; the first plain-PHP reference and VJ01–VJ05 now govern. Docker is deliberately pending.

# Decision and uncertainty register

Updated 5 November 2026. Requirements are grounded in user instructions and the designated active Drive documents. External technical research verifies methods; it does not create project scope. Original wording remains preserved in .context/drive/ and sources are indexed in [SOURCES.md](SOURCES.md).

## Classification

- **Documented requirement:** explicitly supported by user instructions or a designated project source.
- **Verified technical fact:** established by a recorded environment inspection or primary provider documentation, with stated limits.
- **Implementation proposal:** an approach selected for implementation, not attributed to the Drive as a requirement.
- **Unresolved question:** a missing or conflicting fact/decision; investigate first and ask only when material.

## Locked requirements and approved approach

| ID | Class | Decision | Evidence |
| --- | --- | --- | --- |
| R01 | Documented requirement | No push/upload/PR/merge/publish without explicit action-specific user instruction; local completion is not permission | User's planning request and approved plan; AGENTS.md |
| R02 | Documented requirement | Aditya = PayPal + Shops; leader = frontend/agents; other members = backend and ML/proof | User's role clarification; images #1/#3; overrides draft name attribution |
| R03 | Documented requirement | 11 shops with one-command start, deterministic buyer and legacy inventory; buyer pays in sandbox; switch tests pass | Image #1; P12 09 Test shops |
| R04 | Documented requirement | Deliver 16 feasibility outcomes and real recorded sandbox traffic; label simulated buyers | Image #1; P12 09 Step 6 and demo |
| R05 | Documented requirement | PHP-first switches, origin/session continuity, signed configuration and guard events | Image #3 Role 4; P12 03 S4; P12 01 section 7 |
| R06 | Documented requirement | Sandbox Shadow/Heal/Cutback and Zen Cart official-module integration; deterministic decisions | P12 05 H1-H4; P12 08 trace; P12 03 S1/S4 |
| R07 | Documented requirement | No-code links, recurring continuity/PayPal handoff and demo recording | P12 03 S5; P12 05 F1; P12 09; image #3 Role 4 |
| R08 | Documented requirement | Core first; production onboarding/deployment gaps remain parked | VISION_3_NOV sections 1/6; P13 section 7 |
| R09 | Documented requirement | Start local preparation/shops before plug pack; final interface compatibility waits for actual contract | User's selected Local work first option and approved plan |
| P01 | Implementation proposal | Compose Linux containers, pinned compatible upstream/runtime dependencies, health-based readiness | Approved plan; consistent with P12 shop setup |
| P02 | Implementation proposal | Shared deterministic buyers use TypeScript/Playwright; shops retain original languages | Approved plan; exact versions await compatibility inspection |
| P03 | Implementation proposal | Runtime secret mounts; isolated browser contexts; local ignored raw captures/auth state | Approved plan; official Docker/Playwright guidance below |

## Verified observations and technical guidance

| ID | Class | Finding | Source / limit |
| --- | --- | --- | --- |
| F01 | Verified technical fact | Git 2.52.0.windows.1, Node v24.13.1 and Python 3.14.3 are available | Local version checks, 5 November; compatibility with future shops not yet established |
| F02 | Verified technical fact | Docker CLI is absent from PATH; CLI/Desktop standard install paths absent | Local inspection; does not prove no alternate installation exists |
| F03 | Verified technical fact | @playwright/test cannot resolve from this workspace; no package/Compose manifest exists | Local inspection; browser binaries not independently enumerated |
| F04 | Verified technical fact | Checked sandbox environment names and conventional local config paths are absent | Presence-only inspection; does not establish the user lacks an account or credentials elsewhere |
| F05 | Verified technical fact | Compose start order alone does not ensure database readiness; service_healthy waits for healthcheck | [Docker](https://docs.docker.com/compose/how-tos/startup-order/) |
| F06 | Verified technical fact | Compose Linux secrets mount as files with per-service access; _FILE variables depend on image support | [Docker](https://docs.docker.com/compose/how-tos/use-secrets/); do not assume every image supports the convention |
| F07 | Verified technical fact | Playwright uses isolated browser contexts; recording configuration supports diagnostic artifacts | [Isolation](https://playwright.dev/docs/browser-contexts), [recording](https://playwright.dev/docs/test-use-options); raw artifacts may contain secrets and remain ignored |
| F08 | Verified technical fact | Simulator webhooks are not app events; postback verification is unsupported for mocks; real sandbox app events must also be tested | [PayPal webhooks](https://developer.paypal.com/api/rest/webhooks/rest/); simulator self-verification uses documented WEBHOOK_ID |
| F09 | Verified technical fact | Supported operations can reuse PayPal-Request-Id for retry; support/retention are endpoint-specific | [PayPal idempotency](https://developer.paypal.com/api/rest/reference/idempotency/); do not reuse IDs across unrelated operations |
| F10 | Verified technical fact | PayPal-Mock-Response negative testing is supported on documented operations | [PayPal negative testing](https://developer.paypal.com/negative-testing/request-headers/); not a blanket legacy/API capability |
| F11 | Verified technical fact | PayPal does not publish a fixed rate-limit policy; it recommends token caching and notifications over polling | [PayPal rate limiting](https://developer.paypal.com/api/rest/reference/rate-limiting/) |

Technical pages above were inspected during planning on 5 November 2026; recheck version-sensitive behaviour when implementing the affected component.

Follow-up environment setup, 5 November: F03 is historical. Playwright 1.64.1, project-local Chromium 156.0.8078.4 and offline launch/DOM/context-isolation checks now pass. Docker remains absent. WSL setup installed Virtual Machine Platform but was interrupted after C: disk exhaustion; no restart occurred. Current Windows 10 host is outside the Windows 11+ list in the current Playwright install guide despite the successful local smoke check. See [setup evidence](ENVIRONMENT_SETUP.md); these findings do not establish payment readiness.

## Unresolved questions and conflict handling

| ID | Question / conflict | Current decision and gate |
| --- | --- | --- |
| U01 | RESOLVED: plug pack location | Team repo commit 05b5b3b inspected; TEAM_REPO_ALIGNMENT.md records evidence |
| U02 | PARTLY RESOLVED: ShopPack/1 and RawCapture/1 inspected | Buyer live/offline separation and reset/transport semantics still need implementation alignment |
| U03 | RESOLVED: Shadow representation | FORMAT_CHANGES C1.23: kind SHADOW, variant NEW |
| U04 | PARTLY RESOLVED: Ed25519 signing and bucket vectors inspected | Key provisioning, cache/session persistence, guard authentication/dedupe/outage policy remain gates; use stored origin |
| U05 | Actual sandbox account eligibility, NVP/WPS availability, refund compatibility, search lag, links/vault/UCP routes unknown | Feasibility checks establish results; no assumed PASS or silent substitute |
| U06 | Recipe text differs on second-shop vs two-independent-shop activation | Leader/proof owner resolves before declaring ACTIVE; do not manufacture reuse evidence |
| U07 | Source notes describe 45 requests/minute and a five-minute pause near a claimed provider limit | Retain as proposed project controls, not provider guarantees; official docs publish no fixed quota; no load test to force throttling |
| U08 | P12 suggests verify-webhook-signature while simulator mocks do not support postback | Separate real-event postback tests from documented simulator self-verification; no bypass or false failure attribution |
| U09 | Upstream revisions, current licences and runtime compatibility not yet frozen | Inspect before packaging; source-reported licence/version labels are not a completed audit |
| U10 | Docker paused for disk space; team runtime mismatch; sandbox unconfigured | Playwright local smoke passes. Team Node 22/Python 3.12 setup and sandbox capability checks remain pending |

Only an unresolved material choice goes to the user after repository/Drive discovery. Credential entry/account login may require user participation; do not request secret values in chat. No new deadline, production deployment, paid service or smaller shop set is assumed.

## Team repository review — 5 November 2026

See [team repository alignment](TEAM_REPO_ALIGNMENT.md) for the pinned source, exact Aditya Vijay ownership, phases 0–6, executable contract details and unresolved integration gates. This review adds context; it does not mark payment implementation complete.

## Current local implementation — 8 November 2026

These updates supersede earlier environment observations only; [CURRENT_BASELINE.md](CURRENT_BASELINE.md) continues to own current scope.

| ID | Classification | Decision/evidence |
| --- | --- | --- |
| L01 | User instruction | Use portable PHP on D: and existing Playwright instead of further local Docker/WSL repair. No reboot or Docker repair attempted in this slice. |
| L02 | Verified technical fact | Pinned PHP 8.3.36-1 and local PHP/HTTP/restart/Playwright cart checks pass; provider traffic is disabled. This is component evidence, not qualified payment/runtime proof. |
| L03 | Verified technical fact | 23 offline unit tests pass with existing Python 3.12. Node 22 browser execution remains pending; current browser evidence uses Node 24. |
| L04 | Implementation proposal | Private hidden-input wizard stores explicitly loaded sandbox credentials in ignored plaintext `.secrets/sandbox.json`; not a managed vault or team broker. No values are printed by status/probe reports. |
| L05 | Unresolved question | Existing sandbox account access/capabilities remain unverified. User is configuring locally; no real payment flows have run. Follow SANDBOX_SETUP.md, retaining missing capabilities as blocked. |
| L06 | User instruction | Publish reviewed Phase 0/1 content to the personal repository; preserve remote history, exclude secrets/raw artifacts and do not modify the leader repository. Full Phase 1 stays incomplete until its real gates run. |
| L07 | Verified local fact / operator-reported provider outcomes | Private credential groups are configured. The operator reported HTTP 200 PASS for OAuth at 12:37:27 UTC and NVP GetBalance at 12:46:12 UTC, 8 November. Sanitized provenance is in phase1/credential_checks.json. These are not payment captures or independent service-authority verification. |
| L08 | Verified technical fact | Portable Node 22.23.4 and Python 3.12 passed actual offline PHP/browser checks, run 20261108T125243238137Z. Thirty offline tests pass. Global PATH unchanged; Linux/isolation/whole-service qualification remains open. |
| L09 | Verified source finding / user confirmation | Connected main still has only .gitkeep in pieces/backend and pieces/runner; user confirmed GU02/GU03 not ready. No alternate live path is approved. Record all fourteen payment scenarios as BLOCKED/unattempted and retain full Phase 1 HOLD. |
| L10 | User instruction / implementation proposal | Start independent next-phase work locally. Implement repeatable plain-PHP baseline component characterization without moving the blocked qualification gates, adding Zen Cart or inventing shared interfaces. See PHASE2_STATUS.md. |
| L11 | Verified technical fact | Six isolated OLD/OLD_TWIN offline runs passed cart/access/original-store persistence checks; original bytes remained unchanged. Malformed synthetic order JSON was silently read as an empty store in every separate corruption copy. Record a baseline defect, not desired financial behaviour. Combined offline suite: 34 tests passed with Python 3.12. No payment, NEW candidate, runtime qualification or push resulted. |
| L12 | Documented requirement | The refreshed 10 November Drive guide and sponsor docs assign Vijay APIMatic recipes, Kernel checkout scenarios and Postman payment collections. Preserve exactly fourteen scenarios; eight sponsor uses targeted and two conditional, not ten completed integrations. |
| L13 | Verified source fact | On 12 November, main is 25e21594841ae527024854a7267dd707d37584ea. Proof PR1 is merged at 4f9bf0c7f88dd811ba58cba856ff91ae226db172, with a fixture-replay handoff. Current runner explicitly replays fixtures, custody is in memory and callback qualification remains open; the older unmerged/placeholder descriptions are superseded. |
| L14 | Verified local fact / implementation preparation | SDK 2.5.0 argument factory compiled using pinned APIMatic context reference; three deliberate compiler negatives rejected. Newman 6.2.3 executed five local requests and ten assertions, zero failures. No sponsor account, real provider run, vendor session, credit redemption, message or upload occurred. |
| L15 | Unresolved external qualification | APIMatic active plugin/account entitlement, Kernel budget/security/browser/credit profile and actual GU02/GU03/SI01 live boundaries are not established by preparation. Channel3 remains NOT_JUSTIFIED until incremental value and dataset rights are demonstrated. No paid trial, overage or student benefit is assumed. |

## Local candidate decisions — 12 November 2026

Later continuation: [FINAL_LOCAL_STATUS.md](FINAL_LOCAL_STATUS.md) supersedes the pending local bridge/SI01/socket findings below. **Verified implementation facts:** accepted team pin 9968f9b, actual PHP/broker/callback boundary tests, current shared lifecycle model consumers and fresh socket/connected proof execution. **Implementation proposals:** private stdio/platform adapters and conservative domain readiness checks. **Unresolved qualification:** genuine provider, isolation, OCI/runtime, state/apply/finalisation and merchant exit. No new public wire API or cloud action is authorized.

- **Documented requirement:** current first-reference VJ01–VJ05 and fourteen scenarios remain the scope; preserve immutable OLD source and independent NEW state. The refreshed Drive continues to delegate engineering to team GitHub. See [current delivery sources](LOCAL_PHASE_DELIVERY.md).
- **Verified technical fact:** team 525c22de61b504f67ea633e5aac95b8bed0fda64 implements typed broker mutations and fresh read-only GETs; its broker does not forward `Prefer`. Callback verification/inbox code now exists but merchant business effects are not applied by `CallbackGateway`. Host-process execution explicitly reports no isolation.
- **Implementation proposal:** separate PHP candidate using SQLite, `BEGIN IMMEDIATE`, a durable single-dispatch operation journal, trusted catalogue and an injected existing REST vocabulary. Unknown operations hold for reconciliation. This is fresh local state, not a selected/approved merchant storage migration or new shared schema.
- **Verified technical fact:** portable PHP PDO SQLite and Sodium execute the candidate and integrated switch tests. Minimal responses require read-back; no status/amount/provider identity is manufactured. [PayPal idempotency](https://developer.paypal.com/api/rest/reference/idempotency/), [refund API](https://developer.paypal.com/api/payments/v2/captures-refund) and [SQLite transactions](https://www.sqlite.org/lang_transaction.html) informed these methods.
- **Implementation proposal:** private source-inspected Python adapter maps `PayPalClient.rest` operations to `PaymentBroker.execute_orders_v2`; no public HTTP/RPC route or credential mechanism is introduced. The actual PHP/Python bridge must still be qualified with Gupta.
- **Unresolved integration:** actual protected runtime, trusted callback/business-effect boundary, proof integration and GU05 state/apply/exit mechanisms remain required. Local tests do not resolve those gates. No new request for credentials or account registration is necessary.
- **User-authorized publication:** only Phase 0 completion index was newly pushed at 9144ab2. All later local code remains unpublished. This does not grant continuing push permission.
