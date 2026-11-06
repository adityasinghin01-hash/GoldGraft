# Per-person work packages

Reviewed planning targets only; no source modules or tests created/run. These are deltas to inspect/implement, not proof all work missing or complete. Current contract support and actual contribution versions must be checked before changes. All four exchange shared contracts/foundation only; no other-piece code imports.

## SI01 — Singh: Shared contract/fixture/fake bootstrap

Keep/adapt/add: inspect existing contribution, preserve correct code and add only verified gap.

Proposed paths: contracts/src/goldgraft_contracts/{connection_control,connector_adapters,work_package,lifecycle}.py; registry/api route data; existing exporters.

Consumes: Current Python wire authority + final proposed Plan1/3/4 definitions.

Produces: Versioned exact new model/API/schema/TS/examples/fixtures/fakes and legacy-bypass policy.

Dependencies: No upstream product dependency; obtain explicit shared implementation scope in Plan5.

Acceptance IDs: AC31 AC45 AC46 LC32 LC35 LC38. Completion evidence: No invented current fields; all strict validation/compatibility negatives pass; generated checks appropriate in actual implementation, not Plan2.

Tests: named component unit/contract/negative fixtures with own actual component, then real counterpart boundary and separately authorised external qualification; mocks/real/source-inspected evidence labelled. Failure outcome: preserve current merchant assets/effects, deny affected action and give exact missing prerequisite/owner. No release claim from stand-in success.

## SI02 — Singh: Saved-case and variable source/host experience

Keep/adapt/add: inspect existing contribution, preserve correct code and add only verified gap.

Proposed paths: pieces/web/src/connection/.

Consumes: Case/identity/provider-intent/graph/readiness/upload/status API contracts; fakes.

Produces: One workspace, owner/controller handoff, source choices/complete required context and clear missing/unknown recovery.

Dependencies: SI01 for new shapes; GU01/GU02 real hookup later.

Acceptance IDs: AC01 AC02 AC03 AC04 AC33 AC35 AC36 AC37 AC38 AC40. Completion evidence: Actual own UI against mocks with labels then real boundary checks; keyboard/error/profile-return/reselection flows; no fake Started or secret storage.

Tests: named component unit/contract/negative fixtures with own actual component, then real counterpart boundary and separately authorised external qualification; mocks/real/source-inspected evidence labelled. Failure outcome: preserve current merchant assets/effects, deny affected action and give exact missing prerequisite/owner. No release claim from stand-in success.

## SI03 — Singh: Start/operation/review/apply/handover UI

Keep/adapt/add: inspect existing contribution, preserve correct code and add only verified gap.

Proposed paths: pieces/web/src/lifecycle/.

Consumes: Immutable receipt/current WorkStatus, proof/private projection, current controller action plans.

Produces: Truthful queued/claim/operation/reproduced/validated/published/deploy/live/exit status; exact review/approval and unavoidable provider actions.

Dependencies: SI01; GU03/GU05; SH02/03 evidence.

Acceptance IDs: AC22 AC25 AC26 AC27 AC29 LC08 LC16 LC26 LC27 LC38 LC39. Completion evidence: No confirmation-per-check; no source/model/host credentials; no PR/sandbox-as-Done; replay and revoked-role denial.

Tests: named component unit/contract/negative fixtures with own actual component, then real counterpart boundary and separately authorised external qualification; mocks/real/source-inspected evidence labelled. Failure outcome: preserve current merchant assets/effects, deny affected action and give exact missing prerequisite/owner. No release claim from stand-in success.

## SI04 — Singh: Own agent implementation and external boundary tests

Keep/adapt/add: inspect existing contribution, preserve correct code and add only verified gap.

Proposed paths: pieces/agents/.

Consumes: Approved WorkPackage/LifecycleWorkRequest and typed tool/broker contracts.

Produces: Actual component outputs/evidence under scope, handles blocked/unknown/failed/retry/Stop.

Dependencies: Only explicitly started Plan5; do not preselect internal prompts/topology now.

Acceptance IDs: AC16 AC18 AC19 LC02 LC05 LC06. Completion evidence: Untrusted content cannot expand authority; real own code tested against approved stand-ins then qualified mechanisms, no cross-piece imports.

Tests: named component unit/contract/negative fixtures with own actual component, then real counterpart boundary and separately authorised external qualification; mocks/real/source-inspected evidence labelled. Failure outcome: preserve current merchant assets/effects, deny affected action and give exact missing prerequisite/owner. No release claim from stand-in success.

## GU01 — Gupta: Identity/current resource authority/read-provider adapters

Keep/adapt/add: inspect existing contribution, preserve correct code and add only verified gap.

Proposed paths: pieces/backend/connection/{cases,authority,providers,resource_graph}.py.

