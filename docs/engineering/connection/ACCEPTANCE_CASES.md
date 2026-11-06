> Reviewed team baseline, 6 November 2026: this connection proposal is subject to the review addendum, implementation bridge and lifecycle atomic protocols linked from [engineering START](../START_HERE.md). Earlier programme status/owner restrictions in this frozen source are historical. No current API/implemented capability is created by this text.

# Meaningful acceptance specifications

Status: paper engineering specification, 6 November 2026. Nothing here is a deployed feature or current API unless explicitly labelled CURRENT. Proposed components/interfaces require later implementation and contract approval. Plan 1 ends at verified first sandbox operation; agent internals and Plans 2–6 remain outside scope.

Cases below specify future tests; NONE was executed against the product in Plan 1. Earlier 31 abstract checks remain limited prior evidence. Documentary/link/hash audits performed here are separate. A stand-in can pass wire/transition checks, never prove real provider consent, isolation, money or termination. Tests never call network; live checks require opt-in live_ scripts and separate authority.

## AC01 — Origin and URL

- Input/fault: Imitation origin, metadata/private IP, IPv6 loopback, DNS rebinding and redirect to internal target.
- Expected authoritative outcome and forbidden effect: Reject before grant/fetch; no private network request or ownership assertion.
- Evidence/procedure level: offline parser/network harness then isolated network qualification. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S12 S15; CG01 CG08.

## AC02 — Draft claim

- Input/fault: Two browser sessions race to claim draft; second supplies case ID without original secret.
- Expected authoritative outcome and forbidden effect: Exactly one owner; other denied without metadata; URL draft survives rightful login.
- Evidence/procedure level: offline state/race. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S01 S04; CG02.

## AC03 — Session expiry

- Input/fault: Expire/rotate/logout session; replay old cookie and mutation CSRF, login return to arbitrary URL.
- Expected authoritative outcome and forbidden effect: Old session/CSRF denied; only internal bound return; durable accepted job not recreated.
- Evidence/procedure level: offline auth + separate real provider. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S01 S04 S05; CG02.

## AC04 — Invite recipient binding

- Input/fault: Forward invite to a different person; legitimate reader token but no relation approval.
- Expected authoritative outcome and forbidden effect: No private repo/host/source/report disclosed; controller independently authenticates and approves exact relation or denies.
- Evidence/procedure level: offline role matrix + authorised two-person provider flow. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S01 S04 S17 S22; CG02 CG06 CG11.

## AC05 — Role boundaries

- Input/fault: Reviewer calls Start; member changes requester/shop/env/recipient after approval.
- Expected authoritative outcome and forbidden effect: 403 or safe unavailable; stale binding invalid; new recipients see no private findings until approved.
- Evidence/procedure level: offline authorisation. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S02 S03 S19; CG02 CG10.

## AC06 — Provider callback

- Input/fault: Wrong provider/actor/repo/case, expired/replayed state; wrong attempt then rightful attempt.
- Expected authoritative outcome and forbidden effect: All wrong returns denied, no token/case swap; wrong attempt does not consume rightful continuation.
- Evidence/procedure level: offline callback traces + real OAuth/SSO. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S04 S05 S07; CG02.

## AC07 — Reader least authority

- Input/fault: Selected repo token attempts cross-repo read/content/branch/PR/workflow writes.
- Expected authoritative outcome and forbidden effect: Provider and broker deny; no writes; secret token absent from guest/browser/logs.
- Evidence/procedure level: authorised disposable GitHub live denial tests. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S03 S06; CG02 CG04.

## AC08 — Render grant and controller

- Input/fault: Classic key, wrong workspace/service, scoped key without member reads, user email mismatch, inactive/non-admin role.
- Expected authoritative outcome and forbidden effect: Hold; no connected label/private attachment; no substitution of broader key. Workspace read breadth visible.
- Evidence/procedure level: offline provider fixtures then authorised Render account. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S01 S03 S06 S17; CG02 CG03 CG12.

## AC09 — Render side effects

