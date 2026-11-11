# Surveyor — agent-side model handoff, 10 November 2026

This is an input/acceptance checklist for the selected GU boundary. It is not a
backend implementation, an accepted processing profile, a spend reservation or
permission to use a direct inference client. No key is required to read it.

## Own preparation and exact protocol

Surveyor owns the prompt, bounded role inputs, RootMap/1 proposal validator,
source-reference preflight, typed tool selection and independent artifact checks.
Existing ordinary tests/diagnostics use explicit scripted GU counterparts.

The actual wire is in `contracts/src/goldgraft_contracts/agent_runtime.py` and
`plan5_tools.py`. Consume these installed Python models rather than copying this
document into new shared schemas. Existing signatures remain:

```text
ModelPort.turn(ModelTurnRequest) -> ModelTurnResult
ModelPort.reconcile(turn_id) -> ModelTurnStatus
TaskControl: current lease/checkpoint/intent/finish/cancel/snapshot
ToolPort.invoke(ToolInvocation) -> ToolInvocation
ToolPort.reconcile(invocation_id) -> ToolInvocation
```

The broker resolves the context digest and stages inline provider output as
untrusted bytes. It returns typed tool-call refs, a final proposal ref or a typed
issue. Models never mint trusted refs or receipts. Surveyor allows only
`source.read`, `analysis.matches`, `evidence.read`; each actual broker must
recheck current case/run/generation/lease/source scope before disclosing data.

Current own service admission is deliberately disabled: `context.build_context`
accepts scripted zero-budget evidence, and `runtime.run_task` pins fake:scripted.
Those are explicit offline constraints, not a service-ready adapter. Their future
replacement must consume authenticated qualified GU evidence; a local boolean,
SDK install or key cannot enable the path. Shared changes must follow the frozen
input pause/revision protocol if required. No frozen file changes in this phase.

## Evidence required from GU before service adaptation

| Required evidence | Acceptance/check on the agent side |
|---|---|
| Versioned service profile, SDK/model/feature/pricing/token-count pins; approved processing purpose/recipient/retention/region/copies/deletion | Exact refs/bytes/current expiry and entitlement; no alias/provider fallback or extra tools |
| Authenticated context/artifact/producer/usage receipts and scoped source/tool routing | Resolve same case/run/subject; forged or stale receipts deny before data or acceptance |
| Durable TaskControl leases/checkpoints/outbox/current generation and Stop fencing | Existing negative/restart/Stop suites adapted to actual port evidence; late result cannot complete |
| One cross-process project monetary ledger | Before dispatch atomically reserve spent + outstanding + unknown under active $5 checkpoint, within total $20; no per-agent reset |
| Durable model turn ID before submission and turn/reconcile receipts | Timeout/connection loss holds same identity/reservation; no blind retry or automatic new turn |
| Token counting and provider usage reconciliation, including failed/unknown calls | Input cap includes role/tools/observations/history; all billed output counts; unknown reservation retained |
| Broker bounded timeout, retry configuration and secret custody | Hidden SDK retries disabled; no secret in model context, tool args, logs, URLs or artifacts |

Missing evidence stays a named GU-owned gate; agent code does not rebuild these
mechanisms. VJ-qualified detection/mapping coverage and runtime/site/account lenses
remain separate. No source-only result becomes independent SH payment proof.

## Public documentation inspected; candidates are not selected or qualified

