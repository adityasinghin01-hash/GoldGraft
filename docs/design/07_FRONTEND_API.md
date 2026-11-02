# P12 · 07 — Frontend screens + API (Aditya builds the frontend + agent system)
Look: GoldGraft's own identity (gold + living green, botanical "graft" motifs) — never PayPal's look or logo style; built later with skyward-atelier + astral-codex. Rule from his workflow: every number on screen has a plain "what this means" note.

## Screens
| # | Screen | Who | What is on it | Data (API) |
|---|---|---|---|---|
| S0 | **Probe** (landing) | anyone | "Don't cut the tree. Graft." + one box: repo or site URL → card: old PayPal pieces found, deadline notes, official modern module available?, "Start a graft" | `POST /probe` |
| S1 | **Connect** | merchant | 2 steps: GitHub App / site URL; sandbox keys form (straight to vault) → green checks with plain reasons | `POST /shops`, `POST /shops/{id}/connect` |
| S2 | **Graft Board** | merchant, judge | stage rail (Gate → … → Learn) with minutes + $ per stage; live feed of agent actions in plain words; Graft Card numbers | `GET /grafts/{id}`, `GET /grafts/{id}/events` (SSE) |
| S3 | **Root Map** | developer | AG Grid table: family · file:line / page / T-code · lens dots (code/runtime/site/account) · confidence · official target · PayPal-only; mini money-flow graph | `GET /grafts/{id}/rootmap` |
| S4 | **Union view** (hero) | everyone | three aligned timelines per scenario — OLD · NEW · PayPal ledger — noise greyed, deltas labelled, verdict badge; live KERNEL buyer browser panel; "bug found in your current shop" callouts | `GET /grafts/{id}/scenarios`, `/cmel?scenario=`, KERNEL live-view URL |
| S5 | **Proof Strength** | judge, developer | 12 mutant tiles (planted where → caught by which scenario); score gauge; rule ↔ scenario ↔ mutant triangle list | `GET /grafts/{id}/proof` |
| S6 | **Certificate** (public) | anyone | summary, PayPal evidence IDs, Verify button (signature · Rekor · ledger chain · PayPal re-fetch), tamper demo | `GET /certificates/{id}`, `POST /certificates/{id}/verify` |
| S7 | **Heal** | merchant, judge | stage stepper 0/1/10/50/100; live payments (old/new tag); guard status; posterior chart; demo "inject fault"; Cutback timer | `GET /heal/{id}` (SSE), `POST /heal/{id}/inject-fault` (demo only) |
| S8 | **Scion Bank** | PayPal team, judge | recipes (fingerprint, status, confidence, provenance); learning curve (minutes + $ per shop) | `GET /recipes`, `GET /learning-curve` |
| S9 | **Orchard** | PayPal team | AG Studio dashboard + Orchard Analyst chat ("which shops still take WPS money?") | `GET /orchard`, `POST /orchard/ask` |
| S10 | **Security** | judge | Injection Gauntlet replay: each attempt, where it came from, how it was blocked; Sentinel log | `GET /security/gauntlet/{run}` |
| S11 | **Four-arm comparison** | judge | teammate by hand · PayPal AI Toolkit · plain Claude Code · GoldGraft — minutes, $, pieces missed, money bugs left | `GET /comparison` |

## API (control plane)
| Method | Path | Does |
|---|---|---|
| POST | `/probe` | quick scan (no keys) |
| POST | `/shops` · `/shops/{id}/connect` | create shop · store keys in vault + run checks |
| POST | `/shops/{id}/graft` | start Graft Cycle (idempotency key required) |
| GET | `/grafts/{id}` · `/grafts/{id}/events` | state · live event stream (SSE) |
| GET | `/grafts/{id}/rootmap` · `/scenarios` · `/cmel` · `/proof` | artifacts |
| GET/POST | `/certificates/{id}` · `/certificates/{id}/verify` | public certificate · re-verify |
| GET/POST | `/heal/{id}` · `/heal/{id}/inject-fault` | go-live state · demo fault |
| GET | `/switch/config/{graft}` | signed SwitchConfig for shop libraries |
| POST | `/guard/event` | money events from Graft Switch libraries |
| POST | `/pp/webhook/{graft}` · `/gh/webhook` | PayPal + GitHub webhooks (signature-verified) |
| GET/POST | `/recipes` · `/orchard` · `/orchard/ask` · `/security/gauntlet/{run}` · `/comparison` | fleet + demo views |
Errors: RFC 7807 problem+json; every write is idempotent by key; webhooks verified + deduped.

## Agent-system build split (for P14)
Aditya: frontend (S0–S11) + agent system (A0–A12 harness, ledger events, stage machine). Others (to assign in P14): Cage + Capture + runners; Union Judge + MMO-12 + certificate; PayPal integration + test shops + Graft Switch libraries.
