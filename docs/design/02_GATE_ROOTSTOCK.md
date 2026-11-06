> **Status update — 6 November 2026.** The original body below is historical reference and is superseded for current target behaviour by reviewed engineering documents. Read [engineering baseline](../engineering/START_HERE.md), [current/proposed boundary](../engineering/CURRENT_VS_PROPOSED.md) and [atomic lifecycle protocols](../engineering/lifecycle/ATOMIC_DELIVERY_PROTOCOLS.md). Paper only; no implementation or live qualification. Earlier schedules/coverage/Done claims in the retained body are not current status.

---

# P12 · 02 — Gate + Rootstock, built by hand
Format per piece: Job · In · Out · Inside · Who · Fails → · Drawing · Check (Zen Cart).

---
## G1 Connect + Key Guard
**Job** — let a merchant connect in 2 steps without any secret ever reaching an AI.
**In** — (1) repo (GitHub App install on the repo, or public repo URL) or site URL; (2) PayPal sandbox REST app (client id, secret, webhook id) and, for old shops, NVP API credentials (user, password, signature).
**Out** — `Connection{shop_id, repo, site, secrets_ref (Doppler path), checks:{rest_ok, nvp_ok, webhook_ok, version_match}}` → ledger.
**Inside**
1. Secrets go straight from the form to Doppler over TLS; the API only stores `secrets_ref`.
2. REST check: OAuth `client_credentials` → token OK (sandbox host only; live hosts refused).
3. NVP check (old shops): one harmless sandbox call (e.g. GetBalance) → ACK=Success.
4. Version check: keys must belong to the generation the shop uses (PhonePe lesson) — NVP creds for old code, REST app for new; mismatch → plain-language fix.
5. Webhook: register `https://<tunnel or relay>/pp/webhook/{graft}` on the REST app (or reuse given id).
**Who** — deterministic service (D7) + web form. No AI.
**Fails →** bad keys: say which one and why · live keys pasted: refuse, explain sandbox only · no NVP creds: Rootstock runs code + site + account lenses, proof for old shop marked UNVERIFIED.
**Drawing**
```
form ──TLS──▶ Doppler ──ref──▶ API ──▶ checks (REST · NVP · webhook · version) ──▶ ledger: Connection
                 ▲                                   │
                 └──── runner pulls secrets at run time only (never into prompts) ◀┘
```
**Check (Zen Cart)** — our fork + sandbox REST app + sandbox NVP creds → rest_ok, nvp_ok, version_match (old modules use NVP).

---
## G2 Graft Probe
**Job** — one call that tells anyone which old PayPal pieces a shop has and what is at risk.
**In** — repo URL or site URL (no keys needed); optional account read if connected.
**Out** — `ProbeResult{families_found, files_or_pages, official_modern_module_available?, deadline_notes (e.g. WPS "may retire after 1 Jan 2027"), next_step}`.
**Inside** — fast subset of R1: code lens rules only (no AI) or site lens crawl of ≤5 pages; returns in ≤30 s; result cached by commit hash.
**Who** — deterministic; Herald (Haiku) writes the 3-line plain summary.
**Fails →** private repo: ask for the GitHub App · site blocks bots: ask for 1 page URL.
**Check (Zen Cart)** — finds WPS (`includes/modules/payment/paypal.php`), Express Checkout over NVP (`paypalwpp.php` + `paypal/paypal_curl.php` → `api-3t.sandbox.paypal.com/nvp`), Direct Payment (`paypaldp.php`), IPN (`ipn_main_handler.php`, `_notify-validate`) **and** the official REST plugin shipped in the repo (`zc_plugins/PayPalRestful/v2.1.1`, Orders v2 + webhooks).

