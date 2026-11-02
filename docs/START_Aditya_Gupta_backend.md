# START HERE — Aditya Gupta · Backend + Runner

## Your job in one line
Build the real **server** (the API every screen and shop talks to, plus its database) and the **runner** (the machines that start a shop's code in a locked box, buy things in the PayPal test sandbox, and record every payment message).

## GoldGraft in two lines
Old online shops use old PayPal code that PayPal is retiring. GoldGraft's AI agents rewrite that code to PayPal's newest version, **prove** every kind of payment still works by running old and new shops side by side in PayPal's sandbox, then switch real buyers over safely. Full picture: [README](../README.md) and [docs/design/00_SYSTEM.md](design/00_SYSTEM.md).

## What you own (read these parts of the design)
| Part | What it does | Read |
|---|---|---|
| Server API | the 24 endpoints the screens, shop libraries and webhooks call | [07_FRONTEND_API.md](design/07_FRONTEND_API.md), `contracts/api/openapi.json` |
| Database + ledger storage | Postgres on Render; the ledger code already exists in `foundation/` — you host it | [00_SYSTEM.md §2, §4](design/00_SYSTEM.md), `foundation/src/goldgraft_foundation/ledger.py` |
| Runner | GitHub Actions jobs that run a shop: fresh machine per job, locked box (gVisor), only PayPal sandbox + tunnel allowed out | [05_HEAL_HANDOFF_FLEET.md](design/05_HEAL_HANDOFF_FLEET.md) (Cage section), [00_SYSTEM.md §1, §3](design/00_SYSTEM.md) |
| Traffic recorder (Capture) | records every message between shop and PayPal into `RawCapture/1` files; **speed limit 45 requests/min per machine** (PayPal blocks an IP for 5 minutes above 50/min) | [04_UNION_PROOF.md](design/04_UNION_PROOF.md), `contracts/.../runner.py` |
| Tunnel | lets PayPal reach the shop's return and notification URLs (cloudflared) | 09 test 13 |
| KERNEL browsers | real browser for the PayPal popup + live view in the demo ($50 credit) | 09 test 14 |
| Key Guard | sandbox keys go straight to a vault (Doppler); only a `doppler://...` reference is ever stored or shown | [02_GATE_ROOTSTOCK.md](design/02_GATE_ROOTSTOCK.md) |
| Hosting | must stay up until 15 Dec (judging) | Render $50 credit |

## Your folders
Put all your code in `pieces/backend/` and `pieces/runner/`. Never import code from another person's folder — only from `contracts/` and `foundation/`.

## What you build against (stand-ins that already work)
| Stand-in | Run / use | Replaces |
|---|---|---|
| Fake API | `uv run python -m goldgraft_fakes.api --port 8700` → http://127.0.0.1:8700/docs | shows exactly what your real API must answer |
| Fake PayPal sandbox | `goldgraft_fakes.paypal.FakePayPal` (offline: Express Checkout, IPN, Orders v2, refunds, webhooks, the 50/min block) | lets you build the runner + recorder without burning real sandbox calls |
| Example shop | `fixtures/shops/legacy-php-shop/` (real old PHP shop, `docker compose up`) | your first shop to run |
| Sample recordings | `fixtures/proof/legacy-php-shop/raw/` | what your recorder's output must look like |

## Data you produce / consume
- **Produce:** `JobResult/1`, `RawCapture/1` (runner); every API response in `contracts/api/openapi.json`.
- **Consume:** `JobSpec/1` (what to run), `ShopPack/1` (how to start a shop), `GuardEvent/1` (from shop libraries).
- Shapes: `contracts/schemas/*.json` (or the Python models in `contracts/src/goldgraft_contracts/`).

## How the API must behave (non-negotiable)
- Register routes **from** `goldgraft_contracts.api_routes.ROUTES` so you can't drift from the contract.
- Every write needs an `Idempotency-Key` header: same key + same body → same answer; same key + different body → 409.
- Errors are `application/problem+json` (RFC 7807).
- Secrets from `POST /shops/{id}/connect` never appear in any response, log or database row.
- Webhooks: check the signature headers and ignore repeats of the same delivery id.

## Your plug-in test (your "done")
```bash
GOLDGRAFT_API_APP=pieces.backend.app:app uv run pytest plugtests/test_backend_api.py
GOLDGRAFT_RUNNER=pieces.runner.runner:Runner uv run pytest plugtests/test_runner.py
```
Without the variables these tests run against the stand-ins (they pass today). Point them at your code; when they pass, your piece plugs in.

## Dates
3–6 Nov build · **6 Nov night: plug-in tests green** · 7–8 Nov Aditya plugs in · 8 Nov freeze.

## Ask Aditya when
you need a new field or endpoint (formats change only through him), or anything in the design is unclear.
