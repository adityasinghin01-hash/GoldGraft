# Rules for coding agents working in this repo (Codex, Antigravity, Claude)

GoldGraft upgrades a shop's old PayPal checkout to PayPal's newest one and proves the money still behaves the same.
The full design is in `docs/design/` (00–09). The data formats are in `docs/design/01_DATA.md`. They are the law.

## Team pieces (each one is built alone, against stand-ins)
| Folder | Owner | What |
|---|---|---|
| `pieces/web`, `pieces/agents` | Aditya | 12 screens; 13 agents |
| `pieces/backend`, `pieces/runner` | backend teammate | real API, database, GitHub Actions runner, locked box, traffic capture, tunnel |
| `pieces/proof` | ML teammate | money language mapping, Union Judge, 12 bug types + proof strength, go-live maths, recipe confidence, certificate |
| `pieces/shops`, `pieces/switch-libs` | all-rounder teammate | 11 test shops, PayPal sandbox tests, switch libraries, simulated buyers |
Shared (the "plug pack"): `contracts/`, `fixtures/`, `foundation/`, `fakes/`, `plugtests/`, `scripts/`, `docs/`.

## Hard rules
1. A piece imports ONLY `contracts/` (and `foundation/` for the ledger + step tracker). Never another piece's code.
2. Formats change only through `docs/FORMAT_CHANGES.md` (owner: Aditya). Bump the schema version (`RootMap/1` → `RootMap/2`), regenerate schemas + TS types, update fixtures + fakes in the same change.
3. Money is always integer minor units + ISO 4217 currency code. Never floats.
4. Tests never call the network (PayPal, GitHub, LLMs). Use fixtures and fakes. Live checks live in separate scripts marked `live_`.
5. Never write secrets, keys or tokens into code, fixtures, logs or docs. Use `.env.example` with empty values.
6. Licences: our code is MIT. Do NOT copy code from Diffy (CC BY-NC-ND) or Juspay Decision Engine (AGPL) — ideas only. Do NOT copy code from the PayPal AG Grid boilerplate (no licence file). Cutover's `samples/legacy-php-shop` (MIT) may be vendored with its licence notice.
7. PayPal response shapes in fixtures must follow PayPal's public docs; put the doc URL in a comment or a `_source` field.
8. Do not run `git commit` or `git push`. The driver (Claude) runs the full checks and commits.
9. Python 3.12, managed by `uv`; lint with `ruff`; test with `pytest`. Node 22 for TypeScript tooling.
10. When something in the design is ambiguous, choose the simplest reading, write it down in your final report under "Decisions", and keep going.
