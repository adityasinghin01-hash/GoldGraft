> Reviewed team baseline, 6 November 2026: this connection proposal is subject to the review addendum, implementation bridge and lifecycle atomic protocols linked from [engineering START](../START_HERE.md). Earlier programme status/owner restrictions in this frozen source are historical. No current API/implemented capability is created by this text.

# Future implementation slices

Status: paper engineering specification, 6 November 2026. Nothing here is a deployed feature or current API unless explicitly labelled CURRENT. Proposed components/interfaces require later implementation and contract approval. Plan 1 ends at verified first sandbox operation; agent internals and Plans 2–6 remain outside scope.

Implementation has NOT started. New work is proposed for Singh; Singhal can independently review evidence/fixtures. No Gupta/Vijay work assigned. Exact paths below are proposed; current repo guidance must explicitly admit new connector piece in the same approved integration change. Each slice imports only contracts/foundation, never other pieces.

## S01 — Shared contract and safe compatibility

Dependency: None.

Proposed source files: `contracts/src/goldgraft_contracts/connection_control.py`, `contracts/src/goldgraft_contracts/connection_routes.py`, `contracts/src/goldgraft_contracts/registry.py`, `docs/FORMAT_CHANGES.md`.

Fixtures/tests: `fixtures/connection_control/`, `fakes/src/goldgraft_fakes/connection_control.py`, `plugtests/test_connection_contracts.py`.

Consumes/produces: New formats/proposed v2 routes; legacy route protection policy. Exact proposed shapes are in INTERFACE_CHANGE_PROPOSALS.md; current shapes must not be widened silently.

Build order: first add named synthetic cases/stand-in; demonstrate their specified denial/failure on missing boundary; implement the minimal boundary; run targeted offline checks; qualify live component separately when authorised.

Meaningful acceptance: AC31. Generate schemas/OpenAPI/TS through existing exporters, check generated diff; validate all new positive/negative examples offline. Expected extra fields/unknown versions rejected and old API not silently widened.

Verification command pattern (future, no installs implicit): `uv run pytest <the named .py tests>` with network disabled; frontend uses the then-approved package test command on named files. live_ scripts remain separate opt-in; credentials never in args/logs. Exact package pins and image digests are captured during authorised build/qualification, never fabricated here.

Failure/undo of implementation: disable the new feature route, preserve accepted action/receipt/audit rows and schema compatibility; roll forward with corrective migration if data exists. Never destructive database downgrade/drop, revive revoked grants or delete working merchant payment configuration. Empty migrations can be reverted only on disposable local DB with no accepted data.

Review gate: outputs validate through contracts, named negative cases pass and operational limits remain visible. Stand-in success is labelled simulated.

## S02 — Saved case/session/controller relation

Dependency: S01.

Proposed source files: `pieces/connector/api.py`, `pieces/connector/sessions.py`, `pieces/connector/cases.py`, `pieces/connector/authority.py`, `pieces/connector/storage.py`, `pieces/connector/migrations/001_connection.sql`.

Fixtures/tests: `pieces/connector/tests/test_authority.py`, `plugtests/test_connection_cases.py`.

Consumes/produces: ConnectionCase/ControllerBinding and WorkOS/provider stand-ins. Exact proposed shapes are in INTERFACE_CHANGE_PROPOSALS.md; current shapes must not be widened silently.

Build order: first add named synthetic cases/stand-in; demonstrate their specified denial/failure on missing boundary; implement the minimal boundary; run targeted offline checks; qualify live component separately when authorised.

Meaningful acceptance: AC02 AC03 AC04 AC05 AC06. Run offline actor/action/resource and continuation races; assert no private disclosure while pending. Real login separately qualifies WorkOS account and provider redirects.

Verification command pattern (future, no installs implicit): `uv run pytest <the named .py tests>` with network disabled; frontend uses the then-approved package test command on named files. live_ scripts remain separate opt-in; credentials never in args/logs. Exact package pins and image digests are captured during authorised build/qualification, never fabricated here.

Failure/undo of implementation: disable the new feature route, preserve accepted action/receipt/audit rows and schema compatibility; roll forward with corrective migration if data exists. Never destructive database downgrade/drop, revive revoked grants or delete working merchant payment configuration. Empty migrations can be reverted only on disposable local DB with no accepted data.

Review gate: outputs validate through contracts, named negative cases pass and operational limits remain visible. Stand-in success is labelled simulated.

## S03 — Source/host read and custody

Dependency: S02.

Proposed source files: `pieces/connector/providers/github_reader.py`, `pieces/connector/providers/render_reader.py`, `pieces/connector/acquisition.py`, `pieces/connector/custody.py`.

