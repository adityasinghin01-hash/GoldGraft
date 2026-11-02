# GoldGraft — "Don't cut the tree. Graft."

GoldGraft is an AI system that upgrades a shop's **old PayPal checkout** (old Buy Now buttons, old Express Checkout code, old payment notifications) to **PayPal's newest checkout**, end to end. It proves in PayPal's test sandbox that every kind of payment still behaves the same, then moves buyers over a few at a time and switches them back automatically if a payment looks wrong.

Built for the PayPal AI Hackathon 2026 (deadline 13 Nov 2026, 01:30 IST). Licence: MIT.

---

## How the team works: four pieces, built alone, plugged in at the end

Nobody waits for anybody. Each person builds their piece against **stand-ins** (fake versions of the other three pieces) that already exist in this repo. Every piece has a **plug-in test**. When your plug-in test passes against the stand-ins, your piece will plug into the real system. Aditya plugs everything together on 7–8 Nov.

| Person | Piece | Folder | Start here |
|---|---|---|---|
| Aditya | Screens (frontend) + the 13 AI agents | `pieces/web`, `pieces/agents` | [docs/START_Aditya_frontend_agents.md](docs/START_Aditya_frontend_agents.md) |
| Aditya Gupta | Backend + Runner (server API, database, the machines that run shops) | `pieces/backend`, `pieces/runner` | [docs/START_Aditya_Gupta_backend.md](docs/START_Aditya_Gupta_backend.md) |
| Aditya Singhal | Proof + maths (money comparison, bug score, go-live maths, certificate) | `pieces/proof` | [docs/START_Aditya_Singhal_proof.md](docs/START_Aditya_Singhal_proof.md) |
| Aditya Vijay | PayPal + test shops (sandbox, 11 shops, switch libraries, demo) | `pieces/shops`, `pieces/switch-libs` | [docs/START_Aditya_Vijay_paypal_shops.md](docs/START_Aditya_Vijay_paypal_shops.md) |

## What is already here (the "plug pack")

| Folder | What it is |
|---|---|
| `contracts/` | The exact shape of every piece of data that passes between pieces (Python models → JSON Schema + TypeScript types), the API contract (`contracts/api/openapi.json`), the plug-in interfaces (`interfaces.py`) and the agent tool list (`tools.py`). |
| `foundation/` | The shared ledger (an append-only log where every step is recorded and any edit is detectable) and the step tracker (moves a shop through the upgrade stages). |
| `fakes/` | Stand-ins: a fake API server, a fake PayPal sandbox (works offline), and (coming) a fake runner, fake proof and fake agent tools. |
| `fixtures/` | Sample data with answer keys, built on one real old shop (Cutover's MIT `legacy-php-shop`). See `fixtures/INDEX.md`. Every file says whether it is REAL or SYNTHETIC. |
| `plugtests/` | (coming) One plug-in test set per piece. |
| `docs/design/` | The full design (00 system … 09 demo). `01_DATA.md` is the law for data formats. |
| `docs/FORMAT_CHANGES.md` | Every change to a data format, with the reason. |
| `AGENTS.md` | Rules for AI coding tools (Codex, Antigravity, Claude) working in this repo. Humans: read it too — it's short. |

The idea, research and evidence pack (problem, rivals, every number with its source) is on the team Google Drive in **"PayPal AI Hackathon - Team Pack / 00 GoldGraft - FINAL IDEA (1 Nov)"**: https://drive.google.com/drive/folders/10NZ56zh6UlveQTsi7rIrUA9K4GY8uv7a

## Set up (once)

You need: Python 3.12 via [uv](https://docs.astral.sh/uv/), Node 22, git.

```bash
git clone https://github.com/adityasinghin01-hash/GoldGraft.git
cd GoldGraft
uv sync          # installs Python packages into .venv
npm ci           # installs the TypeScript tools
uv run pytest -q # everything should pass
```

Run the stand-in API (the 12 screens can talk to this today):

```bash
uv run python -m goldgraft_fakes.api --port 8700
# open http://127.0.0.1:8700/docs for every endpoint, with examples
```

## Rules everyone follows

1. **Only import `contracts/` (and `foundation/`)**. Never import another person's piece. That is what keeps the pieces independent.
2. **Data formats change only through Aditya.** If you need a new field, ask; the change goes into `docs/FORMAT_CHANGES.md` with a new version (`RootMap/1` → `RootMap/2`), and the stand-ins and sample data are updated the same day.
3. **Money is always a whole number of the smallest unit + a currency code** (19.99 USD = `{"minor": 1999, "currency": "USD"}`). Never decimals.
4. **No secrets in the repo** — no keys, passwords or tokens in code, sample data, logs or docs. Use a local `.env` file (it is ignored by git).
5. **Tests never call the internet.** Anything that talks to the real PayPal sandbox goes in a script whose name starts with `live_`.
6. **Push small and often** to your own branch (`<your-name>/<topic>`), open a pull request into `main`; CI must be green before it is merged.

## Dates

| Date | What |
|---|---|
| 2–3 Nov | Plug pack (this repo) finished |
| 3–6 Nov | Everyone builds their piece alone, against the stand-ins |
| 6 Nov night | Every piece's plug-in test is green |
| 7–8 Nov | Aditya plugs everything together and runs it end to end on Zen Cart |
| 8 Nov | Feature freeze |
| 9–12 Nov | Polish, demo video (recorded twice), submit by 12 Nov 23:30 IST |
