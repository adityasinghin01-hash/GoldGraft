# Surveyor continuation 02 — unattended authority and reset handling

11 November2026. Surveyor remains active; full real-model scope is HELD.

## Authority and access

Aditya reauthorized unattended API testing/improvement, completing Surveyor before
later agents, and waiting for temporary limit resets. His instruction mentions
both a$0.05 cap and a maximum about$0.50 for this model. Conservative execution
keeps **$0.05 active cumulative authority** and records **$0.50 as Surveyor's
outer ceiling**. It does not raise the ledger checkpoint or grant recurring
spend on a timer. The existing$20 project ceiling also remains. All spent,
outstanding and unknown amounts stay cumulative across sessions and resets.

A fresh browser inventory exposed an existing Aditya Chrome profile. Opening
Console Usage in that inspected profile reached the **sign-in form**, with no
authenticated usage/cost data. No login, terms acceptance, OAuth grant, new key,
account/billing change or support message occurred. The Console tab was closed.
This is evidence about that inspected session, not every account/profile.
The separate known analytics401 was not repeated. No live inference/token-count
request was made. The original unknown request and reservation are unchanged.

## Reset diagnostic improvement

Official [Anthropic rate-limit documentation](https://platform.claude.com/docs/en/api/rate-limits)
describes temporary429 responses and reset/delay information. That timing does
not reconcile billing for a different unknown request. The installed SDK's
hidden retries remain disabled.

The provider boundary previously discarded rate-delay information. It now keeps
only an HTTP429 `Retry-After` value containing one to five ASCII decimal digits
in the inclusive0–86,400-second range. Other statuses, negative/fractional/text/
oversized values are excluded. Raw headers, bodies and exception text remain
excluded. Provider observations now include a signed local UTC recording time,
so future bounded delays have an attributable local time anchor after restart.
This is scheduling metadata, not a new usage receipt or automatic retry grant.

Tests first exposed the three missing valid delay values and missing timestamp.
Eight SDK transport cases check valid/invalid header values, three checks deny
reset metadata on other statuses, and one fresh-ledger test proves even delay0
cannot clear an unknown turn, replace its identity or release its reservation.
All tests use synthetic credentials and denied networking. No sleep loop,
background inference daemon or automatic paid retry was installed.

No live API rate limit/reset time has been observed. The current hold requires
provider evidence; elapsed time alone cannot satisfy it. Official
[OpenAI documentation on Codex Goals](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex)
describes controlled continuation and stopping conditions; reading it does not
configure restart in this session. **Automatic restart after Codex itself stops
for a usage limit has not been established or configured.**

## Checks, money and remaining work

Exact current checks/counts and file hashes are recorded by the gateway manifest
and private FINAL_VERIFICATION.json. The full affected regression passed
**573 tests in96.20s**; the targeted provider/gateway/runtime group passed51 tests,
plus Ruff lint and format checks. Counts overlap and must not be added.
Prior continuation01's561-test snapshot remains preserved independently.

Confirmed priced project usage remains **$0.000000**; **$0.012672** is retained,
including **$0.003168 unknown** and **$0.009504 outstanding**. Zero confirmed
usage is not proof of zero charge. Persistent ledger rows/schema, original
batch/turn/result and unknown gate were not mutated. Frozen inputs, original
checkout and frontend remain preserved by the current preservation check.

Next required external evidence: provider-attributable terminal status and
usage/cost for `surveyor-nvp-baseline-v1` and its original turn around
10 November20:18:18 UTC /11 November01:48:18 IST. No inference HTTP/message ID
was retained. Authenticated Console evidence, an attributable export or provider
support must resolve this; a later response or rounded aggregate zero cannot.

Then requalify current pricing/model/SDK/profile/authority and run the tiny paid
baseline; inspect actual output and consumption, improve demonstrated weaknesses
on novel cases, exercise real-model negatives/reliability, and close Surveyor
only on that evidence. Later agents stay sequentially held behind this closure.
No production GU/VJ/SH service, HTTP deployment or merchant qualification follows
from these synthetic gateway tests.
