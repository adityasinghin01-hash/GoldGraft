# Reference source and runtime observations

Source-inspected on 7 November 2026 at team commit da2b5f02d5559c510de6b3b9d81e58400bdf6c89. Upstream Cutover source revision is aedc11dde1a8793285665ca2188aff62ab5aab65 (MIT). They are different identities; neither is an observed deployed image. File paths below are relative to the reference root. No PHP/container/payment was executed.

| Component | Observed source | Qualification consequence |
| --- | --- | --- |
| Build | Dockerfile copies src into php:8.3-apache, creates writable data directory | Base is a mutable tag, not a qualified linux/amd64 digest. PHP curl functions and healthcheck curl executable must be checked in the actual image; no dependency guarantee inferred. |
| Startup | docker-compose.yml maps 8081:80 and health-checks index.php | Healthy HTML is not payment proof or authenticated lab access. Do not publicly expose this baseline. |
| State | src/lib/orders_store.php resolves ../data/orders.json; full-file read/modify/write without lock | Served root data directory; no MySQL. Concurrent writers can lose updates. Isolate synthetic run state; don't assume crash durability or safe shared-volume cutover. |
| Persistence | Compose mounts shop-data at /var/www/html/data | Named local volume is not Render qualification, backup/export, writer fencing or independent merchant ownership. |
| Create | src/api/create-payment.php uses SetExpressCheckout and writes CREATED order | Float arithmetic/quantity handling need normative amount checks. Preserve original baseline bytes; do not tune away defects before characterization. |
| Capture | src/api/execute-payment.php calls GetExpressCheckoutDetails and DoExpressCheckoutPayment | ACK success leads directly to PAID without inspecting actual payment state. Source risk only; real pending behavior must be observed, not invented. |
| Refund | src/api/refund.php checks PAID then RefundTransaction, updates REFUNDED | No authenticated access shown. Existing guard is not concurrent repeated-refund protection or qualified refund idempotency. Never assume NVP IDs work as v2 captures. |
| Order helper | src/api/orders.php returns all orders, no authentication | Protected lab/gateway prerequisite before any exposure; could disclose stored payer details. |
| IPN | src/ipn.php posts raw input prefixed cmd=_notify-validate; on VERIFIED+Completed appends data/ipn.log | No durable unverified receipt-before-ack, state-aware dedupe or full recipient/amount/currency business checks shown. It logs, does not update orders. Backend owns durable receipt/verification mechanism. |
| Callback/return | success.php is a thank-you page; cancel.php is separate | Browser return cannot establish payment outcome. Required handler/state correspondence remains unqualified. |
| Auth/config | src/config.php uses NVP env names, sandbox endpoints, USD and demo fallbacks | No real credentials observed. Reject treating demo fallback or page startup as configured seller/buyer. New probe uses the same NVP variable names/version. |
| Browser driver | buyer.spec.ts contains a credential-gated sandbox payment inside a normal test file | Do not run or copy into default offline tests. Separate future live buyer entry point and qualified popup selectors are required. |
| REST/webhooks | Not implemented by the unchanged NVP sample | NEW candidate evidence and actual app/listener coverage cannot come from the baseline. Simulator evidence is separate. |

Relevant gates: AC13/14/15/34/40/41/42 and LC01/03/04/17/18/19/20/22/30/34/37 from the reviewed engineering baseline. This table is source inspection, not provider observations or proof verdicts. VJ03/04/05 state/finalisation/exit mechanisms remain future work with their owners.
