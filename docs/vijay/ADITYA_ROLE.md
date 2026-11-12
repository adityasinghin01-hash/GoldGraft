> **Current update — 7 November 2026:** Read [CURRENT_BASELINE.md](CURRENT_BASELINE.md) and [PHASE1_STATUS.md](PHASE1_STATUS.md) first. The refreshed Drive explicitly supersedes older build instructions/counts and delegates engineering to the reviewed team repository. Conflicting statements below are historical; the first plain-PHP reference and VJ01–VJ05 now govern. Docker is deliberately pending.

# Aditya — PayPal + Shops Engineer

Execution follows the [phased plan](IMPLEMENTATION_PLAN.md), [decision register](DECISIONS.md) and [persistent instructions](../../AGENTS.md). Current evidence and blockers are in [Phase 0 status](PHASE0_STATUS.md).

Confirmed working assignment from the user's clarification on 5 November 2026: team leader = frontend/agents; teammate 2 = backend; teammate 3 = ML/proof; Aditya = PayPal + Shops. Image #1 calls this the **All-rounder teammate: PayPal + Shops**; image #3 calls it **Role 4: PayPal + Shops Engineer**.

The original Drive names "Aditya" under frontend in some draft notes. That source attribution conflicted with the user's clarification and caused the earlier mistake. This workspace follows the user's explicit assignment. Historical source wording is preserved in ignored snapshots.

## What you deliver

| Work | Concrete deliverable | Acceptance evidence |
| --- | --- | --- |
| Test shops | All 11 frozen shop folders; dependencies, start command, buyer script, legacy-piece inventory and seed/reset procedure | Every shop starts with one command; deterministic buyer completes a sandbox purchase |
| PayPal sandbox | REST application, sandbox seller/buyers, legacy NVP configuration where available, IPN/webhook setup and permissions | The 16 feasibility checks have recorded outcomes, limitations and evidence |
| Recorded traffic | Real old/new sandbox request, notification and payment evidence, with old noise-twin runs when required | Redacted recordings link shop revision, scenario, run and PayPal IDs; backend/proof can consume them |
| Graft Switch | Small runtime libraries, PHP first then Node/Python/Ruby under the agreed scope | Routing, config-failure, origin and in-flight continuity checks pass |
| Safe rollout | Sandbox Shadow, staged rollout and Cutback connected to the team's deterministic guard/controller | Simulated traffic, decision evidence and measured fault-to-switch-back duration |
| Zen Cart | Official modern module plus switch observer and preserved legacy refund/IPN handling | Old and new sandbox purchases and a legacy refund path are demonstrated |
| No-code lane | Licensed static WPS Buy Now fixture and proven replacement links/snippets | Sandbox payment per replacement; unsupported hosted-button access is reported |
| PayPal-only handoff | Validated agreement/profile data from the subscription fixture | IDs, totals by currency, duplicates and inactive entries checked; no automatic live conversion |
| Demo | Simulated buyers, recorded core scenarios, source-linked payment evidence | Under-three-minute team video; real, simulated, replayed and unverified outcomes labelled |

The 11-shop list and 16 tests are in [BUILD_PLAN.md](BUILD_PLAN.md). Shared artifact and service boundaries are in [INTEGRATION.md](INTEGRATION.md).

## Graft Switch requirements from P12 §S4

- Choose OLD/NEW from a valid signed SwitchConfig and a stable session hash at 0/1/10/50/100 percent.
- A buyer's in-flight session finishes on the rail where it started, including NEW sessions during Cutback.
- Captures, refunds, renewals and other money objects retain their origin rail unless a cross-generation path has actually been proved. Legacy refund compatibility is feasibility test 4.
- Poll signed config every 15 seconds and cache it. Fetch failure uses the last valid config until expiry; invalid/expired config defaults to OLD in the sandbox design.
- Emit non-blocking payment events to the guard; buffer when unreachable and freeze promotion. The controller's longer outage hard stop is documented separately.
- Keep IPN and webhooks active through the transition, verify notifications, deduplicate transaction/event IDs, and acknowledge webhooks promptly before asynchronous processing.
- PHP is first in image #3; P12 also names Node, Python, Ruby, Java and .NET. Do not claim six implemented libraries when only a smaller scope is delivered.

Config signing/control-plane storage is a service dependency; your libraries consume the signed config. The exact hashing, wire encoding, key distribution and test vectors still need the shared contract.

## Rollout work

Shadow copies cart items/amounts/currency only into the NEW sandbox path before traffic promotion; it must never make a second real charge. The demonstration uses sandbox traffic on both sides.

The controller advances 0 → 1 → 10 → 50 → 100 only on deterministic evidence. P12 proposes at least 30 NEW payments per demo stage and a Beta-Binomial rule: promotion when probability that NEW success rate is within 0.02 of OLD is at least 0.95; rollback when evidence of worse performance reaches 0.95 or a hard stop occurs. These are design parameters to implement with the proof/maths teammate, not results or production-safe guarantees.

Hard stops include a new-path money-rule failure, acting on an unverified notification, and guard outage beyond 60 seconds. Cutback publishes signed stage 0; polling libraries are expected to pick it up within 15 seconds. Record detection, publication and library-application times separately. Healer may pause/request Cutback; an LLM never authorises promotion.

After LIVE_100 and the agreed soak, cleanup must retain legacy refund/origin handling until it can safely be removed. The later vision warns that an actually retired OLD integration is not a valid production rollback target; production deployment remains future work.

## Team boundaries

| Owner | Owns | You provide or consume |
| --- | --- | --- |
| Team leader | 12 product screens, 13 agents, orchestration and presentation surfaces | Supply sandbox evidence, buyer recordings and switch/rollout states; consume agreed jobs/contracts |
| Backend teammate | Real API/database, runner/Cage, recorder infrastructure, tunnel, vault, throttling, KERNEL/hosting integration | Supply portable shop folders/buyers and integrate against their runner/capture interface |
| ML/proof teammate | CMEL mapping, money rules/Judge, mutations, scoring, certificate/signing and go-live maths | Supply real traffic, PayPal IDs, fault fixtures and rollout events; consume authoritative verdicts |
| Aditya | PayPal + Shops deliverables above | Local Docker + sandbox work, switch libraries, integration and demo evidence |

Ownership overlaps require interfaces, not rebuilding a teammate's component: you produce recordings using the backend recorder; the proof teammate maps/judges them. You implement and demonstrate rollout behaviour with their maths and the backend's signed-config/event services.

## Definition of ready

Image #1 says every shop starts with one command, its buyer pays in the sandbox, and switch libraries pass their tests. It also says this role builds on its own laptop with Docker plus PayPal sandbox, with no other project piece required to begin.

## Team repository review — 5 November 2026

See [team repository alignment](TEAM_REPO_ALIGNMENT.md) for the pinned source, exact Aditya Vijay ownership, phases 0–6, executable contract details and unresolved integration gates. This review adds context; it does not mark payment implementation complete.
