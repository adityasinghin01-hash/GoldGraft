# START HERE — Aditya Vijay · PayPal + test shops

## Your job in one line
Own everything that touches **real PayPal and real shops**: set up the PayPal test sandbox and run its 16 checks, prepare the 11 test shops, build the small "switch" libraries that let a shop send each buyer to the old or new checkout, and record the demo.

## GoldGraft in two lines
Old online shops use old PayPal code that PayPal is retiring. GoldGraft's AI agents rewrite it to PayPal's newest version, prove it in the sandbox, then move buyers over gradually with automatic switch-back. Full picture: [README](../README.md), [docs/design/00_SYSTEM.md](design/00_SYSTEM.md).

## What you own
| Part | In plain words | Design |
|---|---|---|
| PayPal sandbox setup + 16 checks | create sandbox accounts/apps; test the behaviours our design depends on (old NVP checkout, IPN, refunds of old payments with the new API, 50-requests/minute limit, tunnel from GitHub, KERNEL popup …) and write down what really happens | [09 "Step 6 sandbox tests"](design/09_DEMO_TESTS_GAPS.md) |
| 11 test shops | each in its own folder with a `goldgraft-shop.yaml` (how to start it, a buyer script, and the list of every old PayPal spot in its code — the "answer key") | [09 "Test shops"](design/09_DEMO_TESTS_GAPS.md) |
| Real recordings | record real sandbox runs of the example shop; they replace the hand-made sample data | `fixtures/INDEX.md` |
| Switch libraries | tiny libraries (PHP first, then Node, Python) placed in a shop: read a signed `SwitchConfig/1` (what % of buyers go to the new checkout), send each buyer to OLD or NEW, report each payment as a `GuardEvent/1`; if the config is missing, invalid or expired → **old path** | [05 H1–H3](design/05_HEAL_HANDOFF_FLEET.md), [01_DATA.md §7](design/01_DATA.md) |
| Go-live, switch-back, shadow tests (running them) | simulated buyers moving 1 → 10 → 50 → 100%; inject a fault and show the automatic switch-back | [05](design/05_HEAL_HANDOFF_FLEET.md) |
| No-code lane, Zen Cart path | old "Buy Now" button sites → PayPal Payment Links; Zen Cart → its official new PayPal module | [03_SCION.md](design/03_SCION.md), [08_ZENCART_TRACE.md](design/08_ZENCART_TRACE.md) |
| Timed manual upgrade | upgrade one shop by hand, timed — the "human" arm of our comparison | [09](design/09_DEMO_TESTS_GAPS.md) |
| Security demo shop + demo recording | shop with planted malicious comments; record the 3-minute video (twice) | [09 demo table](design/09_DEMO_TESTS_GAPS.md) |

## Your folders
`pieces/shops/` (one folder per shop) and `pieces/switch-libs/` (one folder per language). Import only from `contracts/`.

## What you build against
| Thing | Where |
|---|---|
| Example shop already wrapped | `fixtures/shops/legacy-php-shop/` — copy its layout (`goldgraft-shop.yaml`, `docker-compose.yml`, `buyer.spec.ts`, `NOTICE.md` with source + licence) |
| Fake PayPal sandbox (offline) | `goldgraft_fakes.paypal.FakePayPal` — practise flows without using real sandbox calls |
| Fake API (for switch libraries) | `uv run python -m goldgraft_fakes.api --port 8700` → `GET /switch/config/demo-1`, `POST /guard/event` |
| Formats | `ShopPack/1`, `SwitchConfig/1`, `GuardEvent/1`, `RawCapture/1` in `contracts/schemas/` |

## Rules special to you
- **Sandbox keys and buyer passwords never go in the repo.** Keep them in a local `.env`; scripts that use them are named `live_*`.
- Every shop you add: record its source URL, commit and **licence** in `NOTICE.md`. No code without a licence that allows it.
- Freeze each test shop (commit hash in its `NOTICE.md`) **before** anyone tunes GoldGraft on it.
- Write down every sandbox result honestly, including failures — the design changes based on them.

## Your plug-in test (your "done")
```bash
uv run pytest plugtests/test_shops.py         # every shop folder is valid and complete
uv run pytest plugtests/test_switch_libs.py   # every switch library passes the shared cases
```

## Dates
3–6 Nov build · **sandbox checks that the design depends on: as early as possible** · 6 Nov night: plug-in tests green · 7–8 Nov Aditya plugs in · 8 Nov freeze · 9–12 Nov video.

## Ask Aditya when
a sandbox check gives a surprising result (tell him the same day), or you need a format change.
