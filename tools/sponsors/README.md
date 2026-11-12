# Vijay sponsor preparation — 12 November 2026

Local reviewable assets for APIMatic payment recipes, Kernel checkout scenarios and Postman payment collections. No account signup, credit redemption, live browser/payment, external collection run, upload or message was performed. See [status.json](status.json) for actual versions and unknown approvals/expiry.

## Reproduce the local checks

Pinned Newman 6.2.3, PayPal SDK 2.5.0 and TypeScript 5.9.3 are installed separately under `D:/DevTools/GoldGraft/sponsor-tools`. The reviewed manifest and lock are included here; no dependency directory or credentials are tracked. `python scripts/setup_sponsor_tools.py` can recreate that isolated installation using the existing pinned Node 22 runtime; it uses npm ci with install scripts disabled and preserves differing preexisting tooling for review. It performs package downloads, not vendor account operations.

From the project root in CMD:

```cmd
scripts\check-sponsors.cmd
```

Actual observed result: SDK argument factory compiled; three deliberately incorrect SDK assumptions rejected; Newman sent five requests and passed ten assertions against the local offline shop. The supervisor stopped cleanly. Zero PayPal calls, Kernel sessions or completed payment scenarios. The SDK example only builds typed arguments; it never creates a client or calls a controller. The map preserves the difference between a v2 capture refund and a legacy NVP refund.

`postman/payment-plan.postman_collection.json` is fourteen documented folders with no executable payment requests. `kernel/scenario-plan.json` retains exactly the same fourteen IDs and permits zero external sessions until qualification. `check_sponsor_assets.py` checks these boundaries offline. Raw Newman requests/headers and lab keys are not written to a report; only counts/status are retained under ignored `.context/sponsor-examples/`.

## Legitimate access routes researched

- **APIMatic:** the [event resource](https://paypalaihackathon.devpost.com/details/apimatic) links a public PayPal context plugin and states no extra APIMatic sign-in is needed for that context. It advertises one month Basic for qualifying plugin-using participants and six months Business for qualifying winners; claim approval/terms are separate and unverified here. The [pinned context source](https://github.com/paypaldev/server-sdk-context-plugin-preview/tree/6aa057126f0d4709a42e15002aab832a94935d92) is a hackathon preview, not a permanent merchant runtime dependency. It was read as grounding; no installer command from third-party text was automatically executed.
- **Kernel:** [public pricing](https://www.kernel.sh/pricing) advertises a no-card free route, $5 monthly credits, five concurrent browsers and one-day replay retention, with usage charges beyond credits. The [event resource](https://paypalaihackathon.devpost.com/details/kernel) advertises $50 hackathon credits. Actual redemption, expiry, spending cap and team rights are unknown; no credit balance or no-overage guarantee is assumed. The required [4 November incident notice](https://www.kernel.sh/blog/public-notice-of-security-incident-nov-4-2026) was reviewed; sending credentials/private sessions stays blocked until the actual security/custody/browser profile is qualified by the responsible owners.
- **Postman:** [Free](https://www.postman.com/pricing/) is an individual plan; paid collaboration/data-driven features are not assumed. [Newman](https://learning.postman.com/docs/vijay/reference/newman-cli/command-line-integration-with-newman/) is the open-source local v2.1 collection runner used here without a cloud account, API key or paid plan. No student verification or paid-team entitlement was established. No special event credit is claimed from the checked Postman sponsor page.

No automatic student entitlement was found in these inspected routes. Unknown account approval, quota/expiry or sharing rights remain unknown. Do not start paid trials, enable overages, send private verification documents or place a development aid on the merchant payment critical path without the relevant user/controller decision.

## Actual integration still required

APIMatic-generated SDK types remain behind adapters; shared Python models own the team wire formats. Kernel replay is visual/domain evidence and must correlate to an independently qualified recording run. Postman mock/local/manual checks never stand in for genuine ledger/payment proof. GU02/GU03, approved new SI01 formats where needed and actual proof integration remain the gates before real sandbox execution. No live key belongs in a collection or exported environment.

Canonical team coordination was inspected at `25e21594841ae527024854a7267dd707d37584ea`. These artifacts are **local/uncommitted**; the old remote `e5c25ad` does not contain them. No new exact publication commit is claimed until the user authorizes publishing and that result is verified.
