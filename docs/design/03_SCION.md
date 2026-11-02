# P12 · 03 — Scion (build the new code), built by hand

---
## S1 Target Planner
**Job** — decide, for every touchpoint, what it becomes and in which order — before any code changes.
**In** — RootMap, Contract, RulesHub mappings (shop's language), PayPal llms.txt pages, Scion Bank recipes, platform facts (does an official modern module exist?).
**Out** — `TargetPlan{ path: OFFICIAL_MODULE | REWRITE | LINKS, items:[{touchpoint, target_op, mapping_id, delta_ids, paypal_only}], target_experience:[V6, ORDERS_V2, WEBHOOKS, VAULT?, PAY_LATER_MSG, PLACEMENT, AGENT_READY_CHECK], origin_rules, order:[READ_BOTH → NEW_FLOWS_BEHIND_SWITCH → (later) CLEANUP], handoff:[…] }`.
**Inside**
1. **Prefer official**: if the platform ships a maintained modern PayPal module, plan = enable it + port customisations + switch; else REWRITE; no-code → LINKS.
2. Map each touchpoint literally from RulesHub (no inferred equivalents — RulesHub's own rule); unmapped (e.g. DoDirectPayment → card fields needs eligibility) → item flagged + plain reason.
3. Declare **intent deltas** (allowed differences): e.g. redirect → popup, TOKEN → order id, IPN → webhook names. Each delta cites its PayPal mapping; undeclared differences later count as parity failures.
4. **Origin rules**: objects created by old code (captures, refunds, profiles, billing agreements) keep their old path until proven otherwise (Step 6 test: Orders v2 refund of an NVP capture).
5. **Readers first** (Stripe): first change makes every reader (admin order view, reports, refund screen) understand both generations; then new flows behind the switch; cleanup only after LIVE_100 + soak.
6. Subscribers: never force re-consent; old profiles keep renewing; new sign-ups → Subscriptions API; profile/agreement IDs → handoff file.
7. Target experience items with PayPal's own reasons (vaulted ≥95% conversion, presentment "more than twice the selection rate" — cited, not claimed).
**Who** — Architect (Haiku; Sonnet for hard cases). Deterministic mapping lookups.
**Fails →** mapping missing → item stays on old path, listed as "needs PayPal step" or "not automatable yet".
**Drawing**
```
RootMap ─┐                 ┌─ OFFICIAL_MODULE ─┐
Contract ┼─▶ path choice ──┼─ REWRITE ─────────┼─▶ items (literal RulesHub map) ─▶ deltas ─▶ origin rules ─▶ order
RulesHub ┘                 └─ LINKS ───────────┘
```
**Check (Zen Cart)** — path = OFFICIAL_MODULE: enable `paypalr` (PayPalRestful v2.1.1: "combines … paypaldp and paypalwpp … uses PayPal's now-current REST APIs") for new checkouts; keep `paypalwpp` installed but hidden at checkout so admin refunds/voids of legacy orders still use NVP (origin rule); WPS `paypal.php` off for new checkouts, IPN handler kept for late IPNs on legacy orders; `paypaldp` card flow → REST card fields only if the sandbox account is eligible (flag). Deltas: redirect→popup/redirect per plugin, TOKEN→order id, IPN→webhooks.

---
## S2 Recipe Runner (Scion Bank, deterministic)
**Job** — apply already-proven transformations first, so AI writes as little as possible.
**In** — TargetPlan, matching recipes (fingerprint lookup), repo.
**Out** — commits on branch `goldgraft/<graft_id>`; list of items still open for S3.
**Inside** — fingerprint each touchpoint (lang + framework + family + AST shape hash) → recipes with status ACTIVE and confidence ≥ threshold → run ast-grep / PolyglotPiranha script → commit per recipe → items covered marked `recipe:<id>`. QUARANTINE recipes never run on shops other than their origin.
**Who** — deterministic.
**Fails →** recipe fails to apply cleanly → revert that commit, item goes to S3, recipe confidence updated.
**Check (Zen Cart)** — first Zen Cart: no recipe (cold). After certificate, a recipe `zencart/legacy→paypalr` is stored (env + config + switch observer + scenarios) in QUARANTINE until proven on K more Zen Cart shops.

---
## S3 Graft Writer (the only code-writing agent)
**Job** — write the remaining changes, exactly as the plan says, so the Union Proof can pass.
**In** — TargetPlan items still open, RootMap, Contract (rules only, not scenarios), PayPal grounding pack for the language (RulesHub snippets + server-SDK skills via APIMatic context plugin + llms.txt pages), verdict evidence on repair rounds.
**Out** — commits (readers-first, then new flows behind the Graft Switch); a change list mapping each commit to plan items.
**Inside**
1. Commit 1 — **read both**: every place that reads payment records understands old and new IDs/fields.
2. Commit 2 — **new flows**: Web SDK v6 front end, Orders v2 server calls (server SDK where one fits), webhook handler (verify signature, case-insensitive headers, dedupe by event id), Graft Switch calls at the entry points.
3. Guards (hooks, not trust): SDK hallucination guard (every SDK class/method looked up in the installed package — Cutover idea); dependency allowlist; no secret literals; amount/currency computed server-side.
4. Several attempts allowed (Google pattern); first candidate that passes the Union Proof wins (parallel candidates only for first-of-kind shops, budget permitting).
5. Repair: input = Judge evidence only (rule ids, event refs, diffs), never the Adversary's reasoning.
**Who** — Grafter (Sonnet; Opus after 2nd failed round).
**Fails →** cap hit → PARTIAL certificate with exact open items.
**Drawing**
```
plan items ─▶ grounding pack ─▶ commit 1 (read both) ─▶ commit 2 (new flows + switch) ─▶ guards ─▶ Union Proof
                                        ▲                                                     │ fail
                                        └────────────── evidence-only repair ◀────────────────┘
```
**Check (Zen Cart)** — code written is small: a Graft Switch observer (Zen Cart notifier hook) that sets `paypalr` vs `paypalwpp` `enabled` per session from the signed switch config; config rows for REST creds + webhook; admin order view already reads `TABLE_PAYPAL` for both module codes (verify — else commit 1 adds it); any store customisations hooked to `paypalwpp` notifiers ported to `paypalr`.

---
## S4 Graft Switch (runtime library, one per language)
**Job** — route each buyer to old or new code safely, and keep every money object on the rail it was born on.
**In** — signed SwitchConfig (pulled every 15 s, cached), session id, object refs.
**Out** — route decisions + money events to the guard.
**Inside**
```
route(session):  cfg valid & not expired ? (hash(session) mod 100 < cfg.stage_pct ? NEW : OLD) : OLD     // sticky per session
origin(obj):     legacy id shape / stored origin tag ⇒ OLD ; REST id ⇒ NEW                               // refunds, renewals, captures
emit(event):     non-blocking POST to /guard/event (amount, currency, order ref, ids) ; buffered if offline
in-flight:       a session that started OLD finishes OLD even if the stage changes
```
Notifications: IPN listener and webhook handler both stay live; dedupe by txn/event id (dual-accept, WeChat/Stripe pattern); webhook handler acks fast, processes async (PhonePe).
**Who** — code (tiny library: PHP, Node, Python, Ruby, Java, .NET).
**Fails →** config fetch fails → last valid config until expiry → then OLD; guard unreachable → events buffered, stage frozen.
**Check (Zen Cart)** — PHP observer reads config, sets module enable flags per session; legacy orders' refunds keep using `paypalwpp::_doRefund`.

---
## S5 No-code Lane
**Job** — upgrade shops that only pasted PayPal buttons, with zero effort from the owner.
**In** — site URL; optional NVP creds (to read hosted buttons); REST app (to create links).
**Out** — `LinksPack{buttons:[{page, old_form_fields | hosted_button_id, new_link_url, snippet_html}], proofs:[{link, order/capture ids}], untouched:[Donate, Subscribe (not retiring per PayPal notice)]}`.
**Inside** — crawl pages → parse forms posting to `cgi-bin/webscr` (cmd, business, item_name, amount, currency_code, hosted_button_id) → hosted buttons via `BMGetButtonDetails` if creds → create Payment Links (`POST /v1/checkout/payment-resources`) → one sandbox payment per link via KERNEL buyer → ledger check amount/currency → snippet + plain "replace this with this" guide; if the site lives in a repo (e.g. GitHub Pages) → PR replacing the forms.
**Who** — Surveyor (site lens) + deterministic link creation + Herald.
**Fails →** Button Manager unavailable in sandbox (Step 6 test) → use form fields only.
**Check** — not Zen Cart; demo uses a licensed static Buy Now site.
