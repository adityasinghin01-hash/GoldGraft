# Future lifecycle implementation slices

Status: Plan3 engineering on paper, 6 November 2026. No implementation, account change, deployment, live payment/model/worker job or agent-internal design. CURRENT means inspected existing contract; all new lifecycle states/interfaces/modules below are PROPOSED. Vendor/account/runtime qualification gates remain open.

No source/fixtures/tests below are implemented now. Proposed paths are ownership targets requiring Plan2 current-code reconciliation (especially existing proof PR); never overwrite working contributions or import another piece. Each slice starts with fixtures/stand-ins and meaningful failures before implementation, then targeted conformance and separately authorised live qualification. No package installs/jobs here.

## L01 — Contract/bootstrap and effect state

Dependency: Plan1 canonical shapes.

Proposed files: contracts/src/goldgraft_contracts/lifecycle.py; contracts/src/goldgraft_contracts/api_routes.py; docs/FORMAT_CHANGES.md.

Fixtures/checks: fixtures/lifecycle/; fakes/src/goldgraft_fakes/lifecycle.py; plugtests/test_lifecycle_contracts.py. Acceptance: LC01 LC12 LC32.

Boundary: consume/produce LIFECYCLE_INTERFACE_PROPOSALS.md formats; current contracts reused only where semantically accurate. Record actor/resource/scope/generation and input/output digests; deny missing/unknown authority/evidence.

Owner proposal: Singh shared formats; all consume.

Validation: offline unit/contract/fault checks with exact fixtures, then actual component conformance; live_ scripts explicit opt-in/disposable scope only. Acceptance state/evidence defined per case, not “tests for implementation”.

Safe implementation undo: feature route off preserves accepted/effect/financial records; forward corrective migration, no destructive DB rollback with new money/data, no deleting merchant runtime/secrets.

## L02 — Baseline/candidate workspace boundaries

Dependency: L01 + qualified Plan1 runtime.

Proposed files: pieces/runner/baseline.py; pieces/runner/workspaces.py; pieces/backend/lifecycle/requests.py.

Fixtures/checks: pieces/runner/tests/test_baseline.py; fixtures/lifecycle/baseline/. Acceptance: LC01 LC02 LC03 LC04.

Boundary: consume/produce LIFECYCLE_INTERFACE_PROPOSALS.md formats; current contracts reused only where semantically accurate. Record actor/resource/scope/generation and input/output digests; deny missing/unknown authority/evidence.

Owner proposal: Gupta mechanisms; Vijay runtime/scenario recipes.

Validation: offline unit/contract/fault checks with exact fixtures, then actual component conformance; live_ scripts explicit opt-in/disposable scope only. Acceptance state/evidence defined per case, not “tests for implementation”.

Safe implementation undo: feature route off preserves accepted/effect/financial records; forward corrective migration, no destructive DB rollback with new money/data, no deleting merchant runtime/secrets.

## L03 — Validated domain/proof/review evidence

Dependency: L02.

Proposed files: pieces/proof/evidence.py; pieces/proof/proof.py; pieces/backend/lifecycle/review.py.

Fixtures/checks: plugtests/test_lifecycle_evidence.py; fixtures/lifecycle/review/. Acceptance: LC03 LC05 LC06 LC07 LC08 LC32.

Boundary: consume/produce LIFECYCLE_INTERFACE_PROPOSALS.md formats; current contracts reused only where semantically accurate. Record actor/resource/scope/generation and input/output digests; deny missing/unknown authority/evidence.

Owner proposal: Singhal adapt existing proof; Gupta private projection; Singh UI.

Validation: offline unit/contract/fault checks with exact fixtures, then actual component conformance; live_ scripts explicit opt-in/disposable scope only. Acceptance state/evidence defined per case, not “tests for implementation”.

Safe implementation undo: feature route off preserves accepted/effect/financial records; forward corrective migration, no destructive DB rollback with new money/data, no deleting merchant runtime/secrets.

## L04 — Current controller approval and mutation intents

Dependency: L01 L03.

Proposed files: pieces/backend/lifecycle/approvals.py; pieces/backend/lifecycle/effects.py.

Fixtures/checks: pieces/backend/tests/test_apply_races.py. Acceptance: LC09 LC11 LC12 LC13 LC16 LC27.

