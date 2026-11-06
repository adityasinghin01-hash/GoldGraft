# GoldGraft — “Don't cut the tree. Graft.”

GoldGraft is being designed as a browser connector service that upgrades a shop's older PayPal integration and leaves the approved upgraded shop running under the merchant's control. The service obtains authorised code/context, verifies the actual shop, reproduces an unchanged baseline, tests an isolated upgrade, obtains separate publication/deployment approval and verifies handover/recovery/exit. A PR or sandbox pass alone is not completion.

**Current status:** reviewed paper engineering and shared team build instructions; the complete service is not built or operationally qualified. [Start with the engineering baseline](docs/engineering/START_HERE.md), [inspected current support](docs/engineering/BASELINE_AND_STATUS.md) and [current versus proposed contracts](docs/engineering/CURRENT_VS_PROPOSED.md). MIT licence.

## Fixed journey, variable connections

Enter shop → Sign in → obtain the actual maintainer/controller's permission → Connect code (GitHub by default, with separately qualified local/cloud/host alternatives) → connect required running components → automatic static preparation → review and Start → truthful durable progress → isolated work/proof → separate approved apply → verified merchant-owned operation.

Render is the first reference adapter, selected by Aditya. It is not mandatory merchant hosting or demonstrated universal support. First engineering reference is the pinned licensed plain-PHP legacy shop, not a qualified live merchant migration; unsupported/missing dependencies produce explicit holds. Provider consent/MFA and actual controller decisions cannot be bypassed. Initial Reader permissions stay genuinely read-only; later writes and deployment require independent exact authority.

## Team responsibilities

| Person | Shared build guide |
|---|---|
| Aditya Singh | [Shared formats, saved-case UI, own agents later, integration](docs/START_Aditya_frontend_agents.md) |
| Aditya Gupta | [Backend, runner, custody/brokers and lifecycle mechanisms](docs/START_Aditya_Gupta_backend.md) |
| Aditya Singhal | [Retain proof contribution; evidence/completeness deltas](docs/START_Aditya_Singhal_proof.md) |
| Aditya Vijay | [Reference shop/runtime, payment/state/callback/exit recipes](docs/START_Aditya_Vijay_paypal_shops.md) |

[Seventeen work packages](docs/engineering/work/PER_PERSON_WORK_PACKAGES.md) give inputs/outputs, proposed paths, dependencies and acceptance evidence. Inspect each person's current contribution before adapting it. Unchanged boundaries can proceed independently; new interfaces wait for Singh's approved shared bootstrap. No contribution is called complete from a placeholder or stand-in test. No revised completion dates are invented.

## Repository map

| Folder | Authority / purpose |
|---|---|
| `contracts/` | Current Python wire models and generated schemas/types/OpenAPI; proposals are not existing fields. |
| `foundation/` | Shared ledger and step tracker; new lifecycle semantics still require implementation. |
| `fakes/`, `fixtures/`, `plugtests/` | Offline stand-ins, labelled examples and compatibility checks. These do not prove real account/payment/isolation flows. |
| `pieces/` | Independent team implementations; never import another piece's code. |
| `docs/engineering/` | Reviewed proposed target build, controls, lifecycle, acceptance and all-four work baseline. |
| `docs/design/` | Historical original design, with supersession notices; compatible data descriptions interpreted against current Python. |
| `docs/FORMAT_CHANGES.md` | Existing coded format history and explicitly unimplemented proposal records. |

## Future local development

Existing setup uses Python3.12/uv, Node22 and git. Commands below are reference instructions, not work performed or authorised by this documentation update:

```bash
uv sync
npm ci
uv run pytest -q
uv run python -m goldgraft_fakes.api --port 8700
```

Ordinary tests stay offline. No secrets in code/logs/docs/fixtures. Payment amounts are integer minor units plus currency. Follow [AGENTS.md](AGENTS.md). Only approved versioned shared changes regenerate contracts alongside examples/fakes/fixtures/tests.

## Publication and external sources

This documentation-only publication contains the reviewed engineering baseline and all four people’s work plans. GitHub is the shared engineering authority. Team Drive remains idea/research/pitch context. On 6 November 2026 the 21 affected shared Drive Markdown files in the [Team Pack](https://drive.google.com/drive/folders/10NZ56zh6UlveQTsi7rIrUA9K4GY8uv7a) and [GoldGraft](https://drive.google.com/drive/folders/1Sw-6KObSswVPHMgYdedOitltdpUAcjqR) folders were updated in place (same file links) with supersession and authority notices that point here; their original bodies are preserved, and the saved content was read back and hash-verified. Other Drive research, evidence and archive files were not changed and remain historical reference. No team messages were sent.

Programme order: 1 → 3 → 4 → 2 → 5 → 6. Paper Plans1/3/4 are closed; Plan2 publishes the shared engineering docs and the affected shared Drive files are synchronised and verified. Plans5/6 are Singh's future build/tests and integration/qualification, requiring explicit start. Agent internals, production deployment and merchant financial actions are not authorised by these docs.
