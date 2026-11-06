# Independent Plan4 paper design review

6 November 2026. **Assessment: requires the material paper corrections below before Plan2 treats the lifecycle as a settled build baseline.** One Critical finding and six Important findings. These are design findings, not observed product failures.

## Scope and evidence

Applied the requirements, failure-consequence and severity approach in `/Users/aditya/.agents/skills/wayfarers-compass/parts/requesting-code-review/GUIDE.md` and its reviewer template to paper design. Read all 18 Markdown files in `outputs/plan_3/`, including both research notes; Plan1 `CONNECTION_CONTROL_PROPOSAL.md`; the root `REVISED_PROGRAMME_AND_TEAM_WORK.md` and `DELIVERY_REQUIREMENTS_UPDATE.md`; and relevant Plan1 custody, processing, storage, runtime, source-route and work-package specifications. Locations below use those files' inspected line numbers and section names. Paths are relative to the programme root unless stated otherwise.

This is a bounded independent assessment of these documents. Other Plan4 review findings, matrices and addenda were not used as review evidence; this report does not repeat the inherited catalogue. Targeted public primary-document checks covered Render disk/deploy/image behavior, GitHub merge behavior and PayPal IPN acknowledgement. No product code, account tests, implementation, live validation or team actions were performed. No independent security certification or operational proof is claimed.

The pack correctly separates initial reads from later writes, sandbox evidence from live evidence, and code recovery from financial compensation. Its preservation of historical payment origins and refusal to treat a PR or signature as completed delivery are sound constraints. The findings concern missing mechanisms or inconsistent contracts underneath those constraints.

## Material findings

### IR01 — Critical: the first persistence/callback installation has no complete state-transfer protocol

**Locations:** `outputs/plan_3/RENDER_DELIVERY_AND_STATE.md`, “Persistence and controlled maintenance,” lines 20–24; `RECOVERY_AND_ROLLBACK.md`, “Recovery baseline” and decision procedure, lines 6–15. Requirement: root `DELIVERY_REQUIREMENTS_UPDATE.md`, lines 35–37.

