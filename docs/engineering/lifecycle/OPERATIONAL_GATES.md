# Account, provider and implementation prerequisites

Status: Plan3 engineering on paper, 6 November 2026. No implementation, account change, deployment, live payment/model/worker job or agent-internal design. CURRENT means inspected existing contract; all new lifecycle states/interfaces/modules below are PROPOSED. Vendor/account/runtime qualification gates remain open.

Every gate remains OPEN for actual service release. Paper resolves the mechanism and specifies hold behaviour; it does not simulate away external evidence.

| Gate | Required evidence / responsible boundary / unavailable outcome |
|---|---|
| PG01 current input/authority | Actual complete source/graph/controllers/custody/Start profile; Gupta mechanism + Singh policy; hold intake/sandbox if missing. |
| PG02 baseline/runtime | Qualified isolation/template/egress/dependencies/synthetic state and genuine sandbox auth; Gupta/Vijay; no baseline success from page health/fakes. |
| PG03 proof/review | Required rule/flow/current evidence and scoped expert review; Singhal + actual reviewer; partial report, no apply. |
| PG04 publication/protection | Registered separate Publisher/current exact consent, complete safe CI/preview/Blueprint trigger chain and provider rules; Gupta/controllers; no first push if unsafe/unknown. |
| PG05 protected apply proposal | User/controller accepted LC-A1 policy and provider rights/reviews/checks; no manual protection bypass, no initial Reader write. Missing approval stays awaiting controller; technical finishing remains service responsibility when supported. |
| PG06 Render effective grant | Account scoped-beta availability/effective scope/endpoint denial evidence, matching user/ADMIN role and selected workspace/service; controller/Gupta; no broad classic-key substitute. |
| PG07 runtime/config identity | Actual image SHA/current live record, single-instance profile, trusted secret-free config/runtime correspondence and immutable provenance; Gupta/Vijay; no invented instance/config fields, hold. |
| PG08 state/callback/registry | Merchant-owned persistent state/queue/credentials/registry, approved maintenance and compatibility/backup/restore evidence; Gupta/Vijay/controller; no apply if unsafe. |
| PG09 financial/legacy | Exact merchant/API/app/environment permissions and in-flight/history/refund/subscription reconciliation/continuity; actual controllers/Vijay; unsupported obligations block full delivery. |
| PG10 unknown effects | Real DB/outbox/receipt/reconcile/termination/duplicate-deploy fault qualification; Gupta; retain unknown, no blind retry/financial undo. |
| PG11 provider processing/copies | Named actual model/runtime/region/retention/DPA/support/export/delete conditions; Singh/account owners; hold private transfer or model work when terms unmet. |
| PG12 live observation/handover | Authorised production-safe validation, no synthetic identity substituting live merchant, post-denial/restart continuity and clean temporary exit; Singh integration/all owners; live/exit pending, not completed. |

No external access, account changes, money movement, live test transaction, installation, worker or mutation performed by Plan3. Component implementation/tests belong future Plans5/6/team build work, not paper closure. Some provider documentation is ambiguous (e.g. cancelled-subscription recovery guide/schema disagreement); see research/PAYMENT_CONSTRAINTS.md. Preserve unresolved facts rather than assert eligibility. If a documented mechanism cannot be qualified, reopen affected design/provider scope.
