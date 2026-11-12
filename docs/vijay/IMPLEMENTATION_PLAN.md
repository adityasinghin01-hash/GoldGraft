> **Current update — 7 November 2026:** Read [CURRENT_BASELINE.md](CURRENT_BASELINE.md) and [PHASE1_STATUS.md](PHASE1_STATUS.md) first. The refreshed Drive explicitly supersedes older build instructions/counts and delegates engineering to the reviewed team repository. Conflicting statements below are historical; the first plain-PHP reference and VJ01–VJ05 now govern. Docker is deliberately pending.

# GoldGraft: PayPal + Shops phased implementation

**Latest execution:** [FINAL_LOCAL_STATUS.md](FINAL_LOCAL_STATUS.md) maps the completed local components, actual socket/proof checks and remaining full qualification gates. Use it ahead of earlier execution reports below.

**12 November execution report:** [LOCAL_PHASE_DELIVERY.md](LOCAL_PHASE_DELIVERY.md) maps current local delivery to phases 0–6, including the separate NEW candidate and Phase 0-only publication. Its current first-reference scope and observed results supersede historical counts/implementation statements below.

8 November continuation: [Phase 2 independent baseline characterization](PHASE2_STATUS.md) has started at the user's request. Three OLD and three OLD_TWIN local component runs passed; full Phase 1 and Phase 2 qualification remain held on current team dependencies. Follow CURRENT_BASELINE.md; historical shop breadth below is not reinstated.

Status: Phase 0 documentation and inspection completed locally on 5 November 2026; payment implementation has not started. See [current readiness and registers](PHASE0_STATUS.md).

## Control and source of truth

Follow [AGENTS.md](../../AGENTS.md). No push, upload, PR, merge, remote workflow, deployment or publication without explicit user authorization for that action. Implementation requests alone do not authorize publication. No automatic deadlines, paid services or production-money scope.

Use the user's clarified role and designated current Drive PDFs/docs for requirements. Read source sections before implementation; distinguish requirements, verified technical facts, proposals and gaps using [DECISIONS.md](DECISIONS.md). Search documents and the repository before asking questions. Research must use primary technical sources and cannot silently override team requirements.

The team leader owns screens/agents; backend owns runner infrastructure; ML/proof owns verdicts/maths; Aditya owns PayPal + Shops. See [role boundaries](ADITYA_ROLE.md), [complete shop/test inventory](BUILD_PLAN.md), [integration details](INTEGRATION.md) and [source index](SOURCES.md).

## Implementation approach

- Docker Compose Linux-container shop environments with pinned source revisions, dependencies and compatible runtime versions; health checks gate readiness.
- Deterministic Playwright buyers. TypeScript is the accepted proposed shared automation language; shops retain their original languages. Exact package/runtime pins come from compatibility inspection, not guesses.
- Fresh browser contexts and reset shop state per independent scenario; distinguish provider transaction IDs across runs.
- Runtime-mounted secrets, ignored authentication/raw-evidence files and redacted shareable results.
- Separate offline tests, actual sandbox transactions, provider-simulated responses and replayed evidence.
- PHP switch first; Node/Python next; Ruby later. Java/.NET stay map/plan-only unless team scope explicitly changes.
- Local shop work starts before the plug pack arrives. Final integration formats and switch interoperability require inspection of the actual team contract.

## Phases

| Phase | Deliverables | Completion gate |
| --- | --- | --- |
| 0 — Instructions and preparation | Persistent instructions, this plan, decision register, prerequisite inspection, source/owner mapping, 11-shop and 16-check registers | Findings are recorded accurately; every deliverable has a source and owner; missing prerequisites are visible, not declared operational |
| 1 — Sandbox feasibility | Legacy NVP/WPS/IPN, modern payments, refund-origin, real notifications and remaining capability/tooling outcomes | Every attempted check has steps, actual outcome, redacted evidence and fallback/blocker; unattempted checks remain visible |
| 2 — First working PHP shops | PHP rewrite fixture and Zen Cart baseline; start/readiness/seed/reset commands, buyer scripts and legacy inventories; preserved frozen originals | Each available baseline produces three clean buyer runs with matching payment IDs/shop state; unavailable legacy access remains blocked |
| 3 — Contract alignment and PHP switch | Inspect plug-pack commit; adopt shop/job/evidence interfaces; PHP routing/signatures/cache/session/origin/guard events; Zen Cart observer | Contract checks and switch tests pass; legacy refunds and in-flight continuity work on the correct rail |
| 4 — Shadow, staged rollout and Cutback | Integrate signed config, backend events and proof decisions; sandbox Shadow; 0/1/10/50/100 simulated traffic; fault injection and timing | Deterministic promotion; mismatch stops promotion; measured Cutback does not strand in-flight money |
| 5 — Complete breadth | Node/Python shops and switches, static Buy Now path, customised Zen Cart #2, subscription/handoff, hard-survey, Gauntlet, Poisoner, then Ruby | All 11 shops have visible outcomes; each delivered switch has equivalent tests; no hidden failures or claimed unimplemented coverage |
| 6 — Team integration and demo | Actual backend-runner execution, proof/leader evidence handoff, recipe/comparison results and short demo | Reproducible local handoff, complete result register and measured labelled demo evidence; no automatic push |

