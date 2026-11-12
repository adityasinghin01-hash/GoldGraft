# GoldGraft web

The landing page and the 13 app screens (S0–S12) for GoldGraft. React 18 + TypeScript + Vite.

## Run

```bash
npm install
npm run dev                      # http://127.0.0.1:8780 — sample mode (labelled sample data)
```

To read the checked-in real run recordings, start the recorded-run API from the
repository root, then start the frontend in a second terminal:

```bash
# terminal 1, repo root
uv run python -m integration.agents_app --runs-dir deploy/runs --port 8700
# terminal 2, pieces/web
VITE_API_BASE=http://127.0.0.1:8700 npm run dev
```

This serves existing evidence; it does not execute a fresh agent run. The public
recorded-run API is at `https://goldgraft-api.onrender.com`.

For the separate synthetic stand-in API:

```bash
# terminal 1, repo root with its venv
python -m goldgraft_fakes.api --port 8700
# terminal 2
VITE_API_BASE=http://127.0.0.1:8700 VITE_SSE_SPEED=2 VITE_DEMO_TOOLS=true npm run dev
```

| Variable | Meaning |
|---|---|
| `VITE_API_BASE` | API base URL. Empty = sample mode with the mock banner |
| `VITE_SSE_SPEED` | stand-in only: live events per second |
| `VITE_DEMO_TOOLS` | shows S7 **Inject** and S6 **Tampered copy** (always on in sample mode) |

## Where things are

| Path | What |
|---|---|
| `src/world/` | The living background: silk light shader + gold dust that becomes each chapter's photo as you scroll (three.js, lazy-loaded). `landingStates.ts` lists every picture and where it sits |
| `src/landing/` | Landing chapters (hero → proof → problem → graft → features → steps → FAQ → final) and the gold vine |
| `src/screens/` | S0–S12 app screens, one file each |
| `src/components/` | Shared parts (pack C1–C28), loaders, bar charts |
| `src/api/` | Live client, sample mode (`mock/`), live feeds |
| `src/copy/` | Every word: `landing.ts`, `words.ts` (pack 05), `evidence.ts` (measured agent results) |
| `public/world/` | Chapter photos (AI-generated for GoldGraft) |
| `tools/shoot.mjs` | Screenshot + console harness: `node tools/shoot.mjs <url> --widths 1280,1440,1920 --at 0,1.4 --gpu [--reduced] [--nogl]` |
| `tools/images.sh` | Converts new photos into `public/world` |

## Fonts and licences

Zodiak (ITF Free Font License, self-hosted, `src/assets/fonts/FFL.txt`), Geist and Geist Mono (OFL), Phosphor icons (MIT).
