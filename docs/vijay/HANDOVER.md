# Vijay handover — local implementation ready for integration

The shop-owned local implementation is ready for teammate review and integration. **This is not a fully qualified live/merchant delivery.** Payment responses in the local checks are scripted, loopback simulations or injected HTTP responses; no genuine payment is claimed from them.

## Delivered and checked

- Persistent PHP candidate, exact USD/cart checks, duplicate-operation protection, restart continuity, pending/refund handling and original-rail reconciliation.
- Private PHP↔Python binding to the actual typed broker, plus callback business consumer using the actual gateway/inbox. No caller-supplied verification flag can mark an order paid.
- PHP/Node/Python signed-config switches; staged admission/Cutback/origin continuity; actual proof-decision consumer.
- Executable state, finalisation and exit **domain checks/recipes**. They do not perform merchant fencing, migration, deployment or exit.
- Accepted shop recipe and reproducible local connected-proof handoff against team commit `9968f9b17327f7e424e8d202c7402b1d90c6036b`.

Observed results: ten local check groups passed, including 108 PHP candidate checks and 768 switch checks; seventeen actual-counterpart tests passed. The recipe produced 27 fresh local recordings: nine shared scenarios × OLD/OLD_TWIN/NEW. The actual judge returned eight PASS and one PASS_FIXED. Two executed candidate mutations were caught. Connected proof reports **29 verified / 10 held**; promotion and certificate remain held.

One unique pinned PHP reference is packaged through two entry points. The socket compatibility candidate is an explicitly reviewed operator fixture; the durable SQLite candidate is separately tested through the actual broker binding. Neither is misrepresented as an AI-produced or merchant-qualified deployment.

## Exact handoff to teammates

| Owner | Integration next step |
| --- | --- |
| Singh | Load `pieces/shops/vijay-php-reference/recipe.py` through `integration.shop_socket.load_recipe`; use the existing Scenario/RawCapture/Contract/TargetPlan formats and preserve report qualification flags |
| Gupta + Vijay | Bind qualified custody/authority/recording/listener environments to the tested private payment and callback ports; qualify actual state bootstrap/apply/final runtime/independent merchant exit |
| Singhal + Vijay fixtures | Preserve the real judge results and add executed guards for R02 R04 R05 R06 R08 R11 R12 R17; complete exact-subject proof/signing coverage |

Fourteen role-wide scenarios remain in `pieces/shops/legacy-php-shop/phase1/scenarios.json`. Nine local socket cases do **not** mean all fourteen genuine scenarios passed. There is no public production gateway, live merchant application or qualified isolation claim. The host adapter executes only reviewed local fixture hashes; a different agent patch requires protected execution.

## Reproduce on this configured Windows machine

```cmd
cd /d "C:\Users\Aditya\Documents\ChatGPT\paypal"
scripts\finish-local.cmd
```

The command performs offline checks and builds a local ZIP. It never pushes or starts real payments/models. See [FINAL_LOCAL_STATUS.md](FINAL_LOCAL_STATUS.md) for every delivered file, result and remaining gate.

## Fresh Windows checkout prerequisites

These are setup commands, separate from ordinary offline tests. They download pinned dependencies but do not call payment/model services. Do not copy another person's `.secrets`, browser sessions or private recordings.

1. Install Python 3.12, `uv`, Git and the Node/npm tooling. Create the isolated local Python environment and install `scripts/local-profile-requirements.txt`. The supplied CMD wrappers use `D:\DevTools\GoldGraft\switch-venv\Scripts\python.exe`; adapt explicit paths for your machine if needed.
2. Run `python scripts/setup_portable_php.py` and `python scripts/setup_portable_node.py` to create verified portable runtime metadata. These installers target the documented D: directories; they do not change global PATH. Run `npm ci --ignore-scripts`, then `node scripts/playwright.mjs install chromium --no-shell` for the pinned local browser.
3. Obtain a separate local checkout of the team repository at exactly `9968f9b17327f7e424e8d202c7402b1d90c6036b`, normally `D:\DevTools\GoldGraft\team-9968f9b`. Install its locked third-party dependencies using `uv sync --locked --no-install-workspace --python 3.12` from that checkout. Our checker loads workspace packages directly from that source.
4. Run `python scripts/prepare_local_contracts.py --team-root "D:\DevTools\GoldGraft\team-9968f9b"`. This restores the five ignored unchanged contract snapshots from verified Git blobs and avoids CRLF drift. Nothing private is required.
5. Run `python scripts/phase2_baseline.py --node "D:\DevTools\GoldGraft\node-v22.23.4-win-x64\node.exe"` with Python 3.12 to create independent synthetic baseline state, then run `scripts\finish-local.cmd`.

The current portable supervisor is a Windows trusted-reference development profile. Linux/OCI/protected-runner qualification remains a separate team task. For another OS, use the actual team runtime and qualify its adapter; do not infer cross-platform support from these Windows results.

## Remaining qualification

Genuine fourteen-scenario shop sandbox evidence; qualified isolation/exact image; real callback/custody/authority; eight missing critical proof guards; merchant state transfer/apply/finalisation/independent exit; sponsor remote-account/tool qualification. These require the responsible team components and approved environments. No credential re-entry or general project explanation is needed to begin integration.

The user explicitly authorized publishing the complete local contribution to the personal repository. Credentials, caches, installed dependencies, auth state, raw recordings, databases and local logs stay excluded. The leader repository is unchanged by this publication.
