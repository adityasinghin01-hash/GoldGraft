# Plan3 — full lifecycle paper specification

Status: Plan3 engineering on paper, 6 November 2026. No implementation, account change, deployment, live payment/model/worker job or agent-internal design. CURRENT means inspected existing contract; all new lifecycle states/interfaces/modules below are PROPOSED. Vendor/account/runtime qualification gates remain open.

GoldGraft obtains the required source/context, reproduces the unchanged system, upgrades an isolated copy and hands back an authorised verified working website that remains operational after temporary GoldGraft resources/access are removed. This is a PAPER specification, not a running service.

1. [Lifecycle build specification](LIFECYCLE_BUILD_SPEC.md)
2. [Baseline reproduction](BASELINE_REPRODUCTION.md), [state/effect matrix](STATE_AND_EFFECT_TABLE.md)
3. [Private review and approvals](APPROVAL_AND_EVIDENCE.md), [technical delivery authority](DELIVERY_AUTOMATION_AND_AUTHORITY.md)
4. [Render exact-artifact/config/state delivery](RENDER_DELIVERY_AND_STATE.md)
5. [Recovery](RECOVERY_AND_ROLLBACK.md), [successful/failed exit](SUCCESSFUL_EXIT.md), [working-site handover](WORKING_SITE_HANDOVER.md)
6. [Proposed lifecycle interfaces](LIFECYCLE_INTERFACE_PROPOSALS.md), [future slices](BUILD_SLICES.md), [future acceptance](ACCEPTANCE_CASES.md), [team boundaries](COMPONENT_RESPONSIBILITIES.md)
7. [PayPal primary evidence](research/PAYMENT_CONSTRAINTS.md), [Render primary evidence](research/RENDER_CONSTRAINTS.md), [open operational gates](OPERATIONAL_GATES.md)

Source correspondence, baseline reproducibility, tested candidate correctness and actual live-site/exit verification are different proofs. Plan1 initial access stays read-only; separately approved provider/result actions required later. Internal agent design remains deferred. Plan4 critically reviews this pack before Plan2 publishes team docs/work deltas. Plans5/6 implementation/integration remain unstarted.

**Plan4 corrections:** [Atomic delivery protocols](ATOMIC_DELIVERY_PROTOCOLS.md) settle the material independent-review findings; use these alongside core specs. Non-Git direct-artifact route, first-bootstrap/all-writer transfer, target reservations, exact-image publication, per-controller effect-slot approval and independent exit executor are mandatory. 39 lifecycle acceptance cases, ten build slices; actual account/operational qualification remains open.
