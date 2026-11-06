# Lifecycle acceptance and negative cases

Status: Plan3 engineering on paper, 6 November 2026. No implementation, account change, deployment, live payment/model/worker job or agent-internal design. CURRENT means inspected existing contract; all new lifecycle states/interfaces/modules below are PROPOSED. Vendor/account/runtime qualification gates remain open.

All cases below are FUTURE tests/procedures, unexecuted in the product. Inject faults under offline fixtures or separately authorised disposable/staging/sandbox tests; never send merchant mutations expecting denial. Store redacted current input/outcome/authority/resource/generation/effect-count evidence. Passing a safe hold is not full upgrade success.

## LC01 — Package/source mismatch

Input/fault: Accepted manifest lacks backend/private dependency or source differs from running component.

Expected state/evidence/forbidden effect: Hold before modification; identify exact missing input/controller; no full-scope readiness/proof from frontend-only source.

Stage: BASELINE_VERIFY. Trace: S01 S03 S18 S19; CG03 CG12 CG14.

## LC02 — Baseline isolation

Input/fault: Baseline build hook tries source/host/private-network write; candidate edits source.

Expected state/evidence/forbidden effect: Reject denied effects; immutable baseline source hash unchanged, separate synthetic state; original source/live runtime untouched.

Stage: BASELINE_RUN. Trace: S06 S09 S10 S12 S13; CG08.

## LC03 — Old bug and noise

Input/fault: Old has paid-on-pending defect or noisy IDs differ; new matches old defect.

Expected state/evidence/forbidden effect: Record old defect, enforce normative rule; no PASS from parity/overbroad noise mask, deliberate fix documented.

Stage: VALIDATING. Trace: S18 S19; CG05 CG11.

## LC04 — Required baseline unverified

Input/fault: Baseline HTTP health succeeds but refund/IPN/order loop not observed.

Expected state/evidence/forbidden effect: Healthy page not full baseline; hold required path; synthetic fixture cannot be real credential-path proof.

Stage: BASELINE_RUN. Trace: S10 S18; CG05 CG11 CG12.

## LC05 — Candidate drift/repair

Input/fault: Candidate/dependency/runtime changes after tests/review.

Expected state/evidence/forbidden effect: Invalidate affected evidence/approval; new exact bytes revalidated; bounded repair no scope/control weakening.

Stage: VALIDATING. Trace: S03 S18 S19; CG10 CG14.

## LC06 — Untrusted evidence

Input/fault: Guest/model claims verified or forges capture/signature; reference payload hash differs.

Expected state/evidence/forbidden effect: Do not advance stage until authenticity/current fence/schema/digest validated; public signature not semantic proof.

Stage: VALIDATING. Trace: S11 S18 S22; CG08 CG11 CG14.

## LC07 — Critical partial report

Input/fault: Critical missing flow or surviving rule/mutant while a high average score exists.

Expected state/evidence/forbidden effect: Full approval blocked, explicit incomplete report; no N/A from skipped tests or score-only completion.

Stage: REVIEW_READY. Trace: S18 S19; CG05 CG11.

## LC08 — Private/public projection

Input/fault: Reviewer forwards link or public certificate includes raw source/transaction/customer detail.

Expected state/evidence/forbidden effect: Current recipient scope enforced; no private payload in public view; no reviewer apply privilege.

Stage: REVIEW_READY. Trace: S01 S17 S22 S24; CG06 CG07 CG11.

## LC09 — Provider consent versus action approval

Input/fault: Publisher App installed but no current exact revision/action result approval.

Expected state/evidence/forbidden effect: No publication/merge/deploy; provider scope not action authorisation or current ownership.

Stage: AWAITING_APPLY. Trace: S02 S03 S19; CG04 CG10.

## LC10 — Publication side effects

Input/fault: Review branch/PR triggers deploy or privileged workflow/ungranted reusable workflow.