- Input/fault: Read grant qualification on disposable resources: deploy Run, rollback, service update, secret read denied; attempt deploy-hook GET in broker.
- Expected authoritative outcome and forbidden effect: All forbidden actions denied including GET effects; no live merchant write test; qualification receipt before Ready.
- Evidence/procedure level: separate explicit disposable mutation-test authority. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S02 S06 S12 S19; CG03 CG04 CG08.

## AC10 — Event current authority

- Input/fault: Forged HMAC, genuine wrong installation, duplicate/removal event and role downgrade.
- Expected authoritative outcome and forbidden effect: Forged/cross-resource denied, duplicate no effect; local revoke immediately fences privileged work.
- Evidence/procedure level: offline webhook + provider revoke test. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S03 S07 S08; CG02 CG10.

## AC11 — Archive handling

- Input/fault: Traversal, links, duplicate/case collision, FIFO, deep/huge/expansion archive.
- Expected authoritative outcome and forbidden effect: Reject within limits; no file outside root; partial copy removed and no readiness.
- Evidence/procedure level: offline malicious synthetic archives in bounded harness. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S13 S16; CG08.

## AC12 — Exclusion/custody

- Input/fault: Synthetic canary secrets in .env/source/binary and customer order dump; essential config excluded.
- Expected authoritative outcome and forbidden effect: No canary reaches model/evidence/browser; omission manifest; essential missing input holds; raw quarantine access audited.
- Evidence/procedure level: offline payload fixtures + isolated storage checks. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S06 S17 S24; CG06 CG07 CG08.

## AC13 — Unsupported source

- Input/fault: Missing submodule/LFS/private dep or wrong commit.
- Expected authoritative outcome and forbidden effect: Incomplete acquisition cannot be Ready; no recursive broad token or silent revision change.
- Evidence/procedure level: offline acquisition fixture. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S03 S10 S13; CG03 CG12.

## AC14 — Image correspondence

- Input/fault: Render live image digest differs from provenance or service settings; newer pending deploy disguises older live deploy.
- Expected authoritative outcome and forbidden effect: Match not verified; no Start; preserve actual live and pending identities separately.
- Evidence/procedure level: offline provider/provenance fixtures then hosted reference. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S18 S19; CG03.

## AC15 — Runtime/config correspondence

- Input/fault: Forged/replayed runtime nonce, changed env/config/backend, mutable code overlay, rollout ambiguity.
- Expected authoritative outcome and forbidden effect: Fail affected chain; unknown is hold; no claim signature proves all bytes/payment correctness.
- Evidence/procedure level: offline crypto/chain then authorised reference observations. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S18 S19; CG03 CG08.

## AC16 — Static boundary

- Input/fault: Repo has install hooks; probe text requests model/tools; preflight runner tries script/model/payment call.
- Expected authoritative outcome and forbidden effect: No executable/model/payment call before Start; deterministic denied operation audited.
- Evidence/procedure level: offline call recording, zero forbidden calls assertion. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S09 S10 S11; CG05 CG08.

## AC17 — Processing policy

- Input/fault: No ZDR entitlement, unexpected model/region/endpoint or policy change after review.
- Expected authoritative outcome and forbidden effect: Hold acquisition/egress as applicable; no consumer fallback or unsupported deletion promise.
- Evidence/procedure level: document/account review + gateway fixture. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S17 S19 S23; CG06 CG07.

## AC18 — Isolation/egress

- Input/fault: Malicious guest probes metadata/private IPs/DNS redirects/IPv6, host mounts, management API and other tenants.
- Expected authoritative outcome and forbidden effect: No escape/credential/private-network access; deny egress despite prompt instruction; missing verified controls blocks runtime qualification.
- Evidence/procedure level: authorised isolated escape/egress qualification, not abstract model. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S09 S10 S11 S12 S14 S15; CG08.

## AC19 — Credential/payment semantics

- Input/fault: Sandbox guest requests live endpoint, unrelated transaction refund, headers returned to model or raw credential from broker.
- Expected authoritative outcome and forbidden effect: Reject; real sandbox credential injection path validated separately; synthetic broker cannot claim authentication proof.
- Evidence/procedure level: offline denies then separately authorised sandbox credential-path test. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S03 S06 S10; CG05 CG08.

