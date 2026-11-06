# Plan3 paper research — PayPal payment constraints

Checked: 6 November 2026. Official public PayPal documentation only; no account access, credentials, payment calls, product work or live jobs. All acceptance cases below are **proposed and unexecuted**. Documented behavior is not merchant-specific qualification.

## Decision summary

A timeout, stopped job or code cutback does not establish that money did not move. Preserve each payment's original API/account/app identity and reconcile ambiguous outcomes before another monetary action. Checkout modernization alone does not prove historical refunds, recurring billing or callback continuity.

Local requirements reviewed: `DELIVERY_REQUIREMENTS_UPDATE.md`, `outputs/plan_1/OPEN_GATES.md`, and `/Users/aditya/dev/GoldGraft/docs/design/05_HEAL_HANDOFF_FLEET.md`. This note supplies Plan3 evidence for subsequent Plan4 review and Plan2 documentation; it closes no implementation or release gate.

## Concrete constraints and evidence limits

| ID / topic | Official evidence and API-specific limit | Proposed Plan3 constraint |
|---|---|---|
| C01 — Ambiguous outcome | PayPal's idempotency guide explicitly describes a capture that succeeds remotely while its response times out. Supported REST POST retries use the same `PayPal-Request-Id`; replay returns the **current** result, and simultaneous same-key requests may cause the second to fail. Support and retention depend on the API. [S1][s1] | Persist the intended operation and its request identity before sending. Retry the same logical operation with the same payload/key only within its qualified window. Keep `UNKNOWN` separate from declined, cancelled and completed; a new key or fallback payment is not a safe response to uncertainty. Serialize competing attempts locally. |
| C02 — Retention is not universal | Orders v2 **create-order SDK reference** documents six-hour retention and an account-manager-requested extension up to 72 hours; the Expanded Checkout single-step example agrees. General request guidance gives a refund example of **up to 45 days**. Reviewed Orders capture and Payments v2 refund endpoint pages expose the header but omit a duration. [S2][s2], [S3][s3], [S4][s4], [S5][s5], [S6][s6] | Do not apply 45 days to all payments, or six hours to every capture/refund. Record endpoint, API version, supported key, evidence and actual extension separately. An unspecified/expired window requires reconciliation or a hold, not blind POST replay. Order approval/expiry times are separate from idempotency retention. |
| C03 — Resource state matters | Orders capture requires prior buyer approval or a valid `payment_source`. Payments v2 distinguishes capture states including `PENDING`, `COMPLETED`, `DECLINED`, `FAILED` and refunded states; refund states include `PENDING`, `COMPLETED`, `FAILED`, `CANCELLED`. [S5][s5], [S7][s7] | Keep order, authorization, capture and refund IDs/states distinct. Approval, browser return and HTTP success alone do not prove a completed capture/refund. Read the relevant resource and validate merchant/order binding, amount and currency before fulfillment or reporting completion. Retain later reversal/refund handling. |
| C04 — Refund restrictions | Payments v2 refunds use the **capture ID**; full and partial payloads differ. Checkout guidance requires cumulative refundable-balance checks, same transaction currency, and processing within 180 days, with possible shorter bank windows. It states processed refunds cannot be cancelled. [S6][s6], [S8][s8] | A refund is a separate authorized money movement, not an automatic rollback. Concurrent partial refunds must reserve/check remaining balance; never silently convert a failed refund into an unrelated payout. Request acceptance and customer receipt are different evidence. No guaranteed refund timing or universal eligibility claim. |
| C05 — Stop/cancel/cutback | Payments v2 void applies to an authorization and cannot void one already fully captured. The reviewed public Payments v2 endpoint inventory exposes void/refund, not a generally usable undo-in-flight guarantee. Its JSON includes a `cancel-payment` tag without a corresponding public path in that inventory: the tag alone proves no supported capability. [S9][s9], [S7][s7], [S10][s10] | Stop new submissions; preserve and reconcile already submitted work. Code rollback, browser cancellation, access revocation and deleting a local order do not reverse provider effects. If capture wins a void race, retain the capture and require a separately approved, eligible refund. Do not promise cancellation within seconds for remote money movement. |
| C06 — Legacy IPN validation | IPN requires an empty HTTP 200 receipt, then HTTPS postback of the unchanged fields/order/encoding prefixed with `cmd=_notify-validate`, to the matching sandbox/live `ipnpb` endpoint. Only `VERIFIED` establishes validation; recipient, payment status, amount and currency still need business checks. [S11][s11], [S12][s12] | Receipt acknowledgement is not payment acceptance. Reject/quarantine `INVALID`; validation outage stays unverified. Preserve the received message for recoverable processing without blocking the acknowledgement on slow work. Headers, browser redirects and sender-looking URLs do not substitute for verification. |
| C07 — IPN delivery and deduplication | IPN is asynchronous; delivery may be delayed/lost, with up to 15 retries over four days. PayPal explicitly warns that transaction ID alone cannot deduplicate: pending and completed notifications may share it. [S13][s13] | Suppress repeated effects while accepting legitimate status changes. Reordered/stale notifications must not regress a reconciled state. Separate subscription/profile events, payment transitions and refund/reversal transactions. A missing IPN is not evidence of failed payment; callback retry limits do not define a safe historical-retirement date. |
| C08 — REST webhook validation | Verification uses the subscribed webhook ID, transmission headers and the event. Self-verification uses the **original raw body**, its CRC32 and certificate signature; CRC32 alone is not authentication. Postback verification is another option. Simulator events belong to no app and do not support postback verification. [S14][s14] | Bind verification to the correct environment/app/listener configuration; preserve signed bytes. No order/payment mutation from an unverified event. Test simulator and actual app-event verification separately; simulator success cannot qualify production configuration or real payment effects. |
| C09 — REST webhook reach/delivery | Webhooks are app-specific, including between REST apps on the same merchant account. The special NVP/SOAP webhook app excludes NVP/SOAP recurring payments. Non-2xx delivery is retried up to 25 times over three days, then marked failed, with manual resend available. [S15][s15] | A new REST listener is not a universal replacement for old listeners. Inventory app/event coverage and retain required historical endpoints. Durable receipt, duplicate-safe processing and later reconciliation are required; finite retries provide no exactly-once or indefinite-delivery guarantee. |
| C10 — Historical refunds | NVP `RefundTransaction` has a default 180-day window, original `TRANSACTIONID`, delayed refund states, and a separate `MSGSUBID` retry mechanism available since API version 92.0. Deprecated Payments v1 still documents sale-specific refunds. [S16][s16], [S17][s17] | Retain API family/version, merchant/environment/app, original transaction/sale/capture IDs, refund history and required merchant-controlled access. Do not treat an NVP transaction or v1 sale ID as a v2 capture ID. No reviewed source establishes universal cross-family refund compatibility: preserve the original supported route until exact compatibility and continuity are proved. |
| C11 — Historical subscriptions | The Upgrade Hub maps old recurring calls to new subscription flows but does not establish automatic conversion of existing IDs/consents/history; it also mixes Payments v1 terminology with billing endpoints. Current Subscriptions documentation lists `PAYMENT.SALE.COMPLETED`, `.REFUNDED`, `.REVERSED`, plus billing lifecycle events. [S18][s18], [S19][s19] | Separate existing profiles, billing agreements and new subscriptions. Inventory status, schedule, next charge, outstanding balance, origin and callback route. Never recreate/cancel old billing merely because new checkout works. No blanket “PayPal-only conversion exists” or “conversion never needs consent” claim is supported here. A handoff export is evidence for a qualified conversion request, not conversion completion. |
| C12 — Subscription cancellation/recovery | Modern suspension is a reversible pause; hard cancellation requires sign-up again. Legacy `ManageRecurringPaymentsProfileStatus` permits reactivation only from suspended state. The modern schema likewise requires suspended state for activation and documents activation refusal after the payment-failure threshold. [S20][s20], [S21][s21], [S22][s22] | Pause, cancel, resume and settle debt are different actions. Never promise automatic reactivation, and never substitute suspension for a requested hard cancellation. Read back state after ambiguous responses; preserve already incurred payment/refund obligations. |
| C13 — Recovery is bounded | The current subscription guide describes five-day failed-payment retries, up to twice per billing cycle, and threshold suspension. Its example mentions capture after cancellation, while the schema's capture error specifies eligible states **active, suspended or expired**, excluding cancelled; balance must be positive, currency must match and amount cannot exceed debt. [S23][s23], [S22][s22] | Treat capture from cancelled subscriptions as **unresolved documentation disagreement**; no recovery promise until provider clarification and scoped qualification. Respect current balance/state, account restrictions and PayPal's scheduled retries; avoid duplicate debt collection. Retry cadence is this subscription product's behavior, not a rule for all legacy recurring products. |
| C14 — Reconciliation coverage | Transaction Search documents up to three hours before executed transactions appear, three years of history, maximum 31-day query spans, and potentially multiple reporting entries sharing a transaction ID. [S24][s24] | An immediate empty report cannot prove “not charged”. Preserve original records; page/window reporting correctly and distinguish balance-affecting entries. Older history, missing permissions, wrong app/account/environment or failed reads leave evidence gaps; they do not authorize a replacement charge. |