Expected state/evidence/forbidden effect: Hold before first remote write; record unknown trigger chain; never disable/bypass silently.

Stage: PUBLISHING. Trace: S02 S09 S10 S19 S20; CG04 CG08 CG10.

## LC11 — Unknown publication outcome

Input/fault: Branch/PR creation succeeds but response lost; retry/delete.

Expected state/evidence/forbidden effect: Reconcile exact branch/head/PR before another effect; deletion also side-effect qualified; original action identity.

Stage: PUBLISHING. Trace: S03 S20; CG04 CG09.

## LC12 — Protected merge race

Input/fault: Head/base/check/rule changes; approved merge tree differs from tested artifact.

Expected state/evidence/forbidden effect: No bypass; deny stale head; hold/reprove/reapprove exact resulting tree before deploy; source change not live success.

Stage: MERGING. Trace: S03 S18 S19; CG04 CG10 CG14.

## LC13 — Deploy authority and identity

Input/fault: Reader key used for deploy, wrong service/env, altered image digest or config.

Expected state/evidence/forbidden effect: Deny; separate current controller action/Deploy Run scope; exact bound immutable artifact/config only.

Stage: DEPLOYING. Trace: S01 S02 S03 S19; CG03 CG04 CG10.

## LC14 — Image tag/health illusion

Input/fault: Registry tag changes; provider deploy queued/failed; old instance returns 200.

Expected state/evidence/forbidden effect: No deploy/live success without exact actual active artifact/target/state observations; safe waiting/unknown.

Stage: OBSERVING. Trace: S18 S19 S20; CG03 CG04 CG09.

## LC15 — Deployment response loss

Input/fault: Deploy accepted then crash/timeout or competing deployment.

Expected state/evidence/forbidden effect: Record ID/unknown; reconcile existing provider and runtime before resubmit; no automatic alternate deploy.

Stage: DEPLOYING. Trace: S03 S20; CG04 CG09 CG10.

## LC16 — Stop versus irreversible effect

Input/fault: Stop/revoke races publication/deploy/capture.

Expected state/evidence/forbidden effect: Fence new actions, reconcile dispatched effects; termination does not undo source/runtime/money; no false cancelled-nothing-happened.

Stage: HELD. Trace: S03 S08 S20 S21; CG09 CG10.

## LC17 — Refund/charge unknown

Input/fault: Capture/refund succeeds remotely, lost response, key window unqualified.

Expected state/evidence/forbidden effect: Same logical identity/state retained; no new-key replacement/auto refund; reconcile or hold.

Stage: INCIDENT_UNKNOWN. Trace: S03 S10 S20; CG05 CG09 CG10.

## LC18 — Notifications out of order

Input/fault: Pending→complete→duplicate complete→late pending, forged body/wrong listener.

Expected state/evidence/forbidden effect: Verify correct identity/raw input; dedupe effects while allowing legitimate states; no double fulfillment/state regression.

Stage: OBSERVING. Trace: S06 S07 S18 S20; CG05 CG10.

## LC19 — Callback outage

Input/fault: Listener unavailable through finite provider retry window; no reporting read result yet.

Expected state/evidence/forbidden effect: Merchant-owned durable receipt/reconciliation; absence not failure/no-charge proof; missing coverage holds success.

Stage: HELD. Trace: S07 S18 S20; CG05 CG09.

## LC20 — Persistent state and cutover

Input/fault: Render restart loses orders/IPN data; two processes write same flat-file state; restore older DB after new payments.

Expected state/evidence/forbidden effect: Reject profile/data loss; state-safe quiesce/drain/migration/compatibility; no blind old DB overwrite.

Stage: DEPLOY_PREPARED. Trace: S10 S18 S19 S20; CG03 CG04 CG05.

## LC21 — Retired legacy rollback

Input/fault: Old artifact exists but old API unavailable or schema incompatible after new orders.

Expected state/evidence/forbidden effect: No automatic rollback claim; forward repair/safe hold preserving economic records/origin handlers.