## AC20 — Readiness invalidation

- Input/fault: Expire grant/TTL; change source/env/policy/fixture/budget after Ready.
- Expected authoritative outcome and forbidden effect: Disable Start and re-evaluate dependency; unknown/missing/stale not pass.
- Evidence/procedure level: offline readiness matrix. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S03 S18 S19; CG03 CG05 CG10.

## AC21 — Start before commit crash

- Input/fault: Crash before accepted/outbox transaction commit.
- Expected authoritative outcome and forbidden effect: No accepted receipt/outbox dispatch/job; same action retry may safely accept once.
- Evidence/procedure level: real DB fault injection during later implementation. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S20; CG09.

## AC22 — Commit lost response

- Input/fault: Commit accepted action/outbox then lose HTTP response; reconnect/retry same key/body.
- Expected authoritative outcome and forbidden effect: One work identity/original receipt; same key different body 409; no new dispatch intent.
- Evidence/procedure level: real DB/process restart + HTTP fault. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S01 S20; CG09 CG14.

## AC23 — Concurrent Starts

- Input/fault: Parallel same/different keys for same reviewed active scope and reviewer attempt.
- Expected authoritative outcome and forbidden effect: One accepted active work or explicit conflict/existing receipt; no role bypass; authoritative uniqueness survives restart.
- Evidence/procedure level: DB concurrency stress, offline synthetic. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S02 S20; CG09 CG10.

## AC24 — Outbox/lease crash

- Input/fault: Crash after external allocation before outbox ack; duplicate dispatch; lease expires then old worker acts.
- Expected authoritative outcome and forbidden effect: Reconcile job/generation allocation; fence old actions/results; orphan termination tracked, never exactly-once claim.
- Evidence/procedure level: DB + isolated worker fault injection. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S03 S16 S20; CG08 CG09.

## AC25 — Stop before receipt

- Input/fault: Stop races unacknowledged Start with same action identity; vary transaction order.
- Expected authoritative outcome and forbidden effect: Cancel-first creates durable tombstone/no dispatch; accept-first fences then pending termination. No auto replacement job.
- Evidence/procedure level: DB race test NX03. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S03 S20 S21; CG09 CG10.

## AC26 — Claim without operation

- Input/fault: VM allocated/lease claimed but baseline read never completes, fails digest or guest prints started.
- Expected authoritative outcome and forbidden effect: Queued/preparing/held only; no Sandbox work started.
- Evidence/procedure level: offline receipts + isolated real baseline operation NX04. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S03 S18 S20; CG08 CG09 CG14.

## AC27 — Verified first operation

- Input/fault: Trusted current supervisor computes accepted manifest/byte digest; forge signature, replay old generation or wrong scope.
- Expected authoritative outcome and forbidden effect: Only valid current authenticated operation record advances state once; Details states exact baseline operation, no inference/payment claim.
- Evidence/procedure level: crypto fixture then real isolated supervisor observation. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S03 S18 S20; CG08 CG09 CG14.

## AC28 — Stop/revoke external unknown

- Input/fault: Fence locally; provider termination or in-flight broker response unavailable; reconnect/regrant.
- Expected authoritative outcome and forbidden effect: Cancellation pending/unknown; no new effects; old approvals never resurrect; no false stopped/deleted/rollback.
- Evidence/procedure level: worker/provider outage fault test. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S03 S08 S20 S21; CG09 CG10.

## AC29 — Replay/private projection

- Input/fault: Expired SSE cursor, cross-tenant receipt request, duplicate/out-of-order event, browser close.
- Expected authoritative outcome and forbidden effect: Authorised fresh snapshot/resync; no skipped status or private leakage; no work restart.
- Evidence/procedure level: offline transport/role harness then browser integration. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S01 S18 S20 S22; CG09 CG11 CG14.

## AC30 — Retention/quotas

