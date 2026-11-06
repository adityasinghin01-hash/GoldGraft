> **Status update — 6 November 2026.** Current Python contracts remain wire authority; compatible format descriptions below are reference. New proposals require versioned migration. Read [engineering baseline](../engineering/START_HERE.md), [current/proposed boundary](../engineering/CURRENT_VS_PROPOSED.md) and [atomic lifecycle protocols](../engineering/lifecycle/ATOMIC_DELIVERY_PROTOCOLS.md). Paper only; no implementation or live qualification. Earlier schedules/coverage/Done claims in the retained body are not current status.

---

# P12 · 01 — The data every piece speaks (schemas, by hand)

## 1. Graft Ledger entry (D8) — append-only, hash-chained
```
LedgerEntry {
  seq:int, graft_id, ts,
  type: STAGE | ARTIFACT | MESSAGE | VERDICT | SWITCH | ALERT | COST,
  producer: {kind: agent|service, name, version, model?},
  inputs: [entry_hash],              // what this was built from
  payload_ref: "r2://…" | inline JSON (≤16 KB), payload_hash: sha256,
  schema: "RootMap/1" | "CMEL/1" | "Contract/1" | …,   // rejected if payload fails schema
  prev_hash, entry_hash = sha256(prev_hash ‖ payload_hash ‖ type ‖ producer ‖ seq)
}
```
Daily: ledger root hash → Rekor entry (+ optional OpenTimestamps).

## 2. Root Map (R1 output)
```
RootMap { shop_id, stack: {lang, framework, versions, db}, lenses_run: [code, runtime, site, account],
  touchpoints: [{ id, family: WPS|EC_NVP|EC_SOAP|DIRECT_PAYMENT|RECURRING_NVP|BILLING_AGREEMENT|IPN|PDT|CHECKOUT_JS_V4|JS_V5|REST_V1|SERVER_SDK_OLD|PAYFLOW|BUTTON_HOSTED,
     operation: e.g. SetExpressCheckout, location: {file, line} | {url, selector} | {tcode},
     lenses: [code, runtime, site, account], confidence: 0–1, live: bool (seen at runtime),
     target: {paypal_mapping_id, rest_op}, paypal_only: bool, money_30d?: {minor, currency} }],
  money_flow: { create:[loc], approve:[loc], capture:[loc], mark_paid:[loc], refund:[loc], notify:[loc], recurring:[loc] },
  recall_evidence: { runtime_calls_total, matched_by_static, misses:[…] } }
```

