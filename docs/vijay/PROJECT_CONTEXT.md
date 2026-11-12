> **Current update — 7 November 2026:** Read [CURRENT_BASELINE.md](CURRENT_BASELINE.md) and [PHASE1_STATUS.md](PHASE1_STATUS.md) first. The refreshed Drive explicitly supersedes older build instructions/counts and delegates engineering to the reviewed team repository. Conflicting statements below are historical; the first plain-PHP reference and VJ01–VJ05 now govern. Docker is deliberately pending.

# Project context — PayPal + Shops

Reviewed 5 November 2026 using the active GoldGraft notes and all six supplied images. Relevant Drive guide, Scion, Heal and demo/test files were fetched again for this correction.

## Correct assignment

The user clarified that "you" in the screenshots describes the team leader, who owns frontend/screens and agents. Backend and ML/proof are assigned to two other teammates. The remaining Role 4, **PayPal + Shops Engineer**, is the user's assignment.

Some draft Drive text puts the name Aditya beside frontend/agents; this is source wording, not a reliable identity mapping for this user. The user's explicit clarification governs this workspace. The previous authored files incorrectly mapped that role and have been rewritten.

## Product and your contribution

GoldGraft is designed to take a merchant's legacy PayPal checkout through discovery, recorded baseline, migration, deterministic proof, staged sandbox cutover, automatic rollback and recipe learning.

Your contribution is the working payment environment: shops that boot reliably, buyers that actually pay, sandbox integration answers, genuine recordings, runtime switch libraries and rollout demonstrations. Your laptop plus Docker and PayPal sandbox is enough to begin the assigned shop work.

The latest 3 November vision says core first and audience = anyone with old PayPal code. Seller onboarding/distribution, production deployment connectors and final pitch are later work. PayPal distribution is proposed, not an existing partnership.

## End-to-end handoff

1. You supply a frozen shop folder, deterministic buyer and legacy-component inventory.
2. Backend's runner/Cage boots it and records requests/state/notifications; you configure the shop and execute/debug sandbox buyer flows.
3. Leader's agents plan/rewrite through shared contracts. Proof converts recordings into CMEL and judges old/new/ledger evidence.
4. Your switch libraries enforce signed rollout decisions, sticky sessions and origin routing.
5. You integrate sandbox Shadow, staged buyers and Cutback with deterministic backend/proof services.
6. You supply demo recordings and PayPal-only fixture data; leader's screens display evidence and the team reviews the final video.

## What the design is measuring

CMEL compares money across API generations. Old and old-twin runs identify noise; Union Proof checks contract rules before parity. MMO-12 measures whether scenarios catch planted payment bugs. Certified changes can become quarantined recipes. These are team/proof mechanisms whose input evidence comes from your shops; their implementation is not automatically reassigned to you.

The source targets proof strength >=0.95, recorded runtime/survey evidence, safe 0/1/10/50/100 promotion and rollback after a fault. No achieved proof score, shop count, cost or timing is claimed in this repository.

## Specific operating context

- Two implementation paths matter early: a PHP rewrite shop and Zen Cart's official-module path.
- Eleven frozen test shops cover PHP, Node, Python, Ruby, HTML, subscriptions and adversarial fixtures.
- Sixteen feasibility tests decide legacy access, notifications, refund origin, search lag, hosted buttons, links, vault, messaging, UCP, rate limits and team tooling.
- Switch libraries are PHP-first; remaining language scope is explicit and test-backed.
- Baseline state must be reset for repeatable old/old-twin runs; real payment evidence and simulated notification tests are distinguished.
- All demonstration buyers/payments are sandbox. Show **PayPal sandbox · simulated buyers** on rollout shots.
- Merchant consent remains part of the planned application. Your demo does not authorise production changes.
- Backend owns runners/tunnels/capture/rate limiting; proof owns verdicts/signing/maths; leader owns agents/screens. Shared rollout boundaries need explicit contracts.

## Later-vision cautions relevant to this role

A sandbox pass does not establish a production-safe deployment. FTP/cPanel import, production credentials, live-payment checks, deploy/backup/restore and removing temporary access remain parked. The team notes say code rollback must not restore a database backup that could erase new orders.

Low-volume rollout needs a safety rule beyond the demo's 30 payments per stage. If an old API is retired, it cannot be a valid fallback; a future production design must use a last working version. Existing agreements/profile conversions remain PayPal-only.

The notes qualify WPS Buy Now/Add to Cart as potentially retiring after 1 January 2027. They do not establish that deadline for all legacy APIs. Public code counts count files, not merchants; paper scores and conversion claims are not project outcomes.

## Status and open dependencies

Phase 0 documentation/preparation has been implemented locally: [phased plan](IMPLEMENTATION_PLAN.md), [decision register](DECISIONS.md), [readiness/registers](PHASE0_STATUS.md) and [persistent instructions](../../AGENTS.md). No shop implementation, sandbox purchase, switch, result pack or demo has been produced here. Payment work-plan boxes remain open. No push/upload is authorized by phase completion.

The team plug pack is now inspected at commit 05b5b3b: shop schema, switch signing/routing and Shadow representation are known. Remaining gaps include actual sandbox outcomes, upstream/licence verification for remaining shops, account eligibility and guard transport/cache/session policy. See [TEAM_REPO_ALIGNMENT.md](TEAM_REPO_ALIGNMENT.md).

The source pack lists 8 November as a team freeze target and submission at 13 November 2026, 01:30 IST with demo availability through 15 December. These are source-reported dates to reconfirm with the leader/Devpost before submission. Earlier disputes research is shelved.

See [your role](ADITYA_ROLE.md), [the complete work/test inventory](BUILD_PLAN.md), [integration details](INTEGRATION.md), and [sources](SOURCES.md).

## Team repository review — 5 November 2026

See [team repository alignment](TEAM_REPO_ALIGNMENT.md) for the pinned source, exact Aditya Vijay ownership, phases 0–6, executable contract details and unresolved integration gates. This review adds context; it does not mark payment implementation complete.