---
## R1 Root Survey (four lenses, GG-9)
**Job** — find every old PayPal piece and the shop's money path.
**In** — repo, site URL, account data (if connected), runtime capture (after R3 runs).
**Out** — `RootMap` (01 §2).
**Inside**
1. **Stack** — manifest rules (Razorpay detect_stack idea): composer.json / package.json / requirements / Gemfile / pom / csproj + framework markers.
2. **Code lens** — ast-grep rules per language generated from: PayPal's 11 v4→v6 patterns, every NVP/SOAP operation name in PayPal's docs, WPS fields, IPN markers, endpoint domains (`api-3t…/nvp`, `cgi-bin/webscr`, `ipnpb.paypal.com`, `/v1/payments/`), old SDK package names. Each hit → touchpoint with file:line.
3. **AI sweep** — Haiku reads only files in the import graph of payment code to catch indirect use (wrappers, URLs from config); every AI-only hit must be confirmed by a rule or a runtime call (else confidence ≤0.5, flagged).
4. **Site lens** — Playwright crawl (home, product, cart, checkout): forms → webscr, `hosted_button_id`, script srcs (checkout.js / `sdk/js?client-id` / `web-sdk/v6`), Pay Later messages, button positions.
5. **Account lens** — Transaction Search last 30 days grouped by T-code (T0007 WPS, T0006 Express Checkout, T0005 card, T0002 subscription, T0003 preapproved) with money totals; webhooks list; Button Manager search (if NVP creds).
6. **Runtime lens** (fed back after R3) — every PayPal call seen at runtime is matched to a touchpoint; unmatched = MISS → added + new rule proposed to Librarian; static hits never called = DEAD.
7. **Fusion** — merge by operation + location; confidence = lens agreement; attach official target from RulesHub mapping; mark PayPal-only (billing-agreement conversion, live profile moves).
8. **Money-flow graph** — locations of create / approve / capture / mark-paid / refund / notify / recurring (rules + Sonnet fusion read).
**Who** — Surveyor (Haiku sweep, Sonnet fusion) + deterministic rule engine.
**Fails →** unknown language: Haiku sweep + runtime only, rule learned later · minified JS: site + runtime lens · no account access: lens skipped, shown as "not checked".
**Drawing**
```
 code (ast-grep) ─┐
 AI sweep (Haiku) ┤
 site (Playwright)┼──▶ FUSION ──▶ Root Map + money-flow graph ──▶ ledger
 account (T-codes)┤        ▲
 runtime (capture)┘────────┘ misses → new rules (Librarian)
```
**Check (Zen Cart)** — code: `SetExpressCheckout / GetExpressCheckoutDetails / DoExpressCheckoutPayment / DoDirectPayment / RefundTransaction / DoVoid / DoAuthorization / DoCapture / GetTransactionDetails / TransactionSearch` in `paypal_curl.php`; WPS form in `paypal.php`; IPN postback in `ipn_main_handler.php`; money path: capture + status in `paypalwpp.php::before_process` (Completed → paid status, Pending → pending status), storage in `TABLE_PAYPAL` via `after_process`, refunds `_doRefund`, IPN duplicate check on `TABLE_PAYPAL_PAYMENT_STATUS_HISTORY` (txn_id + payment_status). Account: EC payments under T0006, WPS under T0007.

---
## R2 Shop Builder
**Job** — get the old shop running in the Cage and write its checkout driver once.
**In** — repo, RootMap.stack, env recipe from Scion Bank (if any).
**Out** — `RunnableShop{compose, image digests, seed, base_url (tunnel), health}` + `Driver{steps, selectors, proven_runs:3}`.
**Inside**
1. Env recipe hit? → use it (≈1 min). Else pick base image by stack (php-apache / node / python / ruby / java / dotnet) + services (MySQL / Postgres / Mongo / SQLite from config).
2. Install deps with `--ignore-scripts` first; allowlisted scripts only.
3. Install / seed the app (installer via CLI, SQL import, or Playwright through a web installer); seed 5–10 products incl. odd prices (e.g. 19.99, 0.01, 1000.00) and one zero-decimal-currency product if the shop allows.
4. Configure PayPal module with sandbox creds injected at run time; base URL = cloudflared tunnel URL (needed for PayPal return URLs, IPN, webhooks).
5. Health: home + product + cart pages 200.
6. Driver: Sonnet explores the checkout once (DOM + Root Map money path) and emits a **deterministic Playwright script** (add to cart → checkout → PayPal → approve → return → confirm). Proven = 3 clean runs on the OLD shop.
7. Save env + driver as recipe candidate.
**Who** — Builder (Haiku first, Sonnet on failure) + Cage.
**Fails →** boot fails after budget/time cap → LANE:NO-RUNTIME · driver flaky → raise wait strategy; still flaky → API-level steps for that path, UI path marked UNVERIFIED.
**Drawing**
```
recipe? ─yes─▶ compose up ─▶ health ─▶ driver (recipe) ─▶ 3 proven runs
   └no─▶ base image + services ─▶ deps (no scripts) ─▶ install/seed ─▶ tunnel URL ─▶ explore once ─▶ script ─▶ 3 runs
```
**Check (Zen Cart)** — php:8.x-apache + MySQL 8; install via `zc_install` (web installer driven by Playwright, or its SQL files) with demo products; enable `paypalwpp` with sandbox NVP creds via the admin config (or config rows); `HTTP_SERVER` = tunnel URL. Driver: product → add to cart → checkout → "PayPal Express" → sandbox login → approve → return → confirm → order success.