Fixtures/tests: `pieces/connector/tests/test_providers.py`, `pieces/connector/tests/test_acquisition.py`.

Consumes/produces: Resource/binding to sanitised manifest and private metadata projection. Exact proposed shapes are in INTERFACE_CHANGE_PROPOSALS.md; current shapes must not be widened silently.

Build order: first add named synthetic cases/stand-in; demonstrate their specified denial/failure on missing boundary; implement the minimal boundary; run targeted offline checks; qualify live component separately when authorised.

Meaningful acceptance: AC07 AC08 AC09 AC10 AC11 AC12 AC13. Offline provider fixtures/malicious archives/canary payload checks. Live denial/role checks only on separately authorised disposable provider resources. No classic Render key fallback.

Verification command pattern (future, no installs implicit): `uv run pytest <the named .py tests>` with network disabled; frontend uses the then-approved package test command on named files. live_ scripts remain separate opt-in; credentials never in args/logs. Exact package pins and image digests are captured during authorised build/qualification, never fabricated here.

Failure/undo of implementation: disable the new feature route, preserve accepted action/receipt/audit rows and schema compatibility; roll forward with corrective migration if data exists. Never destructive database downgrade/drop, revive revoked grants or delete working merchant payment configuration. Empty migrations can be reverted only on disposable local DB with no accepted data.

Review gate: outputs validate through contracts, named negative cases pass and operational limits remain visible. Stand-in success is labelled simulated.

## S04 — Source-runtime chain

Dependency: S03.

Proposed source files: `pieces/connector/correspondence.py`, `pieces/connector/provenance.py`.

Fixtures/tests: `fixtures/connection_control/correspondence/`, `pieces/connector/tests/test_correspondence.py`.

Consumes/produces: Provider read inputs + signed provenance + trusted runtime identity to correspondence evidence. Exact proposed shapes are in INTERFACE_CHANGE_PROPOSALS.md; current shapes must not be widened silently.

Build order: first add named synthetic cases/stand-in; demonstrate their specified denial/failure on missing boundary; implement the minimal boundary; run targeted offline checks; qualify live component separately when authorised.

Meaningful acceptance: AC14 AC15. Fail mutated digest/env/nonce/current-deploy cases; first hosted reference needs future qualified identity wrapper and signed image pipeline. Do not add instrumentation to a live shop during intake.

Verification command pattern (future, no installs implicit): `uv run pytest <the named .py tests>` with network disabled; frontend uses the then-approved package test command on named files. live_ scripts remain separate opt-in; credentials never in args/logs. Exact package pins and image digests are captured during authorised build/qualification, never fabricated here.

Failure/undo of implementation: disable the new feature route, preserve accepted action/receipt/audit rows and schema compatibility; roll forward with corrective migration if data exists. Never destructive database downgrade/drop, revive revoked grants or delete working merchant payment configuration. Empty migrations can be reverted only on disposable local DB with no accepted data.

Review gate: outputs validate through contracts, named negative cases pass and operational limits remain visible. Stand-in success is labelled simulated.

## S05 — Gateway/runtime/broker qualification

Dependency: S01, S03; parallel with S04.

Proposed source files: `pieces/connector/brokers/source.py`, `pieces/connector/brokers/dependency.py`, `pieces/connector/brokers/payment.py`, `pieces/connector/brokers/model.py`, `pieces/connector/brokers/evidence.py`, `pieces/connector/runtime_profile.py`.

Fixtures/tests: `pieces/connector/tests/test_brokers.py`, `scripts/live_connection_isolation.py`.

Consumes/produces: Capability-bound operations and qualified runtime/processor profile. Exact proposed shapes are in INTERFACE_CHANGE_PROPOSALS.md; current shapes must not be widened silently.

Build order: first add named synthetic cases/stand-in; demonstrate their specified denial/failure on missing boundary; implement the minimal boundary; run targeted offline checks; qualify live component separately when authorised.

Meaningful acceptance: AC17 AC18 AC19 AC30. Offline deny matrices first; separate real isolated egress/escape/auth-path tests. Missing region/ZDR/vendor terms/budget prevents qualification. Record credentials never in guest/model/artifacts.

Verification command pattern (future, no installs implicit): `uv run pytest <the named .py tests>` with network disabled; frontend uses the then-approved package test command on named files. live_ scripts remain separate opt-in; credentials never in args/logs. Exact package pins and image digests are captured during authorised build/qualification, never fabricated here.

Failure/undo of implementation: disable the new feature route, preserve accepted action/receipt/audit rows and schema compatibility; roll forward with corrective migration if data exists. Never destructive database downgrade/drop, revive revoked grants or delete working merchant payment configuration. Empty migrations can be reverted only on disposable local DB with no accepted data.

