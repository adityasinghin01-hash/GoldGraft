# Cutover legacy PHP shop

Source: https://github.com/jeretc/cutover/tree/aedc11dde1a8793285665ca2188aff62ab5aab65/samples/legacy-php-shop

Commit: `aedc11dde1a8793285665ca2188aff62ab5aab65`. Licence: MIT (see LICENSE.cutover).

Vendored as a test shop; not modified. All 15 upstream sample files are byte-for-byte copies.
This is REAL source code, not a payment recording. Upstream's DEMOPASSWORD and
DEMOSIGNATURE are demonstration placeholders, not credentials.

The proof traces are SYNTHETIC examples of the GoldGraft specification.
They are not executions of this shop. In particular execute-payment.php:23
unconditionally marks successful NVP responses PAID, refund.php:9–12 guards
and checks refunds, and ipn.php:16 appends a log without updating orders.
The requested synthetic OLD pending behavior and second-refund bug must not
be attributed to this code. The float arithmetic in the vendor is preserved.
