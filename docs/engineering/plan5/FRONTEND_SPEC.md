# Reconciled frontend specification

PROPOSED, not a built app. Implementation will be in Antigravity after explicit Phase5.3 start. Local `pieces/web` contains only a placeholder; the protected Desktop pack is27 authored Markdown files plus generated references/samples, not running UI. Preserve its useful concise copy, top layer/Details, explicit sample labels and evidence-linked numbers. This pack supersedes incompatible journey/auth/authority/Done behaviour; Desktop/reference/personal files stay untouched. Palette and visual styling remain later.

## Effective Markdown inputs and launch

The [frontend execution prompt](ANTIGRAVITY_FRONTEND_START_PROMPT.txt) authorises AG1–AG6 when pasted. Open the isolated repository root `/Users/aditya/dev/GoldGraft-plan5-build` after Codex creates it and publishes a checked `docs/engineering/plan5/FRONTEND_READY.json`; implement only `pieces/web`. Follow [two-terminal ownership/readiness](TWO_TERMINAL_WORKFLOW.md). Codex drives shared bootstrap, agents and delivery; Antigravity must consume the actual accepted generated interface/fixture revision rather than the current Markdown proposals alone.

| Markdown source | How implementation uses it |
|---|---|
| This FRONTEND_SPEC | Effective screen/state/copy/action/component/API semantics, including preserved safe authored copy |
| ANTIGRAVITY_HANDOFF | AG1–AG6 task order, exact component targets, fixture scenarios and reporting |
| SHARED_BOOTSTRAP_PLAN | Exact proposed route/type semantics; use actual generated versions only after SI01 checks |
| COMPONENT_TEST_PLAN W01–W10 | Real rendered UI/browser/privacy/access/recovery acceptance against labelled fixtures |
| Canonical connection JOURNEY_AND_COPY_SPEC | J01–J14 source/controller/processing/Start/return requirements, reconciled by this pack's exact draft/claim protocol |
| Protected Desktop words/screens and private frontend inventory | Read-only historical copy/provenance; retain compatible text via this pack, do not import old AGENTS/secret/local-list/Done rules |

No new Figma/mockup stage is required. Build usable accessible structure and actual local interactions first; colour/branding/polish remains the later visual decision. Record implementation changes/results in `pieces/web/docs/FRONTEND_BUILD_REPORT.md`; request shared-interface corrections through the local ownership protocol, not frontend edits to generated/shared files.

## Stack and source of truth

Keep supplied React18 + Vite SPA, strict TypeScript (no `any`), React Router, TanStack Query, same-origin HTTP/native EventSource, CSS Modules and tokens. Keep Community-licensed AG Grid/Charts for views that need them, not for simple forms. Node22 matches the repository toolchain. Initial package lock is created/reviewed during authorised build; no packages installed here. Generated SI01 types are the only wire types. View-model functions narrow server data and format it; they do not create a second contract or authority engine.

Server-authorised saved cases replace localStorage as truth. Case IDs/links confer no access. Use server session HttpOnly/Secure cookies and backend-owned provider return state. UI takes no model, PayPal or ordinary host/source passwords/tokens. The qualified J06 provider-specific once-only scoped-host-key path is an explicit exception: trusted custody intake, ephemeral uncontrolled input, no query/log/state/storage persistence, clear immediately on submit/unmount. Unsupported scoped keys produce Setup needed, not a classic-key workaround.

No current API is silently widened. New routes below are the proposed SI01 map. Legacy `/shops/.../connect` generic secret forms and `/grafts/...` demo routes cannot run the new admitted journey. Safe historical exploration panels may later use explicit legacy adapters labelled sample/legacy; they cannot assert full live delivery.

## Browser routes and exact user-state behaviour

One CaseShell persists case identity, session/access boundary, current step, concise status, required actions and optional Details. Routes are proposed browser destinations, not existing APIs; view count is not a requirement.

