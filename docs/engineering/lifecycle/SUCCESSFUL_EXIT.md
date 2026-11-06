# Successful and unsuccessful service exit

Status: Plan3 engineering on paper, 6 November 2026. No implementation, account change, deployment, live payment/model/worker job or agent-internal design. CURRENT means inspected existing contract; all new lifecycle states/interfaces/modules below are PROPOSED. Vendor/account/runtime qualification gates remain open.

## Three distinct outcomes
A. Upgrade outcome: validated candidate/sandbox; B. Live-site outcome: intended approved deployment/current runtime + required state/payment/callback observations; C. Exit outcome: merchant can operate without temporary GoldGraft runtime/access and required cleanup acknowledged. Do not conflate them. “Live upgrade verified; cleanup pending” is permissible status, overall completed exit is not asserted until required exit checks pass.

## Asset ownership/action manifest
| Asset | After GoldGraft leaves |
|---|---|
| Merchant source, approved production artifact/runtime, domain/TLS, persistent data/schema | Preserve under merchant-controlled account/access; do not remove as job cleanup. |
| Merchant PayPal integration/app credentials, refund/capture authority, notification validation material | Preserve required operational identity; service may remove only its own extra grants/temporary copies, not break merchant payments. |
| Callback/IPN/webhook endpoints and required queues/origin mappings | Merchant-owned durable hosting/storage, correct active registration, private validation/auth and retry/reconciliation; not an expiring worker tunnel. |
| Legacy refunds/pending orders/recurring/in-flight handler obligations | Keep required origin adapters/compatibility until independently proved safe to retire. Inventory long-tail owner, credentials, retention and verification evidence; unsupported migration is blocked. |
| Temporary workers/sandboxes/test resources/tunnels | Fence new work, terminate and confirm; track unknown external resources by job/generation until reconciled. Never delete merchant durable callback ingress. |
| GoldGraft Reader/Publisher/Deploy/test-identity grants | Remove/expire service's temporary grants under explicit disconnect; separate local denial, provider acknowledgement and in-flight effects. No broad account deletion. |
| Raw source/prompt/runtime snapshot/diagnostic/review/backup copies | Enforce disclosed per-store retention and requested deletion/holds; report active/deleted/pending/held/exported limits independently. No claim external exported copies are recalled. |
| Evidence/report/status records | Minimal authorised redacted durable records only per policy; private review and public projection distinct. Pending legal holds/expiry explicit. |

## Finalisation before access removal
Replace temporary rollout switch dependency with switchless final target or durable merchant-owned local config/signing/guard/origin policy. A library that reverts to OLD when a GoldGraft-issued SwitchConfig expires is NOT a safe final upgraded state. First profile requires finalisation artifact removing GoldGraft-control-plane dependence while preserving in-flight/legacy origin routes. That code/config change gets its own relevant regression/proof/review/approval/deployment before declaring exit. Never remove old routes merely because new checkout passes once.

Merchant registry can still pull exact approved artifact after GoldGraft credential removal/restart. Merchant runtime can resolve its own secrets, serve domain, persist state and verify callbacks without service-held keys. Paid tier/cost/operating ownership and support route must be accepted; no silent transfer of running costs/resources or promise zero maintenance forever.

Exit validation under separately authorised qualification: deny GoldGraft temporary access first, terminate worker, then observe actual website/backend/merchant callback operation and authorised restart/registry pull/state recovery. No new live charge/refund without financial test authority. A mere heartbeat at original URL is insufficient evidence of payment continuity. If live required evidence unavailable, report live/exit verification pending.

## Other exits
Cancel before accepted: durable cancelled action, no job. Cancel queued/running: fence and confirm termination plus sandbox effects. Failed upgrade before publish: original intact; copies clean according policy. Failed postpublish/deploy: perform state-aware recovery, report known target/outstanding effects, not upgrade success. Incident: local deny service privileges, preserve evidence and independent merchant operations, scoped controller recovery. Voluntary disconnect: explain what stops/remains; no rollback implied. Delete: warn about loss of future evidence/recovery, export only authorised redacted data, report stores individually. Retention expiry: halt work before exceeding raw-copy policy and delete/reconcile; returning user reauthenticates and reacquires needed source, never revives revoked approval.

Work cannot be marked complete merely because service access is gone. Safe failed exit may be FAILED_SAFE with working original and honest unresolved upgrade; INCIDENT_UNKNOWN when actual target cannot be established. Successful exit requires verified upgraded-site continuity and no hidden technical work left to merchant.

## Primary-evidence constraints
No callback adapter/legacy refund path is retired merely after a fixed soak/refund-window age. Retain disputes/reversals/pending/recurring notification obligations until exact replacement coverage is qualified; otherwise unsupported full migration stays blocked. Finite provider callback retries require durable merchant-owned receipt/reconciliation, not a temporary worker tunnel.

## Non-Git source custody at handover
DirectArtifact route retains exact approved final editable source bundle and build/dependency/config-reference manifest in the approved merchant-controlled private destination, separate from GoldGraft temporary raw copies. Verify merchant ownership/access and image pull rights before removing temporary grants. Original selected local/cloud files are not silently overwritten; no required Git migration or local download/deploy chore. No new merchant-owned persistent copy is created without disclosure/action authority and appropriate retention/operating responsibility.

## Plan4 material-correction authority
[ATOMIC_DELIVERY_PROTOCOLS.md](ATOMIC_DELIVERY_PROTOCOLS.md) is normative for bootstrap state transfer BEFORE first destructive prerequisite change, cross-case target reservations/shared-asset cleanup, exact deployable-image build/test/private publish, IPN unverified receipt→acknowledgement→validation ordering, independent per-resource apply authority/approval-set/per-effect-slot consumption and merchant-owned post-denial exit executor. It supersedes ambiguous earlier single-controller/global consumed_at/per-run-only-lock/post-revoke-self-restart wording. All mechanisms remain paper proposals; actual qualification is open.
