# Separate NEW PHP candidate — local component delivery

Latest continuation: `php_port.py`/`port_worker.php` now implement the private PHP-to-typed-broker binding. `callbacks.py` consumes the actual gateway and triggers original-rail GET reconciliation. Seventeen actual-counterpart tests pass with injected HTTP/verifier responses. The earlier statement below that the private bridge is absent is superseded; real-service/merchant qualification remains open. See [FINAL_LOCAL_STATUS.md](../../../../docs/vijay/FINAL_LOCAL_STATUS.md).

The frozen OLD source remains under `../vendor/`. This candidate implements USD one-time order logic in `Checkout.php`, with private SQLite state and an injected payment port. Its default test/harness ports are **scripted offline**. No PayPal transport, custody, callback verifier, service approval, deployment or financial-proof engine is copied into this role.

Run from the repository root in CMD:

```cmd
scripts\check-candidate.cmd
```

The command executes native PHP domain checks, an independent PHP-process restart, read-only state inspection, actual PHP server startup and Playwright browser lifecycle. The temporary databases and lab key remain ignored and are removed by their owning supervisor. Existing Chromium is reused; no Docker, browser download, account or API key is needed.

## Components and boundary

| File | Implemented behaviour |
| --- | --- |
| `Checkout.php` | Trusted catalogue totals; persistent intent/cart/merchant/origin binding; durable operation identity before dispatch; capture/pending/decline/refund state; strict amount/resource checks; GET-only reconciliation |
| `broker_adapter.py` | Private current `PayPalClient.rest` vocabulary mapped to Gupta's `PaymentBroker.execute_orders_v2`; fixed operation allowlist and bound backend references; explicit evidence-mode checks |
| `continuity.py` | Read-only SQLite snapshot, integrity and origin/resource/journal checks; redacted counts/digest only; no merchant mutation |
| `test_checkout.php`, `restart_check.php` | Scripted domain, restart, actual switch-library/staged-admission/origin continuity checks |
| `offline_router.php`, `offline.html` | Explicitly labelled private scripted browser harness; no public file serving or payment transport |

The PHP port has the same argument/return vocabulary as current `PayPalClient.rest(method,path,body,headers) -> (status,mapping)`. The Python adapter maps that vocabulary to the inspected typed broker; **a PHP/Python bridge has not been qualified or installed**. It is an internal seam, not a new public API. The supervisor disables PHP URL/process helpers and supplies no sandbox credentials. This is trusted local testing, not hostile-code isolation.

## Important semantics

- `open(id,cart)` binds one intent to its exact server-priced cart. Independent test orders need different IDs. An existing intent cannot be changed to a new basket after dispatch.
- Mutations reserve and commit a random stable request identity before sending. An overlapping call or process restart sees the persisted reservation and cannot dispatch again. The operation journal is shop-owned state; it does not replace the broker's journal or authority checks.
- A timeout, malformed body, mismatch or uncertain status holds the operation. Read-only GETs may reconcile a known resource. Unknown create/refund effects without their provider ID remain held for qualified lookup; **no fresh-key retry is invented**.
- Minimal create/refund responses persist the known identity and require GET read-back. The current typed broker does not forward `Prefer`; requesting representation is not enough to establish business binding.
- Only one final USD capture for the exact order/merchant/amount can become `PAID`. Pending, payer action, cancellation, failed or declined responses cannot establish fulfillment. Browser signals never change financial status.
- Refunds use the recorded NEW capture ID. Only one full-amount refund intent is supported. Pending/unknown refund remains unfulfilled/held; a repeated refund cannot dispatch again. OLD NVP transactions remain outside this NEW component and must retain their original rail.
- Switch percentage/expiry controls new admission only. Tests show an existing NEW capture/refund stays NEW through Cutback and expiry. This does not measure a real proof-driven rollback or implement final merchant routing.
- The injected port must return a trusted server-side response. This component does not accept untrusted browser payment JSON or callback verification flags. Callback application remains a counterpart integration gate.

## Scope and sources

**Documented requirements:** [VJ01–VJ05](https://github.com/adityasinghin01-hash/GoldGraft/blob/525c22de61b504f67ea633e5aac95b8bed0fda64/docs/vijay/START_Aditya_Vijay_paypal_shops.md), [first supported path](https://github.com/adityasinghin01-hash/GoldGraft/blob/525c22de61b504f67ea633e5aac95b8bed0fda64/docs/vijay/engineering/connection/SUPPORTED_FIRST_PATH.md), [baseline/candidate separation](https://github.com/adityasinghin01-hash/GoldGraft/blob/525c22de61b504f67ea633e5aac95b8bed0fda64/docs/vijay/engineering/lifecycle/BASELINE_REPRODUCTION.md).

**Verified technical facts:** [current payment protocol](https://github.com/adityasinghin01-hash/GoldGraft/blob/525c22de61b504f67ea633e5aac95b8bed0fda64/contracts/src/goldgraft_contracts/interfaces.py), [typed broker actions](https://github.com/adityasinghin01-hash/GoldGraft/blob/525c22de61b504f67ea633e5aac95b8bed0fda64/pieces/backend/payment_broker.py), [PayPal operation-specific idempotency](https://developer.paypal.com/api/rest/reference/idempotency/), [capture states](https://developer.paypal.com/sdk/orders/v2/definitions/capture/), [refund API](https://developer.paypal.com/api/payments/v2/captures-refund), [SQLite transaction semantics](https://www.sqlite.org/lang_transaction.html).

**Implementation proposals:** SQLite as this separate fresh candidate's local state store, private injected adapter, conservative single-dispatch/GET policy, local inspection and browser harness. These are not an approved legacy-state migration, new shared wire format or completed live checkout. No import/reset of the original `orders.json` is performed.

**Unresolved integration gates:** qualified PHP port binding, protected runtime/recorder, actual callback ingress/business handoff, independently verified sandbox authority, real counterpart/proof execution, approved state bootstrap/apply/finalisation/exit. See [local delivery report](../../../../docs/vijay/LOCAL_PHASE_DELIVERY.md). Ordinary local test success cannot pass those gates.
