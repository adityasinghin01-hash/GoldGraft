# Local switch libraries

PHP, Node and Python implementations of the **unchanged current** SwitchConfig/1/reference routing boundary, grounded at team commit `da2b5f02d5559c510de6b3b9d81e58400bdf6c89`. Shared signatures are real Ed25519 verification over sorted compact UTF-8 JSON excluding `signature`. Buckets use the first 8 SHA-256 hex digits of `graft_id:order_ref`, modulo 100. Allowed stages are 0/1/10/50/100.

For new payments missing/invalid/expired/wrong-graft config falls to OLD. Existing-reference `decide` preserves OLD/NEW origin for follow-ups. **Integration must call route_existing/routeExisting with a trusted stored origin**; the compatibility reference's unknown-origin OLD default is not permission to guess a financial route. Unknown origin raises a local hold in that stricter helper.

`VerifiedConfigCache` is a caller-owned in-memory implementation proposal: only authenticated valid configs are admitted; older versions and same-version changed payloads are rejected, expiry is never extended, returned values are defensive copies. A fetch outage may reuse only a still-valid verified snapshot. No HTTP, guard-event delivery, cache TTL, durable origin/session store or backend authentication convention is invented. These require actual integration. Empty/restarted cache fails safely for new payments; known original obligations remain independent of percentage.

## Actual test execution

Use the isolated D: Python 3.12 environment, portable PHP with bundled Sodium and Node 22:

```cmd
D:\DevTools\GoldGraft\switch-venv\Scripts\python.exe scripts\check_switches.py --node "D:\DevTools\GoldGraft\node-v22.23.4-win-x64\node.exe" --php "D:\DevTools\GoldGraft\php-8.3.36-1\php.exe"
```

Python dependency versions are in `python/requirements.txt`. No global packages/PATH are changed. `plug.json` declarations support the published team plugtest layout once these pieces are copied into the actual integration checkout. PHP requires Sodium enabled; missing crypto causes invalid config, never unconditional NEW. There is no deployed switch or completed rollout claim.

The shared 207 vectors use their **frozen test clock** from 5 November. They are synthetic, contain a public test verification key, and have no operational signing authority. Never substitute that clock/key for real integration. Additional local negative/cache tests use generated ephemeral private keys that are never persisted. No provider, credential, production action, score or money proof is involved.

Ruby is deferred in the current local profile: no interpreter is installed, and current first-reference requirements do not mandate executing it. Java/.NET remain map-only. Report exactly three tested libraries, not broad language coverage.
