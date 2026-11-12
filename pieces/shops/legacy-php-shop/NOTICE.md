# Licensed PHP reference and local lab wrapper

Vendored source: [Cutover legacy PHP shop](https://github.com/jeretc/cutover/tree/aedc11dde1a8793285665ca2188aff62ab5aab65/samples/legacy-php-shop), frozen upstream commit `aedc11dde1a8793285665ca2188aff62ab5aab65`. License: MIT, retained in `vendor/LICENSE.cutover` (copyright 2026 jeretc).

Retrieved via the team repository at `da2b5f02d5559c510de6b3b9d81e58400bdf6c89`, reference root `fixtures/shops/legacy-php-shop`. The fifteen files under `vendor/src` are unchanged retrieved application bytes; `vendor/source.json` records Git blob and SHA-256 hashes. Upstream and team revisions are provenance, not this local build's commit or a deployed image identity.

The Dockerfile, Compose configuration and `lab/` are newly authored GoldGraft local-lab packaging. They use a digest-pinned PHP base, a separate authenticated allowlist router, non-root/read-only runtime and an isolated synthetic-state volume. They deliberately disable all payment/callback execution. The PHP built-in server is a local test harness, not production hosting or the team's qualified runner/gateway. This wrapper does not fix or conceal the baseline's money/state defects.

No source from Diffy, Juspay Decision Engine or the unlicensed PayPal AG Grid boilerplate is included. No credentials, real payment records or private merchant code are vendored.

The separately authored `candidate/` implements local shop-domain behaviour and an offline scripted test harness. It consumes the licensed catalogue by value and the existing `domain/` helper, leaving all vendored bytes unchanged. It is not a deployed merchant checkout, production payment integration or qualified callback/runner implementation.