**Trigger and consequence:** A shop needs the prerequisite disk, maintenance control or durable callback route installed before the main upgrade. Line 22 permits a separately approved prerequisite installation/deployment, but does not specify how existing ephemeral orders/payment intents survive that *first* deployment. Merely adding a disk does not copy existing files into it. Render documents that disk attachment triggers deployment and that ephemeral filesystem changes disappear on redeploy/restart. A prerequisite redeploy can therefore destroy the very state the subsequent migration assumes exists. [Render disks](https://render.com/docs/disks)

Even with an existing disk, blocking **new checkout creation** is not a fence on existing captures, returns, refunds or notification writers. The text simultaneously requires their continued handling and a snapshot/quiescent migration after the old writer stops. An independent callback queue does not by itself serve browser returns/captures or preserve the economic intent ledger. There is no specified transfer boundary connecting the snapshot, subsequent accepted events and the replacement writer. A payment can complete while its local intent/state is omitted, leading to lost orders, duplicate processing or an unrecoverable cutover.

**Required paper correction:** Define an ordered bootstrap and cutover protocol covering the first prerequisite mutation as well as the upgrade. It must identify all writers and handlers; preserve a consistent current-state export before any destructive restart; retain origin/session identifiers and idempotency records; durably capture changes after the export; establish an explicit writer fence and replay boundary; and verify restored state plus backlog processing before reopening admission. State who serves existing browser/payment operations while the single disk-backed instance is unavailable. If this cannot be provided, require an explicitly approved bounded interruption/drain policy or hold delivery. Do not assume a sibling service can mount the same Render disk.

**External qualification gate:** The actual source export, shutdown behavior, queue/handler ownership, restore/replay consistency and interruption remain untested. A disposable failure case must interrupt the prerequisite install and the migration while an existing capture/callback completes. Public disk documentation cannot close that gate.

### IR02 — Important: run/action-group fencing does not define exclusive control of shared live targets

**Locations:** `outputs/plan_3/LIFECYCLE_INTERFACE_PROPOSALS.md`, “Durable tables,” line 83; `STATE_AND_EFFECT_TABLE.md`, lines 5 and 18–26; `RENDER_DELIVERY_AND_STATE.md`, lines 13–17. Inherited admission: Plan1 `RUNTIME_AND_BROKERS_SPEC.md`, line 21 permits two concurrent jobs per tenant.

**Trigger and consequence:** Two cases or runs target the same service, datastore or callback route. Each has a valid generation and a different action-group lock, and both can observe the same precondition before starting. The proposed uniqueness/fencing rule is per **run**, while the lock is per **action group**. The unspecified “single local effect lock” does not establish a shared-resource exclusion rule. Render serializing deploy requests does not serialize the service's state export, migration, route changes, recovery or cleanup. One run can recover or clean up underneath the other.

**Required paper correction:** Specify a durable reservation/fence keyed to canonical provider resource/environment identities, covering every affected shared state/route dependency across cases and runs. Define conflict admission, lock ordering, crash recovery and release only after unknown effects are reconciled. Cleanup must distinguish resources/grants created exclusively for this run from shared installations, keys and callback assets; it must not revoke or delete another active use. Maintain the existing rule that an external controller can still race this local reservation: detect drift and hold rather than claim provider-wide exclusion.

**External qualification gate:** Later test two real component runs against one disposable target, including overlapping dependency graphs, crash, cancellation and recovery. Neither per-run generations nor provider deploy queuing alone establish this property.

### IR03 — Important: the exact tested OCI artifact has no defined build-and-publication boundary

**Locations:** `outputs/plan_3/LIFECYCLE_BUILD_SPEC.md`, stage contract, lines 36–40; `DELIVERY_AUTOMATION_AND_AUTHORITY.md`, lines 16–23; `LIFECYCLE_INTERFACE_PROPOSALS.md`, `ReviewBundle`/`ApplyApproval`, lines 30–42; `BUILD_SLICES.md`, L02, L05 and L07. Supporting constraint: `research/RENDER_CONSTRAINTS.md`, lines 9–11 and 19.

**Trigger and consequence:** Candidate source passes tests and the controller approves delivery, but no qualified component has produced, tested and published its image into the target registry namespace. The narrative jumps from candidate checks/PR publication to a required `artifact_digest` and deployment. GitHub Contents/PR publication authority and Render Deploy Run authority do not supply registry push authority. The Render deploy endpoint also requires the image's host/repository/name to match the service configuration. A service cannot simply substitute a convenient temporary image destination. [Render trigger-deploy contract](https://api-docs.render.com/reference/create-deploy)

Without the missing boundary, builders must either invent an unreviewed privileged pipeline, ask the merchant to build/push/wire it, or deploy a separately rebuilt image whose bytes were not the tested subject.

**Required paper correction:** Add the external artifact-build/test/export/publication contract and its primary responsibility. Bind exact source, recipe, dependency/base inputs, trusted builder evidence and output image digest. Define whether tests run against the deployable image itself and how any post-merge rebuild is requalified. Give the registry publisher separate scoped authority, recipient/privacy approval, destination, immutable subject, retry/reconciliation and merchant ownership rules. Explicitly cover approval of any target image-configuration change. These are lifecycle boundaries, not internal agent design.

**External qualification gate:** Registry entitlement, private-image publication/pull permissions, provenance verification and restart pull behavior remain actual account/runtime checks. The paper should name the mechanism before those checks; it must not imply that existing source/deploy permissions already provide it.

### IR04 — Important: the common callback recipe contradicts IPN acknowledgement ordering

**Locations:** `outputs/plan_3/RENDER_DELIVERY_AND_STATE.md`, line 22: “Persist raw authenticated callback receipt before acknowledgement”; contrast `research/PAYMENT_CONSTRAINTS.md`, C06, line 20, and P07/P10, lines 42 and 45.

**Trigger and consequence:** The ingress interprets “authenticated” as requiring successful IPN postback validation before storing/acknowledging a notification. IPN authenticity depends on a separate PayPal request, which can be slow or unavailable. The delivery recipe then couples acknowledgement and potentially durable acceptance to that remote dependency. It conflicts with both the research note and PayPal's documented acknowledgement-then-validation flow. If only validated messages are retained, recoverable unverified messages can also disappear. [PayPal IPN request-response flow](https://developer.paypal.com/api/nvp-soap/ipn/IPNImplementation/)

**Required paper correction:** Split callback receipt, validation and business acceptance. For IPN, durably record bounded original bytes and listener/environment identity as **unverified**, acknowledge receipt, then perform retryable postback validation and business checks before any financial/order effect. Keep verification-outage and invalid states distinct. Define separate REST webhook validation handling rather than a universal “already authenticated receipt” assumption. Raw unverified input needs size/rate limits, private retention and no propagation into model/public evidence.

**External qualification gate:** Actual app/listener binding, genuine notification delivery, outage recovery and duplicate-safe processing remain unexecuted. The ordering contradiction is a paper correction, not something to postpone to account testing.

### IR05 — Important: the apply proposal does not settle how resource authority and one-use approval groups compose

**Locations:** Plan1 `CONNECTION_CONTROL_PROPOSAL.md`, `ResourceBinding`, lines 22–28; Plan3 `APPROVAL_AND_EVIDENCE.md`, lines 15–19; `LIFECYCLE_INTERFACE_PROPOSALS.md`, `ApplyApproval`/`EffectIntent`, lines 36–48 and durable ownership, line 83.

**Trigger and consequence:** The source controller and host controller differ, or one approval group contains publish, merge, infrastructure/configuration, deployment and later cleanup effects. The policy correctly requires each controller's approval or valid delegation. However, the inherited binding permits only `view|connect|start|review`; the new proposal has a single `controller_id`, a broad `allowed_actions` list and one `consumed_at`, while each effect refers to one `approval_id`. It does not define the canonical required set of controller approvals/delegations, how it is derived per resource, or whether consumption reserves a whole sequence or spends one effect.

Multiple approval records could solve this, but their composition is currently unspecified. Builders can implement incompatible interpretations: the first write consumes permission needed by the next step, or an already consumed group becomes reusable authority for extra effects. Installing provider apps does not resolve either ambiguity.

**Required paper correction:** Define the versioned apply-authority/delegation record without widening the initial Reader binding. Specify required approvers for each resource/action and the immutable action-group plan, including separately authorized financial operations. Define approval-set completeness, per-effect identity/cardinality, reservation/consumption, expiry between steps, retries after a lost response, and invalidation by any required controller. Never infer host consent from source-controller approval or vice versa.

**External qualification gate:** LC-A1 acceptance, current provider roles/protections and actual scoped rights remain open. Resolve the composition semantics on paper first, with examples for split controllers, missing host approval, expiry after publication and duplicate merge/deploy requests.

### IR06 — Important: source-independent intake still has a mandatory GitHub delivery path

**Locations:** `outputs/plan_3/LIFECYCLE_BUILD_SPEC.md`, lines 9–11; `STATE_AND_EFFECT_TABLE.md`, PUBLISHING/MERGING, lines 16–17; `LIFECYCLE_INTERFACE_PROPOSALS.md`, lines 39 and 50; `BUILD_SLICES.md`, L05/L07, lines 71–109. Requirement: root `DELIVERY_REQUIREMENTS_UPDATE.md`, lines 10 and 15; Plan1 `SUPPORTED_FIRST_PATH.md`, “Product scope versus first route,” lines 23–24.

**Trigger and consequence:** A local-folder or other qualified non-Git snapshot matches a merchant's image-backed service. Intake can describe it, but the selected lifecycle requires a Publisher App, review branch/PR, protected merge and source head/base. L07 also depends on the GitHub publisher slice. No alternative publication/state path explains how this case reaches deployment without creating or moving the merchant's source into GitHub. The generic statement that local revisions are snapshots does not define that delivery route.

**Required paper correction:** Give publication a typed, provider-specific plan with explicit applicability. Define a source-independent immutable result/archive and artifact-delivery branch, including its durable merchant-controlled source destination and approval, or explicitly mark that combination unsupported for full delivery in pre-Start feasibility. GitHub can remain the first implemented reference; do not equate that with a completed generic delivery design or require a hidden repository migration. Required Git fields must be conditional/provider-typed, and stage transitions must state when a PR/merge is inapplicable.

**External qualification gate:** Additional source/delivery adapters remain future qualification. This finding does not require implementing every provider now; it requires an honest paper branch and admission rule.

### IR07 — Important: post-revocation restart proof and recovery lack an executing authority

**Locations:** `outputs/plan_3/SUCCESSFUL_EXIT.md`, lines 15–16 and 23–28; `LIFECYCLE_BUILD_SPEC.md`, line 42; `STATE_AND_EFFECT_TABLE.md`, EXITING/COMPLETE, lines 22–23; `OPERATIONAL_GATES.md`, PG12, line 20.

**Trigger and consequence:** Exit denies/removes GoldGraft access and terminates its worker, then requires an authorized actual restart and observation of private state/payment/callback continuity. The specification does not identify the independent actor/mechanism that can initiate that restart, retain the necessary scoped observation authority, return trustworthy evidence, and recover if the restart fails. It risks a circular proof using credentials supposedly removed, an unsafe outage after recovery access is gone, or a hidden instruction for the merchant to restart/debug the service.

**Required paper correction:** Define the exit-check executor and its separately approved restart/observation/recovery scope before disconnect. A merchant-owned bounded procedure can operate after GoldGraft denial; alternatively, stage revocation explicitly and state exactly which qualification capability remains until the test is complete. Distinguish denial of GoldGraft's ordinary capabilities, full remote revocation and loss of the control plane. Identify the failure owner and permitted recovery route without resurrecting revoked approvals or granting automatic financial compensation. Set required observation criteria before the test; a public heartbeat cannot supply private continuity evidence.

**External qualification gate:** Restart permission mapping, independent evidence collection, image availability and actual post-denial continuity remain open. A paper execution/authority path is required before authorizing the disruptive check.

## Open qualification gates that are not additional defects

The inspected research and PG gates already disclose scoped-key early-access entitlement, endpoint permission mapping, absent secret-free Render config/per-instance attestation, ambiguous queued/lost deployment responses, actual isolation/egress and termination, processor terms/retention, genuine sandbox behavior, live merchant eligibility/history and post-exit continuity. They are **not passed** by this review, but their honest open status is not itself a contradiction.

In particular, retaining an unknown deploy outcome without replay, refusing to infer no charge from an empty report, preserving origin refund/callback routes, and holding unsupported recurring conversion are appropriate. The PayPal guide/schema disagreement over cancelled-subscription recovery remains an external clarification gate. No new conclusion on that disputed capability is made here.

Plan2 should carry IR01–IR07 as explicit corrections or reviewed scope restrictions, with acceptance examples and named component boundaries. Documentation or stand-ins can settle those design choices; only later authorized implementation/account qualification can establish conformance. This report changes no source document or team allocation and closes no operational gate.
