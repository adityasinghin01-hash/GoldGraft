# PHP reference: local offline lab

**12 November:** a separate [NEW PHP candidate](candidate/README.md) now implements local order/payment-domain state and an explicitly scripted browser harness. Run `scripts\check-candidate.cmd` from CMD. It does not modify this frozen baseline or qualify a real payment. [Current phase report](../../../docs/vijay/LOCAL_PHASE_DELIVERY.md).

**8 November update:** the [portable PHP + Playwright path](../../../docs/vijay/PORTABLE_RUNTIME.md) is now working on Windows without Docker. Run `python scripts/portable_lab.py` from the repository root for the self-contained local check. The Docker recipe below remains available for later Linux qualification; its earlier engine blocker does not prevent current local development.

This is Vijay's first runtime packaging slice under the reviewed VJ01 scope. The fifteen MIT application files are preserved unchanged under `vendor/src`; see [NOTICE.md](NOTICE.md). The wrapper in `lab/` protects access and disables all payment/callback execution. Baseline money/state defects remain visible for later characterization.

The base is official PHP 8.3 Apache, pinned to linux/amd64 manifest digest `sha256:8732e645530351f2f16aa7dd7619a44dad614bcfde6b4eb994f9a228d24f9b98`, resolved from the registry on 7 November 2026. No extra mutable package installs are performed. The image must verify PHP curl and every PHP file's syntax when Docker actually builds it. This recipe uses PHP's built-in server for the local lab; it is not the production host adapter.

## Run from repository root

```powershell
python scripts/reference_lab.py config
python scripts/reference_lab.py up
python scripts/reference_lab.py check
python scripts/reference_lab.py down
```

`config` validates Compose without requiring a running engine. `up` builds and waits for container health. `check` tests local HTTP access denial, private-route denial, disabled payment helpers, the shop HTML, PHP curl and a synthetic persistence marker across a restart. It never creates a payment. `down` stops only this Compose project and preserves its state volume; it does not delete provider transactions or unrelated Docker resources.

The script resolves Docker's Windows installation even if it is missing from PATH and makes its bundled credential helper available only to the child process. Build diagnostics and results remain ignored in `.context/reference-lab/`. On a failed engine check it returns HOLD (exit 2) before dispatching a build. PASS from `config` is configuration validation only. These checks are prepared; actual image/PHP/HTTP/restart checks have not run on this machine because Docker's engine is unavailable.

## Access and state

Only host loopback `127.0.0.1:8081` is published. Requests need the random runtime-mounted lab key in `X-GoldGraft-Lab-Key`; the key is generated once under ignored `.context/reference-lab/lab.key`, never printed or baked into the image. Only the non-secret `/__lab/health` response is unauthenticated. Browser navigation alone will return 401 until the lab header is supplied by an authorized local client. Do not put the key into URLs, source files or chat.

Source files are copied into a read-only image. Only `/opt/shop/src/data` has a named writable state volume; `/tmp` is disposable. The process is uid/gid 33, has no added capabilities and uses no-new-privileges. The Compose network is internal. These are declared local-lab controls; actual enforcement and the backend's required isolation are separately qualified, not established by YAML validation.

All POSTs are disabled even with a valid lab key. Only fixed pages, the authenticated orders read helper and fixed assets are served. There is no generic static-file fallback. No sandbox credential is passed into this offline image. Do not attach a public tunnel or use it for live payment/callback tests. The original page references PayPal checkout.js in the browser; local browser checks must block external requests, and page HTML alone is not checkout evidence.

The synthetic persistence marker is separate from orders/payment state. Restart success for it will not qualify full financial state migration, concurrent writers, callback persistence, backup restore or merchant-owned exit. The baseline/OLD_TWIN/NEW jobs will need independent run state and qualified broker/recorder interfaces later.

This lab is not yet a complete team ShopPack, qualified existing merchant migration, current WorkPackage contract, trusted callback gateway, proof result or Render deployment. See [current build status](../../../docs/vijay/LOCAL_BUILD_STATUS.md) and [Phase 1 tools](phase1/README.md).