- Input/fault: TTL expiry during queued/running work, exported copy, backup hold, evidence flooding.
- Expected authoritative outcome and forbidden effect: Fence new work; termination/delete state tracked per store; pending/held not deleted; bounded generation, exported-copy limit visible.
- Evidence/procedure level: storage/processor account evidence + synthetic expiry tests. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S16 S17 S21 S23 S24; CG07 CG08.

## AC31 — Legacy compatibility

- Input/fault: Old client calls v1 Start with empty body; forged new v2 field passed to v1; unsupported version.
- Expected authoritative outcome and forbidden effect: No security bypass or fake readiness; explicit compatible/unsupported path, shared types/examples/fakes align.
- Evidence/procedure level: offline full route/version conformance. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S01 S02 S19; CG14.

## AC32 — Publication tripwire

- Input/fault: Future review branch push would trigger Render auto-deploy/preview/privileged CI.
- Expected authoritative outcome and forbidden effect: Plan1 never writes; later publication held until trigger chain/current config reviewed and authorised.
- Evidence/procedure level: paper fixture for NX01; operational deployment testing belongs Plan3. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S02 S09 S10 S19 S20; CG04 CG08 CG10.

## AC33 — Usability and recovery

- Input/fault: Owner URL only; separate maintainer; wrong agency client; MFA/key entry/denial; keyboard/screen reader; return later.
- Expected authoritative outcome and forbidden effect: Same saved case, essential disclosures visible, no repeated routine Accept, honest unsupported/queued/unknown states; record all human effort and waiting.
- Evidence/procedure level: paper walkthrough now, real users later. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S01 S04 S17; CG12 CG13.

## AC34 — Reference payment scope

- Input/fault: Fixture source supports full listed loop but required merchant recurring/history path absent; sample helper unauthenticated.
- Expected authoritative outcome and forbidden effect: Do not expose sample publicly or say complete merchant upgrade; required unsupported path holds; actual payments not tested in Plan1.
- Evidence/procedure level: source inventory now; payment lifecycle acceptance deferred. Capture before/after state, action/resource/generation IDs, redacted denial/operation evidence and trace links.
- Trace: S02 S10 S18; CG05 CG11 CG12.

## AC35 — Adapter replacement without core rewrite
Input: Render stand-in and independently shaped synthetic host stand-in, with different native IDs, consent mechanism and evidence availability. Run the same case/authority/readiness/Start suite by changing registry/config only. Expected: common case identity, actor checks, scoped custody, durable acceptance and cancellation semantics unchanged; missing capability holds. No provider-name branch in common policy/UI. Evidence: offline simulated conformance, not real second-provider support. Trace: S01 S02 S03 S18 S19; CG03 CG12 CG14.

## AC36 — Split-provider shop completeness and live claim boundary
Input: frontend host A connected; required backend host B and callback owner initially missing; then add authorised bindings and correspondence; revoke or drift one node. Expected: full Start blocked until entire required graph current, private data scoped per controller/recipients; drift/revoke invalidates dependents; no all-connected label from frontend alone. Offline evidence is simulated; demonstrated multi-host claim additionally requires two actual independently qualified host adapters and real authorised resource observations. Trace: S01 S03 S17 S18 S19; CG02 CG03 CG12 CG13 CG14.

## AC37 — Local-folder safe capture
Input/failure and authoritative expected outcome: Permission cancelled/expired, unsupported picker fallback, secret/customer-data canaries, malicious relative paths and source edits mid-upload. Expected: read-only user-selected root only; no forbidden canary upload; trusted server rechecks; changed/incomplete captures cannot finalise/Start; no disk write or silent scan.
Evidence: future offline synthetic/browser/provider-conformance checks, not executed here. Trace: S01 S06 S13 S17; CG02 CG06 CG08 CG12 CG13 CG14.

## AC38 — Resumable non-Git snapshot
Input/failure and authoritative expected outcome: Interrupt/retry/reorder/duplicate chunks, close browser, reselect different folder, expire upload/binding. Expected: same authorised session dedupes bounded chunks, wrong-folder/digest denied, honest reselection required, no invented commit or background-sync guarantee, expired partial data swept.
Evidence: future offline synthetic/browser/provider-conformance checks, not executed here. Trace: S01 S03 S16 S20 S24; CG07 CG09 CG12 CG14.

