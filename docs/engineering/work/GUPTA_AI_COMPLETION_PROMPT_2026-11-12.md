# Copy-paste prompt for Gupta's AI — complete GU01–GU05

You are working for Aditya Gupta on GoldGraft. Your job is to finish Gupta's
backend/runner/provider work, test it, and deliver an integration-ready GitHub
revision. FIRST create the implementation plan below; THEN execute it. Continue
through your own remaining tasks without routine permission questions. Report
after each phase and immediately report a genuine blocker.

## 1. Your scope and the current starting point

Own GU01–GU05: resource identity/authority; source/custody/readiness/brokers;
durable Start/Stop/runtime/recording; exact build/publish/apply; state/recovery/
independent exit mechanisms. Preserve correct existing work instead of rewriting
it. You do NOT own Singh's 13-agent internals or model routing, Claude's frontend,
Singhal's proof engine, or Vijay's domain recipes and payment scenarios.

Use your own existing GoldGraft checkout and owner PR branch. Do not modify
`/Users/aditya/dev/GoldGraft-plan5-build` or another person's worktree. That is
the integrator's active workspace and contains unpublished work. Do not assume
its untracked files exist in GitHub. Do not create another integration branch.

Last verified GitHub snapshot, 12 November 2026:

- Main: `f2c86ef832ae2506bf3cc5fa36379eebd3b72ee6`.
- Your [PR #13](https://github.com/adityasinghin01-hash/GoldGraft/pull/13):
  `150ad893ba0998b05593860c980e93ff1a9c04c6`, open, CI passed at that revision,
  but GitHub reports merge conflicts with main.
- Singhal's [PR #12](https://github.com/adityasinghin01-hash/GoldGraft/pull/12):
  `4ce2fdb836a8c3fd560257691078e4370752d1fd`, based on your provider branch.
  It contains useful durable-upload/effect changes in addition to proof work.

Recheck these revisions before editing; they are observations, not permanent
facts. Continue the existing owner PR, reconcile current main in that branch
without force pushes, and keep the final target the single GitHub main. You may
commit/push your checked owner branch and update its PR description. The
integrator handles the final main merge. Do not delete others' branches, stash,
reset away work, or merge unreviewed proof changes just to clear conflicts.

This owner-specific assignment governs this run even if a recent AGENTS.md
paragraph broadly assigns non-frontend work to Codex. It does not authorise you
to edit the other owners' components or to spend their model budget.

## 2. Read before writing the plan

Read the current AGENTS.md and these repository documents in order:

1. `docs/engineering/START_HERE.md`.
2. `docs/START_Aditya_Gupta_backend.md` — all GU01–GU05 packages.
3. `docs/engineering/work/SHARED_INTERFACES_AND_DEPENDENCIES.md` and
   `DONE_AND_TEST_MATRIX.md`.
4. `docs/engineering/review/CONTRACT_AND_IMPLEMENTATION_BRIDGE.md`.
5. `docs/engineering/connection/CONNECTION_BUILD_SPEC.md`,
   `SUPPORTED_FIRST_PATH.md`, and `ACCEPTANCE_CASES.md`.
6. `docs/engineering/lifecycle/ATOMIC_DELIVERY_PROTOCOLS.md`,
   `OPERATIONAL_GATES.md`, `ACCEPTANCE_CASES.md`, `RECOVERY_AND_ROLLBACK.md`,
   and `SUCCESSFUL_EXIT.md`.
7. `docs/engineering/work/VIJAY_TEAM_INPUTS_REPLY.md` and
   `SPONSOR_UTILISATION_AND_OWNERSHIP.md`.
8. Actual Python contracts in `contracts/src/goldgraft_contracts/`, especially
   `api_routes.py`, `connection_control.py`, `connector_adapters.py`,
   `work_package.py`, `agent_runtime.py`, `lifecycle.py`, and `plan5_tools.py`.
9. Your actual code, tests, PR diff and CI results; Singhal's shared-file diff.

Current Python owns the wire. Planning Markdown does not establish implemented
APIs. Read the actual symbols and fixture loaders before choosing commands.

## 3. FIRST deliver a concrete plan

Create `docs/engineering/work/GUPTA_COMPLETION_PLAN_2026-11-12.md` before product
edits. It must contain:

- A GU01–GU05 table with implemented/partial/missing, exact source locations,
  actual checks, input/output contracts and remaining acceptance cases.
- A function/route/tool matrix separating actual implementations, scripted
  counterparts, and external capabilities not yet qualified.
- Exact files to change, failing tests to add, implementation order, commands,
  expected outcomes, phase exit gates and dependency owners.
- A scope/cost/authority register for any external check. Source execution,
  payment, deployment and account changes have separate authority.
- A shared-file resolution plan: GU owns final upload/effect implementations;
  inspect and preserve the useful fixes in PR #12 together with your limits and
  filename checks. Do not discard either set or duplicate the same mechanism.
- A handoff checklist containing the precise callable entry points, setup,
  versions, records, examples, failures and evidence the integrator will consume.

Do not stop after writing the plan. Execute it phase by phase, using a failing
test for a real gap, the smallest correct fix, green tests, and a recorded gate.
Do not infer readiness from the former rough percentage estimates.

## 4. Phase G1 — authority, source and actual service routes

1. Implement real server-side case/tenant/controller access using current
   authenticated identities and current resource bindings. Email, invitation
   possession, an arbitrary actor header or possession of an API key is not
   ownership. Selected-resource scope must not silently cover the workspace.
2. Inspect all 23 `PLAN5_ROUTES`. At the audited main the backend registered
   none of those v2 routes. Implement the applicable real handlers and accepted
   service bindings, not only route registration or a seeded demo response.
   Preserve legacy fixture mode with explicit labels and a separate boundary.
3. Cover draft claim, case list/view, provider/controller handoff, uploads,
   readiness/action intent, Start/status/cancel/resume, review/approval, events,
   public projection and service-only collector intake. A missing prerequisite
   returns the correct typed hold/problem; it never fabricates accepted work.
4. Require verified session/worker identity, server-side resource ACLs, browser
   CSRF where required, bounded intake, exact idempotency and tenant-bound
   pagination. Revocation and wrong-case access must fail before private loads.
5. Make the initial Reader genuinely read-only at both provider grant and tool
   boundary. Reject classic/writable credential fallback and indirect write
   triggers. Read-only acquisition may occur when authorised; source execution,
   inference and payment must not happen before durable Start.
6. Implement complete bounded source acquisition, quarantine and immutable
   provenance for supported routes. Reject traversal, symlink escapes, archive
   bombs, chunk/manifest mismatch and unresolved required components. Unknown
   source/runtime correspondence is a hold, not a positive readiness boolean.
7. Use secret references and nonsecret credential-version metadata. Never print,
   copy or hash API-key values, the model signing key or a Zapier hook URL. An
   in-memory dictionary named Doppler is not an external custody integration.

Gate: actual handler/storage/authority tests pass, including cross-tenant,
revocation, forged identity, stale binding, missing component, unsafe upload,
duplicate request, different-body conflict and server restart. Report precisely
which external identity/source profiles are still unqualified.

## 5. Phase G2 — durable acceptance, control, isolation and collection

1. Commit acceptance, immutable work identity and outbox before worker dispatch.
   Same logical Start must survive concurrent calls and process death without
   a second job. Changed-body reuse must conflict.
2. Implement the current TaskControl/runtime/artifact/tool service protocols
   required by the agent runtime, with current case/run/generation/lease/subject
   checks. Do not return the offline fake profile as a service implementation.
3. Cover Stop before acceptance, Stop after dispatch, stale/expired workers,
   checkpoint/resume, lease renewal, cancellation and termination observations.
   Queued, claimed, running, operation-observed and terminated are different facts.
4. Run source only inside a qualified execution profile with bounded resources,
   egress and credential access. A host `subprocess.run()` with changed cwd/env
   is not an isolation boundary. Your current process helper requires this audit.
5. Bind actual template/runtime/source/image/config/seed identities to execution
   and captures. Capture actual exchanges through an independent recorder; do
   not label generated in-process exchanges real by changing evidence_class.
6. Preserve original request identity on timeout/unknown. Observe actual child/
   sandbox termination; elapsed timeout or a kill request is not termination.
7. Supply the runner/collector export consumed by proof: exact JobSpec/JobResult,
   sealed capture bytes, source/runtime subjects, permitted scenario/variant
   scope, producer/authenticity and artifact lookup. Do not invent GitHub
   workflow/SHA fields for local or E2B execution.

Gate: process-crash/concurrency/Stop/restart/isolation/collector negatives pass.
Vijay's real scenario recordings are an input dependency; complete your runner
and broker mechanisms independently, using labelled component probes and the
existing interfaces without implementing his domain recipes.

## 6. Phase G3 — payment broker and callback authenticity

Audit and fix these concrete risks in the observed PR #13 revision:

- A failed live IPN/webhook check falls through to the old parameter/header
  heuristic. Remove that fallback. Invalid, unavailable or inconclusive actual
  verification must stay UNVERIFIED/UNKNOWN; it must never become VERIFIED.
- A signature string, `_notify-validate` parameter, mock header or certificate
  URL prefix is not authenticity. Test missing certs and deceptive host suffixes.
- Allowing a broker labelled real_sandbox into the existing synthetic recorder
  does not make that recorder an actual shop execution/capture mechanism.

Then complete these steps:

1. Pin account/app/environment and permitted operations from trusted server
   authority, not ambient environment variables or a caller's `live=True` alone.
2. Allow only typed supported operations; validate amount/currency and request
   bounds. Internal money uses integer minor units + currency; provider decimal
   strings are parsed/produced exactly at the documented boundary, never floats.
3. Persist logical financial intents/idempotency across restart, bound to their
   exact operation/payload/account/scope. Reconcile an unknown outcome before
   another economic action. Apply the actual rate/time/quantity limits.
4. Separate scripted transport from actual transport explicitly. No failed live
   request may silently produce a simulated success, including the mock-name
   fallback. NVP cannot remain synthetic while advertised as live.
5. Preserve original callback bytes and listener/app/environment. Persist the
   required ingress safely before acknowledging it; authentication and local
   business processing are separate later facts. Implement the actual PayPal
   IPN postback/webhook verification protocol and required business bindings.
6. Test duplicate transport, legitimate later status, replay, wrong account/app,
   wrong amount/currency, invalid signature, verification outage, failed durable
   receipt and process restart. Dedupe must be scoped and durable; never upgrade
   an unverified duplicate to verified or lose an event after failed persistence.
7. Keep raw bodies/credentials private. Use closed diagnostics rather than raw
   exceptions or regex-only redaction of arbitrary captured output.

Use current official PayPal docs, especially
https://developer.paypal.com/api/rest/webhooks/rest/ and
https://developer.paypal.com/api/nvp-soap/ipn/IPNIntro . Record the versions and
actual supported protocol. Do not make a real capture/refund/charge just because
a test or script name contains "sandbox".

Gate: meaningful positive and negative transport-contract tests pass with no
network in pytest; separately authorised actual evidence is identified as such.

## 7. Phase G4 — exact build, publication and deployment

1. Build the exact source/dependency/recipe subject. Observe the actual OCI
   manifest/layers/config/runtime, then bind tests to those bytes. A hash of
   descriptive strings is not a built image or reproducibility evidence.
2. Implement resource-scoped reservations, current approvals and per-effect
   intent-before-submit with expected provider versions and immutable identities.
3. Publish the exact tested private artifact/source under the merchant's
   permitted destination. Independently retrieve/verify it and persistent pull
   access. Never return a fabricated publication/PR ID after an exception.
4. Respect protected Git rules and exact head/base/tree. A PR receipt is not a
   completed merge, deployment or working upgrade. Preserve non-Git provenance.
5. Render accepted/queued deploy responses are not LIVE. Observe completion,
   active image/config and actual service identity. The current default LIVE
   status and swallowed-error paths must be removed from actual mode.
6. Verify persistent image/config settings, not only a one-off deploy-hook
   override; observe the real target URL instead of guessing it from service ID.
7. Test partial publication, timeout/no ID, duplicate submission, Stop, drift,
   expired approval, target conflict, wrong image/config and registry pull failure.
   Reconcile the original effect; never retry just to obtain an ID.

Gate: actual mechanism tests and separately scoped provider observations support
each claim. Missing provider permission or observation remains a hold.

## 8. Phase G5 — state, recovery, finalisation and independent exit

1. Inventory all writers and long-tail obligations. Before the first destructive
   restart/config/disk prerequisite, verify compatible export, all-writer fence,
   high-water mark, durable ingress/handlers and disposable restore/replay.
2. Preserve current order/customer/payment/origin state and original required
   callback/listener/credential paths. Never restore an old database over newer
   economic history or treat code rollback as payment compensation.
3. Replace auto-approved state plans and superficial clean reconciliation with
   evidence-backed state/effect resolution. Recovery must fit the current state;
   unsupported recovery holds safely or requires a scoped forward-repair plan.
4. Implement the approved finalisation and Q0–Q4 exit mechanism. The merchant's
   independent executor must exist before disruptive exit verification. Ordinary
   GoldGraft grants are denied/revoked; do not secretly reuse them to pass restart.
5. Verify retained merchant-owned source/image/registry/runtime/state/handlers,
   bounded evidence read, final evidence-capability revocation and itemised
   temporary-resource cleanup/retention. Pending cleanup is not complete exit.
6. Consume Vijay's state/origin/finalisation/exit recipes through the existing
   contracts. Do not rewrite them; identify a missing required recipe precisely.

Gate: all applicable GU-owned AC/LC cases have actual assertions/results. Use
the acceptance ownership matrix; distinguish not-applicable from unimplemented.
Missing external evidence may block live acceptance, not justify leaving your
own state-machine, validators, reconciliation and tests unfinished.

## 9. Phase G6 — sponsors, regression and a clean GitHub handoff

Finish GU-owned meaningful uses from the sponsor register: Render, Postman,
guarded Kernel integration, redacted Elastic ingestion and opt-in Zapier event
delivery. Consume APIMatic/domain inputs from Vijay. Astropods stays conditional.
Do not implement Singhal's search/proof policy or Claude's UI. A connector outage
must not alter authority/proof/payment state. Sending a notification still needs
its explicit recipient/send scope; creating accounts or buying access is not
authorised by this prompt.

Run relevant actual-component tests and the full offline suite with actual
implementations selected, not default fakes. Useful retained baseline commands:

```sh
uv sync --locked
GOLDGRAFT_API_APP=pieces.backend.app:create_app uv run --locked pytest -q plugtests/test_backend_api.py
uv run --locked pytest -q plugtests/test_connection_and_providers.py plugtests/test_broker_runner_real.py plugtests/test_lifecycle_advanced.py
GOLDGRAFT_PROOF=pieces.proof.proof:Proof GOLDGRAFT_API_APP=integration.app:create_app uv run --locked pytest -q
uv run --locked python scripts/check_spec_coverage.py
bash scripts/check_generated.sh
npm run check:types
git diff --check
```

Those existing API/fixture commands do not close new v2/runtime/provider gates.
Add and run the actual new boundary/fault tests; record the exact selected
factory and dependency configuration. Tests never call the network. Pin Python
3.12, Node 22, lockfiles, required PHP/isolation tools and exact SDK versions.
Missing required dependencies/skipped tests must be resolved or explicitly held.
Lint/format only files in your owned change set; do not reformat unrelated code.

Write `docs/GUPTA_INTEGRATION_READY_2026-11-12.md` containing:

- Exact commit, PR, tested main input and interface/schema versions.
- GU01–GU05 status: implemented, actual boundary-tested, externally qualified or
  BLOCKED, with counts and evidence. No invented completion percentage.
- Exact startup/import/factory and configuration variable names only; one
  minimal safe request→receipt→status→cancel/resume example.
- Runner/collector exports, opaque evidence lookup, source/image/config lineage,
  private/public/redaction rules and narrow adapter contracts for agents/proof.
- Unknown-effect/Stop/restart/revocation recovery instructions and resource owner.
- Every external/Vijay input still needed, its exact schema/example, why it is
  required and the fail-closed result. Distinguish component-ready from live-ready.
- Check commands/results, required failure cases, live scopes actually exercised,
  costs, limits, licence/retention and any unsupported profile.

Refresh current main in your PR, resolve conflicts without overwriting other
owners' work, push your scoped revision and obtain fresh CI on that exact head.
Return a mergeable PR, the handoff file and exact verification command. Stop
only after own work is finished or a real external prerequisite is documented
concretely. Do not claim whole-service/live completion from mocked success.

## Non-negotiable rules throughout

Pieces import only contracts/foundation across piece boundaries. No second
scheduler/connector. Use current schemas; necessary shared changes follow
`docs/FORMAT_CHANGES.md`, approved versioning and coordinated generated types,
examples/fakes/compatibility checks. Do not alter frozen fixtures or weaken an
oracle to get green. Preserve raw original results and disclose any corrected
test expectation. No model/financial budget reset, raised cap, unknown replay,
hold release, external messages, new accounts, merchant jobs or unapproved
deployments/payments. These restrictions do not prevent completing code and
offline tests autonomously.