| View / browser route | Main copy and actions | Evidence / holds / recovery |
|---|---|---|
| Entry `/` | “Which shop needs an upgrade?” URL → Continue | Verified origin/support identity; bounded draft only. Invalid/blocked URL error preserves entered safe value; no ownership claim |
| Saved cases `/cases` | “My upgrades” → Open case / New case | Authorised current membership, loading/empty/error/session expiry; no cached private case from another session |
| Setup `/cases/:id/setup` | “Sign in to save your case”; “Who manages this shop?” → Connect resources / Ask maintainer | J03–J04 identity/controller/recipient binding. “Waiting for your maintainer”; invite copy only when server permits, never auto-send |
| Source, within setup | “Connect this shop’s code” → Connect GitHub / Code is somewhere else / Ask maintainer | Selected read-only Reader; show approved repo/revision/breadth/recipient. Qualified local-folder/cloud/host-export choices; unavailable routes explain limitation, no dead upload route |
| Host, within setup | “Connect the running shop” → qualified adapter | Resource/environment/controller/read breadth visible; split providers allowed. Wrong account→change; scoped-key entitlement unknown→Setup needed |
| Processing/readiness, within setup | “Where your code goes”; “Checking setup” → View checks | Named actual storage/runtime/model recipients, copy/retention/region limits, sandbox scope and later apply approval. Material facts always visible; no invented terms. Missing/stale evidence shows item, owner and next action |
| Ready, within setup | “Ready for sandbox work” → Start | Current WorkPackage/graph/policy/grant epochs/source/expiry; required flow scope/exclusions. Disabled Start reason is visible; readiness is not payment proof |
| Progress `/cases/:id/work` | “Submitting” → Stop; then “Accepted. Waiting for a worker” / “Preparing sandbox” / “Sandbox work has started” | Immutable receipt separate current status; operation_started only from verified BASELINE_READ. Model call/build/payment success need their own facts |
| Evidence `/cases/:id/evidence` | “Old pieces”, “Payment tests”, “Proof” → choose scenario / Details / Replay saved result | Scoped RootMap/capture/proof projection; OLD defects and NEW regressions distinct. Missing→“No verdict yet.” / “Not proven yet: some evidence is missing.” Synthetic/replay labels always visible |
| Review `/cases/:id/review` | “Review upgrade” → Approve eligible actions / Later | Exact bundle/source/image/config/state/recovery/trigger plan, required controllers/resources/destinations/expiry. Viewer/requester cannot approve others' resources; separate source/registry/host/data/callback authority. DirectArtifact shows no Git/PR requirement |
| Delivery `/cases/:id/delivery` | “Applying upgrade” / “Checking the running shop” / “Checking delivery status” | Submitted/queued/pending/unknown versus observed active runtime distinct; no manual deploy instructions. Stop cannot imply no change. Recovery panel exposes approved current-compatible route and required controller action |
| Handover `/cases/:id/result` | “Checking independent operation”; then current outcome and keep/remove/pending record | Actual site/config/state/callback/legacy checks, Q0–Q4, merchant retained assets, scoped cleanup. Upgrade observed with exit pending is not Complete |
| Public proof `/proof/:public_id` | Scoped test/integrity description → Check | Public-safe projection only. Signature check≠payment/delivery safety; no provider transaction IDs/captures/source/customer identity. Explicit consent/policy for public availability; no public link by default |

Optional recipes/fleet/security/comparison views stay outside the critical merchant journey and behind authorised aggregate/private or explicit sample projections. No comparative performance/coverage/time/cost assertion from placeholders. `Mock mode: showing saved sample data, not a live system.` remains visible for every synthetic adapter, including a localhost HTTP fake.

## Copy preserved and corrected

Keep `Details`, `Hide details`, `Retry`, `Reconnect`, `No verdict yet.`, `Not proven yet: some evidence is missing.`, `The new checkout is wrong here.`, `Replaying the saved result`, `Payment tests`, `Old pieces`, `Proof`, `Progress`. Keep short top-layer text and optional technical Details. Consent/scope/unknown/exclusions/sample/required-action facts must not be folded away to meet an artificial word/dialog limit.