## Proposed failure acceptance cases

These are future acceptance requirements, not observations or permission to execute. For each case record the API/environment/resource identity, injected failure, provider evidence or explicit absence, resulting local state, permitted next action and monetary-effect count. A safe hold can pass the failure-handling case while full delivery remains blocked.

| Case | Failure/edge condition | Required acceptance outcome |
|---|---|---|
| P01 — Lost capture response | Provider completes capture; response is lost; application restarts. | Existing intent/key survives. Supported replay/readback finds one capture; one fulfillment; no fresh-key fallback charge. Unavailable evidence remains unknown. C01–C03. |
| P02 — Retry window | Retry just inside, at and beyond the qualified endpoint window; repeat with no documented window. | No assumed 45-day/72-hour extension. Unqualified replay is held; expiry never becomes proof of failure. C02. |
| P03 — Concurrent attempts | Two callers capture/refund the same intent; one receives a conflict/error. | Losing response does not mark the winning operation failed. Reconciliation establishes monetary effects; altered payload/new intent cannot reuse the old key. C01, C04. |
| P04 — Pending outcome | Capture/refund request succeeds at HTTP level but returns pending; completion arrives later. | UI and fulfillment distinguish pending from complete; repeated notifications cause one transition/effect. C03–C04. |
| P05 — Refund race | Two partial refunds together exceed the remaining amount; inject timeout after one succeeds. | No excess refund or blind second refund. Balance reservations and original refund identity survive restart; denied/pending outcomes stay distinct. C01, C04. |
| P06 — Stop versus capture | Stop/cutback/access revocation races an already submitted capture or void. | New work stops; remote outcome is reconciled and survives code rollback. Captured funds are not labelled cancelled; no unapproved compensating refund. C05. |
| P07 — Forged/misbound IPN | `INVALID`, verification timeout, altered encoding, wrong recipient/currency/amount, sandbox message at live handler. | No paid/fulfilled/refunded state from unverified or mismatched input; recoverable validation failures remain recorded. C06. |
| P08 — IPN state sequence | Same transaction sends pending → completed → duplicate completed → late pending; then refund/reversal. | Completion is not discarded by transaction-ID-only deduplication; fulfillment occurs once; stale pending cannot regress it; later financial events remain processable. C07. |
| P09 — Forged/replayed webhook | Wrong webhook ID, modified raw body, invalid signature, duplicate event; simulator event sent through postback verification. | No monetary/order effect before verification; repeated valid event has one effect. Simulator limitation is explicit, without weakening real-event verification. C08–C09. |
| P10 — Callback outage | Listener remains unavailable beyond provider retry period; delivery resumes after restart. | No assumption that all missed events will return. Recover via authorized reconciliation/resend where supported; identify unresolved gaps and prevent duplicate effects. C07, C09, C14. |
| P11 — Upgrade with history | New checkout passes; old NVP refund, v1 sale refund or recurring profile still exists. | Each historical family retains its qualified original route and notifications. Unknown cross-family compatibility blocks adapter removal; no recreated duplicate subscription. C10–C11. |
| P12 — Cancel/resume/debt | Hard-cancelled, paused, threshold-suspended, expired and zero-balance subscriptions; scheduled retry races manual recovery. | Enforce API-specific states/debt limits; no automatic revival or duplicate collection. Cancelled-state documentation disagreement remains a hold. C12–C13. |
| P13 — Delayed/absent reports | Empty report within three hours; duplicate reporting ID; history outside supported range; authorization/read fails. | No “not charged” conclusion from absence alone. Distinguish report entries and disclose unreconciled records without issuing replacement money movement. C14. |
| P14 — Clean exit/restart | Remove temporary service access and restart merchant runtime while an old callback/refund/pending payment remains. | Merchant-controlled state, runtime credentials and required old/new routes continue operating; reconciliation resumes. Preserve evidence through restored backup/code cutback. Otherwise hold completed-handoff status. C01, C07, C09–C11. |

