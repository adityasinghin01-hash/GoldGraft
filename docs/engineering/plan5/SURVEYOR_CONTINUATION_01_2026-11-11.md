# Surveyor continuation 01 — 11 November 2026

**Result: offline reconciliation strengthened; actual-model scope remains HELD.**
Surveyor stays active. Herald and later agents have not advanced.

## Original request investigation

The project ledger was opened read-only, without its constructor or migrations.
It contains the same single unknown turn in `surveyor-nvp-baseline-v1`, no saved
usage/result and no provider-observation table. Integrity check returned `ok`.
The original saved result and batch/turn fingerprint remain unchanged. No newer
provider receipt was found in the inspected local evidence. Nothing here
reconstructs the original response or establishes its cause or charge.

No integrated browser session was available. Native Chrome showed its profile
picker; Safari was on Start Page. The read-only Console Usage page briefly
showed its title/cookie notice and then remained blank, including after one
reload. No authenticated account, usage or cost evidence was obtained. The
created tab was closed. The known analytics401 was not reprobed, and no new
credentials, account settings or support messages were created.

The installed pinned SDK accepts the fields used by the gateway, including
standard speed. This rules out that narrow signature mismatch in the inspected
installation; it does not diagnose the historical request. No real inference or
token-count request was sent during this continuation.

## Bounded fix and verification

Inspection found that `ModelPort.reconcile` returned an observed status without
authenticating its persisted result/usage, whereas result retrieval and turn
reuse already checked the signature. Two regression cases first failed because
tampered result and usage records were reported as observed. Reconciliation now
verifies the existing signed receipt before returning observed status. The fix
adds no new reconciliation authority and does not resolve the original unknown.

Seven additional offline cases exercise the actual Anthropic2.7.0 client,
private synthetic credential loader, gateway, existing runtime and synthetic
control/tools/collector through HTTP MockTransport. Ordinary pytest networking
remains denied. The success case uses two controlled SDK responses, consumes a
validated one-refund inventory with its exact file/line, and reopens runtime
state without new requests. Six fault cases cover HTTP400/401/429/500, timeout
and connection loss: one preflight and one inference attempt each, no retry,
signed safe diagnostics, full reservation retained and no replacement identity
after fresh ledger/runtime instances. These HTTP statuses are synthetic faults;
they provide no evidence about the original paid call or its credential.

The first success-test run had an incorrect test call to `inspect_inventory`;
it was corrected to supply its required provenance arguments. Product behavior
was not relaxed. Initial lint/format failures were corrected before regression.

| Check | Observed result |
|---|---|
| Receipt regression before fix | 2 failed as intended |
| Broker suite after fix | 16 passed |
| SDK/runtime success and faults | 8 passed, including the existing controlled-provider case |
| Full affected agent/gateway suite | **561 passed in94.81s**, no network/API calls |
| Ruff lint and changed-file format | Passed |
| Frozen frontend inputs | All454 hashes unchanged |
| Original checkout | All327 tracked hashes, HEAD and full untracked-file status unchanged |
| Frontend and baseline result | Unchanged |
| Persistent project ledger | Logical rows/schema unchanged; integrity `ok` |

Counts overlap; do not add them. The nine added cases are two receipt negatives
and seven SDK/runtime cases. Transport-controlled output is offline component
evidence, not model competence or actual API output.

## Versions, money and remaining gate

Model/profile unchanged: `claude-haiku-5-5`, Anthropic2.7.0, 24,000 input and
1,536 output tokens per turn, four turns, retries0, timeout90s, standard speed/
tier, thinking disabled, no hosted tools/cache writes. Prompt, policy, tools,
shared schemas and runtime architecture were unchanged. Fresh source/check
hashes are in the updated gateway manifest and qualification; previous snapshots
are preserved under `continuation-01/before/`. Model/pricing/account freshness
must still be verified before any future paid batch; no new entitlement claim
is made by this offline qualification refresh.

Confirmed ledger-priced usage remains **$0.000000**; retained reservation is
**$0.012672**, including **$0.003168 unknown** and **$0.009504 outstanding**.
Zero confirmed usage does not prove zero charge. Active authority stays$0.05,
outer reviewed checkpoint$5, target$15 and hard shared project ceiling$20.
No new paid identity, budget increase, key read or ledger write occurred.

Required next evidence is provider-attributable terminal status and usage/cost
for the original request around10 November20:18:18 UTC /11 November01:48:18 IST,
bound to the configured key/model and original batch/turn. If Console cannot
attribute it, provider support or an attributable export is required. A rounded
aggregate zero, later HTTP error or locally invented receipt cannot clear it.
The bounded packet is `continuation-01/reconciliation-packet.json` in the private
evidence root `/Users/aditya/reports/goldgraft-model-gateway-20261111/`.

P1–P4 selected offline scope remains passed; P5 sponsor phase is N/A. P6 actual
model pilot is attempted/held; P7 model improvement and P8 model reliability are
held. P9 offline output use is checked, full selected model closure is held.
Literal catalog/dynamic-call/context/output limits and production GU/VJ/SH
qualification remain unchanged. No perfection or absolute capability claim.
