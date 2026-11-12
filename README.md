# GoldGraft — “Don't cut the tree. Graft.”

**Reference demo, 12 November 2026:** [open the app](https://goldgraft.vercel.app) or [read the hosted runs API](https://goldgraft-api.onrender.com/runs). The public API serves recorded evidence; it does not start paid model jobs. The hosted setup is described in [deploy/README.md](deploy/README.md).

| Recorded evidence (`r9-final-connected`) | Result |
|---|---|
| Agents on real models | 13/13 roles passed |
| Connected backend → PHP execution → independent proof | 34/39 critical checks verified; result **HOLD** |
| Executed planted bugs | 6/10 caught; four remain unverified |
| PayPal sandbox | AI-written PHP checkout's HAPPY flow independently verified against real sandbox; additional refund/duplicate flows recorded separately |
| E2B sandbox runner | Live-tested on 3 real E2B VMs (normal run, deliberate failure, timeout), internet off, each VM confirmed killed. The PHP proof does not run inside it yet, so runner isolation stays held |
| Vijay's shop recipe | Plugs into the shop socket. With his hand-reviewed candidate, all 9 scenarios are judged (8 PASS, 1 PASS_FIXED) and the full connected run verifies 30/39 checks with his state, final-setup and exit-check recipes attached. AI-written code is refused until it can run in a protected sandbox (`plugtests/test_vijay_recipe_socket.py`) |
| Proof signature | ProofResult signed by the GitHub workflow; public Rekor entry **3833925707** |
| Qualification certificate | **Not issued**; a signed held result is not a qualification certificate |

These are the checked-in [connected-run records](deploy/runs/r9-final-connected/connected-run/). They describe recorded evidence, not a new execution when a visitor opens the app. The real-provider gate covers **HAPPY only**. The five open checks are four planted-bug gaps and runner isolation. Merchant deployment, state transfer and independent exit remain separate qualification work. See the [live-check scope and limitations](docs/engineering/work/SANDBOX_LIVE_CHECKS_2026-11-12.md).

GoldGraft is being designed as a browser connector service that upgrades a shop's older PayPal integration and leaves the approved upgraded shop running under the merchant's control. The service obtains authorised code/context, verifies the actual shop, reproduces an unchanged baseline, tests an isolated upgrade, obtains separate publication/deployment approval and verifies handover/recovery/exit. A PR or sandbox pass alone is not completion.

**Current scope:** an implemented reference demo with real model runs, executed PHP checks and a signed held proof result. The complete merchant delivery service is not operationally qualified. The [engineering baseline](docs/engineering/START_HERE.md), [inspected support](docs/engineering/BASELINE_AND_STATUS.md) and [current versus proposed contracts](docs/engineering/CURRENT_VS_PROPOSED.md) contain dated design snapshots; current code and run records establish what is implemented. MIT licence.

## How GoldGraft uses PayPal and AI

| Tool | What it does in GoldGraft |
|---|---|
| **PayPal Orders v2 API (Sandbox)** | The upgrade target. The AI-written PHP checkout creates an order, the buyer approves it, the shop captures it, and refunds use the Payments v2 refund call. Every result is independently re-fetched from PayPal before it counts. Live script: [`scripts/live_shop_sandbox.py`](scripts/live_shop_sandbox.py); scope in [SANDBOX_LIVE_CHECKS](docs/engineering/work/SANDBOX_LIVE_CHECKS_2026-11-12.md). |
| **Legacy PayPal integrations** (Express Checkout NVP, checkout.js, IPN) | What GoldGraft finds and replaces: `SetExpressCheckout`, `DoExpressCheckoutPayment`, `RefundTransaction`, `paypal.Button.render` and IPN validation in the reference shop. |
| **Anthropic Claude** (Haiku first, Sonnet fallback) | Powers 13 role agents (Surveyor maps the shop, Grafter rewrites the checkout, Adversary hunts for weaknesses, plus scenario, diagnosis, notification, learning and reporting roles) through a model gateway with a cost ledger and a hard per-run budget cap ([`pieces/agents`](pieces/agents), [`pieces/backend/model_gateway`](pieces/backend/model_gateway)). Recorded run `r9-final-connected`: 13/13 roles passed, $0.48. |

### Sponsor and supporting tools

| Tool | Use |
|---|---|
| **Render** | Hosts the public read-only API that serves the recorded runs ([deploy/README.md](deploy/README.md)). |
| **E2B** | Optional isolated command runner ([`pieces/runner/e2b_backend.py`](pieces/runner/e2b_backend.py), [docs/E2B_RUNNER.md](docs/E2B_RUNNER.md)); live-tested on three VMs. |
| **Zapier** | The Herald agent can send upgrade notifications to a Zapier webhook ([`scripts/live_herald_zapier_send.py`](scripts/live_herald_zapier_send.py)). |
| **Sigstore / Rekor + GitHub Actions** | Keyless signing of the proof result; public Rekor entry #3833925707 ([`.github/workflows/sign-proof.yml`](.github/workflows/sign-proof.yml)). |
| **Vercel** | Hosts the web app at https://goldgraft.vercel.app. |

Setup instructions are under [Local development](#local-development).

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
| `foundation/` | Shared ledger, step tracker and evidence helpers. |
| `fakes/`, `fixtures/`, `plugtests/` | Offline stand-ins, labelled examples and compatibility checks. These do not prove real account/payment/isolation flows. |
| `pieces/` | Independent team implementations; never import another piece's code. |
| `integration/` | Composition of the pieces, connected proof execution and recorded-run API. |
| `deploy/` | Public, recorded evidence served by the hosted API. |
| `docs/engineering/` | Target design, controls, acceptance criteria and dated implementation audits. |
| `docs/design/` | Historical original design, with supersession notices; compatible data descriptions interpreted against current Python. |
| `docs/FORMAT_CHANGES.md` | Existing coded format history and explicitly unimplemented proposal records. |

## Local development

Use Python 3.12/uv, Node 22 and git:

```bash
uv sync
npm ci
GOLDGRAFT_PROOF=pieces.proof.proof:Proof GOLDGRAFT_API_APP=integration.app:create_app uv run pytest -q
uv run python -m integration.agents_app --runs-dir deploy/runs --port 8700
```

In a second terminal, from the repository root:

```bash
cd pieces/web
npm ci
VITE_API_BASE=http://127.0.0.1:8700 npm run dev
```

The API command serves recorded runs without enabling paid model execution. See [pieces/web/README.md](pieces/web/README.md) for frontend data modes. For the offline synthetic fixture API, use `uv run python -m goldgraft_fakes.api --port 8700` instead. Ordinary tests stay offline; PHP is required for the executed shop checks. No secrets in code/logs/docs/fixtures. Payment amounts are integer minor units plus currency. Follow [AGENTS.md](AGENTS.md). Only approved versioned shared changes regenerate contracts alongside examples/fakes/fixtures/tests.

## Publication and external sources

GitHub is the shared engineering authority and this repository is public. Team Drive remains idea/research/pitch context. On 6 November 2026 the 21 affected shared Drive Markdown files in the [Team Pack](https://drive.google.com/drive/folders/10NZ56zh6UlveQTsi7rIrUA9K4GY8uv7a) and [GoldGraft](https://drive.google.com/drive/folders/1Sw-6KObSswVPHMgYdedOitltdpUAcjqR) folders were updated in place with supersession notices pointing here. Other Drive research and archive files remain historical reference.

Programme order: 1 → 3 → 4 → 2 → 5 → 6. The paper plans and publication preceded the current build and reference integration. Engineering proposals and these instructions do not themselves authorise new external access, paid runs, production deployment or merchant financial actions.
