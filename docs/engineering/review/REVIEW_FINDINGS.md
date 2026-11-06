# Plan4 review findings

Whole-system paper critique, not independent security certification, implemented-system test or product validation. Latest user scope permits Plan3→Plan4→Plan2 paper/docs; internal agent design/build/live/account actions remain excluded. Independent findings are recorded separately in INDEPENDENT_REVIEW.md.

## F01 — Whole-scope source completeness versus static inference

Severity: high. Location: Plan1 WorkPackage/readiness and Plan3 BASELINE_REPRODUCTION.

Trigger/consequence: A partial static graph appears complete while backend/private dependency/notification path is absent.

Required resolution: Require declared bounded scope, missing-input hold and after-Start baseline evidence before changes; no “whole” certainty from listing.

Disposition/evidence boundary: Specification hold retained; empirical completeness remains open.

## F02 — Current runtime/config evidence absent from provider API

Severity: high. Location: Plan3 RENDER_DELIVERY_AND_STATE / research RENDER_CONSTRAINTS.

Trigger/consequence: Instance API only IDs, env GET contains secrets; matching source label or one200 could be old/unqualified code.

Required resolution: First profile single-instance/trusted nonsecret config/provenance observation only when qualified; missing trustworthy correlation blocks readiness/apply. Never invent configVersion/per-instance digest.

Disposition/evidence boundary: Mechanism/gate specified; no account/runtime qualification claim.

## F03 — Image-backed deployment can be accepted without attributable ID

Severity: high. Location: Plan3 effect ledger/Render adapter.

Trigger/consequence: 202/lost response plus external competing deploys can produce duplicate deploy/migration on blind retry.

Required resolution: Commit intent, bounded exact reconciliation, hold INCIDENT_UNKNOWN if uniqueness absent; local lock alone not provider idempotency.

Disposition/evidence boundary: Paper correction required in all shared adapter docs; implementation gate open.

## F04 — Scope does not mean selected-service or zero-write automatically

Severity: high. Location: Plan1 HOST_ADAPTER_FEASIBILITY / cloud source routes.

Trigger/consequence: Workspace read/Deploy Run broader than UI choice; cloud role may protect one file but still permit creates/shares.

Required resolution: Disclose provider breadth and enforce broker limits; qualify effective source grant against all create/update/delete/share/write actions, not existing-file write only; no classic/broad fallback.

Disposition/evidence boundary: Add explicit cloud effective-capability correction; live scope assurance open.

## F05 — Old switch expiry and worker/tunnel dependency break final shop

Severity: high. Location: Old design05 versus Plan3 SUCCESSFUL_EXIT.

Trigger/consequence: At100% then GoldGraft exits; expiring config returns old or notifications stop with tunnel.

Required resolution: Finalised merchant-owned steady state, registry/secret/callback/origin continuity and post-denial/restart proof before overall exit complete.

Disposition/evidence boundary: Plan3 replaces unsafe old completion rule; shared docs must supersede it.

## F06 — Database/code rollback falsely reverses economic effects

Severity: high. Location: Old design cutback/cleanup versus Plan3 recovery.

Trigger/consequence: Capture/refund succeeds remotely then service restores old DB or replays under new key.

Required resolution: Preserve financial/origin events; endpoint-specific retry window, explicit compensation authority, backward-compatible cutback or forward repair/hold.

Disposition/evidence boundary: Payment primary constraints retained; no real rollback tested.

## F07 — No-technical-finishing expectation versus protected controller merge

Severity: high. Location: Plan3 LC-A1 policy extension.

Trigger/consequence: Original policy controller merges, new UX could imply unattended merge/deploy from Start.

Required resolution: Explicit later controller-approved Apply broker under provider reviews/checks; old Reader untouched; unavoidable provider action shown, no auto-bypass or guaranteed unattended claim.

Disposition/evidence boundary: Policy proposal must be labelled at each authoritative entry; actual consent pending.

## F08 — Existing certificate cannot represent whole multi-source/E2B private evidence

Severity: high. Location: Current Certificate fields versus Plan3 new bundles.

Trigger/consequence: Builders fill Git SHA/workflow placeholders or publish private transaction/source data to satisfy current types.

Required resolution: Retain current contract; use proposed new private lifecycle bundle/versioned projection, signer outside worker; do not fake current compatibility.

Disposition/evidence boundary: Shared bootstrap dependency required before full integration.

## F09 — Phases/ownership and contribution evidence must stay current

Severity: medium. Location: Latest root revision versus old docs/START files.

Trigger/consequence: Old handoff/no-extra-Gupta/Vijay rules or pending PR treated as merged create conflicting responsibilities.

Required resolution: Order1→3→4→2→5→6; all-four keep/adapt/add/defer; inspect/reuse open proof PR, local/unpushed other work unknown.

Disposition/evidence boundary: Plan2 must reconcile actual team build guides without personal README edits.

## F10 — Non-Git plans changed old out-of-scope catalogue relevance

Severity: medium. Location: SC026–SC031/SC059–SC060 versus newer folder/source routes.

Trigger/consequence: Outside-first-scope historical label interpreted as solved or irrelevant after proposing local/cloud import.

Required resolution: Preserve frozen disposition; add new-route designed relevance and explicit browser/cloud permission/completeness tests, not historical-provider support claims.

Disposition/evidence boundary: Full coverage matrix records supplement/relevance, empirical gaps remain open.

## F11 — Closure counts and historical drafts can confuse authority

Severity: medium. Location: Plan1/3 draft schemas and intermediate counts.

Trigger/consequence: Builder follows old single-host/mandatory-commit/generation or old temporaryrunner contract.

Required resolution: One final proposed model authority and active entry/supersession map; historical content labelled with links, no current generated edits.

Disposition/evidence boundary: Plan2 exports consolidated authoritative shared documents.

## F12 — Paper design review is not operational validation

Severity: medium. Location: All plans/convenience/certification claims.

Trigger/consequence: Green document audit, reportedCI or31 abstract checks presented as real payment/isolation/user proof.

Required resolution: Separate documentary/design/model/offline-component/real-account/isolation/live-site/user evidence; publish actual limits and open gates.

Disposition/evidence boundary: No timings, coverage%, security/production conformance invented.


## F13 — Non-Git intake still meets a Git-only publication path

Severity: high. Location: Plan3 DELIVERY_AUTOMATION_AND_AUTHORITY / LIFECYCLE_INTERFACE_PROPOSALS.

Trigger/consequence: a valid local/cloud/host source has no source_head/base/PR, but the selected downstream recipe assumes GitHub publish/merge. Forcing GitHub or asking the merchant to deploy breaks the stable flexible-source journey.

Required resolution: distinguish Git-backed protected publication from direct approved immutable-artifact publication. Direct route needs merchant-owned registry/source destination, independently granted destination writes and full trigger inspection before registry/object writes; original source/local disk stays read-only/unmodified. Optional Git revision/PR fields are nullable and validated only on Git route. No public registry/source upload or mandatory Git migration.

Disposition: paper correction applied: direct_artifact route, route-aware approval/state/schema/slices, merchant-owned private source/registry custody and LC33. Actual destination/trigger/pull/runtime qualification remains open.
