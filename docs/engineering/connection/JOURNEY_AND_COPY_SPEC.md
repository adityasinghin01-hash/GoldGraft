> Reviewed team baseline, 6 November 2026: this connection proposal is subject to the review addendum, implementation bridge and lifecycle atomic protocols linked from [engineering START](../START_HERE.md). Earlier programme status/owner restrictions in this frozen source are historical. No current API/implemented capability is created by this text.

# Continuous case and exact visible behaviour

Status: paper engineering specification, 6 November 2026. Nothing here is a deployed feature or current API unless explicitly labelled CURRENT. Proposed components/interfaces require later implementation and contract approval. Plan 1 ends at verified first sandbox operation; agent internals and Plans 2–6 remain outside scope.

All copy below is proposed. No frontend built. Identity/processing disclosures are essential visible information; technical proofs are optional Details. Route paths here are conceptual UI destinations, not current API assertions.

| Step | Visible words → user action → automatic work / evidence / recovery |
|---|---|
| J01 laptop | Open verified GoldGraft origin. Publisher/support identity visible before grants. Canonical domain unregistered/unverified in this run; no invented live link. Uncertain origin: stop. |
| J02 shop | “Which shop needs an upgrade?” / Continue. URL is sole initial input. Bounded server draft; no private scan or shop ownership inference. Correct URL without losing case. |
| J03 identity | “Sign in to save your case” / Continue. WorkOS email code in provider flow, MFA when required. Return to same draft via bound continuation. Resend/expiry preserves draft; email proves contact only. |
| J04 maintainer | “Who manages this shop?” / Connect resources or Ask maintainer. Copy scoped invitation; actual controller authenticates and approves exact requester/shop/resource/recipients. “Waiting for your maintainer” while pending; no private findings disclosed. |
| J05 source | “Choose this shop’s code” / Connect GitHub. Official selected-repo Reader consent and role check; exact repo/revision/read permissions shown after controller binding. Wrong org/account: Change account; denied approval: Waiting for owner. |
| J06 host | “Connect the running shop” / Connect Render. Scoped-key controller setup in official provider page, then secure once-only field. Show workspace read breadth and chosen service/environment. No scoped keys: Setup needed. No password or terminal commands. |
| J07 preparation | “Preparing your test setup”. No routine user input. Check qualified synthetic identities/fixture/callback catalogue only. Not merchant live identity; missing genuine fixture -> Setup needed. |
| J08 trust | Inline “Where your code goes”: selected code is copied; named storage/runtime/model recipients; initial read only; Start sandbox scope; retention/deletion limitations; later publication separately approved. Provider/policy values come from qualified runtime configuration, never placeholders rendered as a promise. Details optional; material facts not folded. |
| J09 checks | “Checking setup”. Static inventory, correspondence, scopes/policy/runtime readiness; optional View checks. Failure shows exact missing capability plus responsible controller and Retry/Connect resource, preserving safe progress. No fake percentage. |
| J10 review | “Ready for sandbox work” / Start, only when current predicate true. Show shop/env/source/scope/exclusions and processing. Stale check disables Start with short reason. Readiness not payment proof. |
| J11 submit | “Submitting” / Stop. Server commits acceptance/outbox. Timeout: Checking status of same action; never duplicate job. |
| J12 queued | “Accepted. Waiting for a worker” / View receipt. Durable private receipt, queue/retry visible. VM/lease alone: Preparing sandbox. |
| J13 started | “Sandbox work has started” / View progress. Only valid supervisor baseline read evidence advances label; Details says “Baseline files verified”, not model/payment complete. Agent-inference claim needs separate gateway evidence. |
| J14 return | “Your case is saved” / Resume. Authenticated server case status; replay/current grant checks. Accepted work may continue without laptop once implemented; no automatic resurrection on regrant. |

Recovery catalogue: invalid URL (correct); blocked destination (supported public URL only); wrong account/resource (switch before disclosure); invite expired (new invite same case); controller denies (no source attached); unavailable scoped key (await provider entitlement); unverified image/runtime (Match not verified); processing terms missing (Setup needed, no egress); stale source/config (review new scope); worker outage (accepted/queued); ambiguous Stop (Cancellation pending); unauthorised read (generic unavailable, no enumeration).

Keyboard/focus: one heading/label per state, visible labels, provider return focus to relevant case step, aria-live polite for status not every log line, errors linked to inputs, no colour-only status. No per-step Accept popup, installer, ZIP, terminal or routine expert config. Render's one-time scoped-key creation is an explicit unresolved convenience cost; cannot be disguised as universal one-click consent.

Later observed tests: owner with URL only, maintainer with separate host/code identities, agency wrong client, expired session/invite, closed-tab return, keyboard/screen reader and controller unavailable. Count both people's active effort, trust reading, provider login/MFA/key creation, coordination and backend wait separately. No under-one-minute or coverage claim until observed.

## Permanent J05, variable source route
J05 top layer is “Connect this shop’s code”. Default Connect GitHub; secondary Code is somewhere else / Ask maintainer. Alternatives shown only when needed: Other Git provider, Choose project folder, Cloud files or From hosting (only qualified routes actionable). Keep same case and downstream preparation/Start; do not require every owner to know code location. “Files received” never means “Running shop matched”. Local read access/copy disclosure and missing-cloud-permission limitations stay visible. No prevalence/coverage percentage claimed.