Stage: HELD. Trace: S03 S18 S19 S20; CG04 CG05 CG10.

## LC22 — Historical obligations

Input/fault: New checkout passes but old NVP refund/profile/notification route remains needed.

Expected state/evidence/forbidden effect: Inventory/retain qualified origin access/handler; no assumed ID conversion or new duplicated subscription.

Stage: FINALISING. Trace: S02 S03 S18 S21; CG05 CG12.

## LC23 — Final switch expiry

Input/fault: Temporary GoldGraft switch/signing/control plane disappears after 100% target.

Expected state/evidence/forbidden effect: Final artifact/local policy preserves upgraded path and origin obligations; expiry cannot silently send all buyers old.

Stage: EXITING. Trace: S08 S18 S21; CG04 CG09 CG10.

## LC24 — Registry/credential dependency

Input/fault: Revoke GoldGraft account/key then merchant runtime cannot pull image/read secret/verify callback.

Expected state/evidence/forbidden effect: Handover blocked; merchant-owned runtime/registry/keys/handlers must survive; preserve operational credentials.

Stage: EXITING. Trace: S03 S06 S08 S21; CG04 CG05 CG10.

## LC25 — Cleanup unknown and deletion

Input/fault: Workers/tokens/raw/backup/model/export copies unacknowledged or held.

Expected state/evidence/forbidden effect: Local denial first; show pending/held/exported limits individually; no all-deleted/exit-complete claim.

Stage: EXITING. Trace: S08 S17 S21 S23 S24; CG06 CG07 CG09.

## LC26 — Actual successful exit

Input/fault: Qualified actual target works; stop service worker/deny service grants and perform authorised restart.

Expected state/evidence/forbidden effect: Observe supported site/state/payment/callback continuity without GoldGraft dependencies before exit Complete. No unapproved live test payment.

Stage: COMPLETE. Trace: S03 S08 S18 S21; CG03 CG04 CG05 CG09 CG10.

## LC27 — No route to full delivery

Input/fault: PR/result exists but no protected deploy authority/state-safe route or required controller.

Expected state/evidence/forbidden effect: Managed saved-case setup/review hold, no deploy-it-yourself surprise or PR-as-complete; explicit missing action.

Stage: AWAITING_APPLY. Trace: S02 S03 S19; CG04 CG12 CG13.

## LC28 — Return and evidence expiry

Input/fault: User returns after session/grant/source-custody expiry or revoked action.

Expected state/evidence/forbidden effect: Authorised historical receipt accessible per policy; reacquire/revalidate only needed context; no approval/work resurrection.

Stage: HELD. Trace: S01 S03 S08 S20 S23; CG02 CG07 CG09 CG10.

## LC29 — Production test identity

Input/fault: Service tries proving production with its sandbox buyer/merchant identity or unauthorised live refund.

Expected state/evidence/forbidden effect: Deny; sandbox success does not prove actual merchant eligibility/history; live observation/test authority separate.

Stage: OBSERVING. Trace: S02 S06 S10 S18; CG05 CG10 CG12.

## LC30 — In-flight origin routing

Input/fault: New buyer cutback while older/newer checkout sessions or callback/refund effects remain.

Expected state/evidence/forbidden effect: New routing changes never reassign existing payment origin; preserve per-session/API/account IDs and one-effect order processing.

Stage: HELD. Trace: S03 S07 S18 S20; CG04 CG05 CG09.

## LC31 — Thin rollout evidence

Input/fault: Historical 30-sample posterior threshold green but critical event evidence unavailable/real traffic thin.

Expected state/evidence/forbidden effect: No promotion on missing critical evidence; sandbox demo arithmetic not live safety certification or timing guarantee.

Stage: OBSERVING. Trace: S18 S19; CG05 CG11 CG13.

## LC32 — Contract compatibility

