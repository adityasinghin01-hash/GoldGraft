# Portable PHP + Playwright — 8 November 2026

Latest continuation: portable Node 22.23.4 was installed from the official checksum-verified Windows archive on D:. The actual offline lab passed under Python 3.12 with that Node version, run `20261108T125243238137Z`. Thirty offline unit tests pass. Credential probes reported by the operator passed separately; all fourteen required payment flows are still blocked by missing qualified counterparts. See [handoff](PHASE1_HANDOFF.md).

This is the user-approved alternative to local Docker/WSL. All changes are local. The original fifteen application files remain unchanged; Windows is a development/test path, not the qualified Linux runner or production host.

## Source refresh

The current Drive team guide was fetched again on 8 November. Its text remains the 6 November reviewed baseline. Root/final/craft/judging listings show no newer changes in the inspected active sources. The leader repository's main remains `da2b5f02d5559c510de6b3b9d81e58400bdf6c89`. Scope and VJ01–VJ05 ownership therefore remain as recorded in [CURRENT_BASELINE.md](CURRENT_BASELINE.md). No Drive or leader-repository file was changed.

## Runtime installed

Official Windows PHP 8.3.36-1 x64 NTS archive, selected to match the PHP 8.3 reference family. [Official release metadata](https://downloads.php.net/~windows/releases/releases.json) and [download guidance](https://www.php.net/downloads.php?os=windows&version=8.3) were checked before installation.

- Installation: `D:/DevTools/GoldGraft/php-8.3.36-1/`.
- Archive SHA-256: `1a097d52b7a68622cdc723073b61cc70caf79c941218ff65b2d8441dbc6b10d4`, matched before extracting/executing.
- Archive size: 34,179,998 bytes; extracted runtime: 91,825,874 bytes. Both are on D:; no system PATH or registry modification.
- PHP reports 8.3.36 with cURL and OpenSSL enabled. Existing Microsoft VC runtime was sufficient; no additional system installer was run.
- Machine-specific runtime metadata: ignored `.context/portable-php.json`.

The setup script is `scripts/setup_portable_php.py`; it downloads only the pinned official archive, checks its digest and archive paths/size, and writes under the named D: directory. It does not silently upgrade to another PHP family. A checksum mismatch or incomplete existing install needs investigation rather than execution or overwrite.

## Run the verified local check

From the repository root:

```powershell
python scripts/portable_lab.py
python -m unittest discover -s tests -v
```

To reproduce the team Node version without changing global PATH:

```cmd
python scripts/setup_portable_node.py
python scripts/portable_lab.py --node "D:\DevTools\GoldGraft\node-v22.23.4-win-x64\node.exe"
```

The Node ZIP is 35,604,229 bytes, stored on D:, SHA-256 `cbc74b5e0982c9dbb41525fd8fb5dcd32fbee237863f7829072f4639a1ce5f20` from the [official checksum list](https://nodejs.org/dist/v22.23.4/SHASUMS256.txt). The installer checks archive paths/size and installed bytes before execution. No registry/global PATH change or extra browser download was needed. Local npm tooling should use this Node installation; package engines now target 22.x.

For a new machine, first run `python scripts/setup_portable_php.py` after choosing/authorizing its D: installation location. These scripts use Python standard-library code and the already installed Playwright dependency/browser. Both Python 3.12 and Node 22 component checks pass; qualified protected runtime integration remains pending.

`portable_lab.py` checks the pinned vendor file set and Git blob identities, creates a fresh run directory under `D:/DevTools/GoldGraft/portable-lab/`, and copies unchanged source into it. Each run has separate synthetic data and a random local key. The server binds only 127.0.0.1 on an available port. It starts, checks and stops its own PHP child, restarts it against the same run state, then stops it on completion. It does not leave an always-running service or kill unrelated processes.

Only a harmless health response is unauthenticated. Other routes require the local lab header; config/lib/data paths are denied and every payment/callback POST stays disabled. Inherited PayPal credentials are removed from the child environment. PHP outbound URL access and network/process helper functions are disabled for the offline server. Browser CSP and Playwright routing block external page requests, including checkout.js. These are local component safeguards, not hostile-code isolation; do not run Gauntlet/Poisoner or private merchant code this way.

The router's source/key paths now come from trusted process configuration, with existing Docker defaults preserved. The vendored source was not edited to implement portability. Playwright checks authenticated page rendering, three product cards, cart total changing from $25.00 to $62.50 and denial in an independent unauthenticated browser context. The original PayPal script does not execute; checkout, popup and payment functionality are not claimed.

## Actual results

- All application/wrapper PHP files passed real PHP syntax checks.
- Local health, authentication and wrong-key checks passed.
- Direct/encoded private-path access was denied; payment/callback POSTs were denied.
- Synthetic persistence marker survived an actual PHP process stop/start. It is separate from order/financial state and does not prove financial migration or callback durability.
- Original and run-copy application hashes stayed unchanged.
- Playwright/Chromium 156.0.8078.4 passed the real local browser checks.
- Thirty offline unit/negative tests pass with Python 3.12, including altered/unlisted-source admission rejection, private configuration validation and preventing green preparation from becoming payment proof. They call no real providers.

Run reports, server logs and screenshots live on D: in the individual run folder. A safe result pointer/copy is in ignored `.context/portable-lab-result.json`. No key, credential or browser authentication state is tracked. No PayPal API call, payment, Docker execution, cloud provisioning, push or upload occurred.

Docker/Linux image qualification, actual sandbox identities/broker/recorder, required real payment flows, SI01 new shared contracts and full merchant handover/exit remain pending. Windows success does not close those gates. PHP's [built-in server](https://www.php.net/manual/en/features.commandline.webserver.php) is intended here only as a local test server.