Consumes: SI01 contracts, WorkOS/GitHub/Render actual identities/grants.

Produces: Server-side same-case memberships/controller bindings/private projections/resource observations.

Dependencies: Keep inspected existing service code; new routes wait SI01; real accounts/controllers external.

Acceptance IDs: AC03 AC04 AC05 AC06 AC07 AC08 AC09 AC10 AC36. Completion evidence: Email/invite/key possession not ownership; selected resource vs actual workspace scope disclosed; no classic/writable Reader fallback.

Tests: named component unit/contract/negative fixtures with own actual component, then real counterpart boundary and separately authorised external qualification; mocks/real/source-inspected evidence labelled. Failure outcome: preserve current merchant assets/effects, deny affected action and give exact missing prerequisite/owner. No release claim from stand-in success.

## GU02 — Gupta: Trusted source/custody/model/dependency/payment brokers

Keep/adapt/add: inspect existing contribution, preserve correct code and add only verified gap.

Proposed paths: pieces/backend/connection/{acquisition,custody,upload_sessions,readiness}.py; brokers/.

Consumes: Snapshot/graph/policy refs, tenant/case authority and vendor qualified profiles.

Produces: Complete bounded quarantine/safe manifests, typed narrow capabilities/current checks.

Dependencies: SI01; VJ01/02 shop recipe; account processing/region/isolation gates.

Acceptance IDs: AC11 AC12 AC13 AC16 AC17 AC18 AC19 AC20 AC30 AC37 AC38 AC39 AC41 LC01. Completion evidence: No model/execution/payment before Start; no guest tokens/live/private-network access; effective cloud write/create/share denial; terms and source omissions hold.

Tests: named component unit/contract/negative fixtures with own actual component, then real counterpart boundary and separately authorised external qualification; mocks/real/source-inspected evidence labelled. Failure outcome: preserve current merchant assets/effects, deny affected action and give exact missing prerequisite/owner. No release claim from stand-in success.

## GU03 — Gupta: Durable Start/cancel/runtime/recorder

Keep/adapt/add: inspect existing contribution, preserve correct code and add only verified gap.

Proposed paths: pieces/backend/connection/{acceptance,cancellation}.py; pieces/runner/.

Consumes: ActionIntent/WorkPackage and fixed runtime policy; current JobSpec only where fits.

Produces: Outbox/current generation, immutable acceptance/current status, authenticated actual operation/capture/termination records.

Dependencies: SI01; VJ01 runtime/scenarios; preserve recorder/runner contribution after inspection.

Acceptance IDs: AC21 AC22 AC23 AC24 AC25 AC26 AC27 AC28 AC43 AC46 LC02 LC04 LC06 LC16. Completion evidence: Crash/retry/concurrency/Stop-before-accept/stale worker/real supervisor checks; claim not Started, timeout not terminated.

Tests: named component unit/contract/negative fixtures with own actual component, then real counterpart boundary and separately authorised external qualification; mocks/real/source-inspected evidence labelled. Failure outcome: preserve current merchant assets/effects, deny affected action and give exact missing prerequisite/owner. No release claim from stand-in success.

## GU04 — Gupta: Exact artifact build/publish and resource-authorised apply

Keep/adapt/add: inspect existing contribution, preserve correct code and add only verified gap.

Proposed paths: pieces/runner/artifact_build.py; pieces/backend/lifecycle/{reservations,approvals,effects}.py; providers/{github_publisher,artifact_publisher,render_deploy}.py.

Consumes: ActionPlan/ApplyAuthority/ApprovalSet/ArtifactBuild and target graph/controller sets.

Produces: Exact tested OCI image+private source provenance, reserved effect slots, protectedGit or DirectArtifact delivery receipts/current observations.

Dependencies: SI01; SH01/02 proof; VJ01/03; actual registry/host/protection qualification.

Acceptance IDs: AC32 LC09 LC10 LC11 LC12 LC13 LC14 LC15 LC33 LC35 LC36 LC38. Completion evidence: Target locks across cases, unique effect slots/unknown reconciliation, no initial read→write escalation, no hidden Git migration/public source upload.

Tests: named component unit/contract/negative fixtures with own actual component, then real counterpart boundary and separately authorised external qualification; mocks/real/source-inspected evidence labelled. Failure outcome: preserve current merchant assets/effects, deny affected action and give exact missing prerequisite/owner. No release claim from stand-in success.

## GU05 — Gupta: State migration/recovery/independent exit mechanisms

Keep/adapt/add: inspect existing contribution, preserve correct code and add only verified gap.

Proposed paths: pieces/backend/lifecycle/{state_plan,reconcile,recovery,exit}.py.

Consumes: StateCutover/ExitCheckPlan/origin ledger, merchant runtime/controller authority.