## Changes the later paper design must carry

- **Cutback:** limit any seconds-based target to routing/configuration observations. Preserve every submitted transaction on its originating payment path until reconciled; do not describe code rollback as financial rollback.
- **Cleanup:** a soak period or elapsed refund window alone is insufficient. Retain necessary refund, recurring, delayed-payment, dispute/reversal and callback handling until their obligations and replacement coverage are explicitly qualified.
- **Handoff:** inventory/export does not prove provider conversion, consent portability, preserved billing dates or successful renewal. Merchant-specific eligibility, permissions, conversion route and post-exit operation remain open.
- **Proof:** compare baseline and upgraded behavior against payment requirements; known baseline defects are not acceptance criteria. Seeded events can check handling, but cannot establish real renewal timing, risk decisions, settlement, account eligibility or production continuity. No tests were run for this note.

## Official source register

All sources were retrieved as public documentation on 6 November 2026. They are multiple PayPal pages, not independent validation of PayPal behavior. Generic guides, rendered references and schemas can disagree; the limits above retain those disagreements instead of inventing universal guarantees.

1. [S1 — REST idempotency][s1]
2. [S2 — Orders v2 create-order SDK header][s2]
3. [S3 — Expanded Checkout single-step Orders use case][s3]
4. [S4 — REST request guidance and refund retention example][s4]
5. [S5 — Orders v2 capture][s5]
6. [S6 — Payments v2 refund captured payment][s6]
7. [S7 — Payments v2 official JSON schema][s7]
8. [S8 — Checkout refund guidance][s8]
9. [S9 — Payments v2 void authorization][s9]
10. [S10 — Payments v2 public endpoint inventory][s10]
11. [S11 — Implement an IPN listener][s11]
12. [S12 — Process IPN messages and business validation][s12]
13. [S13 — IPN introduction, retry and state-aware duplicate checks][s13]
14. [S14 — Webhook integration and simulator limitations][s14]
15. [S15 — Webhook scope, validation and retries][s15]
16. [S16 — NVP RefundTransaction][s16]
17. [S17 — Payments v1 sale refund, deprecated][s17]
18. [S18 — Express Checkout subscription upgrade guide][s18]
19. [S19 — Subscription webhook event families][s19]
20. [S20 — Modern subscription pause/resume][s20]
21. [S21 — Legacy recurring-profile status restrictions][s21]
22. [S22 — Subscriptions v1 official JSON schema][s22]
23. [S23 — Subscription payment failures and recovery][s23]
24. [S24 — Transaction Search limits][s24]

