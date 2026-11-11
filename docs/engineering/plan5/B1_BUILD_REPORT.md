# B1 shared contracts — as built, 10 November 2026

**B1 complete for the shared contract/export/example boundary. Stop before B2.**
Aditya will create the agents by hand later, with Codex directing the steps.
No agents, agent prompts, scheduler, model adapter, delivery engine or frontend
were created or launched here. No sub-agents were used.

Workspace: `/Users/aditya/dev/GoldGraft-plan5-build`, branch
`plan5-build-20261110`, inspected base
`0365c5e1adcb1875a7f72c99dc7c63631501e131`. This is an uncommitted local
implementation, not a new Git revision or published team interface revision.

## Implemented boundary

| Area | Actual implementation |
|---|---|
| Wire authority | Python3.12/Pydantic declarations under `contracts/src/goldgraft_contracts`; 177 registered keys: 42 existing and 135 additive keys |
| Source and acquisition | Provider/resource graph/binding declarations; snapshots, bounded manifests/chunks/upload sessions; typed component/dependency/configuration/flow/omission/package records |
| Case journey | Draft/claim, saved case, readiness, action intent, immutable acceptance, current status, cancellation, baseline-operation and browser projection records |
| Lifecycle | Exact review/approval/effect/reservation/image/state/finalisation/exit records; delivery snapshots/decisions and service Protocol declarations |
| Future agent boundary | Task/context/lease/checkpoint/result, subject manifest/derivation, model/tool/wake/event records; closed role-operation/tool/output declaration catalog and typed GU-facing ports |
| Version migration | ChangeList/2 represents Git or snapshot provenance; ChangeList/1 is retained. Stage/1 and JobKind/1 are not widened |
| Tools | 16 closed v2 argument shapes and role capability ceilings; no arbitrary shell, SQL, URL/provider or financial tool executor |
| Routes | 23 v2 route contracts, separate from legacy route registration; exact success/error/status, session/draft/service identity, CSRF/idempotency, multipart and SSE export metadata |
| Examples | 135 positive and 19 deliberate negative synthetic payloads, indexed with actual SHA256 hashes; explicit version-aware fixture lookup |
| Generated outputs | 177 standalone JSON schemas, boundary TypeScript, OpenAPI and API TypeScript produced through exporters |

The 23 routes are **contract-only**, explicitly marked in OpenAPI. Existing GU
handlers do not acquire new v2 behavior merely because the routes are described.
The 135 keys include nested structures, tool arguments and requests; they are not
135 agents or services. The role catalog is shared declaration data for the
future manual build, not an implemented role runtime.

## Validation and safety checks

Implemented structural validation rejects unknown fields/enums, bool/float
counts, non-UTC/naive/numeric timestamps, malformed SHA256/OCI identities,
conditional-result contradictions, duplicate/cyclic tasks or effect slots,
unsafe paths, invented snapshot Git provenance and unsupported role/tool/output
declarations. Payment money remains the existing integer minor-unit/currency
contract; ModelBudget/1 uses integer micro-USD and includes spent/outstanding/
unknown amounts within the cumulative $20 ceiling. It does not reserve or spend.

Pure accepting-boundary helpers check authenticated tenant/producer inputs,
case/run/generation/subject/input binding, bytes/hash, artifact ownership/trust,
collector-derived lineage, upload coverage/content/replay, draft claim inputs,
required package scope and exact controller approvals. Approval tests include
two independent controllers, missing authority, expiry, epochs, image and trigger
drift. Incremental plan admission validates the full accumulated DAG, preserving
existing tasks while allowing an extension to reference them.

These helpers assume their caller supplies authenticated current identities and
resolved records. They do not authenticate provider accounts, resolve remote
references, implement custody, atomically claim drafts, issue approval, persist
effects, terminate workers or verify real exit. GU remains responsible for those
mechanisms and authority-at-use. Record shape, including a complete or verified
label, is never sufficient evidence of actual operation.

Normal pytest now denies Python IP socket connections with a root fixture;
offline tests use synthetic input and local/in-process dependencies. Safe service
validation errors expose a closed error record without echoing private input.
This is test protection, not execution-isolation or egress qualification.

## Actual results