Input/fault: Non-Git source/E2B runner forced into current Certificate.commit/workflow fields.

Expected state/evidence/forbidden effect: Use labelled proposed version/private bundle; no invented SHA or generated/current API mutation.

Stage: REVIEW_READY. Trace: S18 S22; CG11 CG14.

## LC33 — Non-Git source and safe direct-artifact delivery

Input/fault: local/cloud source has no Git repo; registry/object webhook could deploy; destination private/pull rights are absent or GoldGraft-owned.

Expected: no mandatory Git/PR or fake commit; choose declared direct_artifact route only with current exact controller-approved private merchant source/registry destination, qualified triggers and digest/pull ownership. Otherwise managed setup hold. Original folder stays untouched, no public upload or deploy-it-yourself final result. Actual live handover evidence still required.

Stage: PUBLISHING/DEPLOY_PREPARED/EXITING. Trace:S01 S02 S03 S17 S18 S19 S21; CG03 CG04 CG06 CG10 CG12 CG14. Specified only, not executed.

## LC34 — First prerequisite migration loses ephemeral state

Input/fault: Attach disk/redeploy before snapshot; old capture/return/refund writer commits during callback queue bootstrap.

Required outcome: No first destructive mutation until all-writer/handler inventory, existing export/drain/bridge, fence/high-water/export/restore/replay qualified; otherwise hold original live.

Trace: S01 S03 S07 S17 S18 S19 S20 S21; CG03 CG04 CG05 CG09. Future offline/fault/disposable qualification only; not executed.

## LC35 — Overlapping cases and shared grant cleanup

Input/fault: Two valid case/run generations target same service/state/callback; one exits or lease expires with unknown deploy.

Required outcome: Canonical cross-case target reservation/fence; conflict/queued hold; unknown effects keep reservation; shared asset/grant not revoked for one run.

Trace: S01 S03 S07 S17 S18 S19 S20 S21; CG04 CG09 CG10. Future offline/fault/disposable qualification only; not executed.

## LC36 — Source tests versus actual image and registry rights

Input/fault: Source-tree tests pass but different OCI image published or registry destination/pull rights not approved.

Required outcome: Bind source/recipe/inputs/trusted builder and exact deployable-image tests; separate private registry publish authority; no merchant build/push chore/public upload.

Trace: S01 S03 S07 S17 S18 S19 S20 S21; CG03 CG04 CG06 CG08 CG14. Future offline/fault/disposable qualification only; not executed.

## LC37 — IPN verification outage before acknowledgement

Input/fault: Unverified raw IPN arrives, PayPal postback unavailable or durable receipt storage fails.

Required outcome: Bounded private unverified persistence then receipt ack then retry validation; no order effect before checks; persistence failure not acknowledged accepted; REST path distinct.

Trace: S01 S03 S07 S17 S18 S19 S20 S21; CG05 CG09 CG10. Future offline/fault/disposable qualification only; not executed.

## LC38 — Split controllers and effect slot reuse

Input/fault: Source approves but host missing; publish consumes approval then expiry; duplicate merge/deploy tries reuse group.

Required outcome: Required authority/ApprovalSet per immutable ActionPlan; slotcardinality1; expiry blocks future effects while preserving known prior effects; no authority union/bypass or new retry identity.

Trace: S01 S03 S07 S17 S18 S19 S20 S21; CG04 CG09 CG10 CG14. Future offline/fault/disposable qualification only; not executed.

## LC39 — Post-denial exit executor unavailable

Input/fault: Remove service keys then service attempts restart/read/recover with them or merchant asked technical scripts.

Required outcome: Prequalified merchant-owned bounded executor/current plan/reservation and separate disclosed evidence-read capability; no executor holds exit; no revoked credential reuse/hidden finishing chore.

Trace: S01 S03 S07 S17 S18 S19 S20 S21; CG03 CG04 CG07 CG09 CG10. Future offline/fault/disposable qualification only; not executed.