Use `Your case is saved` only after server persistence; `Stopped` only after confirmed termination/current external status; `Upgrade verified; cleanup pending` only when both facts are supported; `Upgrade complete` only from current exact completion projection with required exit evidence. `PR created`, `Signature verified`, `Files received` and `Baseline files verified` describe their narrow facts. Remove “any shop,” fixed41-minute promises, green connected-as-ready and unconditional switch-back/old-code-delete copy.

## Reusable components and data ownership

| Component / target file | Props derived from generated contracts; responsibility | Required states/actions |
|---|---|---|
| `case/CaseShell.tsx` | case ID/name, current authenticated CaseView | loading, unavailable, expired, current snapshot; clear query cache on identity change |
| `connection/ResourceConnectionCard.tsx` | resource/controller/scopes/recipient/check projection | missing, waiting, current, revoked; provider redirect/refetch, never trust return query flag |
| `connection/SourceRoutePicker.tsx` | server-qualified route capabilities | Git/default, folder/upload resume, unavailable cloud/export, no-code maintainer path |
| `connection/ProcessingDisclosure.tsx` | qualified actual processing projection | missing profile holds Start; copy, recipients, limits and authority visible |
| `connection/ReadinessChecks.tsx` | versioned check status/reason/owner/actions | pass/missing/unsupported/failed/stale/unknown; no local all-green calculation |
| `lifecycle/AcceptanceReceipt.tsx` | immutable WorkAcceptance | submitting, accepted receipt separate current status; lost response query |
| `lifecycle/WorkStatusPanel.tsx` | WorkStatus + lifecycle/task projection | queued/provisioning/operation/held/unknown/retry/failed; no elapsed fake percentage |
| `lifecycle/StopControl.tsx` | current cancel permission/status | intent pending/fenced/termination pending/confirmed/unknown; one logical cancellation |
| `evidence/EvidencePanel.tsx` | private evidence/proof refs and subject | no data/partial/old defect/new defect/subject mismatch/sample/replay; literal escaped text |
| `lifecycle/ApplyReview.tsx` | current exact review/action plan/authority hints | stale/incomplete/split-controller/expired/revoked; approve current exact plan only |
| `lifecycle/DeliveryStatus.tsx` | DeliverySnapshot and observation projections | accepted != live; unknown reconnect queries same effect; never local retry deploy |
| `lifecycle/RecoveryPanel.tsx` | authorised RecoveryPlan and current evidence | known safe/incident/approval required/unavailable; no financial undo button |
| `lifecycle/ExitChecklist.tsx` | merchant keep + temporary cleanup/exit projection | preserved/local denied/revoke pending/deleted/backup held/exported unknown; no generic Delete everything |
| `components/Details.tsx`, `StatusRegion.tsx`, `ProblemBanner.tsx`, `EvidenceClass.tsx`, `MoneyAmount.tsx` | shared accessible presentation | truthful empty/loading/error, sample tags, polite meaningful status, integer minor-unit money |

At `pieces/web/src/` centralise `api/http.ts`, `api/sse.ts`, `api/contracts.ts` (generated import/re-export only), `api/caseAdapter.ts`, `state/caseProjection.ts`, `copy/messages.ts`, `lib/format.ts` and `testing/fixtureAdapter.ts`. Do not place secret values into React Query/global context, analytics/error events or persistence. Money formatting uses integer/string minor-unit arithmetic with currency exponent policy; no floating payment arithmetic. AI usage cost is separately labelled accounting data.

## API/SSE contract map

All listed paths are **proposed new v2** until SI01. Exact request/response registry in [shared bootstrap](SHARED_BOOTSTRAP_PLAN.md). Same-origin session/CSRF/current role checks apply to every mutation; Idempotency-Key identifies one action, not permanent permission.

