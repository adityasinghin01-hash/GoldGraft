# Shared START guide — Aditya Vijay

Reviewed planning update, 6 November 2026. First complete shop/runtime/payment/state/notification/finalisation/exit domain recipes and qualified evidence.

Read [engineering baseline](engineering/START_HERE.md), [current versus proposed](engineering/CURRENT_VS_PROPOSED.md), [all-four deltas](engineering/work/TEAM_WORK_DELTA.md), [dependencies](engineering/work/SHARED_INTERFACES_AND_DEPENDENCIES.md) and [completion evidence](engineering/work/DONE_AND_TEST_MATRIX.md) first. These are documented work packages, not a claim of implementation, task delivery or messages sent.

Inspect your actual branch/local contribution before changing it; preserve valid work. The inspected main cannot show unpushed work. Singh owns new shared contract/fixture/fake bootstrap. Existing unchanged boundaries may continue independently; new boundaries require approved versions and fixtures. All pieces exchange contracts/foundation only.

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


## Existing offline regression commands — future execution only

These commands reference existing plugtests and proposed real implementations. They were not run during this docs update. Passing them is one compatibility check, not live account/isolation/payment/working-site proof.

```bash
uv run pytest plugtests/test_shops.py
uv run pytest plugtests/test_switch_libs.py
```

Use the AC/LC cases attached to each package to add meaningful actual component and boundary failure checks after implementation starts. Any real account/live check is separately scoped and marked `live_`; ordinary tests stay offline. Do not install/provision/change accounts or run live jobs because a guide describes future work. No commit/push/merge by an agent. Personal READMEs/reference and generated files remain protected until an expressly authorised shared-format implementation.
