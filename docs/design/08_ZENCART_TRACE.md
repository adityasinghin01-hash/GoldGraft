> **Status update — 6 November 2026.** The original body below is historical reference and is superseded for current target behaviour by reviewed engineering documents. Zen Cart trace is historical; the first qualification reference is the bounded plain-PHP shop, not all eleven shops. Read [engineering baseline](../engineering/START_HERE.md), [current/proposed boundary](../engineering/CURRENT_VS_PROPOSED.md) and [atomic lifecycle protocols](../engineering/lifecycle/ATOMIC_DELIVERY_PROTOCOLS.md). Paper only; no implementation or live qualification. Earlier schedules/coverage/Done claims in the retained body are not current status.

---

# P12 · 08 — Zen Cart traced through every piece (on paper)
Shop: zencart/zencart (PHP, pushed 31 Oct 2026). Our fork, sandbox only. Facts from its code (read via GitHub API 1 Nov): legacy modules `paypal.php` (WPS), `paypalwpp.php` + `paypal/paypal_curl.php` (Express Checkout over NVP, `api-3t.sandbox.paypal.com/nvp`), `paypaldp.php` (Direct Payment), `ipn_main_handler.php` (IPN postback, duplicate check on txn_id + payment_status); official REST plugin `zc_plugins/PayPalRestful/v2.1.1` (combines paypaldp + paypalwpp on REST, webhook handlers for capture completed/pending/declined/refunded/reversed).

| # | Piece | What happens to Zen Cart | Artifact |
|---|---|---|---|
| 1 | G1 Connect | fork connected via GitHub App; sandbox REST app + NVP creds into vault; checks: REST ✓, NVP ✓, version match (old modules = NVP) ✓, webhook registered to tunnel/relay ✓ | Connection |
| 2 | G2 Probe | WPS, EC-NVP, Direct Payment, IPN found; official REST plugin present; note: WPS Buy Now "may retire after 1 Jan 2027" | ProbeResult |
| 3 | Gardener | lane = FULL (PHP, boots in a container) | LaneChange |
| 4 | R2 Builder | php-apache + MySQL; zc_install with demo products; `paypalwpp` enabled with sandbox NVP creds; `HTTP_SERVER` = tunnel URL; driver written (product → cart → checkout → PayPal Express → sandbox approve → return → confirm) and proven 3× | RunnableShop, Driver |
| 5 | R3 Recorder | ~20 scenarios × 2 (old + twin) under 45 req/min/IP across runners; IPN arrives through tunnel | CMEL OLD/OLD_TWIN |
| 6 | R1 Survey (runtime fed back) | runtime calls: SetExpressCheckout, GetExpressCheckoutDetails, DoExpressCheckoutPayment, RefundTransaction (admin refund scenario), IPN postback — all matched to code hits; DEAD: DoDirectPayment path if card module disabled | RootMap (recall measured) |
| 7 | R4 Scribe | base pack R01–R16 + 4 shop rules: pending → `order_pending_status`; one `TABLE_PAYPAL` row per txn; IPN dup ignore; capture currency = `selectCurrency(order currency)` | Contract |
| 8 | S1 Architect | path OFFICIAL_MODULE: `paypalr` for new checkouts; `paypalwpp` hidden but installed for legacy refunds/voids (origin rule); WPS off for new; IPN handler kept; card flow flagged (eligibility); deltas: TOKEN→order id, IPN→webhooks | TargetPlan |
| 9 | S2 Recipes | none yet (first Zen Cart) | — |
| 10 | S3 Grafter | commit 1: admin order view reads both module codes (verify; add if missing) · commit 2: install/enable `paypalr`, REST creds + webhook config, Graft Switch observer (per-session module choice from signed config), port store customisations | Commits |
| 11 | U1 Adversary | scenarios: happy, cancel, decline (mock), payer-action (mock), two tabs, lost response, tamper (currency/amount), pending (mock), refund, refund twice, forged webhook, duplicate webhook, restart, edge currency; property carts; 12 mutants placed on the `paypalr` path + observer | ScenarioSet, MutantSet |
| 12 | U2 Judge | each scenario: OLD (+twin) vs NEW vs ledger → PASS / PASS_FIXED / PROBLEM; any old-shop bug reported as a current-shop finding | Verdicts |
| 13 | U3 Strength | mutants run only against linked scenarios → score; target ≥0.95 | proof_strength |
| 14 | U4 Repair | e.g. if a webhook handler config is missing → evidence → Grafter fixes → re-run | Commits |
| 15 | U5 Certify | round 1 smoke → round 2 full → gate → signed on runner → Rekor → certificate page | Certificate |
| 16 | F2 PR | PR on our fork: changes, certificate link, rollback steps (Cutback), PayPal-only items (none unless recurring) | PR |
| 17 | Merge (consent) | teammate approves as "merchant" | MERGED |
| 18 | H1 Shadow | simulated buyers on old module; `paypalr` path shadow-run in sandbox; parity all PASS | Shadow verdicts |
| 19 | H2 Heal | 1% → 10% → 50% → 100% on simulated traffic (n_min 30 per stage) | SwitchConfig versions |
| 20 | H3 Cutback (demo) | fault injected (M1 currency ignore) on live new path → first mismatch → Cutback; time shown | Cutback entry |
| 21 | H4 Cleanup | after soak: switch observer removed; `paypalwpp` left non-selectable until legacy orders age out | Cleanup PR |
| 22 | B1 Learn | recipe `zencart/legacy→paypalr` (env, config, observer, scenario templates) → QUARANTINE; 2nd Zen Cart test shop proves it → ACTIVE; minutes + $ drop shown | Recipe |
| 23 | B2 Orchard | Zen Cart row: family mix, stage, certificate, cost, time | Fleet row |

**Honest notes from this trace**
- Zen Cart already ships an official REST plugin → its upgrade is mostly "enable official module + prove + switch safely + keep legacy refunds working", not a rewrite. The REWRITE path is shown on custom shops (Cutover's PHP sample, django-oscar-paypal, better_spree_paypal_express, expressCart).
- Zen Cart's licence shows NOASSERTION on GitHub (project says GPL) — confirm before forking publicly.
- Live IPN/webhook delivery needs a public URL → cloudflared quick tunnel from the runner (Step 6 test) or our relay on Render.
