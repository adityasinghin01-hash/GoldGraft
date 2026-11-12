> **Current update — 7 November 2026:** Read [CURRENT_BASELINE.md](CURRENT_BASELINE.md) and [PHASE1_STATUS.md](PHASE1_STATUS.md) first. The refreshed Drive explicitly supersedes older build instructions/counts and delegates engineering to the reviewed team repository. Conflicting statements below are historical; the first plain-PHP reference and VJ01–VJ05 now govern. Docker is deliberately pending.

# Phase 0 — readiness, ownership and registers

Inspection date: 5 November 2026 (IST). Status: **documentation/preparation complete; runtime prerequisites blocked or unverified**. No PayPal purchase, account login, credential validation, container run or deployment was attempted. Nothing was pushed or uploaded during that initial inspection. The subsequent personal-repository upload is explicitly user-authorized.

Follow-up setup on 5 November: **Playwright 1.64.1 and Chromium are installed and the offline browser smoke check passed**. Docker/WSL remain blocked after system-drive disk exhaustion. The table below preserves the original Phase 0 inspection; current setup evidence and recovery steps are in [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md). No PayPal feasibility result changed.

## Local prerequisite evidence

| Prerequisite | Observed status | Next dependency |
| --- | --- | --- |
| Git | Available: 2.52.0.windows.1 | Local diffs/checks usable; no push authorized |
| Node | Available: v24.13.1 | Check compatibility and pin automation dependency versions when buyer implementation begins |
| Python | Available: 3.14.3 | Available tooling; not assumed compatible with legacy shop dependencies |
| Docker CLI / Desktop | Not on PATH; standard CLI/Desktop install paths absent | Verify alternate install or install/configure Docker with Linux-container support before runtime work |
| Docker daemon / Compose | Not executable through checked Docker installation | Not tested; require working Docker before reporting readiness |
| Playwright | @playwright/test not resolvable from this workspace | Install/pin buyer dependencies and Chromium during runtime setup; binary availability not otherwise asserted |
| Workspace manifests | No package.json, compose.yaml or docker-compose.yml | Future phases create actual shop/automation manifests; none claimed now |
| Sandbox environment variables | Checked names absent | Runtime configuration still needed; absence is not an account-status determination |
| Local sandbox configuration | .env, .env.local, .env.sandbox and .secrets absent | User-controlled credential entry/runtime configuration; no values requested in chat |
| Team plug pack | Located and read at team commit 05b5b3b on 5 November | Contracts/reference inspected; implementation and executable integration checks still pending; see TEAM_REPO_ALIGNMENT.md |

Presence checks inspected only PAYPAL_SANDBOX_CLIENT_ID, PAYPAL_SANDBOX_CLIENT_SECRET, PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_NVP_USERNAME, PAYPAL_NVP_PASSWORD and PAYPAL_NVP_SIGNATURE. These are conventional discovery candidates, **not mandated team variable names**. No values were printed. Credentials under other names, vaults or account sessions were not inspected.

## Requirement-to-source and owner map

The original active notes are linked by exact title in [SOURCES.md](SOURCES.md). User clarification governs identity where draft notes conflict.

| Deliverable | Owner / dependency | Source section |
| --- | --- | --- |
| 11 portable shops, buyers, inventories and sandbox payment readiness | Aditya; backend consumes folders | Image #1 PayPal + Shops; P12 09 Test shops; P12 02 R2 |
| 16 feasibility results and real recordings | Aditya coordinates; backend supplies capture/tunnel and leader supplies own tool-account outcomes | Image #1; P12 09 Step 6; P12 02 G1/R3 |
| PHP-first runtime switches | Aditya; backend signed-config/events; proof verdicts | Image #3 Role 4; P12 03 S4; P12 01 section 7 |
| Shadow, Heal and Cutback integration | Aditya integrates; proof maths/Judge and backend persistence/signing services | P12 05 H1-H4; P12 08 steps 18-21 |
| Zen Cart official-module path | Aditya; leader migration agents/proof evaluation | P12 03 S1/S3/S4; P12 08 |
| No-code Buy Now lane | Aditya payment fixture/links; leader Surveyor/Herald | P12 03 S5 |
| Recurring continuity and PayPal-only handoff | Aditya supplies fixture data; leader Herald; PayPal performs conversion | P12 03 S1; P12 05 F1/X2 |
| Demo buyers, recordings and comparison evidence | Aditya runs/records; everyone reviews; leader provides screens | Image #3 shared demo note; P12 09 demo |
| Core first and production exclusions | All roles | VISION_3_NOV sections 1/6; P13 section 7 |

## Frozen-set preparation register — all 11 shops

All rows are **UNVERIFIED: not packaged or executed**. Freeze source commit, licence and dependency versions before tuning. No shop-folder schema is invented here.

