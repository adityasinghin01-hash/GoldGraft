# B3 guarded offline runtime — 10 November 2026

The B3 **offline runtime vertical slice** is implemented in the preserved isolated
workspace `/Users/aditya/dev/GoldGraft-plan5-build`, on branch
`plan5-build-20261110`, base `0365c5e1adcb1875a7f72c99dc7c63631501e131`.
This is the security/runtime foundation before B4 role construction. The two
scripted task names demonstrate control flow; they do not constitute accepted
real Surveyor/Herald agents or qualification of the remaining roles.

## Behavior implemented

- `pieces/agents/context.py`: current lease/task version/owner/epoch/time,
  case/run/generation, input ref and subject, accepted work and verified
  BASELINE_READ bindings, prompt/policy identity, current authority, deadline and
  explicit zero-budget profile admission. The user's nine earlier negative
  tests remain and pass; their source was backed up before this work.
- `pieces/agents/tools.py` and `runtime.py`: closed typed argument catalog,
  full read-batch preflight, per-call rechecks at the runtime and offline broker,
  scoped blob/argument digest checks and exact invocation/result scope binding.
  No host shell, arbitrary URL, SQL, credential or financial tool exists in this
  profile. Source/status ref checks run before tool dispatch and again inside it.
- Strict JSON rejects duplicate keys, nonfinite values and recognised secret
  patterns. Context preserves observation refs, byte hashes and explicit
  untrusted provenance; source/tool text cannot widen declared capabilities.
  Required oversized observations cause a hold instead of silent removal.
- At most 12 turns, 24 tools, 4 independent read calls per batch and one malformed
  output correction. Model output is an untrusted scoped blob until schema
  staging and TaskControl's exact output-owner/subject acceptance checks.
- Stable task/attempt/turn/invocation identities survive process restart.
  Checkpoints retain counters and observation refs; their stored context,
  policy, generation and input binding are checked on recovery. Intent precedes
  dispatch. Observed original results are reconciled rather than redispatched.
- Lease renewal uses the authoritative counterpart clock at 15-second boundaries
  and a heartbeat during blocking calls. Stop/revocation/expiry fences subsequent
  calls and final acceptance. A late result cannot turn cancellation into success.
- `scheduler.py`: deterministic serial claims, snapshot-driven dependency
  advancement and a counterpart-owned due-timer recovery scan. Approval,
  authority and counterpart waits require their own authenticated observation;
  timer expiry does not manufacture approval. No new state owner or scheduler
  framework was added.
- `cli.py`: developer-only `doctor`, `run`, `status`, `cancel`, `resume` with
  closed offline/service mode and explicit persistent state file. `service`
  refuses before creating a database. Resume rechecks the same persisted run;
  it cannot clear Stop, revive held/unknown work or erase completed effects.

`fakes/.../plan5_profile.py` explicitly composes the two-task synthetic profile.
Herald's status observation contains the **actually committed** predecessor
artifact refs, checked in the model context by a test. One invocation completes
both tasks without browser or manual per-agent dispatch. A separate CLI process
observed the same two accepted results, four scripted model dispatches and two
read-tool dispatches.

## Actual checks

The final accepted check records and their complete local outputs are under
`/Users/aditya/reports/goldgraft-phase5.3-b3-2026-11-10/checks/`.
The repository manifest links the accepted records and hashes the delivered files.

| Check | Actual result |
|---|---|
| Runtime/context/tool/scheduler/restart tests | 56 passed |
| Full offline suite, including agents in root discovery | 2,149 passed; one existing Starlette/httpx deprecation warning |
| Ruff | Passed |
| Shared TypeScript check | Passed |
| Generated examples/views/schemas/TS/OpenAPI parity | Passed; 177 schemas, 15 modes |
| CLI doctor/run/status in separate processes | Passed; scripted, 2 accepted results, 4 model/2 tool dispatches |
| Original/source/reference preservation | 496 files unchanged; original status, HEAD and index unchanged |
| Frozen frontend inputs | Revision 1 hashes unchanged; verified separately |

Meaningful checks include missing baseline/budget/input, lease mismatches,
cross-case input/ref/subject access, traversal, forbidden role/tool/extra args,
forged argument refs and tool receipts, wrong output owner, injection text,
secret canary, context overflow, malformed JSON, turn/tool/batch limits,
revocation between intent and dispatch, Stop during a call, lease expiry,
heartbeat renewal, duplicate/reordered outbox acknowledgements and due-timer
recovery after reopening persistent state.

Six tests use `os._exit(73)` in a subprocess, bypassing cleanup, then recover in
another process after lease expiry: before model call, after model result,
before tool dispatch, after tool result, before result acceptance and after
acceptance. Every persisted model/tool identity has dispatch count at most one.
Five cases finish both tasks; the pre-tool-dispatch intent case conservatively
holds as described below. B2 separately tests crashes inside model/tool broker
intent/submission boundaries; these remain in the passing full suite.