[s1]: https://developer.paypal.com/api/rest/reference/idempotency/
[s2]: https://developer.paypal.com/sdk/orders/v2/orders-create/
[s3]: https://developer.paypal.com/api/rest/integration/orders-api/api-use-cases/advanced/
[s4]: https://developer.paypal.com/api/rest/requests/
[s5]: https://developer.paypal.com/api/orders/v2/orders-capture
[s6]: https://developer.paypal.com/api/payments/v2/captures-refund
[s7]: https://developer.paypal.com/api/payments/v2/schema.json
[s8]: https://developer.paypal.com/checkout/refund-payment
[s9]: https://developer.paypal.com/api/payments/v2/authorizations-void
[s10]: https://developer.paypal.com/api/payments/v2
[s11]: https://developer.paypal.com/api/nvp-soap/ipn/IPNImplementation/
[s12]: https://developer.paypal.com/api/nvp-soap/ipn/ht-ipn/
[s13]: https://developer.paypal.com/api/nvp-soap/ipn/IPNIntro/
[s14]: https://developer.paypal.com/api/rest/webhooks/rest/
[s15]: https://developer.paypal.com/api/rest/webhooks/
[s16]: https://developer.paypal.com/api/nvp-soap/refund-transaction-nvp/
[s17]: https://developer.paypal.com/api/deprecated/payments/v1/sale-refund
[s18]: https://developer.paypal.com/upgrade/ec/guide/Subscriptions/
[s19]: https://developer.paypal.com/subscriptions/webhooks
[s20]: https://developer.paypal.com/subscriptions/pause-or-resume
[s21]: https://developer.paypal.com/api/nvp-soap/manage-recurring-payments-profile-status-nvp/
[s22]: https://developer.paypal.com/api/subscriptions/v1/schema.json
[s23]: https://developer.paypal.com/subscriptions/payment-failure-retry/
[s24]: https://developer.paypal.com/api/transaction-search/v1/search-get
