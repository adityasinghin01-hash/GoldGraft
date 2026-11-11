# Agent 1 — Surveyor: supported offline implementation completed

10 November 2026. Completion of the **supported source-only offline implementation
and verification**, not full real-model or service acceptance. Direct construction
was authorised; no manual command results or sub-agents were required. Remaining
twelve roles were not started.

## What now runs without an API

`pieces/agents/source_inventory.py` derives RootMap proposals from supplied bytes
and a pinned detection catalog, without reading the evaluation's expected answers.
The proposal passes through the existing guarded runtime, actual scoped source/
match/omission tools, artifact validation and TaskControl acceptance. A read-only
inspector consumes the actual accepted output. The offline ModelPort stages the
deterministic proposal through its scripted counterpart; these are not provider
calls. Static analysis executes no source and makes no network requests.

The source-driven path handles changed file names/layouts, nested paths, Unicode,
repeated operations with distinct location-bound IDs, and no known indicators.
It produces source-located create/approve/capture/refund/notify entries. Empty
mark-paid/recurring fields are not proof that real-shop behaviour is absent.

Literal PHP require/include references resolve against the supplied manifest,
including nested parent-relative references and __DIR__ concatenation. Missing
components create required omissions. Absolute, URL and escaping references hold
before dispatch; targets are never read or fetched. This is conservative literal
analysis, not PHP execution or exhaustive dependency resolution. Dynamic includes
may be missed; comment/string lookalikes may produce a safe hold.

Unsafe/empty/oversized packages and recognised secret values are refused. Limits
remain16 files,16,384 source UTF-8 bytes,4 reads/batch,12 turns,24 tools and4,000
final JSON bytes; required overflow holds instead of discarding evidence. The CLI
exposes only four original synthetic packages and does not scan a merchant folder.

## Actual checks and evidence

| Measure | Observed result |
|---|---|
| Surveyor/source checks | **79/79 passed**: original61 plus18 source-driven checks |
| Independent source inventory cases | **4/4 passed**, with3/2/2/0 indicators respectively |
| Full offline regression | **2,240 passed**, one pre-existing TestClient/httpx warning |
| Ruff and shared TypeScript | Passed |
| Model/provider API calls and spend | **0 / $0** |
| Real-model competence | **NOT EVALUATED** |

Private evidence: `/Users/aditya/reports/goldgraft-b4-surveyor-20261110/`.
checks/19-source-driven-red.log,20-source-gaps-red.log,21-source-bounds-red.log
retain failures observed before fixes. Final command/status/duration/log hashes:
checks/22-source-final.json,23-source-full.json,24-source-lint.json,25-source-types.json.
source-driven/results.json and four case outputs retain actual accepted input/
output/subject/evidence refs and independent artifact-checker outcomes. Cases use
separate persistent SQLite files. Old/unknown state is not deleted to force retries.

Example from the isolated root (reuse this matching saved run, or choose a new
explicitly named path):

```sh
uv run --locked --no-sync python -m pieces.agents.source_inventory --case inventory-layout-injection --state-file /Users/aditya/reports/goldgraft-b4-surveyor-20261110/source-driven/inventory-layout-injection.sqlite
```

## Role checklist

| Obligation | Offline disposition |
|---|---|
| Purpose/operation/prompt/bounded context | Versioned Surveyor policy/prompt; survey only; pinned source/package metadata |
| Typed tools/prohibitions | source.read,analysis.matches,evidence.read only; no candidate/host/payment/publication tool |
| Output/producer/subject | RootMap/1; Surveyor descriptor producer; exact task/case/run/generation/input and persisted SubjectManifest |
| Existing runtime integration | Original lease/checkpoint/model/tool/result loop; source-driven proposal uses the same path |
| Positive/missing input | Four independent packages; missing backend/include/omission/lens checks; actual dispatch counts |
| Wrong case/subject/generation/tool/owner | Rejected before disclosure/acceptance; inherited B3 guards remain active |
| Safety/failure/restart | Secrets, injection data, bounds, Stop, stale leases, unknowns and six real process-crash boundaries |
| Useful consumer | Read-only inspection resolves and consumes actual accepted output |
| Evidence | Code/prompt/policy hashes, commands/results and case refs in reports/manifests |
| Real-model competence | OPEN; API evaluation NOT RUN |
| Runtime/site/account lenses | Unavailable and held when required; no fabricated observations |

The catalog covers **five literal indicators in three families**: EC_NVP,IPN,
CHECKOUT_JS_V4. This is not all-PayPal coverage, AST/call-graph analysis, runtime
replay or money-flow proof. Confidence≤0.5, live=false,paypal_only=false,target
operations=unqualified. Runtime recall is explicitly NOT MEASURED; required zero
counters are legacy-schema placeholders, not measured zero events. Earlier
B4_SURVEYOR_REPORT and MODEL_ACCESS_PREFLIGHT retain all inherited limitations.

## Honest API handoff boundary

It is **not true that a key is the only remaining prerequisite for full Agent1
acceptance**. Published GU code lacks the qualified model broker and cumulative
reservation mechanism; actual model/account entitlement, processing/retention/
region conditions and pricing/tokenizer evidence are unverified. Local tests and
declarations cannot manufacture qualification. No GU mechanism was recreated
inside Singh's agents; no direct-client bypass, framework/provider/model switch,
extra scheduler or silent profile relaxation was added.

GU must provide/qualify the selected Anthropic Python SDK adapter behind its
boundary, disable hidden retries, authenticate scope, enforce the pinned model/
tool/token/deadline policy, reserve cumulatively before dispatch, and preserve
unknown billed outcomes and original identities. The source-processing gate must
qualify for the actual evaluation profile. Then configure ANTHROPIC_API_KEY locally
or in the approved secret store; never paste it into chat. No account/billing
changes are authorised by this report.

All13 agents and every calibration/evaluation/retry/regression/demo share **one
$20 ceiling**, starting at a cumulative$5 checkpoint, with reviewed approved
increases to$10/$15/$20. It is not per-agent/session; spent+outstanding+unknown
reservations count together. No training job is planned. Current service/paid
admission stays disabled even with a key present.

Offline implementation is completed for the supported scope. Full real-model
Agent1 acceptance remains open until qualification and actual evaluation pass;
this must not be presented as an unqualified “Agent1 completed” claim.