Each requested phase ends with a local report and its actual gate status. Later phases follow the user's instructions. Infrastructure blocked in one area does not stop independent source-backed preparation.

## Shared interface gate before Phase 3

Inspect the executable contract for shop startup/reset, buyer inputs/outputs, scenario/run naming, raw recording format, SwitchConfig signing bytes/keys/hash vectors, guard delivery/auth/dedupe/outage policy, origin metadata and Shadow-run representation.

Preserve /switch/config/{graft} and /guard/event. Do not freeze a competing schema, canonical signing encoding or cross-language hash based only on P12 pseudocode. The plug pack is located at team commit 05b5b3b. Use its inspected signing/routing/schema rules and remaining interface gaps in [TEAM_REPO_ALIGNMENT.md](TEAM_REPO_ALIGNMENT.md).

## Evidence and validation

Every run records shop revision, environment, scenario, run ID, OLD/OLD_TWIN/NEW or contract-defined Shadow variant, actual timestamps, observed outcome, relevant PayPal IDs and redacted artifact references. Database reset does not reset PayPal; use distinct provider order identifiers for independent runs. The Judge supplies payment verdicts; a buyer script exit code is not proof.

| Area | Required checks |
| --- | --- |
| Shop reliability | Clean startup, healthy dependencies, deterministic seed/reset, three repeatable baseline purchases |
| Payments | Cancel, decline, pending, retries/double clicks, lost response, amount/currency tamper, refund/second refund, forged/duplicate notifications and restart |
| Switch | 0/100 boundaries, stable routing, signature/expiry rejection, cached-valid fetch failure, in-flight OLD/NEW continuity and origin routing |
| Rollout | Shadow mismatch, insufficient traffic, guard outage, deterministic promotion and measured Cutback |
| Honest coverage | All 16 checks have PASS/FAIL/BLOCKED/UNVERIFIED; simulator events do not establish genuine transaction proof |
| Security fixtures | Hostile content inert until agreed isolated execution; no credentials or buyer PII in tracked evidence |

The original Phase-0 gate is documentation/readiness inspection, not a claim Docker or sandbox execution passed. Future gates cannot pass without the required behaviour running.

## Research-backed methods

These are verified technical guidance, not new product requirements. Details and conflicts are in [DECISIONS.md](DECISIONS.md).

- [Docker startup readiness](https://docs.docker.com/compose/how-tos/startup-order/) and [service-scoped secrets](https://docs.docker.com/compose/how-tos/use-secrets/).
- [Playwright browser isolation](https://playwright.dev/docs/browser-contexts) and [failure recording options](https://playwright.dev/docs/test-use-options).
- [PayPal real vs simulator webhook verification](https://developer.paypal.com/api/rest/webhooks/rest/).
- [Endpoint-specific idempotency](https://developer.paypal.com/api/rest/reference/idempotency/) and [supported negative-testing headers](https://developer.paypal.com/negative-testing/request-headers/).
- [PayPal rate-limit guidance](https://developer.paypal.com/api/rest/reference/rate-limiting/): source figures are planning settings, not guaranteed provider quotas; cache tokens, minimise polling and do not evade throttling.

## Team repository review — 5 November 2026

See [team repository alignment](TEAM_REPO_ALIGNMENT.md) for the pinned source, exact Aditya Vijay ownership, phases 0–6, executable contract details and unresolved integration gates. This review adds context; it does not mark payment implementation complete.
