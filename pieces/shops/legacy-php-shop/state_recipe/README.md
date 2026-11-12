# VJ03 domain state and callback recipe

This is a local domain recipe and read-only inspector, not Gupta's export/fence/replay mechanism or a new StateCutover wire format. It follows the reviewed team VJ03 and atomic IR01/IR04 requirements. Source/runtime/authority/state consistency and actual callback evidence remain qualification gates.

## Current reference inventory

| Handler | Current write/route | Required preservation |
| --- | --- | --- |
| `vendor/src/api/create-payment.php` | SetExpressCheckout; writes `data/orders.json` CREATED | Original intent/token, exact amount/USD, originating sandbox account/API family and retry/reconcile identity |
| `vendor/src/api/execute-payment.php` | GetExpressCheckoutDetails/DoExpressCheckoutPayment; writes PAID | In-flight browser capture/return, original token/payer/transaction correspondence; pending must not be assumed paid |
| `vendor/src/api/refund.php` | NVP RefundTransaction; writes REFUNDED | Original NVP merchant/environment/transaction, refund history and remaining obligation; never reinterpret as a v2 capture |
| `vendor/src/ipn.php` | Validates synchronously then appends `data/ipn.log`; no order update | Original raw bytes/listener/environment, durable unverified receipt before acknowledgement, independent validation/business checks and state-aware effect dedupe |
| `vendor/src/api/orders.php` | Reads all orders without original authentication | Private/read-only qualified export only; never expose this original helper publicly |
| `vendor/src/success.php`, `cancel.php` | Browser pages | Redirect is not proof of money state; browser requests cannot be replaced by a callback queue |

These are static facts for the pinned source. Live workers, extra instances, scheduled tasks or external writers require separate actual discovery. The sample has no qualified admission control, all-writer fence, consistent authenticated export, durable callback receipt, high-water mark or independent exit executor. Installing such a primitive through a destructive restart before state preservation is forbidden by IR01.

## Read-only inspection

```cmd
python pieces/shops/legacy-php-shop/state_recipe/inspect.py --orders "PATH_TO_AUTHORIZED_LOCAL_SYNTHETIC_ORDERS.json"
```

The inspector emits only record counts, fixed status labels and finding categories. It rejects malformed/duplicate-key/oversized/linked input instead of treating it as empty, makes no changes or provider calls, and always retains migration_gate HOLD. It does not export private records or resolve unknown financial outcomes. An omitted input yields NOT_SUPPLIED, not an empty qualified store.

## Required cutover sequence for the actual backend

1. Establish approved controller/resource scope, exact current runtime/source/config and full writer/handler inventory.
2. Qualify independent merchant-owned notification receipt and original browser-handler continuity before touching the target. Unknown sessions or unsupported bridging cause hold.
3. Stop new admission through an existing safe control, drain/serve current sessions, then fence every writer and reconcile in-flight writes/effects. Admission stop alone is not a writer fence.
4. Record durable event high-water H and a consistent authorized export containing orders plus intent/origin/idempotency/callback obligations. Verify bounded export integrity and disposable restore/replay before the first destructive prerequisite mutation.
5. Under actual approved resource reservation, restore into one designated writer and replay post-H effects using their existing identities. Do not run old/new flat-file writers concurrently or restore an older snapshot over newer payments.
6. Read back state, backlog, browser/callback/refund routes and unresolved effects before reopening. Failure uses qualified current-state repair; code cutback does not reverse money.

No local implementation here performs these effects. Share primitive capabilities and approved schema versions through TEAM_INPUTS_NEEDED.md. Test cases for the responsible mechanisms: missing exporter/fence, active browser capture, late IPN completion, duplicate completion, legitimate later refund, missed callback, malformed source state, restore over newer money and unknown external effect. Expected failure is preservation plus a hold, not an invented success receipt.
