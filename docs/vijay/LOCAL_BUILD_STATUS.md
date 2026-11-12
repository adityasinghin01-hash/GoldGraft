> **Current runtime — 8 November 2026:** Portable PHP on D: and existing Playwright now pass actual local shop/HTTP/restart/browser checks without Docker. Drive/team baseline rechecked with no newer changes in inspected active sources. See [portable runtime and evidence](PORTABLE_RUNTIME.md). Docker/Linux and genuine payment qualification remain pending; older Docker-blocked statements below are historical.

# Local PHP build preparation — 7 November 2026

The user reports Docker installed and authorizes starting the build. Earlier deferral is lifted for local work. All changes remain local: no commit/push/PR/upload, remote deployment, account/grant change or PayPal payment.

## Implemented

- Fifteen verified, unmodified Cutover application files plus MIT license and source hashes under the reference piece.
- Official PHP base pinned to a real linux/amd64 registry manifest; no invented image/build identity.
- Compose recipe with loopback publishing, non-root/read-only filesystem, separate synthetic state, runtime lab-key secret and internal network.
- Authenticated allowlist lab router; direct config/data/lib access and all payment/callback mutations denied.
- Local `reference_lab.py` commands for config/build/health/access/persistence/restart/stop; failure holds before build when engine is unavailable.
- Five additional offline checks: vendored-byte/license preservation, key reuse/invalid-key hold, engine-failure no-build behavior, access-bypass detection and redirect denial.

## Observed checks

| Check | Result | Evidence limit |
| --- | --- | --- |
| Docker CLI | 29.9.2 installed under user's Programs/DockerDesktop/resources/bin | Not initially in this shell's PATH; wrapper resolves it |
| Docker Compose | v5.6.1 available | Parser/config support only |
| Compose configuration | PASS via installed Compose | No container started; no runtime/security/payment qualification |
| Offline tests | 18 pass | Includes prior 13 Phase 1 checks; no real providers |
| Official base lookup | linux/amd64 manifest resolved for php:8.3-apache | Registry read only; base image not built/run locally |
| Docker Linux engine | HTTP 500 on API 1.56 and 1.47; Desktop status reported stopped; start command says app already running | Desktop application availability is distinct from engine readiness |
| WSL | --status exit 50; --list --verbose yields installation-help output | Not a usable WSL runtime in this process |
| Windows | HypervisorPresent False; system RebootPending registry marker True | Exact post-restart readiness not yet established |

The wrapper's actual `up` result is retained locally in `.context/reference-lab/last-result.json`. No successful image build, PHP syntax/curl execution, container health, authenticated HTTP or restart result is claimed until that command and the actual checks succeed.

## Next dependency

Save work and restart Windows, then open Docker Desktop and wait for its Linux engine to report running. Do not reset Docker, unregister WSL or delete images/volumes as a workaround. After the restart, recheck `python scripts/reference_lab.py up` and `check`. If WSL/virtualization still fails, complete the supported Windows/WSL prerequisites before claiming runtime readiness. No automatic Windows restart was performed.

Actual sandbox accounts/broker/recorder/required payment scenarios and SI01 new shared contracts remain independent dependencies. This local lab has payments disabled intentionally; unblocking Docker does not automatically authorize sandbox transactions.

Methods: [Docker Compose service configuration](https://docs.docker.com/reference/compose-file/services/) and [official PHP image/extension guidance](https://hub.docker.com/_/php), checked during implementation. This is a local reference recipe, not a replacement for the backend's qualified runner/isolation.
