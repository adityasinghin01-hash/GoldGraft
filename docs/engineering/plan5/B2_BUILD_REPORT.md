# B2 persistent offline counterparts — 10 November 2026

**B2 complete for offline counterpart construction. Stop before B3.** No agent,
agent prompt, scheduler, model client, delivery coordinator or frontend was built.
Aditya will create the agents by hand later with Codex guidance. No sub-agents
were used. This report supersedes B1's dated “B2 not started” status only for the
work and check results recorded here.

Workspace: `/Users/aditya/dev/GoldGraft-plan5-build`; branch
`plan5-build-20261110`; base `0365c5e1adcb1875a7f72c99dc7c63631501e131`.
The frontend coordination manifest is **revision 1**, not a Git commit. Shared
inputs are frozen at its actual hashes. No commit, push, merge or publication
occurred.

## Implemented

| Files under `fakes/src/goldgraft_fakes/` | Actual behavior |
|---|---|
| `offline_store.py` | Local SQLite WAL transactions, stable keys, content-addressed synthetic blobs, private file mode and persisted counterpart tables |
| `task_control.py` | Shared TaskControl signatures: seed/extend CAS, claim/renew fences, checkpoints, scoped invocation intent/observation, finish, wait/wake, snapshot and cancel; accepted result and newly ready dependency/outbox rows commit together |
| `offline_artifacts.py` | Scoped synthetic bytes, validated proposal staging and explicit fake outputs; model inline content begins as untrusted blobs, not trusted evidence |
| `model_broker.py` | Scripted final/tool-call/blocked output forms, durable turn intent/dispatch/result, explicit zero-cost profile, persisted unknown state and stable original request identity |
| `guarded_tools.py` | Role/tool/argument/generation/lease/capability checks after persisted intent; scripted bounded observations; path and recognizable credential denial; stale/revoked/unknown paths |
| `lifecycle_control.py` | Injected synthetic lifecycle observations, exact configured fake approval slots, unique request/slot identities, persisted pending/unknown/results, scoped fake artifacts; no delivery decision reducer |
| `case_views.py` | Hash-verified, synthetic-actor-bound case/evidence projections; persistence and rejection of unbound actors, changed fixture bytes and unsupported real-service modes |

`scripts/make_plan5_views.py` generates **42 valid payloads across 15 modes**.
The shared fixture index records mode/schema/path/hash/evidence metadata. The
normal fixture inventory includes these positive examples while retaining B1's
deliberate negatives. `check_generated.sh` now checks both example and frontend
fixture reproducibility before checking schemas, TypeScript and OpenAPI.

Modes: `ready`, `controller_wait`, `missing_source`, `start_response_lost`,
`claimed_no_operation`, `cancel_before_accept`, `cancel_pending`, `event_gap`,
`proof_missing`, `apply_split_controllers`, `deploy_unknown_no_id`,
`persistent_config_mismatch`, `exit_executor_missing`, `cleanup_pending`,
`synthetic_complete`.

Every CaseView and public proof sample has `evidence_class=scripted`. Every mode
carries the catalog label: **“Mock mode: showing saved sample data, not a live
system.”** A future frontend must display this label even on the synthetic
complete screen. Claims/provisioning do not imply operation started; cancelled
before acceptance has no acceptance receipt; termination pending is distinct from
confirmed; no-ID deployment remains unknown; cleanup pending does not mean exit
complete. Supplementary typed review/approval/deployment/exit projections explain
the respective mode. These are saved synthetic observations, not authenticated
real backend responses or merchant authority.

## Actual checks

Checked final code on 10 November 2026 at approximately 13:00 UTC:

| Command from the workspace | Result |
|---|---|
| `.venv/bin/python -m pytest -q fakes/tests/test_plan5_task_control.py fakes/tests/test_plan5_brokers.py fakes/tests/test_plan5_lifecycle.py fakes/tests/test_plan5_views.py fakes/tests/test_plan5_faults.py` | **47 passed** |
| `.venv/bin/python -m pytest -q` | **2,093 passed**, one existing Starlette TestClient/httpx deprecation warning; includes the 47 B2 checks |
| `.venv/bin/ruff check .` | Passed |
| `npm run check:types` | Passed |
| `sh scripts/check_generated.sh` | Passed: 135 B1 positives, 19 negatives, all 15 frontend modes and generated export bytes reproduce |
| `git diff --check` | Passed |
| Original preservation audit | 496 source/reference/backup files unchanged; original status/HEAD/index unchanged |

