# State-aware recovery and safe stopping

Status: Plan3 engineering on paper, 6 November 2026. No implementation, account change, deployment, live payment/model/worker job or agent-internal design. CURRENT means inspected existing contract; all new lifecycle states/interfaces/modules below are PROPOSED. Vendor/account/runtime qualification gates remain open.

## Recovery baseline is not a blind restore button
Record before each consequential action: immutable code/artifact/config/source/dependency versions; runtime topology and domain routes; schema/forward/backward compatibility; live data ownership/backup/capture policy; durable event/transaction-origin mapping; outstanding captures/refunds/subscriptions/notifications; legacy provider availability; prior approved route and exact restore/compensation permissions. Verify selected backup restores into a disposable copy before relying on it. Live data backup/export needs explicit authority/privacy and provider-consistent snapshot method; never use synthetic seed as production recovery.

Classify each effect E0/E1/E2/E3/EU from STATE_AND_EFFECT_TABLE.md. Undoing code or pointing traffic old cannot undo a capture/refund, order created, delivered webhook or retired API. Default recovery preserves monotonic economic records and current data; no overwrite with old DB/snapshot while newer orders/payments exist. Restore only when evidence proves no intervening effects or an explicitly approved reconciled state plan accounts for every effect; otherwise forward repair/compensation/hold. Service cannot promise exact previous world state for external effects.

## Recovery decision procedure (deterministic responsibility, not agent algorithm)
1. Fence new privileged actions for affected work/target; retain independent merchant payment/notification runtime that must continue servicing existing obligations. Stop new checkout admission only via an authorised merchant-owned safety control, not revoking all payment credentials.
2. Establish current source/runtime/config/routes and known versus pending external effects. Query original provider IDs; a timed-out operation may already have succeeded. No automatic new request IDs for unknown captures/refunds/deploys.
3. For each outstanding checkout/order pin origin code/payment identity. Existing NEW sessions continue via supported origin handler; switching new buyers does not reroute existing capture/refund flows to incompatible legacy code. No duplicate charge from replaying old checkout.
4. If old artifact/provider/API/schema/config is currently compatible and safe, authorise version-bound code/config traffic cutback; preserve new economic state and origin handlers. Test current qualified recovery route before claiming rollback; do not restore retired integrations by assumption.
5. If incompatible or unknown, use safe hold/maintenance/forward-fix with durable notifications/reconciliation and controller visibility. Compensation (e.g. refund) is separate financial action requiring its own current authority; never an automatic database undo.
6. Verify actual target/runtime/routes and required obligations after recovery. Record safe original/forward-repaired outcome versus failed/unknown, and exact remaining controller/provider dependencies. Resume only after new current evidence/approval.

## Failure matrix
| Failure | Required safe behaviour |
|---|---|
| Bad baseline/missing source before change | Hold isolated work; original stays running, identify exact needed component/controller. |
| Candidate/tests/review fail | Return private incomplete evidence; no publication, no fake certificate. |
| Branch/PR write response lost | Reconcile remote branch/head/PR before retry/delete; source effect recorded, shop not claimed deployed. |
| Merge result differs/base races | No image deployment until exact resulting tree/artifact retested/reapproved; record source changed/runtime old. |
| Deployment accepted but status lost | Provider deploy ID + current runtime reconciliation; don't start alternate deploy blindly. |
| Deployment/migration half-applied | Preserve current data/events; compare schema compatibility; continue safe ingress/drain; forward repair or compatible rollback, no old DB overwrite. |
| Old PayPal API unavailable | Recovery cannot depend on it; maintain supported origin bridge or hold migration until continuity solved. |
| Secret rotated/revoked mid-run | Local deny affected broker calls, rebind under current controller; no resurrection of cached token/approval. |
| Guard/control plane unavailable | Merchant-owned safe policy handles existing sessions; no auto-promotion; do not depend on GoldGraft-only service for ongoing critical payments. |
| Stop/incident/delete during apply | Fence future effects, reconcile dispatched ones and preserve merchant operational assets; no “cancelled so nothing happened”. |

No hard-coded seconds-to-rollback guarantee. Time-to-cutback is observed evidence after implementing/qualifying provider/runtime/queue handling. The historical 15s switch polling and 30-payment confidence examples are not live assurance. Lost events, thin evidence or unknown state produce held/incident-unknown, not a green restored badge.

## Primary-evidence constraints
PayPal-specific constraints and unresolved guide/schema ambiguity are in research/PAYMENT_CONSTRAINTS.md. No universal REST idempotency duration or cross-family refund/renewal conversion is asserted. Report absence can be delayed and does not prove no charge. Origin API/account identity, stateful notification dedupe and separately authorised compensation remain mandatory.

## Plan4 material-correction authority
[ATOMIC_DELIVERY_PROTOCOLS.md](ATOMIC_DELIVERY_PROTOCOLS.md) is normative for bootstrap state transfer BEFORE first destructive prerequisite change, cross-case target reservations/shared-asset cleanup, exact deployable-image build/test/private publish, IPN unverified receipt→acknowledgement→validation ordering, independent per-resource apply authority/approval-set/per-effect-slot consumption and merchant-owned post-denial exit executor. It supersedes ambiguous earlier single-controller/global consumed_at/per-run-only-lock/post-revoke-self-restart wording. All mechanisms remain paper proposals; actual qualification is open.
