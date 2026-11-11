"""State cutover planning (GU05).

A known order count is not approval, and a count is not preservation evidence.
The plan is ``approved`` only when every prerequisite the atomic protocols
require is present: a writer/handler inventory, an ingress route, a high-water
mark, a consistent export, a verified restore, a replay manifest and no
unresolved external effects. Otherwise the plan is created unapproved with
typed holds, which is what the caller must surface.

No database is ever restored as a financial rollback here.
"""

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class StateCutoverPlan:
    plan_id: str
    graft_id: str
    source_origin: str
    target_origin: str
    inventory_order_count: int
    created_at: str
    approved: bool = False
    holds: list[str] = field(default_factory=list)
    writer_inventory_ref: str | None = None
    handler_inventory_ref: str | None = None
    ingress_ref: str | None = None
    high_water_mark: int | None = None
    fence_epochs: dict[str, int] = field(default_factory=dict)
    export_manifest_ref: str | None = None
    restore_verified_ref: str | None = None
    replay_manifest_ref: str | None = None
    pending_effect_refs: list[str] = field(default_factory=list)
    approvals: list[str] = field(default_factory=list)

    @property
    def preserved_order_count(self) -> int:
        return self.inventory_order_count

    def __post_init__(self):
        if self.approved and self.holds:
            raise ValueError("an approved cutover plan cannot carry holds")
        if self.approved and not (
            self.export_manifest_ref
            and self.restore_verified_ref
            and self.replay_manifest_ref
            and self.fence_epochs
            and self.high_water_mark is not None
        ):
            raise ValueError("approved cutover requires export/restore/replay and fence evidence")


REQUIRED_EVIDENCE = (
    ("writer_inventory_ref", "no current state-writer inventory"),
    ("handler_inventory_ref", "no current callback/handler inventory"),
    ("ingress_ref", "no qualified merchant-owned ingress receipt path"),
    ("export_manifest_ref", "no consistent state export"),
    ("restore_verified_ref", "no verified restore into a disposable copy"),
    ("replay_manifest_ref", "no replay manifest"),
)


class StatePlanner:
    """Plans and bounds state migrations across shop payment origins."""

    def create_cutover_plan(
        self,
        graft_id: str,
        source_origin: str,
        target_origin: str,
        known_orders: list[str],
        *,
        writer_inventory_ref: str | None = None,
        handler_inventory_ref: str | None = None,
        ingress_ref: str | None = None,
        high_water_mark: int | None = None,
        fence_epochs: dict[str, int] | None = None,
        export_manifest_ref: str | None = None,
        restore_verified_ref: str | None = None,
        replay_manifest_ref: str | None = None,
        pending_effect_refs: list[str] | None = None,
        approvals: list[str] | None = None,
        **extra: Any,
    ) -> StateCutoverPlan:
        if "approved" in extra:
            raise ValueError("approval is derived from evidence, never passed in")
        raw = f"{graft_id}:{source_origin}:{target_origin}:{uuid.uuid4()}".encode()
        plan = StateCutoverPlan(
            plan_id=f"plan-{hashlib.sha256(raw).hexdigest()[:12]}",
            graft_id=graft_id,
            source_origin=source_origin,
            target_origin=target_origin,
            inventory_order_count=len(known_orders),
            created_at=datetime.now(UTC).isoformat(),
            writer_inventory_ref=writer_inventory_ref,
            handler_inventory_ref=handler_inventory_ref,
            ingress_ref=ingress_ref,
            high_water_mark=high_water_mark,
            fence_epochs=dict(fence_epochs or {}),
            export_manifest_ref=export_manifest_ref,
            restore_verified_ref=restore_verified_ref,
            replay_manifest_ref=replay_manifest_ref,
            pending_effect_refs=list(pending_effect_refs or []),
            approvals=list(approvals or []),
        )

        holds = [reason for name, reason in REQUIRED_EVIDENCE if getattr(plan, name) is None]
        if plan.high_water_mark is None:
            holds.append("no durable event high-water mark")
        if not plan.fence_epochs:
            holds.append("no writer fence epochs")
        if not plan.approvals:
            holds.append("no current controller approval for the cutover")
        if plan.pending_effect_refs:
            holds.append("unresolved external effects must be reconciled first")
        plan.holds = holds
        plan.approved = not holds
        return plan
