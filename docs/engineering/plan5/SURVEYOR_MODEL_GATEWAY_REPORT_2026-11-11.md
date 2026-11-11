# Surveyor local model gateway — observed results

**Current,11 November2026 continuation03:** Surveyor's tiny actual-model
pilot works: **seven accepted outputs across four distinct synthetic cases**,
including all five literal indicators, an injection sample and empty inventory.
Final transport-policy refund and browser/IPN checks passed2/2. Three earlier
quality/limit runs were blocked, including one of three original refund repeats;
those failures remain in the denominator. **595 affected offline tests passed**,
Ruff lint/format passed, and all accepted outputs were consumed/reopened without
new dispatch. The400 speed-field rejection, repeated reads, source-only claim
limits and catalog-ID confusion were corrected without relaxing validation.

Conservative priced usage **$0.026663**, retained original reservation
**$0.012672**, available **$0.010665** under the unchanged$0.05 cumulative cap.
Another full$0.012672 batch cannot fit. Original unknown request was never
replayed or cleared. User-authorized signed case/batch exceptions retained it;
two separate attributable HTTP400 rejections were proven terminal/unbilled.
Console authentication succeeded but did not attribute the original request.

**Tiny pilot/correction round complete; full Surveyor model acceptance HELD.**
The reviewed20×3 design was not run or silently narrowed. Broader model negatives
and repeats still need a reviewed affordable design/budget; original usage still
requires attributable provider evidence to release its reserve. Herald has not
advanced and its model grant remains unqualified. Sponsor phase N/A; production
GU/VJ/SH, merchant/payment work and universal reliability remain unqualified.
No money reset or automatic Codex restart is scheduled. Current evidence, exact
counts, hashes, phase decisions and limits: [continuation03](SURVEYOR_CONTINUATION_03_2026-11-11.md) and the current manifest.

## Historical snapshots and original plan

The dated statements below describe their recorded state; the current block above
and continuation03 supersede older sign-in, zero-output and no-new-call statements.

**Continuation02:** the inspected Chrome session reaches Console sign-in but
supplies no usage receipt. Full model work remains HELD. Bounded429 `Retry-After`
metadata and signed local observation time now survive restart without clearing
unknown usage or enabling retries. Active$0.05 is preserved; $0.50 is recorded as
Surveyor's outer ceiling. No new live request or automatic Codex restart. See
[continuation02](SURVEYOR_CONTINUATION_02_2026-11-11.md) and the current manifest.

**Continuation01:** Read-only investigation obtained no new provider evidence.
Original usage remains UNKNOWN and the full reservation is retained. Observed
status reconciliation now verifies its signed result/usage receipt; actual SDK
success/fault paths were exercised through offline HTTP transport and existing
runtime. **561 affected tests passed**, plus Ruff/format and preservation checks.
See [the continuation report](SURVEYOR_CONTINUATION_01_2026-11-11.md) for exact
cases, evidence and gate. Earlier552-test results below remain dated snapshots.

11 November2026. Surveyor is still the first active agent. The phase plan is in
[MODEL_GATEWAY_BUILD_PLAN_2026-11-11.md](MODEL_GATEWAY_BUILD_PLAN_2026-11-11.md).
The local gateway is implemented and offline checked. **Surveyor's actual-model
evaluation is held after its first uncertain request; model competence and an
improved model-quality result have not been established.** No Herald progression.

## What was built

Aditya authorized the missing local test gateway in this session. The new
`pieces/backend/model_gateway/` uses the selected Anthropic Python client behind
the shared ModelPort, with signed task/input/prompt/policy grants, current lease
checks, allowlisted native tools, private key loading and signed usage receipts.
The existing Python scheduler, validators and collector still own execution.
An opt-in `scripts/live_surveyor_model_eval.py` composes the two pieces; agents
never import backend code. Production GU/control/custody, real source collection,
provider/payment jobs, isolation and merchant delivery remain separate gates.

One SQLite project ledger in `~/.config/goldgraft/model-budget.sqlite` atomically
reserves allowance across processes and all agents. Stable request identities,
unknown usage, Stop and restart survive process death. No allowance reset or cap
increase is implemented. Unknown requests block new paid identities. The key stays
in its existing owner-only private configuration; no key value or hash was saved
in this evidence or repository.