An initial full-suite/parity attempt failed because macOS's `/usr/bin/git`
launcher selected an incompatible x86_64 `libxcrun`. The private evidence runner
now puts the installed ARM CommandLineTools directory first in PATH. The same
checks then passed. No tests were weakened and no system/tool installation was
changed. Failed attempt records are retained.

## Decisions and limits

1. **Offline only, $0.** A nonzero model budget or non-scripted evidence class
   is refused. No Anthropic SDK/client, key, provider job or paid call was used.
   Real tokenizer enforcement, pricing calibration, cumulative $15 target/$20
   ceiling reservations and actual GU model/provider operation remain qualification
   gates; no unqualified service path can spend money through this runtime.
2. **Conservative byte bounds.** The offline envelope is capped at 24,000 UTF-8
   bytes and final JSON at 4,000 bytes, stricter than the numerical token caps
   for this synthetic profile. This is not a provider-tokenizer measurement.
   Real profile admission must supply the selected tokenizer and approved policy.
3. **Incomplete intent rebinding holds.** A prior tool intent from an expired
   lease, with no observed dispatch/result, cannot be rewritten under a fresh
   epoch. Without a qualified counterpart rebinding/reconciliation receipt the
   slice holds it; it never creates another invocation to get around the hold.
   Submitted/unknown model/tool outcomes also remain held/unknown, with original
   identities and reservations retained. `resume` does not override these states.
4. **Scope of the synthetic adapter.** One run per SQLite file; source reads
   cover the explicit synthetic `checkout.php` entry and the same run's status.
   Input inventory and accepted baseline evidence are injected synthetic
   preconditions, not evidence generated by an agent. SQLite is not GU Postgres,
   and a scripted fixture is not real proof or merchant completion.
5. **Composition stays explicit.** The CLI imports contracts/foundation and its
   own runtime. A developer-only deferred composition loader in foundation loads
   the already-installed offline fakes; importing normal foundation code does
   not load or activate it. Runtime admission/artifact/timer extensions are own
   Python Protocols, not new shared wire formats or frozen-contract edits.
6. **No external termination claim.** The profile starts no runner/model child
   process or provider effect. CLI status says external termination is not
   applicable. Actual slow/hung runner termination and provider cancellation
   remain GU/isolation qualification gates; a timeout is never labelled stopped.
7. **B4 remains separate.** Exclusive role prompts, multi-output role handling,
   real-model competence and all 13 individual positive/negative/use acceptances
   have not been built or evaluated here. B5 delivery, B6 frontend and B7 combined
   qualification are also separate. No Sentinel is needed to enable these guards.

## Reproduce locally

From `/Users/aditya/dev/GoldGraft-plan5-build`:

```sh
uv run --locked --no-sync python -m pytest -q pieces/agents/tests
uv run --locked --no-sync python -m pieces.agents.cli doctor --mode offline
uv run --locked --no-sync python -m pieces.agents.cli run --mode offline --fixture two_task_read --state-file /private/tmp/goldgraft-b3-own-demo.sqlite
uv run --locked --no-sync python -m pieces.agents.cli status --mode offline --state-file /private/tmp/goldgraft-b3-own-demo.sqlite
uv run --locked --no-sync python -m pieces.agents.cli cancel --mode offline --state-file /private/tmp/goldgraft-b3-own-demo.sqlite
uv run --locked --no-sync python -m pieces.agents.cli resume --mode offline --state-file /private/tmp/goldgraft-b3-own-demo.sqlite
```

Use a new, explicitly named file for another synthetic run; do not delete an
unknown-state database to force retry. With the macOS launcher issue, use the
installed native Git via `PATH="/Library/Developer/CommandLineTools/usr/bin:$PATH"`
for commands needing Git. No shell profile modification is required.

## Frontend handoff

The B2 `FRONTEND_READY.json` remains byte-identical at revision 1, with 6 spec,
209 contract and 239 fixture file hashes. Its phase limitations record the B2
publication snapshot; this report and BUILD_STATUS describe subsequent B3 work.
No `pieces/web` files were changed. Its current contents remain the pre-existing
README; no frontend writer/status file was present at inspection.

The new `CODEX_TWO_ANTIGRAVITY_FRONTEND_COORDINATOR_PROMPT.txt` is the single
execution prompt for Codex inside the user's IDE. It starts AG1 then divides
AG2/3 and AG4/5 between the two manually opened application workers with disjoint
paths and coordinator-owned integration/configuration. The installed app IDs
and versions were inspected locally. Codex extension compatibility/login/quota
inside those apps has not been verified. Local packets/status files provide an
explicit fallback when separate chats cannot communicate directly.

No sub-agents, Git commits/staging/push/merge, deployment/publication, teammate
messages, account changes, private-source transfer or provider/payment work
occurred. Work stayed in the isolated workspace and private report directory.