Produces: Safe first-bootstrap export/fence/H/replay; immutable effects; independent executor/revocation/cleanup observations.

Dependencies: GU04; VJ03/04/05; SH02/03; live export/handler/registry/exit primitives must qualify.

Acceptance IDs: AC44 LC17 LC18 LC19 LC20 LC21 LC22 LC23 LC24 LC25 LC26 LC28 LC30 LC34 LC35 LC37 LC39. Completion evidence: No first disk-redeploy data loss, no oldDB financial undo, no own revoked keys for restart, no shared-resource cleanup under other cases.

Tests: named component unit/contract/negative fixtures with own actual component, then real counterpart boundary and separately authorised external qualification; mocks/real/source-inspected evidence labelled. Failure outcome: preserve current merchant assets/effects, deny affected action and give exact missing prerequisite/owner. No release claim from stand-in success.

## SH01 — Singhal: Inspect/reuse existing deterministic proof

Keep/adapt/add: inspect existing contribution, preserve correct code and add only verified gap.

Proposed paths: pieces/proof/ PR1; existing plugtests/test_proof*.py.

Consumes: Existing mapper/judge/posterior/mutation/certificate/evidence helpers and synthetic index.

Produces: Evidence-backed keep/adapt gap report and unchanged APIs where sufficient.

Dependencies: PR1 inspect/review not auto merge; SI01 for changed wire; no rewrite of existing maths.

Acceptance IDs: LC03 LC04 LC05 LC07 LC31. Completion evidence: Preserve normative-rule precedence/old defects; no score-only/fixture-only/live safety claim; reported tests not rerun by planning.

Tests: named component unit/contract/negative fixtures with own actual component, then real counterpart boundary and separately authorised external qualification; mocks/real/source-inspected evidence labelled. Failure outcome: preserve current merchant assets/effects, deny affected action and give exact missing prerequisite/owner. No release claim from stand-in success.

## SH02 — Singhal: Bind evidence completeness and exact tested subject

Keep/adapt/add: inspect existing contribution, preserve correct code and add only verified gap.

Proposed paths: pieces/proof/evidence.py; proposed lifecycle_evidence.py.

Consumes: Baseline/candidate exact image/package/config/domain/runtime/origin/fence results.

Produces: Deterministic ready/partial/hold decisions with required evidence/flow exclusions and missing reason.

Dependencies: SI01; GU03/GU04 recorders; VJ02/03 fixtures.

Acceptance IDs: LC01 LC03 LC04 LC06 LC07 LC17 LC18 LC22 LC32 LC36. Completion evidence: Wrong/missing image/scope/generation, unsupported paths, unknown provider read and old-origin mismatch cannot certify full outcome.

Tests: named component unit/contract/negative fixtures with own actual component, then real counterpart boundary and separately authorised external qualification; mocks/real/source-inspected evidence labelled. Failure outcome: preserve current merchant assets/effects, deny affected action and give exact missing prerequisite/owner. No release claim from stand-in success.

## SH03 — Singhal: Private review/public-safe projection and lifecycle negatives

Keep/adapt/add: inspect existing contribution, preserve correct code and add only verified gap.

Proposed paths: pieces/proof/certificate.py; proposed review_projection.py; plugtests/test_lifecycle_evidence.py.

Consumes: Current cert and new private ReviewBundle/StateCutover/ExitCheck evidence.

Produces: Scoped private report/public projection proposal and strong regression/unknown/tamper/privacy cases.

Dependencies: SI01; GU05 actual evidence; Singh recipient/UI integration.

Acceptance IDs: LC08 LC20 LC21 LC23 LC25 LC26 LC32 LC34 LC39. Completion evidence: No fake Git/workflow fields for local/E2B, no private capture/customer/transaction details public, signature not behavioural/operational proof.

Tests: named component unit/contract/negative fixtures with own actual component, then real counterpart boundary and separately authorised external qualification; mocks/real/source-inspected evidence labelled. Failure outcome: preserve current merchant assets/effects, deny affected action and give exact missing prerequisite/owner. No release claim from stand-in success.

## VJ01 — Vijay: Qualify first complete reference package/runtime

Keep/adapt/add: inspect existing contribution, preserve correct code and add only verified gap.

Proposed paths: pieces/shops/<reference>/manifest/recipes; existing licensed fixture.

Consumes: Pinned PHP source + full component/build/dependency/config/state/callback inventory.

Produces: Complete supported-scope ShopPack/WorkPackage fixture and qualified original/candidate runtime recipe.

Dependencies: Inspect actual existing work; SI01 schema for new evidence; no forced all11 shops.

