# Independent NEW-side PHP stand-in

SYNTHETIC — hand-made from PayPal docs; not a recording and not a claim about the real shop.
MIT, authored for GoldGraft. No Cutover migrated code is included.

Sources: [Orders v2](https://developer.paypal.com/api/orders/v2/),
[Payments v2](https://developer.paypal.com/api/payments/v2/),
[webhook verification](https://developer.paypal.com/api/webhooks/v1/verify-webhook-signature-post).
The front-end target is [v6 sessions](https://developer.paypal.com/sdk/js/reference/).

`payments.php` supplies create, capture, refund and webhook functions. Its HTTP
callable and durable storage are injected stand-ins, not supplied infrastructure.
It has no secret literals, no network on load and no external dependencies.
The file is a small mutation target, not a complete deployable checkout.

The storage stand-in has the following semantic obligations:

- `catalogueTotalMinor`, `save`, `get` use an integer catalogue and durable rows.
- `locked` is an atomic per-order critical section; writes are atomic upserts.
- `saveApproval` persists the approved remote order for restart recovery.
- `setPaid`/`setPending` upsert the same capture ID, never a second charge.
- `recordRefund` deduplicates refund IDs. Only completed PayPal refunds are recorded.
- `verifiedNotification` atomically deduplicates event IDs and matches the trusted
  signed resource's order, amount and currency to its locally approved order.
  It relies on its caller to have verified the signature. This trust boundary is
  precisely what M08 removes. It does not independently re-verify the signature.

PayPal's one-order capture guard and idempotency are part of the HTTP stand-in.
These explicit guarantees explain equivalent suspects M03, M04 and M12.
Only M03 is dropped. M04 and M12 remain in the denominator: guards can change
recorded API observations even when duplicate economic IDs prevent extra money. They are not blanket claims about arbitrary PHP shops or PayPal retries.
M01, M04, M05, M09, M10, M11 and M12 survive the linked tests: see `../mutants/runs.json`.

Mutation outcomes are hand-authored expected answers. They were not measured by
executing PHP or calling PayPal; no PHP CLI is available on PATH in this environment. Each
patch is nevertheless checked offline against the original source with strict
unified-diff context/line matching. The baseline for mutation runs is this correct
stand-in, so PENDING starts PASS here, unlike the intentionally broken NEW PENDING
trace in the mapper/Judge corpus. M06 is killed by static R16; M07 is killed by
static source dependence and the 1 EUR browser quote versus 2500 USD catalogue.

Proof strength is 4 / (12 - 1) = 4/11. It deliberately fails the >=0.95 U5 gate.

For the mutation NOTIFY_FORGED run, pause after saveApproval and before capture.
The approved local row exists durably, but PayPal has no completed capture. This
explicit stand-in state lets M08 trust a forged completion; independent amount
and approval checks still pass. The correct handler rejects the signature.

The DOUBLE mutation run queues two approvals, then invokes confirmation handlers
sequentially. M04 survives that schedule; overlapping critical sections need a
separate test. REFUND_TWICE remains PASS_FIXED for a surviving NEW mutant because
the OLD synthetic R11 bug is still reported. The storage callback is typed as
verifiedNotification(string eventId, string orderId, array resource); M09 passes
a missing order ID and aborts the run, hence UNVERIFIED rather than a U3 kill.
