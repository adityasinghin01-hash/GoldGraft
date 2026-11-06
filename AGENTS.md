# Rules for coding agents working in GoldGraft

Read [docs/engineering/START_HERE.md](docs/engineering/START_HERE.md) and the relevant shared START guide before implementation. The reviewed target is a browser connector service with fixed saved-case journey, variable sources/hosts, genuinely read-only initial access, isolated work and separately authorised complete working-site delivery/recovery/exit. Render is first reference, not universal host support.

Current Python models under `contracts/src/goldgraft_contracts/` own actual wire support. New records/routes in reviewed engineering Markdown are **PROPOSED**, not existing APIs. Original `docs/design/` has historical bodies; use its supersession notices. Do not silently widen current formats, fill fake Git/workflow certificate fields, or create a second `pieces/connector` package from superseded sketches.

| Owner | Boundary |
|---|---|
| Singh | `pieces/web`, `pieces/agents`, approved shared-format bootstrap; future own Plan5 and integration Plan6. Agent internals deferred until explicitly started. |
| Gupta | `pieces/backend/connection`, `pieces/backend/lifecycle`, `pieces/runner` proposed mechanisms; inspect and preserve actual existing work. |
| Singhal | `pieces/proof`; reuse inspected proof PR1 and adapt verified evidence gaps. |
| Vijay | `pieces/shops`, `pieces/switch-libs`; first qualified runtime/payment/state/origin/finalisation/exit domain recipes. |

Shared `contracts/`, `foundation/`, `fixtures/`, `fakes/`, `plugtests/`, `scripts/`, `docs/` remain common boundaries. New shared shapes require Singh's bootstrap before dependent consumers; unchanged boundaries may proceed independently.

Paper Plans1/3/4 completion and Plan2 docs do not authorise product jobs, Plans5/6, installs, account/grant changes, private source/model transfers, live payments, publishing or deployment. Preserve dirty work/secrets/personal READMEs/Desktop reference. Initial Reader grant must stay read-only; publication/registry/host/data/financial authority is separate. Missing required permission, unknown effect or unsupported state-transfer/exit capability causes a hold, never a bypass or fabricated success.

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


## Reviewed qualification rules

- Where a simplified design reading conflicts with current authority, money/state safety or a normative held profile, use the explicit reviewed protocol and record/hold the missing prerequisite; rule10 does not authorise guessing a provider capability.
- Claim/document audits, mock conformance, actual component tests, actual provider/isolation/payment behaviour and working-site exit separately. Old31 abstract tests and green plugtests do not close release gates.
- Do not redesign agent internals in paper work. Future component tests remain meaningful negative/fault checks attached to AC/LC cases; no network in ordinary tests.
