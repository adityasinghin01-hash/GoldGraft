# Phase 1 reference review and sandbox preparation

This directory contains the **local review tool and scenario worksheet**, not a shared ShopPack/WorkPackage or qualified runtime. The parent piece now includes fifteen unchanged upstream application files under `vendor/src` and a separate offline PHP lab wrapper. The complete 22-file source-review snapshot remains ignored. Read [current baseline](../../../../docs/vijay/CURRENT_BASELINE.md) before continuing.

From the repository root:

```powershell
python -m unittest discover -s tests -v
python pieces/shops/legacy-php-shop/phase1/readiness.py --source-root .context/review-2026-11-07/reference
python scripts/live_sandbox_probe.py --probe oauth
```

The source root above is an ignored local snapshot, not distributed with the repository. In another checkout, supply the pinned team's `fixtures/shops/legacy-php-shop` directory. The inventory checks all 22 source/build/reference files by Git blob SHA-1, holding on missing/changed/unexpected files or links. It never executes PHP, Docker, install hooks or the buyer. A SOURCE_MATCH is only static consistency; the phase remains HOLD. Git blob SHA-1 here matches Git object identity and is not a signed attestation or substitute for future artifact SHA-256 evidence.

`scenarios.json` describes fourteen required initial payment flows, their expected semantics and AC/LC trace links. All remain UNVERIFIED. These are local worksheets, deliberately not claimed to validate against Scenario/1 or new proposed lifecycle schemas. Their statuses do not become passing results when unit tests pass.

## Sandbox probes

`scripts/live_sandbox_probe.py` defaults to no network and returns BLOCKED (exit 2). It supports only OAuth client-credential exchange and NVP GetBalance. It does not create, capture, refund, void, subscribe or alter merchant configuration. Actual calls additionally require all of:

- Explicit `--live` on the operator's invocation.
- `PAYPAL_ENVIRONMENT=sandbox` and credentials supplied privately through the process environment or explicit `--config .secrets/sandbox.json`. See [private setup](../../../../docs/vijay/SANDBOX_SETUP.md). Scripts do not load `.env` or the local JSON automatically.
- `--authority-ref` naming a separately established local operator approval. This is audit context, not validation of a shared service ActionIntent, Start or account ownership.

After those prerequisites are actually established, an operator can run `python scripts/live_sandbox_probe.py --probe oauth --live --authority-ref <local-approval-reference>`, or select `nvp-balance`. Do not paste credentials in the shell command, chat, evidence or Git. Do not run these inside a merchant product worker in place of the future qualified broker.

Only fixed sandbox HTTPS endpoints are permitted; redirects, ambient proxies and automatic retries are disabled. Reports omit credentials, tokens, balances and provider error bodies. OAuth PASS or balance PASS is **credential-probe-only**, never a passing checkout/refund/callback scenario. Blocked/unverified exits are 2; auth rejection is 1; credential-probe success is 0. Default offline tests inject synthetic transport responses and have no network.

Docker repair stays deferred by user instruction; the [portable PHP/Playwright lab](../../../../docs/vijay/PORTABLE_RUNTIME.md) runs local component checks. See [runtime/source observations](RUNTIME_REVIEW.md) and [Phase 1 status](../../../../docs/vijay/PHASE1_STATUS.md). Neither component success nor credential probes qualify real payments.