## AC39 — Cloud permission and completeness
Input/failure and authoritative expected outcome: Selected-file write-capable scope, whole-drive scope offered as fallback, missing child access/revision change/shared shortcut. Expected: no read-only misrepresentation or broad escalation; hold direct adapter or controller-selected local fallback; no complete-source label from partial listing.
Evidence: future offline synthetic/browser/provider-conformance checks, not executed here. Trace: S03 S06 S17 S19; CG02 CG03 CG06 CG12 CG14.

## AC40 — Owner-no-code and stale candidate
Input/failure and authoritative expected outcome: Owner knows URL only, maintainer unresponsive or source locally stale; host-platform owns code. Expected: same case handoff, no private disclosure from invitation/possession alone, no forced GitHub/ZIP, no HTML-as-backend assertion; accepted snapshot still blocked until actual host correspondence; platform limitation explicit.
Evidence: future offline synthetic/browser/provider-conformance checks, not executed here. Trace: S01 S03 S17 S18 S19; CG02 CG03 CG12 CG13.

## AC41 — Complete required source/context inventory
Input/failure and required outcome: Upload frontend only while website depends on separate backend/notification code/private package/state schema. Expected: exact missing graph nodes/authority/config named, same-case recovery, no full complete/ready label, no ungranted private fetch.
Evidence level: future fixtures/implementation checks; Plan3-specific live proof deferred, no jobs run here. Trace: S01 S03 S10 S17 S19; CG02 CG03 CG05 CG12 CG14.

## AC42 — Source identity versus runnable baseline
Input/failure and required outcome: Candidate builds/runs but source/artifact/runtime belongs to different website, or matched source fails unchanged baseline. Expected: reject correspondence or hold baseline separately; no patch-induced passing run substitutes for the original baseline. Actual unchanged execution belongs Plan3 after Start.
Evidence level: future fixtures/implementation checks; Plan3-specific live proof deferred, no jobs run here. Trace: S18 S19; CG03 CG05 CG08 CG14.

## AC43 — Isolated baseline and working copy
Input/failure and required outcome: Malicious/build/test process tries writing original source/repo/live host or baseline root; working snapshot changes. Expected: only isolated working copy writable; provider read-only retained, baseline digest stable, production untouched during experiments; no remote branch writes before separate authority.
Evidence level: future fixtures/implementation checks; Plan3-specific live proof deferred, no jobs run here. Trace: S02 S06 S09 S10 S20; CG04 CG08 CG10.

## AC44 — Working site after service handover
Input/failure and required outcome: Later lifecycle fixture: PR exists but not deployed, image-tag push not deployed, ephemeral state lost on restart, callback/credentials disappear when worker/access removed. Expected: no Completed; service finishes qualified authorised technical route or reports hold, preserves working merchant assets/state; verified live/post-disconnect result required. Full operational proof deferred Plan3, not run here.
Evidence level: future fixtures/implementation checks; Plan3-specific live proof deferred, no jobs run here. Trace: S02 S03 S08 S18 S20 S21; CG03 CG04 CG05 CG07 CG09 CG10 CG12.

## AC45 — Final common-contract conformance
Input/interleaving and outcome: Same case contains Git snapshot plus local capture and split frontend/backend providers; client submits mandatory fake commit or attempts optional-node scope bypass. Expected: canonical typed graph/package validation works without fabricated commit; incomplete required graph blocks readiness; stale historical fields rejected by final proposed formats.
Evidence: future offline contract/DB fault checks, not executed during paper closure. Trace: S01 S03 S18 S19; CG03 CG12 CG14.

## AC46 — Pre-accept cancellation and immutable receipt
Input/interleaving and outcome: Persist action intent then Stop before work allocation, and separately accept→lose response→Stop→retry same Start. Expected: null pre-accept work/generation valid, durable tombstone prevents acceptance; accepted receipt remains immutable while current status shows pending/stopped; retry never resurrects work.
Evidence: future offline contract/DB fault checks, not executed during paper closure. Trace: S01 S03 S20 S21; CG09 CG10 CG14.