The isolated evaluation environment pins **Anthropic Python2.7.0** and
**claude-haiku-5-5**, with 24,000 input /1,536 output tokens per turn, four turns
per batch, retries0,90-second timeout, standard tier/speed, thinking disabled and
no hosted tools or cache writes. Current standard list prices are $0.10/$0.50
per million input/output tokens for this bounded profile. See the official
[model overview](https://platform.claude.com/docs/en/models/haiku-5-5/overview),
[pricing](https://platform.claude.com/docs/en/about-claude/pricing) and
[SDK release](https://github.com/anthropics/anthropic-sdk-python/releases/tag/v2.7.0).
Token counting is a preflight estimate; returned usage must still reconcile.
API processing was limited to original synthetic MIT snippets; account-specific
retention, residency and credits were not asserted or changed.

## Pilot result and improvement

The named question was whether the model could read source/matches/omissions and
produce a checked RootMap for `inventory-nvp`. Worst-case allowance was presented
before dispatch: **3,168 micro-USD per turn ×4 =12,672 micro-USD ($0.012672)**.
The active cumulative checkpoint remains50,000 micro-USD ($0.05), inside the
shared $20 project ceiling. $5 remains an outer reviewed checkpoint.

One count-token preflight returned successfully, then one SDK inference request
was attempted under `surveyor-nvp-baseline-v1`. The runtime returned UNKNOWN in
1.100541 seconds. There is **no accepted model inventory, confirmed provider
usage, message ID or HTTP request ID for that inference attempt**. The attempt
finished around **11 November01:48:18 IST /10 November20:18:18 UTC**, using the
saved report's file timestamp; this is a local timestamp, not a provider receipt.
The report's `actual_inference_calls:1` means one SDK request was attempted; it
does not establish that generation completed or that the request was free.

The original gateway caught both provider exceptions and response-validation
errors as UNKNOWN and discarded their diagnostic metadata. That was an
implementation gap: the original failure cannot now be attributed confidently
to the key, account, network, model, SDK or output. It is not a scored model
quality failure. The original saved result remains unchanged.

The gateway now journals signed, immutable, bounded provider metadata before
normalizing responses. Known response token/model/request fields survive a later
validation failure. SDK failures retain only a closed category, HTTP status and
validated request ID; error bodies, headers and arbitrary exception text are
excluded. Tests cover actual pinned-SDK HTTP-error behavior without network,
restart persistence, unqualified-model usage retention, private text exclusion
and no extra dispatch. This improves failure diagnosis; it does not recover the
first receipt or demonstrate better Surveyor model quality.

A subsequent **read-only, non-generative** usage-analytics check with the existing
credential returned HTTP401. Its request ID is recorded privately in
`read_usage_result.json`; it belongs to the analytics check, **not the inference**.
No billing/account setting changed. The
[Usage and Cost Analytics API](https://platform.claude.com/docs/en/manage-claude/usage-cost-analytics-api)
requires an eligible admin/analytics credential; this401 does not establish that
the inference key is invalid. No broader credential was requested or created.

## Budget and remaining gate

| Item | Current recorded USD |
|---|---:|
| Confirmed usage priced by the ledger | $0.000000 |
| Entire retained batch reservation | $0.012672 |
| Uncertain submitted turn, included in that reservation | $0.003168 |
| Unused batch allowance, also retained | $0.009504 |
| Active cumulative checkpoint | $0.050000 |
| Shared project hard ceiling | $20.000000 |

Zero confirmed spend is **not proof of zero charge**. The whole batch reservation
is retained. No replacement inference, second case, automatic retry or prompt
quality comparison has been run. Available numerical allowance is unusable for
another paid request while this original request is uncertain.

To resume, obtain provider-side status and usage/billing evidence attributable to
this request. Check [Console Usage](https://platform.claude.com/usage) and Cost for
the configured key/model around the timestamp above. Delayed/rounded aggregate
zero alone is insufficient to release the reservation. If the Console cannot
identify it, provider support or a suitably attributed usage export is needed.
Do not paste the key, reset the ledger, declare the request free or retry under a
new identity. Reconciliation must retain the original batch/turn identity and
verified evidence; then offline qualification and a concretely scoped next batch
can resume within the existing allowance.

## Verification and scope

Private evidence root:
`/Users/aditya/reports/goldgraft-model-gateway-20261111/`.
The baseline qualification snapshot pins the code used for the first attempt;
the refreshed qualification pins the corrected gateway. Historical evidence is
retained. Check records contain exact commands, exit statuses and log hashes.

The earlier affected suite passed548 tests before the pilot. Final checks and
hashes are recorded in `FINAL_VERIFICATION.json` and
`SURVEYOR_MODEL_GATEWAY_MANIFEST_2026-11-11.json`. The runtime integration test
uses the actual local gateway and two controlled provider responses, inspects
the accepted refund inventory, and verifies resume makes no extra dispatch.
This is offline component evidence, not an API-generated output.

All454 frozen frontend inputs,327 original tracked files, original status/HEAD
and frontend bytes are unchanged. No shared format, frozen fixture, frontend,
deployment, other agent, merchant/payment, Git mutation or Plan6 work was added.
Surveyor's source-only sponsor connection phase is N/A. Its existing literal
catalog, bounded source context and unqualified API mappings remain limitations.
The broader20-case/three-repeat real-model design remains unrun.

## Decisions

The new boundary is an in-process local synthetic evaluation gateway; no server
or replacement agent framework was necessary. The shared contracts and default
offline runtime remain unchanged. When the first request became uncertain,
preserving its allowance took precedence over completing more paid cases.
The observed result is **local build complete, API qualification held**, not
perfection, an absolute capability ceiling or a finished Surveyor model evaluation.