The official [Python SDK release](https://github.com/anthropics/anthropic-sdk-python/releases/tag/v2.7.0)
shows v2.7.0, released9 November2026, commit prefix d497641. This release metadata
was inspected; no package/lockfile was installed or resolved. GU must pin and
qualify its actual dependency graph. The [SDK configuration docs](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/python)
document automatic retries and `max_retries=0`; the broker needs the latter plus
the reviewed90-second turn deadline, not the SDK's longer default.

The [model catalog](https://platform.claude.com/docs/en/models/overview) lists
`claude-haiku-5-5` and `claude-sonnet-5-5`. They are candidates only. The
[versioning policy](https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions)
describes these newer dateless IDs as pinned snapshots, while serving behavior
can still vary. No key/account entitlement or capability was tested.

The [pricing page](https://platform.claude.com/docs/en/about-claude/pricing) gives
Haiku5.5 at$0.10 input/$0.50 output per million tokens for prompts≤100,000 tokens,
and Sonnet5.5 at$2/$10. These are observed standard text rates, not a negotiated
or approved project price. No cached/batch/fast/regional discounts, credits,
server-side tools or free inference are assumed. The24,000 input-token cap is
below the inspected Haiku tier threshold; the actual profile must enforce it.

[Token-counting documentation](https://platform.claude.com/docs/en/build-with-claude/token-counting)
provides model-specific input estimates, including tool definitions. Counting
requests are documented as free but still send data and require approved scope;
none were made. Counts are estimates; GU must enforce a qualified conservative
bound and reconcile actual usage, never treat UTF-8 bytes as measured tokens.

[Data handling documentation](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)
distinguishes feature- and organization-specific arrangements. It does not prove
this project's settings, rights, region or retention. Initial evaluation data is
original synthetic MIT source only; no merchant/private source transfer is
authorized. No account, billing, retention or terms setting was changed.

## Concrete first paid batch proposal — NOT AUTHORISED TO DISPATCH

Question: can the selected model inventory four small source packages through
the guarded tools, produce grounded RootMap proposals, and preserve uncertainty?

Named cases: `inventory-nvp`, `inventory-browser-ipn`,
`inventory-layout-injection`, `inventory-no-known-indicators` (one run each).
Use the independent labels in `surveyor_cases.json`; expected answers never enter
model context. Tool/provider/financial effects remain synthetic and labelled.

Candidate to review first: Haiku5.5 as an inexpensive extraction baseline. This
is a cost-based proposal, not a competence claim. Any comparison with Sonnet
needs a separately reviewed batch/profile; no automatic upgrade is allowed.

Worst-case arithmetic, not a reservation:4 cases ×12 turns ×(24,000 input +4,000
output tokens). Twelve includes the one malformed-output correction. Include all
tool-schema/context overhead inside that input cap, and any billed reasoning
inside the output cap; if the actual provider profile cannot enforce those
bounds, recalculate before approval. No provider-hosted tools, cache writes,
batch/fast service or paid tool calls are permitted in this proposal.

| Candidate / standard rate | Per-turn bound | Four-case bound |60-run trial at12 turns/run |
|---|---:|---:|---:|
| Haiku5.5 |4,400 micro-USD ($0.0044)|211,200 micro-USD ($0.2112)|3,168,000 micro-USD ($3.168)|
| Sonnet5.5 |88,000 micro-USD ($0.088)|4,224,000 micro-USD ($4.224)|63,360,000 micro-USD ($63.36)|

The last column conservatively assumes all60 runs dispatch12 turns; pre-admission
holds do not dispatch inference. The reviewed20-case/three-repeat **overall
real-model acceptance** design remains the starting point, not20×3 per agent by
default. Even the cheap worst-case60-run budget repeated independently for13
roles would exceed$20; reuse deterministic guard checks and schedule only named
model questions. Never infer affordability of all roles from one four-case price.

Before the first batch, GU must reconcile actual project spent/outstanding/
unknown and atomically reserve its worst case under the existing cumulative$5
checkpoint. Recorded local spend remains$0; there is no qualified ledger here to
certify external/current unknown usage. The $15 target/$20 ceiling covers all13
agents, calibration, retries, evaluation, regression and demos together.

Stop/hold on any missing/expired qualification, bad-subject evidence, secret/
canary disclosure, unauthorized request, unsupported success claim, unknown
billable result, input/output/turn/deadline overflow, budget exhaustion or Stop.
Record model/profile/SDK/prompt/tool/schema pins, tokens/cost/latency and actual
per-case outcomes; never average away a safety-negative failure. Three provider
repeats require their own reviewed cost and repeat identity; no unsupported
provider seed parameter is assumed.

## When API access is useful

After the actual GU model/cost/custody boundary and own service adapter qualify,
and this named paid batch is reviewed, Aditya configures ANTHROPIC_API_KEY in the
local server environment or approved GU secret store. Check presence only; no
environment dump and no secret in chat, repository or logs. Then run an approved
token-count/calibration step and recalculate reservations before inference.
Do not ask Aditya for the key while the engineering boundary is still absent.