## 3. CMEL — Canonical Money Event Log (GG-1)
```
MoneyEvent { graft_id, run_id, variant: OLD|OLD_TWIN|NEW, scenario_id, seq, t_ms,
  source: SHOP_HTTP | SHOP_DB | PAYPAL_CALL | PAYPAL_LEDGER | NOTIFICATION,
  kind: INTENT | APPROVE | AUTHORIZE | CAPTURE | VOID | SHOP_PAID | SHOP_PENDING | SHOP_UNPAID
        | NOTIFY | NOTIFY_VERIFIED | NOTIFY_REJECTED | REFUND | RECUR_SETUP | RECUR_CHARGE | ERROR,
  order_ref, pp: {legacy_token?, txn_id?, order_id?, capture_id?, refund_id?, profile_id?, debug_id?},
  money?: {minor:int, currency}, status_norm?: COMPLETED|PENDING|DECLINED|REFUNDED|FAILED,
  items_hash?, raw_ref, noise:[field] }
```
### Mapping table (each PayPal generation → CMEL)
| Source | Signal | CMEL |
|---|---|---|
| WPS form POST to `cgi-bin/webscr` | `amount`/`amount_n`, `currency_code`, `invoice`/`custom` | INTENT |
| NVP `SetExpressCheckout` | `PAYMENTREQUEST_0_AMT`, `…CURRENCYCODE`, `TOKEN` | INTENT (pp.legacy_token) |
| NVP `DoExpressCheckoutPayment` | `PAYMENTINFO_0_TRANSACTIONID`, `…AMT`, `…CURRENCYCODE`, `…PAYMENTSTATUS` | CAPTURE (Completed→COMPLETED, Pending→PENDING) |
| NVP `DoDirectPayment` | `TRANSACTIONID`, `AMT`, `ACK` | CAPTURE |
| NVP `RefundTransaction` | `REFUNDTRANSACTIONID`, `GROSSREFUNDAMT` | REFUND |
| NVP `CreateRecurringPaymentsProfile` | `PROFILEID` | RECUR_SETUP |
| IPN POST | `txn_type`, `payment_status`, `mc_gross`, `mc_currency`, `txn_id` | NOTIFY |
| IPN postback `_notify-validate` | `VERIFIED` / `INVALID` | NOTIFY_VERIFIED / NOTIFY_REJECTED |
| REST `POST /v2/checkout/orders` | `id`, `purchase_units[0].amount` | INTENT (pp.order_id) |
| v6 session `onApprove` | `orderId` | APPROVE |
| REST capture | `captures[0].id/amount/status` | CAPTURE |
| REST refund | `id`, `amount`, `status` | REFUND |
| Webhook `PAYMENT.CAPTURE.COMPLETED` | `resource.id`, `supplementary_data.related_ids.order_id`, amount | NOTIFY |
| `verify-webhook-signature` | `SUCCESS` / `FAILURE` | NOTIFY_VERIFIED / NOTIFY_REJECTED |
| Shop DB write | order status → paid / pending / unpaid | SHOP_PAID / SHOP_PENDING / SHOP_UNPAID |
| PayPal ledger read (after run) | GET order / capture / refund / transaction | PAYPAL_LEDGER copies of CAPTURE/REFUND |
Money always as integer minor units + ISO currency; zero-decimal currencies (e.g. JPY) handled by a currency table (verify PayPal's list in build).

## 4. Money Contract (GG-4) — rule format (WeChat rule/test idea, extended)
```
Rule { id, title, correct_flow:[text], counter_examples:[text],
  predicate: CMEL-DSL expression,           // executable
  sources: {code:[file:line], traces:[run_id]}, agreement: BOTH | CODE_ONLY | TRACE_ONLY,
  triangle: {scenarios:[id], mutants:[id], killed:bool}, severity: CRITICAL|MAJOR|MINOR }
```
### Base rule pack (every shop starts with these; Scribe adds shop-specific ones)
| ID | Rule (plain) | Predicate idea | Origin |
|---|---|---|---|
| R01 | paid only if PayPal shows one COMPLETED capture for this order | SHOP_PAID(o) ⇒ ∃! LEDGER CAPTURE(o, COMPLETED) | Checkout Proof I2 |
| R02 | captured amount = order total | CAPTURE.money.minor = INTENT(o).money.minor | I3 |
| R03 | captured currency = order currency | CAPTURE.money.currency = INTENT(o).money.currency | I3, D2 bug |
| R04 | not paid ⇒ no completed capture | ¬SHOP_PAID(o) ⇒ ¬∃ CAPTURE(o, COMPLETED) | I4 |
| R05 | retries/double clicks ⇒ ≤1 capture, no 5xx | count(CAPTURE COMPLETED, o) ≤ 1 | I5, WeChat debounce |
| R06 | unapproved order never confirmed | SHOP_PAID(o) ⇒ ∃ APPROVE(o) | D1 bug |
| R07 | pending capture ≠ paid | CAPTURE(PENDING) ⇒ SHOP_PENDING, not SHOP_PAID | Zen Cart pending path |
| R08 | notification acted on only if verified | NOTIFY ⇒ NOTIFY_VERIFIED before any SHOP_PAID it causes | IPN/webhook |
| R09 | duplicate notifications are harmless | same txn/event id twice ⇒ no second state change | WeChat, Alipay retries |
| R10 | replayed confirmation returns the same result, no second charge | replay(confirm) ⇒ same capture id | Cutover replay trap |
| R11 | refunds ≤ captured; second full refund refused | Σ REFUND ≤ CAPTURE | CP #13 |
| R12 | amounts never from the browser | INTENT.money derived server-side (static + mutant M7) | WeChat zero-trust |
| R13 | no callback ⇒ backend asks PayPal | missing NOTIFY within T ⇒ ledger lookup by shop | WeChat rule |
| R14 | restart mid-payment loses nothing | restart between APPROVE and CAPTURE ⇒ eventual single CAPTURE + SHOP_PAID | CP #9/restart |
| R15 | old objects stay on old rails | REFUND of a legacy txn uses the legacy path (or a proven REST equivalent) | Alipay+ |
| R16 | money as integers | static check + mutant M6 | WeChat iron rule |

## 5. Scenario + Mutant + Verdict
```
Scenario { id, family: HAPPY|CANCEL|DECLINE|PAYER_ACTION|DOUBLE|LOST_RESPONSE|TAMPER|PENDING|REFUND|REFUND_TWICE|NOTIFY_FORGED|NOTIFY_DUP|RESTART|RENEWAL|EDGE_CURRENCY|PROPERTY,
  cart, steps:[driver_step|api_step|mock(PayPal-Mock-Response code)], rules:[R..], expect, assured:{passes_on_old:bool, flake_free_runs:int} }
Mutant { id, op: M1..M12, location:{file,line}, patch, rule:R.., equivalent_suspect:bool, killed_by:[scenario] }
Verdict { scenario_id, grade: PROBLEM|UNVERIFIED|PASS|PASS_FIXED|N/A, rule_hits:[{rule, side: OLD|NEW, evidence:[event refs]}], parity_diff:[…], noise_masked:[field], deltas_applied:[delta_id] }
```
### MMO-12 (money mutation operators)
| Op | Fault planted in NEW code | Breaks |
|---|---|---|
| M1 | ignore currency in the amount check | R03 |
| M2 | skip capture-status check | R01 |
| M3 | confirm without approval | R06 |
| M4 | remove the per-order lock (two tabs) | R05 |
| M5 | random `PayPal-Request-Id` on retry | R05/R10 |
| M6 | money as float | R02/R16 |
| M7 | take amount/currency from the browser | R12/R02 |
| M8 | skip webhook signature verification | R08 |
| M9 | read order id from `related_resources` instead of `supplementary_data.related_ids` | R01 |
| M10 | case-sensitive signature header lookup | R08 |
| M11 | keep approved-but-uncaptured state only in memory | R14 |
| M12 | no refund-state check | R11 |

## 6. Certificate (GG-8)
```
Certificate { cert_id, shop_id, repo, commit_old, commit_new, branch, issued_at,
  results: {scenarios: n, pass, pass_fixed, problem:0, unverified, n_a},
  proof_strength: {mutants_total, equivalent_dropped, killed, score},
  survey: {recall, precision, misses_learned},
  security: {secrets_found:0, injection_attempts_blocked, deps_blocked},
  paypal_evidence: [{scenario, order_id, capture_id, debug_id}],
  cost: {usd, tokens}, time: {minutes by stage},
  ledger_root, runner_identity (workflow + sha), signature, rekor_entry, ots_proof? }
```

## 7. Recipe (Scion Bank) + Switch config + Budget
```
Recipe { id, fingerprint: {lang, framework, family, ast_shape_hash}, transform: ast-grep/PolyglotPiranha script,
  env: {dockerfile, compose, seed, driver_template}?, scenarios:[template], provenance:[cert_id],
  confidence: Beta(passes+1, fails+1) mean, status: QUARANTINE|ACTIVE|RETIRED, signature }
SwitchConfig { graft_id, stage_pct: 0|1|10|50|100, version, expires_at, origin_rules, signature (ed25519) }   // invalid/expired ⇒ old path
BudgetRecord { graft_id, agent, model, tokens_in, tokens_cached, tokens_out, usd, cap_usd }
```