Review gate: outputs validate through contracts, named negative cases pass and operational limits remain visible. Stand-in success is labelled simulated.

## S06 — Static readiness

Dependency: S04, S05.

Proposed source files: `pieces/connector/readiness.py`, `pieces/connector/preflight.py`.

Fixtures/tests: `pieces/connector/tests/test_readiness.py`, `plugtests/test_connection_readiness.py`.

Consumes/produces: ConnectionReadiness binding current versions/checks to actor/scope. Exact proposed shapes are in INTERFACE_CHANGE_PROPOSALS.md; current shapes must not be widened silently.

Build order: first add named synthetic cases/stand-in; demonstrate their specified denial/failure on missing boundary; implement the minimal boundary; run targeted offline checks; qualify live component separately when authorised.

Meaningful acceptance: AC16 AC20 AC34. Instrument all side-effect call sites; assert zero pre-Start model/execution/payment/writes. Table-driven missing/unknown/stale coverage; changes invalidate dependent checks only.

Verification command pattern (future, no installs implicit): `uv run pytest <the named .py tests>` with network disabled; frontend uses the then-approved package test command on named files. live_ scripts remain separate opt-in; credentials never in args/logs. Exact package pins and image digests are captured during authorised build/qualification, never fabricated here.

Failure/undo of implementation: disable the new feature route, preserve accepted action/receipt/audit rows and schema compatibility; roll forward with corrective migration if data exists. Never destructive database downgrade/drop, revive revoked grants or delete working merchant payment configuration. Empty migrations can be reverted only on disposable local DB with no accepted data.

Review gate: outputs validate through contracts, named negative cases pass and operational limits remain visible. Stand-in success is labelled simulated.

## S07 — Durable Start/cancel/worker boundary

Dependency: S02, S06.

Proposed source files: `pieces/connector/acceptance.py`, `pieces/connector/cancellation.py`, `pieces/connector/dispatch.py`, `pieces/connector/worker_evidence.py`, `pieces/connector/adapters/runner_http.py`.

Fixtures/tests: `pieces/connector/tests/test_start_races.py`, `pieces/connector/tests/test_receipts.py`, `plugtests/test_connection_worker.py`.

Consumes/produces: WorkAcceptance/Cancellation/WorkerOperation, current Idempotency-Key and proposed authenticated runner bridge. Exact proposed shapes are in INTERFACE_CHANGE_PROPOSALS.md; current shapes must not be widened silently.

Build order: first add named synthetic cases/stand-in; demonstrate their specified denial/failure on missing boundary; implement the minimal boundary; run targeted offline checks; qualify live component separately when authorised.

Meaningful acceptance: AC21 AC22 AC23 AC24 AC25 AC26 AC27 AC28. Postgres concurrency/restart fault injection plus qualified isolated supervisor check. No agent internals. Outbox acceptance authority separate from downstream graft projection; bridge errors retain accepted/held state.

Verification command pattern (future, no installs implicit): `uv run pytest <the named .py tests>` with network disabled; frontend uses the then-approved package test command on named files. live_ scripts remain separate opt-in; credentials never in args/logs. Exact package pins and image digests are captured during authorised build/qualification, never fabricated here.

Failure/undo of implementation: disable the new feature route, preserve accepted action/receipt/audit rows and schema compatibility; roll forward with corrective migration if data exists. Never destructive database downgrade/drop, revive revoked grants or delete working merchant payment configuration. Empty migrations can be reverted only on disposable local DB with no accepted data.

Review gate: outputs validate through contracts, named negative cases pass and operational limits remain visible. Stand-in success is labelled simulated.

## S08 — Continuous browser case/status

Dependency: S02 for skeleton; S06/S07 for integration.

Proposed source files: `pieces/web/src/connection/CaseWorkspace.tsx`, `pieces/web/src/connection/api.ts`, `pieces/web/src/connection/copy.ts`, `pieces/web/src/connection/status.ts`.

Fixtures/tests: `pieces/web/src/connection/connection.spec.ts`, `pieces/web/e2e/live_connection.spec.ts`.

Consumes/produces: Private case/readiness/receipt/status and SSE replay. Exact proposed shapes are in INTERFACE_CHANGE_PROPOSALS.md; current shapes must not be widened silently.

Build order: first add named synthetic cases/stand-in; demonstrate their specified denial/failure on missing boundary; implement the minimal boundary; run targeted offline checks; qualify live component separately when authorised.

