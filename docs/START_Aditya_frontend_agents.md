# START HERE — Aditya · Frontend + agent system (and final integration)

## Your job in one line
Build the **12 screens** and the **13 AI agents**, and on 7–8 Nov plug all four pieces together.

## What you own
| Part | Design |
|---|---|
| 12 screens S0–S11 (Probe, Connect, Graft Board, Root Map, Union view, Proof Strength, Certificate, Heal, Scion Bank, Orchard, Security, Four-arm comparison) | [07_FRONTEND_API.md](design/07_FRONTEND_API.md) |
| 13 agents (Gardener, Surveyor, Builder, Explorer, Scribe, Architect, Grafter, Adversary, Healer, Librarian, Herald, Orchard Analyst, Sentinel) | [06_AGENTS_SERVICES.md](design/06_AGENTS_SERVICES.md), `contracts/.../tools.py` |
| Step tracker + ledger (already built in `foundation/`), Budget Governor | [00_SYSTEM.md §2](design/00_SYSTEM.md) |
| Data-format owner: every change goes through you → `docs/FORMAT_CHANGES.md` | `AGENTS.md` rule 2 |

## Folders
`pieces/web/` (screens) and `pieces/agents/` (agents). Import only from `contracts/` and `foundation/`.

## What you build against
| Stand-in | Use |
|---|---|
| Fake API `uv run python -m goldgraft_fakes.api --port 8700` | every screen's data, incl. the live ledger feed (`/grafts/demo-1/events`) and go-live feed (`/heal/demo-1`) |
| TypeScript types | `contracts/ts/goldgraft-api.d.ts` (API) and `contracts/ts/goldgraft-contracts.d.ts` (formats) |
| Agent tools | `contracts/.../tools.py` (which agent may call what) + stand-in tools (`goldgraft_fakes.tools`, coming) |

## Plug-in tests
```bash
GOLDGRAFT_AGENTS=pieces.agents.registry:AGENTS uv run pytest plugtests/test_agents.py
```
Screens: the plan for the frontend (step 2) adds a browser smoke test against the stand-in API.
