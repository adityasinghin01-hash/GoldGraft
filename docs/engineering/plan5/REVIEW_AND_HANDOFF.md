# Paper review, corrections and construction handoff

6 November2026. Review scope: source/mechanism reconciliation, type/route/state/ownership consistency, manual construction and component-test coverage. This is not an implementation/code/security certification or provider qualification. Document audit evidence is kept privately; product tests have not run.

## Review findings and resolved design changes

| Finding | Resolution and evidence target |
|---|---|
| Baseline Explorer needs Contract while Scribe needs baseline Explorer | Baseline uses Driver+required-flow inventory; candidate uses final Contract. Separate scribe-draft/followups/scribe-final DAG, R04/R14 |
| Model is asked to return refs it cannot create | Broker stages bounded untrusted inline JSON; runtime validates then makes proposal descriptors; no model-created trusted refs, A04 |
| Waiting condition cannot survive from Issue/time alone | WakeCondition/1 binds exact subject/digest/version/owner/expiry; persisted by wait/checkpoint, F03 |
| ChangeList/1 cannot represent non-Git without fake branch/commit | Add explicit ChangeList/2 Git/snapshot union semantics, preserve /1 legacy, C03 |
| Model timeout has no reconciliation port | Persist turn/budget before dispatch; ModelPort.reconcile same ID; unknown holds, F04/A07 |
| Triangle followups would form dependency cycle or undefined dynamic spawn | Bounded CAS append-only extend, distinct immutable draft/final tasks, whole graph cap/cycle check, R14 |
| Pure delivery reducer has only refs | resolve_delivery materializes typed records/predicates first; reducer consumes ResolvedDeliveryView, D02 |
| Finalisation changes artifact but lacks exact return-to-review path | Explicit final candidate→exact test/proof→review/new plan/approvals→reserved apply/observe→Q0, D11 |
| Lifecycle request receipt unnamed | LifecycleWorkRequestReceipt/1 declared once; request/result identity stable |
| One-off deployment image mistaken for persistent config | Persistent configured image/pull identity and independent restart mandatory; no-ID202 same-effect reconcile, D05/D10 |
| Frontend upload endpoints/types not exact | Fully scoped method/path/request/response route table plus inline bounded manifest/chunk transport definitions; C06/C08 |
| New Problem would discard current RFC7807 shape | New P5Problem extends standard core fields/status with closed Plan5 recovery fields; legacy class unchanged |
| Pre-signin case requires nonexistent requester/session | Explicit bounded anonymous DraftCase capability then bound authenticated atomic claim; no private findings before claim, C08/W01 |
| Vite mode name not exposed / public Check endpoint invented | Explicit public nonsecret VITE_GOLDGRAFT_WEB_MODE; Check is GET projection refetch only, W09/W10 |
| Potential stale/timeout/legacy bypass | Current-authority broker/output checks, exact unknown/termination evidence, legacy demo separation; C07/A05/A09 |
| Adversary followup would require a future candidate/plan | Early followups restricted to Explorer traces; Adversary guard execution waits for exact candidate, R14 |
| Immutable tasks would contain unknown future digests; transforms cannot equal parents | Incremental admission after producer commit; explicit subject manifest/collector derivation validates parent→new subject, R14/R15 |

Three research threads independently checked their mechanisms against the drafts; parent consolidated corrections and performed final whole-pack self-review. No reviewer ran product tests. Any future implementation deviation from these resolved semantics requires updating shared types/policy/tests consistently rather than silently widening permission.

## Construction-ready design versus unresolved evidence

Settled: Python coordinator choice after delegated user judgment,13 verified logical roles/exclusive duties, communication/state/context/scheduling/retry/Stop policy, shared bootstrap proposals, delivery/exit coordination, reconciled frontend/Antigravity pack and exact build/test dependency plan. Simon/Nessie remain unverified unused transcriptions; no runtime routing depends on them. Colours/styling intentionally await later visual decision.

Open: all actual component implementations/test results, real-model profile/competence, GU/VJ/SH real integrations, effective grants/accounts/processor/isolation/runtime/payment/state/provider/exit evidence. Unknown teammate local work is inspected before implementation, not assumed absent. These are explicit qualification dependencies with holds, not unanswered safety mechanisms papered over by a success claim.

## Handoff and stop

Next authorised work in this session ends with paper pack/readback/preservation review. No Phase5.3 or Plan6 auto-start, no install/provision/account grant/model/payment/worker/deploy job, no commit/push/merge/publication or teammate message. Plans1/3/4 frozen on paper, Plan2 complete; do not repeat uploads.

When Aditya explicitly starts Phase5.3, use MANUAL_CONSTRUCTION_PLAN B0→B7. Terminal focus is agents then delivery; Antigravity frontend consumes settled SI01+fixture versions. Product component results must be recorded from actual execution. Successful fake paths remain synthetic; merchant operation after GoldGraft removal requires separate Plan6 evidence.

Private before-edit backups/hash manifests/document verification and research sources remain private. Portable local engineering additions are not yet GitHub-published. The Plan2 EXPORT_MANIFEST is a dated publication snapshot, not a claimed hash inventory for this new pack or modified entry docs.

## Launch-prompt documentation update

At Aditya's subsequent request, prepared exactly two complete construction prompts and reconciled frontend Markdown inputs with the two-terminal workflow. Codex starts in the existing repo, creates the isolated build worktree and checks shared bootstrap/fixtures; Antigravity starts in that worktree after a real frontend-ready manifest. Codex owns shared/agent/delivery/final handoff files; Antigravity owns pieces/web/report files. Shared revisions have an explicit pause/check/re-ready protocol. Full prompt authorisation avoids re-requesting approval for each already-scoped step. No worktree creation, installation, implementation or product test occurred while preparing the prompts; the prior research/spec audit is retained as a dated snapshot and a separate launch-documentation audit records these edits.
