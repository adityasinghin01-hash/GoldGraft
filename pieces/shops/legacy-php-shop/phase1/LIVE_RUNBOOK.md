# VJ02 execution runbook — blocked pending qualified counterparts

This is Vijay's domain recipe, an implementation proposal grounded in the pinned team requirements. It is not a shared request schema, payment recorder, proof engine or permission to bypass missing infrastructure. All fourteen scenarios are unattempted. The user confirmed GU02/GU03 are not ready on 8 November 2026.

## Admission

Follow the [current scope](../../../../docs/vijay/CURRENT_BASELINE.md), [counterpart handoff](../../../../docs/vijay/PHASE1_HANDOFF.md), original `SUPPORTED_FIRST_PATH.md`, `BASELINE_REPRODUCTION.md` and `PAYMENT_CONSTRAINTS.md` at team revision `da2b5f02d5559c510de6b3b9d81e58400bdf6c89`.

Required inputs: approved sandbox identities/broker/run authority, bounded permitted operations, pinned original and separately qualified candidate, verified exact runtime/build identity, protected helpers, isolated per-run order state, real recorder/ledger reads and trusted callback handling. Local `.secrets` possession and successful OAuth/GetBalance do not establish service authority. Do not attach a public tunnel to the offline lab; its payment/callback routes deliberately remain disabled.

The existing original uses NVP Express Checkout and IPN; it is not a REST/webhook implementation. NEW coverage requires its actual separate implementation, not relabelling the same source. Preserve baseline defects for characterization; do not make them the expected correctness rule.

## Per-run observations

Record actual shop/team revisions, source/runtime/config/scenario identity, sandbox environment, variant, unique run/order identity, timestamps, original API/account/object origin and redacted capture references. OLD and OLD_TWIN have separate stores and independently planned transaction namespaces. A new local run never deletes or reverses provider transactions. Retry an ambiguous effect only under its qualified API-specific identity/reconciliation policy; no blind new-key retry.

Retain secret-free raw body bytes where required for IPN/webhook verification through the trusted recorder. Credentials, auth headers, buyer PII and browser state remain private/ignored. Do not invent PayPal fields or convert sanitized reports back into signed raw notifications. Shared `RawCapture`/`JobResult` validation must use actual Python models; new formats wait SI01.

## Scenario execution and evidence

| ID | Exercise | Required observed evidence / stop condition |
| --- | --- | --- |
| S01 | Create, buyer approval, capture, browser return | Original order/provider IDs, USD amount/recipient, provider state and matching persisted order; repeat clean baseline purchases only after qualification |
| S02 | Cancel at buyer approval | Cancel path and provider readback; no paid/fulfilled state inferred from redirect |
| S03 | Decline | Supported provider-induced outcome labelled genuine or provider simulation; no fulfillment; simulation cannot replace real payment evidence |
| S04 | Pending then completed | Actual supported pending response and subsequent completion/verified event; HTTP 200 alone is not paid |
| S05 | Additional payer action | Exercise supported account/product path; unavailable required capability is a documented hold, not a silent skip |
| S06 | Duplicate submission/two tabs | Concurrent attempts, logical intent identity, provider effect count and local state; losing response must not overwrite winning state |
| S07 | Lost response/restart/retry | Persisted original request identity, authorized readback/replay, one economic effect; missing evidence remains unknown |
| S08 | Full/repeated refund | Refund through original API family/object/account, remaining refundable amount, pending/completed distinction and repeated attempt outcome |
| S09 | IPN authenticity/business checks | Original bytes and matching sandbox postback; recipient/status/amount/currency checks; forged/mismatched event has no financial effect |
| S10 | Pending/completed/duplicate/late IPN | State-aware dedupe, one fulfillment, legitimate status transition retained and no regression |
| S11 | Webhook authenticity/duplicate/wrong listener | Actual NEW app/listener binding and raw-body verification; duplicate suppressed; simulator evidence explicitly separate |
| S12 | Callback outage/reconciliation | Durable unverified receipt before acknowledgement, restart/recovery evidence, authorized reconciliation and unresolved gaps |
| S13 | Order persistence/restart | Actual payment/order correspondence survives process restart; no concurrent flat-file writers or state restoration over later payments |
| S14 | Amount/currency tamper | Trusted USD order amount and intended recipient against submitted/observed provider request; manipulation never silently accepted |

Do not force unsupported outcomes, stress the provider or guess negative-testing support. Keep PASS/FAIL/BLOCKED/UNVERIFIED distinct, with evidence provenance. The proof owner, not this runbook or a successful buyer exit, supplies monetary verdicts. Full completion needs all required evidence and qualified integration; a correctly blocked run is not completed payment delivery.

## Current hold

GU02 broker, GU03 protected runner/recorder/gateway, qualified runtime identity, approved new interfaces where needed and actual proof integration are missing. `scripts/phase1_status.py` lists all fourteen as BLOCKED/unattempted. They cannot be executed by enabling network functions or passing real credentials to the existing Windows lab.