Boundary: consume/produce LIFECYCLE_INTERFACE_PROPOSALS.md formats; current contracts reused only where semantically accurate. Record actor/resource/scope/generation and input/output digests; deny missing/unknown authority/evidence.

Owner proposal: Gupta; Singh approval UI/shared policy.

Validation: offline unit/contract/fault checks with exact fixtures, then actual component conformance; live_ scripts explicit opt-in/disposable scope only. Acceptance state/evidence defined per case, not “tests for implementation”.

Safe implementation undo: feature route off preserves accepted/effect/financial records; forward corrective migration, no destructive DB rollback with new money/data, no deleting merchant runtime/secrets.

## L05 — Qualified publisher/protected apply adapter

Dependency: L04 + provider permission/trigger qualification.

Proposed files: pieces/backend/providers/github_publisher.py; pieces/backend/lifecycle/trigger_checks.py.

Fixtures/checks: scripts/live_lifecycle_publish.py; fixtures/lifecycle/triggers/. Acceptance: LC10 LC11 LC12.

Boundary: consume/produce LIFECYCLE_INTERFACE_PROPOSALS.md formats; current contracts reused only where semantically accurate. Record actor/resource/scope/generation and input/output digests; deny missing/unknown authority/evidence.

Owner proposal: Gupta trusted actions; Singh integration.

Validation: offline unit/contract/fault checks with exact fixtures, then actual component conformance; live_ scripts explicit opt-in/disposable scope only. Acceptance state/evidence defined per case, not “tests for implementation”.

Safe implementation undo: feature route off preserves accepted/effect/financial records; forward corrective migration, no destructive DB rollback with new money/data, no deleting merchant runtime/secrets.

## L06 — Persistent state/callback/origin plan

Dependency: L02 L04 + domain/state evidence.

Proposed files: pieces/shops/<reference>/delivery_manifest.yaml; pieces/switch-libs/php/origin_routes.php; pieces/backend/lifecycle/state_plan.py.

Fixtures/checks: fixtures/lifecycle/state/; plugtests/test_lifecycle_state.py. Acceptance: LC18 LC19 LC20 LC22 LC30.

Boundary: consume/produce LIFECYCLE_INTERFACE_PROPOSALS.md formats; current contracts reused only where semantically accurate. Record actor/resource/scope/generation and input/output digests; deny missing/unknown authority/evidence.

Owner proposal: Vijay shop logic/fixtures; Gupta service state adapter; Singhal checks.

Validation: offline unit/contract/fault checks with exact fixtures, then actual component conformance; live_ scripts explicit opt-in/disposable scope only. Acceptance state/evidence defined per case, not “tests for implementation”.

Safe implementation undo: feature route off preserves accepted/effect/financial records; forward corrective migration, no destructive DB rollback with new money/data, no deleting merchant runtime/secrets.

## L07 — Render exact-artifact deploy/observe

Dependency: L04 L05 L06 + host qualification.

Proposed files: pieces/backend/providers/render_deploy.py; pieces/backend/lifecycle/observations.py.

Fixtures/checks: scripts/live_lifecycle_render.py; fixtures/lifecycle/deploys/. Acceptance: LC13 LC14 LC15 LC20 LC27 LC29.

Boundary: consume/produce LIFECYCLE_INTERFACE_PROPOSALS.md formats; current contracts reused only where semantically accurate. Record actor/resource/scope/generation and input/output digests; deny missing/unknown authority/evidence.

Owner proposal: Gupta; Vijay runtime recipes; Singh status.

Validation: offline unit/contract/fault checks with exact fixtures, then actual component conformance; live_ scripts explicit opt-in/disposable scope only. Acceptance state/evidence defined per case, not “tests for implementation”.

Safe implementation undo: feature route off preserves accepted/effect/financial records; forward corrective migration, no destructive DB rollback with new money/data, no deleting merchant runtime/secrets.

## L08 — Recovery and stop reconciliation

Dependency: L04 L06 L07.

Proposed files: pieces/backend/lifecycle/recovery.py; pieces/backend/lifecycle/reconcile.py.

Fixtures/checks: plugtests/test_lifecycle_recovery.py; fixtures/lifecycle/effect_races/. Acceptance: LC16 LC17 LC18 LC19 LC21 LC28 LC30.