Named tests inspect persisted state and dispatch counts, not only log text:

- A fresh Python process sees exactly one accepted result and the ready dependent
  task before any outbox acknowledgement; repeated output acceptance is deduped.
- Duplicate same-content keys return the original identity; changed content
  conflicts. Concurrent claimers obtain one current lease. Expired leases and
  revoked authority cannot commit or dispatch.
- Checkpoint and exact approval wake survive reconstruction; wrong digest or
  insufficient version cannot wake; expiry holds. Renewal retains the fence.
- Hard process exits at model intent and dispatch boundaries preserve the original
  turn. A known not-dispatched intent resumes once; a submitted/unknown turn holds
  its original zero-cost usage reservation and cannot be silently replaced.
- Unknown tools hold task success. A tool-dispatch crash followed by lease reclaim
  reconciles the old invocation, without another dispatch identity.
- Path escape/internal-URL-as-path and oversized/sensitive scripted tool outputs
  are denied; another task cannot read a scoped blob. Wrong output subject cannot
  finish. Scripted inline JSON is not an accepted artifact merely because a model
  port returned it.
- Lifecycle request/slot replay persists across instances; changed requests,
  absent approval, cancellation and cross-scope artifact lookup deny. Existing
  unknown status remains inspectable rather than reporting false undo.
- All 15 view modes validate against the B1 generated interfaces; unsupported
  real/same-origin modes and unbound actors are rejected.

Earlier failures and fixes remain in private records: missing implementations,
an initial SQL insert arity error, a test checkpoint using the wrong policy hash,
unknown-dispatch completion, oversized output, request-cap revalidation and
duplicate cancellation events. No failed result is represented as a pass.

## Limits and replacement map

This SQLite profile supports **one synthetic task run per database**, bounded to
32 tasks by shared admission. Separate offline databases can be used for separate
cases. It is not GU's multitenant durable TaskControl, credential custody,
Postgres/outbox implementation, isolated runner, effect broker or exit executor.
Task policy/scheduling and automatic model/tool loops are B3 work, not hidden
inside this fake. No actual source execution, PayPal operation, model inference,
provider callback, host deployment or independent merchant restart occurs.

The lifecycle fake uses explicitly configured synthetic slot observations; it
does not derive production approval or current state. It never advances a whole
delivery workflow on its own. It cannot establish cryptographic signature
validity; fake references use synthetic namespaces and evidence classification.
Real provider/custody/isolation/state/payment/proof/exit conformance remains open.

These stand-ins use an injected clock in behavioral tests. Browser fixtures are
saved samples with fixed timestamps, not renewable authorisations. Ordinary
tests deny Python IP connections; this is not a production isolation certificate.
Model cost is zero and no real-model competence was tested. The model stand-in
accepts only `fake:scripted` with `fake:zero-budget`; it cannot use an inference
key or fall back to a provider. No new dependencies or lockfile changes were
needed. GU/VJ/SH and all `pieces/` code remain unchanged.

## Readiness and stop

After the checks above, `BUILD_STATUS.md` and an atomically written
`FRONTEND_READY.json` publish **offline frontend readiness revision 1**. The
manifest includes real base/workspace identity, specification/contract/fixture
hashes and redacted command evidence in `docs/engineering/plan5/checks/`.
It is a local coordination record, not a deployment or team publication.

When Aditya chooses to start frontend work, open the repository root:
`/Users/aditya/dev/GoldGraft-plan5-build` and use the saved
`docs/engineering/plan5/ANTIGRAVITY_FRONTEND_START_PROMPT.txt`. Antigravity must
verify the manifest and own only `pieces/web`; it has not been launched here.
Shared changes after that must follow updating → paused acknowledgement → checked
new revision → ready. No edits were made to `pieces/web`.

**Stop before B3.** The agent runtime and thirteen logical roles remain for a
later, user-directed manual build. No model key, paid call, spend reservation,
account action, message, commit, publication, deployment or Plan6 action occurred.