Final checked implementation, 10 November 2026 at 12:21 UTC:

| Command from the workspace | Result |
|---|---|
| `uv run --locked --no-sync pytest -q` | **2,004 passed**, one existing dependency warning; the recorded equivalent command used `.venv/bin/python -m pytest -q` |
| `.venv/bin/python -m pytest -q contracts/tests/test_plan5_contracts.py contracts/tests/test_plan5_routes.py contracts/tests/test_plan5_relationships.py contracts/tests/test_plan5_compatibility.py contracts/tests/test_plan5_offline.py` | **131 passed**; included in, not additional to, the full-suite denominator |
| `.venv/bin/ruff check .` | Passed, no findings |
| `npm run check:types` | Passed, including negative TypeScript assignments for new conditional forms |
| `sh scripts/check_generated.sh` | Passed; example/index hashes and generated schema/TS/OpenAPI bytes reproduce |
| Controlled stale-byte export test | Verification rejected a changed TaskContext schema; the exporter restored the exact valid bytes |
| `git diff --check` | Passed |
| Original preservation check | 496 original/reference/backup files unchanged; original status, HEAD and index unchanged |

The warning is the already observed Starlette TestClient/httpx deprecation. No
dependency upgrade was made to hide it. No new dependency installation was needed
after B0; lockfiles and tooling manifests retain their original bytes.

Earlier failures were retained privately and fixed: absent inventory/routes,
missing JSON-schema conditional forms, exact-image/epoch/trigger/authority
coverage gaps, incremental dependency admission, legacy OpenAPI inventory and
negative-fixture inventory assumptions. These were genuine failed checks, not
planned passes. Private command records contain exact argument arrays, outputs,
timestamps and exit codes.

## Preservation, inventory and decisions

Before edits, 432 build files were byte-backed-up and readback-verified, with a
fresh-path registry restore probe. Original-checkout and Desktop reference bytes
were never edited. GU/VJ/SH code and all `pieces/` files remain unchanged. No
commit, stage, push, merge, remote publication, account change or message occurred.
Observed remote main/proof heads still match the B0 inspection; proof PR1 remains
unmerged and was not exercised as a real counterpart.

`B1_FILE_MANIFEST.json` lists actual changed/new B1 files, hash values, schema
inventory, relevant check-record hashes and preservation results. It excludes
private backup bytes and secrets. Private details remain under
`/Users/aditya/reports/goldgraft-phase5.3-b1-2026-11-10/` outside publication paths.

Decisions:

1. Expose typed contracts and Protocols without inventing service implementations.
2. Prefix new OpenAPI components to prevent collisions with legacy response
   serialization schemas. Existing legacy examples and schema bytes are retained.
3. Keep Python relationship checks distinct from JSON Schema/TypeScript: ACL,
   exact byte identity, current authority and cross-record lineage cannot be
   established by generated type declarations alone.
4. Permit existing-task references in an untrusted PlanProposal extension; the
   accepting helper requires the complete existing snapshot and validates the
   full DAG before the eventual GU transaction.
5. Compare generated current bytes with regeneration, rather than requiring a
   commit. The deliberate stale-byte test confirms drift still fails.
6. Preserve later independently owned fixture entries/modes when regenerating B1
   examples. B1's empty frontend-mode list is honest, not frontend readiness.

## Stop boundary and remaining gates

**B2 has not started.** Persistent SQLite counterpart stand-ins, scripted
model/tool behavior, lifecycle conformance and complete frontend fixture modes
remain next-phase work. Therefore no FRONTEND_READY marker exists and frontend
construction is not released by this report.

B3 runtime, B4 role implementation/use, B5 delivery coordination, B6 frontend,
combined B7 qualification and Plan6 are not completed by B1. Aditya's latest
manual-agent instruction overrides the saved launch prompts' automatic agent
construction wording. Continue only when he selects the next phase.

Real-model, provider/payment, GU durability/custody/isolation, VJ recipes,
independent SH proof integration, controller authority and merchant exit checks
are **NOT RUN** here. No new live qualification gate closes. Model usage: **zero
calls, $0 spent, zero paid-spend reservations**. No key is needed for B1 or the
future offline B2 work.