Boundary: consume/produce LIFECYCLE_INTERFACE_PROPOSALS.md formats; current contracts reused only where semantically accurate. Record actor/resource/scope/generation and input/output digests; deny missing/unknown authority/evidence.

Owner proposal: Gupta current effects; Vijay safe domain routes; Singhal evidence checks.

Validation: offline unit/contract/fault checks with exact fixtures, then actual component conformance; live_ scripts explicit opt-in/disposable scope only. Acceptance state/evidence defined per case, not “tests for implementation”.

Safe implementation undo: feature route off preserves accepted/effect/financial records; forward corrective migration, no destructive DB rollback with new money/data, no deleting merchant runtime/secrets.

## L09 — Merchant-owned steady state and exit

Dependency: L07 L08.

Proposed files: pieces/shops/<reference>/finalisation_recipe.yaml; pieces/backend/lifecycle/exit.py.

Fixtures/checks: plugtests/test_lifecycle_exit.py; scripts/live_lifecycle_exit.py. Acceptance: LC22 LC23 LC24 LC25 LC26.

Boundary: consume/produce LIFECYCLE_INTERFACE_PROPOSALS.md formats; current contracts reused only where semantically accurate. Record actor/resource/scope/generation and input/output digests; deny missing/unknown authority/evidence.

Owner proposal: Vijay final runtime/legacy fixture; Gupta cleanup/mechanisms.

Validation: offline unit/contract/fault checks with exact fixtures, then actual component conformance; live_ scripts explicit opt-in/disposable scope only. Acceptance state/evidence defined per case, not “tests for implementation”.

Safe implementation undo: feature route off preserves accepted/effect/financial records; forward corrective migration, no destructive DB rollback with new money/data, no deleting merchant runtime/secrets.

## L10 — End-to-end case/review/handover experience

Dependency: L03–L09 interfaces; stand-ins first.

Proposed files: pieces/web/src/lifecycle/; pieces/agents/<external boundary adapter>.

Fixtures/checks: pieces/web/e2e/lifecycle.spec.ts; plugtests/test_lifecycle_integration.py. Acceptance: LC08 LC16 LC25 LC26 LC27 LC28 LC31.

Boundary: consume/produce LIFECYCLE_INTERFACE_PROPOSALS.md formats; current contracts reused only where semantically accurate. Record actor/resource/scope/generation and input/output digests; deny missing/unknown authority/evidence.

Owner proposal: Singh; internal agent design deferred to own Plan5.

Validation: offline unit/contract/fault checks with exact fixtures, then actual component conformance; live_ scripts explicit opt-in/disposable scope only. Acceptance state/evidence defined per case, not “tests for implementation”.

Safe implementation undo: feature route off preserves accepted/effect/financial records; forward corrective migration, no destructive DB rollback with new money/data, no deleting merchant runtime/secrets.

## Route-aware delta from Plan4
L01 adds delivery_route and nullable Git-only fields; L05/L07 implement either protected Git provider or direct_artifact registry/private source bundle publisher plus exact-digest deploy, never mandatory GitHub for non-Git sources. New proposed backend/provider files include artifact_publisher.py and source_bundle_destination.py; actual registry provider endpoint/capability must be selected/qualified by the merchant environment, missing destination is explicit setup hold. Input source grants remain read-only; destination writes separate. Trigger checks cover Git AND registry/object automation. No product implementation now.

## Independent-review implementation deltas
L01 defines TargetReservation/StateCutover/ArtifactBuild/ApplyAuthority/ActionPlan/ApprovalSet/ExitCheckPlan proposals and their typed fixtures. L02/L03 tests exact exported OCI candidate image with trusted outside-guest build attestation. L04 adds target-key sorted reservations and per-slot approval-set consumption, not only run locks. L05 includes separate artifact publisher. L06 implements complete first-bootstrap writer/drain/fence/export/high-water/replay protocol; lack of pre-existing safe export/handler is admission hold. L09 requires a prequalified merchant-owned bounded exit executor and separate evidence-read revocation, no use of removed service grants. Added negative cases LC34–LC39. Gupta owns mechanism; Vijay state/domain/executor recipes; Singhal evidence sufficiency; Singh contracts/UX/integration.