---
## R3 Golden Recorder
**Job** — record exactly how the OLD shop handles money, twice, as CMEL.
**In** — RunnableShop, Driver, scenario list (from U1, old-shop-safe subset first).
**Out** — CMEL streams `OLD` and `OLD_TWIN` per scenario + raw blobs (R2) + runtime calls for R1.
**Inside**
1. Capture layers: outbound PayPal calls via mitmproxy (sandbox CA injected only inside the Cage) or Keploy eBPF on Linux; inbound buyer HTTP via reverse proxy; DB writes via the DB's query log; notifications (IPN/webhooks) arriving through the tunnel.
2. Rate limiter 45 req/min/IP; 429 → pause worker 5 min.
3. Each scenario run twice (noise twin) on fresh DB state.
4. After each run: ledger reads by IDs (GET transaction / order / capture) → PAYPAL_LEDGER events.
5. Mapping table (01 §3) turns raw records into CMEL; fields that differ between OLD and OLD_TWIN → `noise`.
**Who** — Explorer (Haiku/Sonnet) chooses runs to cover every money-flow edge; capture + mapping are deterministic.
**Fails →** IPN never arrives (sandbox delay) → wait window, then R13 backstop path recorded; scenario can't run on old → marked "new-only".
**Drawing**
```
driver ─▶ OLD shop ─▶ mitm ─▶ PayPal sandbox            ×2 (OLD, OLD_TWIN)
   │          │db log         │ IPN via tunnel ─▶ shop
   └──────────┴───────────────┴──▶ mapper ─▶ CMEL + noise fields ─▶ ledger
```
**Check (Zen Cart)** — happy path CMEL: INTENT(SetExpressCheckout, 19.99 USD, token) → APPROVE (return with token+PayerID) → CAPTURE(DoExpressCheckoutPayment, txn_id, 19.99 USD, Completed) → SHOP_PAID(order status) → (IPN for EC txn) NOTIFY → NOTIFY_VERIFIED. Noise: token, txn_id, timestamps, order number.

---
## R4 Money Rule Miner (GG-4)
**Job** — write this shop's Money Contract: base pack + shop-specific rules, each proven three ways.
**In** — old code (money-flow locations), CMEL OLD/OLD_TWIN, base pack R01–R16.
**Out** — `Contract{rules[]}` with agreement + triangle status.
**Inside**
1. Code read (Sonnet, SpecGen-style): propose shop rules from the money path, each with code refs.
2. Trace pass (deterministic, Daikon-style): mine invariants over CMEL (e.g. "SHOP_PAID always follows CAPTURE COMPLETED", "pending status id = X", "currency of capture ∈ {selectCurrency(order)}").
3. Agreement gate: keep rule as BOTH when code + traces agree; CODE_ONLY → Explorer asked for a trace; TRACE_ONLY → Scribe asked for the code reason; unresolved → MINOR/advisory.
4. Triangle: for each kept rule, Adversary must deliver ≥1 scenario + ≥1 mutant; Judge marks `killed` when the scenario fails on the mutant.
5. Old shop already breaks a rule? → recorded as a **current-shop bug** (fix-forward in GG-2).
**Who** — Scribe (Sonnet) + trace miner (code) + Explorer + Adversary + Judge.
**Fails →** no runtime (lane) → CODE_ONLY rules, marked so on the certificate.
**Check (Zen Cart)** — shop-specific rules found: (a) pending captures set `order_pending_status`, not paid; (b) one `TABLE_PAYPAL` row per transaction with `payment_status`; (c) IPN duplicates ignored by (txn_id, payment_status) in history table; (d) currency may be converted to a PayPal-supported currency (`selectCurrency`) — so R03 becomes "capture currency = selectCurrency(order currency) and amount converted consistently".