Acceptance IDs: AC13 AC14 AC15 AC34 AC40 AC41 AC42 LC01 LC04 LC20. Completion evidence: No unauthenticated helper exposure, missing backend/private dep or mutable source/state disguised as complete; licenses/source revisions recorded.

Tests: named component unit/contract/negative fixtures with own actual component, then real counterpart boundary and separately authorised external qualification; mocks/real/source-inspected evidence labelled. Failure outcome: preserve current merchant assets/effects, deny affected action and give exact missing prerequisite/owner. No release claim from stand-in success.

## VJ02 — Vijay: Genuine sandbox flow/capture/domain evidence

Keep/adapt/add: inspect existing contribution, preserve correct code and add only verified gap.

Proposed paths: pieces/shops/<reference>/scenarios; scripts/live_<qualified_sandbox_checks>.py.

Consumes: Approved sandbox identities/broker/recorder, full required one-time flow inventory.

Produces: Actual when-authorised old/oldTwin/new captures plus expected semantics and honest unavailable paths.

Dependencies: GU02/GU03; SH01 mapping; account/test authority required.

Acceptance IDs: AC19 LC03 LC04 LC17 LC18 LC19 LC22 LC29 LC30. Completion evidence: No fabricated PayPal shapes/auth or universal refunds/subscription assumptions; API-specific idempotency/pending/raw-IPN/business checks; no production transactions by implication.

Tests: named component unit/contract/negative fixtures with own actual component, then real counterpart boundary and separately authorised external qualification; mocks/real/source-inspected evidence labelled. Failure outcome: preserve current merchant assets/effects, deny affected action and give exact missing prerequisite/owner. No release claim from stand-in success.

## VJ03 — Vijay: State/notification/origin bootstrap and persistence recipes

Keep/adapt/add: inspect existing contribution, preserve correct code and add only verified gap.

Proposed paths: pieces/shops/<reference>/state_recipe; pieces/switch-libs/php/origin_routes.php.

Consumes: Current complete writer/handler inventory, safe export/admin control and durable callback/state recipes.

Produces: Consistent export/drain/fence/high-water/replay expectations and domain fixtures for first prerequisite mutation/cutover.

Dependencies: GU05 mechanism; existing runtime/export primitive required or admission hold.

Acceptance IDs: LC18 LC19 LC20 LC21 LC22 LC30 LC34 LC37. Completion evidence: Queue alone not browser handler; no concurrent flat-file writers, lost ephemeral orders or paid-event replay; no migrate via predeploy disk assumption.

Tests: named component unit/contract/negative fixtures with own actual component, then real counterpart boundary and separately authorised external qualification; mocks/real/source-inspected evidence labelled. Failure outcome: preserve current merchant assets/effects, deny affected action and give exact missing prerequisite/owner. No release claim from stand-in success.

## VJ04 — Vijay: Final runtime independent of temporary GoldGraft

Keep/adapt/add: inspect existing contribution, preserve correct code and add only verified gap.

Proposed paths: pieces/shops/<reference>/finalisation_recipe; pieces/switch-libs/.

Consumes: Qualified upgrade result and legacy transaction/API/callback obligations.

Produces: Merchant-owned steady state, retained origin routes and persistent domain/state/credential/registry dependencies.

Dependencies: GU04/05 deploy+exit; SH02 evidence.

Acceptance IDs: AC44 LC21 LC22 LC23 LC24 LC26 LC30. Completion evidence: Switch expiry cannot revert whole shop or kill callbacks; no premature old/refund/subscription removal; postrestart state preserved.

Tests: named component unit/contract/negative fixtures with own actual component, then real counterpart boundary and separately authorised external qualification; mocks/real/source-inspected evidence labelled. Failure outcome: preserve current merchant assets/effects, deny affected action and give exact missing prerequisite/owner. No release claim from stand-in success.

## VJ05 — Vijay: Independent exit-check domain recipe

Keep/adapt/add: inspect existing contribution, preserve correct code and add only verified gap.

Proposed paths: pieces/shops/<reference>/exit_check_recipe.

Consumes: Prequalified merchant-account executor/current explicit controller action plan.

Produces: Expected public/private continuity/restart/recovery criteria and redacted signed result fixtures.

Dependencies: GU05 executor/mechanism; merchant job/workflow must preexist/be separately approved, no Workflows escalation.

Acceptance IDs: LC24 LC25 LC26 LC39. Completion evidence: No hidden merchant restart/debug scripts; no revoked GoldGraft capability reuse; unavailable executor blocks exit qualification.

Tests: named component unit/contract/negative fixtures with own actual component, then real counterpart boundary and separately authorised external qualification; mocks/real/source-inspected evidence labelled. Failure outcome: preserve current merchant assets/effects, deny affected action and give exact missing prerequisite/owner. No release claim from stand-in success.