| ID | Planned shop | Stack / purpose | Owner | Source |
| --- | --- | --- | --- | --- |
| SHOP-01 | Zen Cart fork | PHP; official modern module + switch/legacy refunds | Aditya | P12 09 Test shops; P12 08 |
| SHOP-02 | Customised Zen Cart #2 | PHP; independent recipe reuse | Aditya | P12 09 Test shops |
| SHOP-03 | Cutover legacy-php-shop | PHP; NVP/checkout.js/IPN rewrite baseline | Aditya | P12 09 Test shops |
| SHOP-04 | expressCart | Node; REST v1 migration/comparison | Aditya | P12 09 Test shops |
| SHOP-05 | django-oscar-paypal sandbox | Python; EC-NVP | Aditya | P12 09 Test shops |
| SHOP-06 | better_spree_paypal_express | Ruby; EC-NVP | Aditya | P12 09 Test shops |
| SHOP-07 | Licensed static Buy Now site | HTML; no-code links | Aditya | P12 09 Test shops; P12 03 S5 |
| SHOP-08 | Seeded hard shop | PHP; wrappers/templates/dead-code survey ground truth | Aditya | P12 09 Test shops |
| SHOP-09 | Subscription shop | PHP; legacy continuity, simulated renewal and handoff | Aditya | P12 09 Test shops; P12 05 F1/X2 |
| SHOP-10 | Gauntlet shop | Node; inert hostile fixtures for isolated security demo | Aditya; backend/proof dependencies | P12 09 Test shops; P10 |
| SHOP-11 | Poisoner shop | PHP; bad-recipe quarantine fixture | Aditya; leader/proof dependencies | P12 09 Test shops; P12 05 B1 |

Each future folder needs its agreed start command, deterministic buyer, legacy inventory, health/seed/reset procedure, revision/licence/dependency records and redacted evidence references. Local register IDs are planning labels, not replacements for plug-pack identifiers.

## Feasibility register — all 16 checks

All checks are **UNVERIFIED / not run**. Owner means accountable for collecting the result, not permission to access another teammate's account. Docker-dependent execution is blocked; external account availability is unknown. Every eventual result must include actual steps, expected/observed behaviour, date/environment, evidence, limitation and fallback. Source: P12 09 Step 6, with role ownership from image #1.

| ID | Check | Result owner / dependency | Evidence or decision required |
| --- | --- | --- | --- |
| CHECK-01 | NVP credentials and EC purchase | Aditya | Available legacy access, actual approval/capture IDs |
| CHECK-02 | WPS purchase + IPN to tunnel | Aditya; backend tunnel | Actual payment and received/verified notification |
| CHECK-03 | IPN simulator | Aditya | Supported simulator cases distinct from purchases |
| CHECK-04 | Modern refund of NVP-era transaction | Aditya; proof validates origin rule | Actual cross-generation compatibility or retained legacy rail |
| CHECK-05 | Transaction Search permissions, T-codes, lag | Aditya | Observed classification and evidence delay |
| CHECK-06 | Button Manager sandbox | Aditya | Hosted-button capability or form-only fallback |
| CHECK-07 | Webhook simulator recurring/subscription events | Aditya; backend/proof listener | Supported event list and correct simulator verification; not true renewal timing |
| CHECK-08 | Payment Links sandbox | Aditya | Link creation and real sandbox amount/currency evidence |
| CHECK-09 | Vault v3 repeat purchase | Aditya | Account eligibility and observed repeat behaviour |
| CHECK-10 | Pay Later rendering | Aditya | Eligible rendering and unsupported states |
| CHECK-11 | Agent Ready/UCP route | Aditya; leader | Actual route availability or prerequisites-only unverified execution |
| CHECK-12 | Rate limits / runner IP behaviour | Aditya collects; backend controls traffic | Bounded observations; no forced throttling or assumed unique IPs |
| CHECK-13 | cloudflared on GitHub runner | Aditya collects; backend runs | Callback/return delivery evidence; remote run awaits explicit authorization |
| CHECK-14 | KERNEL v6 popup buyer | Aditya; backend tool access | Repeatable buyer; local Playwright fallback if unavailable |
| CHECK-15 | AG Studio trial/framework access | Aditya collects; leader account owner | Access/trial outcome without assuming frontend ownership |
| CHECK-16 | Claude spending cap and Actions dev auth | Aditya collects; leader/backend account owners | Redacted configuration outcome; no new spending or remote workflow authorized |

## Phase exit and next gate

Persistent instructions, plan, decision log and source-backed registers are present. Readiness inspection is complete. Operational environment readiness and all payment results remain unverified/blocked; this is not a sandbox feasibility pass.

Next implementation work: environment setup followed by authorised Phase 1 checks and available PHP baseline work. The plug pack is now found; Phase 3 interoperability still requires implementing and running its contracts/tests plus resolving transport/session gaps. No Phase 1-6 completion is claimed.

## Team repository review — 5 November 2026

See [team repository alignment](TEAM_REPO_ALIGNMENT.md) for the pinned source, exact Aditya Vijay ownership, phases 0–6, executable contract details and unresolved integration gates. This review adds context; it does not mark payment implementation complete.
