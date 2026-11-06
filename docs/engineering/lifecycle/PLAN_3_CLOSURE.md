# Plan3 requirements and paper closure

Status: complete as paper engineering; operational gates unqualified. Each requirement is specified, not executed. No internal agent design or build. Plan4 review is complete on paper, including targeted independent follow-up; operational qualification remains open.

| Required area | Deliverable |
|---|---|
| Whole forward lifecycle | [LIFECYCLE_BUILD_SPEC.md](LIFECYCLE_BUILD_SPEC.md) |
| Stage actor/input/output/effect/failure | [STATE_AND_EFFECT_TABLE.md](STATE_AND_EFFECT_TABLE.md) |
| Complete context/unchanged baseline/working copy | [BASELINE_REPRODUCTION.md](BASELINE_REPRODUCTION.md) |
| Proof/independent private review/current exact approval | [APPROVAL_AND_EVIDENCE.md](APPROVAL_AND_EVIDENCE.md) |
| Service handles technical delivery, protected apply proposal | [DELIVERY_AUTOMATION_AND_AUTHORITY.md](DELIVERY_AUTOMATION_AND_AUTHORITY.md) |
| Render git/image/scope/config/state/persistence/downtime | [RENDER_DELIVERY_AND_STATE.md](RENDER_DELIVERY_AND_STATE.md) |
| Cancel/revoke/drift/provider outage/unknown/inflight | [RECOVERY_AND_ROLLBACK.md](RECOVERY_AND_ROLLBACK.md) |
| Reversible/compensatable/irreversible/no oldDB overwrite | [RECOVERY_AND_ROLLBACK.md](RECOVERY_AND_ROLLBACK.md) |
| Durable merchant operation/legacy origins/credentials | [SUCCESSFUL_EXIT.md](SUCCESSFUL_EXIT.md) |
| Successful/failed/disconnect/incident/delete/expiry/return | [SUCCESSFUL_EXIT.md](SUCCESSFUL_EXIT.md) |
| Actual working-site/handover evidence | [WORKING_SITE_HANDOVER.md](WORKING_SITE_HANDOVER.md) |
| Current/proposed contracts and no agent internals | [LIFECYCLE_INTERFACE_PROPOSALS.md](LIFECYCLE_INTERFACE_PROPOSALS.md) |
| Ordered future slices/shared fixtures/acceptance | [BUILD_SLICES.md](BUILD_SLICES.md) |
| All four component ownership boundaries | [COMPONENT_RESPONSIBILITIES.md](COMPONENT_RESPONSIBILITIES.md) |
| Primary provider/payment constraints | [research/PAYMENT_CONSTRAINTS.md](research/PAYMENT_CONSTRAINTS.md) |
| Primary Render/GitHub constraints | [research/RENDER_CONSTRAINTS.md](research/RENDER_CONSTRAINTS.md) |
| Explicit external holds and reopen rules | [OPERATIONAL_GATES.md](OPERATIONAL_GATES.md) |

Ten future lifecycle build slices and 39 lifecycle acceptance cases, supplemented by 14 PayPal and 18 Render paper failure cases. Inherited traceability retains 166 baseline records, four supplements, 24 controls and 14 release gates without empirical closures. Proposed LC-A1 protected apply automation is an explicit later authority change, not granted by Start or this paper. Actual process/DB/provider/money/state/exit conformance remains future qualification.

## Review corrections and closure boundary

[ATOMIC_DELIVERY_PROTOCOLS.md](ATOMIC_DELIVERY_PROTOCOLS.md) is normative for state/bootstrap, target reservations, exact image build, IPN receipt, approval composition and independent exit. Direct-artifact delivery supports non-Git source without invented Git fields. All seven independent findings were addressed on paper; the follow-up found no remaining material contradiction within its targeted scope. Missing operational primitives cause explicit holds, not fabricated feasibility. Plan3 paper specification is CLOSED. Plan5/6 implementation, real isolation/payment/provider/migration/exit proof remain unstarted.