| API operation | Response / frontend use |
|---|---|
| `POST /v2/connection-drafts` `{shop_url}` then authenticated `POST /v2/connection-drafts/{draft_id}/claim` | DraftCase/1 then ConnectionCase/1; bounded anonymous capability/continuation/claim preserves J02→J03 and same case. Already signed-in new case uses POST /v2/connection-cases |
| `GET /v2/connection-cases` cursor/limit | CaseList/1 authorised summaries only |
| `GET /v2/connection-cases/{case_id}/view` | CaseView/1 coherent versioned private projection; not arbitrary client-join of stale fragments |
| `POST .../{case_id}/provider-intents` | ProviderIntent/1 bound controller/action/resource/continuation; official return then refetch |
| `POST .../{case_id}/invitations` | ControllerInvitation/1 scoped copy-link, no automatic outbound message |
| `POST .../{case_id}/source-uploads`; `/source-uploads/{upload_id}/chunks`, `/finalise`, `/cancel`; GET status | Canonical UploadSession/1 and chunk receipt; bounded hashes/cover/resume; completion≠source-to-site match |
| `POST .../{case_id}/action-intents` | ActionIntent/1 before Start, bound current readiness |
| `POST .../{case_id}/actions` StartWorkRequest | 202 immutable WorkAcceptance/1 only after commit; rejection/current-cancelled/unknown typed distinctly |
| `GET .../{case_id}/actions/{action_id}` | ActionStatusView/1 with current WorkStatus and accepted receipt ref/null |
| `POST .../{case_id}/actions/{action_id}/cancellation` | WorkCancellation/1 intent/status, never false termination |
| `POST .../{case_id}/lifecycle-runs/{run_id}/resume` | LifecycleRun/1 after current scope/input/authority validation; no old Start replay |
| `GET .../{case_id}/review-bundles/{bundle_id}` | PrivateReviewView/1 scoped exact subject + safe evidence summaries |
| `POST .../{case_id}/apply-approvals` | ApplyApproval/1 from authenticated actual controller, exact plan; backend derives allowed resource scope |
| `GET .../{case_id}/events` | CaseEvent/1 committed cursor stream; projection ACL checked on connect/reconnect/role change |
| `GET /v2/public-proof/{public_id}` | PublicProofView/1 only if publication authorised; Check refetches this projection, never invents a verification POST; old certificate endpoint cannot leak private bundle |

Provider return tokens/codes are handled by backend-specific routes and never stored/logged by SPA; security-critical provider callback endpoints belong GU01. The only qualified credential intake is a separate trusted surface/port, not a generic SPA object or the ordinary connect request. Unqualified source/host routes stay disabled; frontend cannot invent functional integrations.

SSE uses same-origin cookie session, credentials policy and no query tokens. Native reconnect supplies Last-Event-ID for the same EventSource; page reload first fetches snapshot/cursor. Snapshot includes last_event_seq; new stream's nonsecret `after` cursor is a proposed server-supported replay parameter, authorised independently. Duplicate/old cursor is ignored only after schema validation; gap/unknown schema/required malformed event marks projection stale and forces snapshot refetch. No event after three reconnects never means done. Stream204/closed/errors change connection health, not work outcome. A role/session revoke clears private display/cache and stops stream; Stop is a separate backend action.

While snapshot/authority is stale, disable Start/apply/resume and show reason; safe status refetch/sign-in remains. For lost mutation response, retain logical action identity in safe in-memory state and recover via current case snapshot/server action lookup on reload, not a new POST. Server keeps pending action identity in CaseView, so browser storage is unnecessary. Payload details with secrets are never retained for retry.

## Accessibility and actual browser acceptance

Visible labels/error association, logical heading/reading/focus order, keyboard-operable route/source selection, focus restoration on provider return, status text beyond colour and one polite meaningful live region. Avoid announcing every log/token/tick. Critical action error is announced with next action. Review page supports long disclosures; any dialog has accessible name, focus containment, Escape-to-close and return to invoker. Closing a dialog/feed never cancels an accepted effect. Reduced motion does not hide status; responsive layout preserves required actions and scopes.

Standards basis: [W3C status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html), [APG dialogs](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/), [WHATWG SSE](https://html.spec.whatwg.org/dev/server-sent-events.html), [OAuth security BCP](https://datatracker.ietf.org/doc/html/rfc9700). These guide the design; no accessibility/provider conformance is claimed before actual checks. Browser cases and privacy assertions are specified in COMPONENT_TEST_PLAN.