Meaningful acceptance: AC01 AC29 AC33. Route through existing client/SSE abstraction after frontend-spec reconciliation; mock banner mandatory for stand-ins. Keyboard/error/return tests and real provider flow observation separately. No imaginary real states.

Verification command pattern (future, no installs implicit): `uv run pytest <the named .py tests>` with network disabled; frontend uses the then-approved package test command on named files. live_ scripts remain separate opt-in; credentials never in args/logs. Exact package pins and image digests are captured during authorised build/qualification, never fabricated here.

Failure/undo of implementation: disable the new feature route, preserve accepted action/receipt/audit rows and schema compatibility; roll forward with corrective migration if data exists. Never destructive database downgrade/drop, revive revoked grants or delete working merchant payment configuration. Empty migrations can be reverted only on disposable local DB with no accepted data.

Review gate: outputs validate through contracts, named negative cases pass and operational limits remain visible. Stand-in success is labelled simulated.

## S09 — Integrated qualified reference

Dependency: S01–S08.

Proposed source files: `scripts/live_connection_reference.py`.

Fixtures/tests: `fixtures/connection_control/qualification/`, `plugtests/test_connection_integration.py`.

Consumes/produces: One real source/Render/controller/processing/runtime boundary trace through actual operation evidence. Exact proposed shapes are in INTERFACE_CHANGE_PROPOSALS.md; current shapes must not be widened silently.

Build order: first add named synthetic cases/stand-in; demonstrate their specified denial/failure on missing boundary; implement the minimal boundary; run targeted offline checks; qualify live component separately when authorised.

Meaningful acceptance: AC07 AC08 AC09 AC14 AC15 AC17 AC18 AC19 AC21 AC27 AC33. Authorised accounts/disposable reference only; distinguish source/host read qualification, real baseline read, model call and payment tests. Publication tripwire AC32 belongs later Plan3; no writes/deployments to merchant. Full build/service completion not implied.

Verification command pattern (future, no installs implicit): `uv run pytest <the named .py tests>` with network disabled; frontend uses the then-approved package test command on named files. live_ scripts remain separate opt-in; credentials never in args/logs. Exact package pins and image digests are captured during authorised build/qualification, never fabricated here.

Failure/undo of implementation: disable the new feature route, preserve accepted action/receipt/audit rows and schema compatibility; roll forward with corrective migration if data exists. Never destructive database downgrade/drop, revive revoked grants or delete working merchant payment configuration. Empty migrations can be reverted only on disposable local DB with no accepted data.

Review gate: outputs validate through contracts, named negative cases pass and operational limits remain visible. Stand-in success is labelled simulated.

## Mandatory additions to existing slices
S01 adds connector_adapters.py resource graph/capability schemas and offline two-provider fixtures. S03 adds providers/base.py and registry.py; GitHub/Render implement common interfaces. S04/S06 add resource_graph.py completeness and cross-provider correspondence/invalidation. S08 renders component-specific connection/missing-capability states in the same workspace. S09 requires a second real qualified host before a demonstrated multi-host claim; second-host selection remains targeted follow-on adapter qualification, not an assumed implementation. AC35/AC36 apply. These extend the nine slices without executing them. See CONNECTOR_EXTENSIBILITY_SPEC.md.

## Source-location amendment to existing slices
S01 adds proposed SourceSnapshot/UploadSession types and non-Git fixtures; S03 adds local_upload.py/upload_sessions.py, client+server exclusion and bounded chunk protocol; S04/S06 make correspondence/readiness independent of Git commit; S08 adds SourceChoice.tsx/LocalFolderInput.tsx with capability-detected browser fallback and maintainer routing; S09 qualifies browser transfer and selected cloud/host sources independently. No direct Drive service integration until genuine read-only/minimum-scope gate passes. AC37–AC40 apply. No product implementation or new teammate assignment.

## Complete code/context amendment
S01 proposes shared work_package.py boundary and fixtures; S03 adds component_inventory.py/work_package.py assembly and missing-authority/input recovery; S04/S06 enforce graph closure, current website correspondence and read-only delivery-feasibility constraints. S07 sends exact pinned package to worker; initial baseline read is not a successful build. Actual baseline/working-copy execution and full upgrade/live handover are Plan3 build-slice requirements, not extra implementation performed here. AC41–AC44 added.

## Closure addenda
S01 must implement final proposed shapes in CONNECTION_CONTROL_PROPOSAL.md, not historical draft blocks. S07 adds persisted ActionIntent, null pre-accept work/generation, immutable acceptance/current-status separation and AC45/AC46. Nine-slice count unchanged. Snapshot/graph/package references remain typed/authorised at resolution; no single-host/Git-only assumptions in common code.
