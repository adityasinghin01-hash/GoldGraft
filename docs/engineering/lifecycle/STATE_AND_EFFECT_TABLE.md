# Lifecycle states, effects and truthful recovery

Status: Plan3 engineering on paper, 6 November 2026. No implementation, account change, deployment, live payment/model/worker job or agent-internal design. CURRENT means inspected existing contract; all new lifecycle states/interfaces/modules below are PROPOSED. Vendor/account/runtime qualification gates remain open.

All names below are proposed lifecycle states, distinct from existing Stage enums. Status transitions require committed versioned evidence, active actor/action scope and current fence. Retry transports keep same action; intentional rework creates a new attempt and invalidates downstream approval. Every stage has finite configurable lease/time/budget; timeout may be unknown external outcome, not automatic failure/rollback.

| Stage / authority and entry | Output, side effect and failure/exit |
|---|---|
| ACCEPTED / current Start delegate, immutable receipt | DB acceptance/outbox; no production effects. Stop-before-accept tombstone or queue cancellation; no worker termination claim from DB alone. |
| BASELINE_VERIFY / trusted supervisor, package+assignment | Actual bounded baseline manifest read; authenticated operation receipt. Missing digest/fence -> held; no working-site proof. |
| BASELINE_RUN / sandbox work scope | Build/run OLD/OLD_TWIN with synthetic independent state/provider sandbox effects. Results/captures/versioned defects. Fail -> diagnose/hold; Stop fences/terminates but does not undo sandbox payment effects. |
| CANDIDATE_READY / same sandbox scope | Candidate-only bytes/diff/deps; no remote branch/host mutation. Invalid output/unsupported scope -> reject/held, retain pinned baseline. |
| VALIDATING / exact candidate inputs | Required flow/regression/security/mutation evidence; provider sandbox requests tracked. Missing/critical unverified -> not review-ready; bounded repair -> revalidation, no auto-relax. |
| REVIEW_READY / private scoped reviewer | Evidence bundle/diff, limitations and proposed apply plan; no write grant implied. Reviewer cannot Start/apply. Withdrawal/change invalidates review. |
| AWAITING_APPLY / actual source/host controllers | Exact current result/environment/action approval plus separate provider consent; expiring one-use authorisation. Missing role/protection/CI metadata -> hold. |
| PUBLISHING / qualified Publisher broker | Branch/PR write is external consequential effect; record intent and actual commit/PR. Unknown response -> query exact branch/commit/PR before retry; no default-branch push or workflow write. |
| MERGING / proposed controller-authorised protected apply broker | Merge exact reviewed head under current protections, record actual merge tree/base/head. Base/merge-result difference -> hold/rebuild/reprove/reapprove before deployment; never presume old artifact matches. |
| DEPLOY_PREPARED / host controller apply approval | Merchant-owned runtime/registry/state/callback/recovery prerequisites verified; any new infrastructure/config mutation explicitly bound. No shared live state mounted into test copies. |
| DEPLOYING / separate host deploy capability | Provider deployment request/external deploy ID of exact tested digest/config/target; reconcile after timeout. Accepted deploy != active healthy runtime. Stop after dispatch means reconcile/possibly safe cutback, never “not changed”. |
| OBSERVING / approved read/guard scope | Actual target identity/domain/config and required state/notification evidence, no unapproved live payment test. Drift/failed checks -> hold/cutback-safe route; no final completion. |
| FINALISING / exact separately authorised cleanup candidate | Remove service-only rollout dependency while preserving merchant assets/legacy obligations. New bytes/config -> revalidate/reapprove; no cleanup bypass or blind legacy removal. |
| EXITING / explicit stop/revoke/delete boundaries | Fence temporary capabilities, confirm worker termination/provider revoke, expiry/deletion states per store. Live merchant resources survive; unresolved temp copies/termination remains pending. |
| COMPLETE / current final evidence | Intended live supported outcome verified and no hidden technical tasks; post-service operational evidence. Separate cleanup pending from active upgrade outcome; overall completed exit requires applicable required cleanup evidence. |
| HELD / reason/owner/evidence dependency | Preserve case and known effects; no new privileged work. Re-auth/revalidation/reapproval resumes affected stage only. |
| FAILED_SAFE / known safe preserved target | Original or safe repaired shop verified, outcome not upgraded success; cleanup tracked. |
| INCIDENT_UNKNOWN / external result uncertain | Deny additional effects, reconcile provider/runtime/money/state under current controller authority. No duplicate deploy/charge or claimed rollback. |

## Effect classes
E0 metadata/temporary isolated files (no external money); E1 source/config writes reversible only under recorded current preconditions; E2 deploy/route mutations reversible only if current state/code/provider compatibility allows; E3 payment/order/refund/subscription/notifications externally consequential, may only be compensatable or irreversible; EU unknown/in-flight. Every action records class, precondition snapshot, intended effect, provider receipt/query strategy, idempotency semantics, compensation permission and current outcome.

## Mandatory interrupted paths
Before acceptance -> cancelled original intent, no job. Queued -> fence/remove dispatch intent atomically. Sandbox-running -> fence broker calls, request/confirm process termination, reconcile external sandbox effects. Prepublication failure -> source/production preserved. Published/no deploy -> report actual PR/branch, no shop-upgrade claim; removing branch may also trigger CI, so explicit safe cleanup only. Merge/no deploy -> source changed, runtime old, exact recorded state. During deploy -> pending/unknown until provider+runtime confirm. Postdeploy failure -> state-aware cutback/repair, not unconditional old DB restore. Provider outage/revoke -> local deny, remote status pending. Later return -> authorised historical receipt plus fresh scope/roles; no resurrection of old approval.

## Route and expiry rules
MERGING applies only to git_protected. direct_artifact instead publishes exact authorised image/private source bundle to merchant-controlled destinations, verifies ownership/pull/provenance then enters DEPLOY_PREPARED; no Git fields/PR required. Every registry/blob trigger is assessed before write. Expired apply approval denies new consequential effects; already-submitted actions are still reconciled/read-observed under current read authority, never treated as undone by expiry. Need further mutation/recovery -> fresh current action approval.

## Plan4 material-correction authority
[ATOMIC_DELIVERY_PROTOCOLS.md](ATOMIC_DELIVERY_PROTOCOLS.md) is normative for bootstrap state transfer BEFORE first destructive prerequisite change, cross-case target reservations/shared-asset cleanup, exact deployable-image build/test/private publish, IPN unverified receipt→acknowledgement→validation ordering, independent per-resource apply authority/approval-set/per-effect-slot consumption and merchant-owned post-denial exit executor. It supersedes ambiguous earlier single-controller/global consumed_at/per-run-only-lock/post-revoke-self-restart wording. All mechanisms remain paper proposals; actual qualification is open.
