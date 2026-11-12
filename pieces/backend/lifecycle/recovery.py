"""Safe recovery and cutback (GU05).

Compensation is not rollback, and restoring an old database is never a
financial rollback. A cutback here is only *prepared* when a consistent export
exists, the restore into a disposable copy was verified, no external effect is
unknown, and no attempt is made to undo money.

A missing prerequisite returns a held receipt without touching the ledger, so a
claimed stage transition is never fabricated.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

from goldgraft_contracts.common import Producer, ProducerKind, Stage
from goldgraft_contracts.ledger import EntryType
from goldgraft_foundation.ledger import Ledger

RecoveryOutcome = Literal["prepared", "held", "unknown"]


@dataclass
class RollbackReceipt:
    rollback_id: str
    graft_id: str
    prior_stage: str
    reverted_to: str | None
    reason: str
    inventory_order_count: int
    timestamp: str
    outcome: RecoveryOutcome
    state_preservation_ref: str | None = None
    holds: list[str] = field(default_factory=list)
    ledger_seq: int | None = None

    @property
    def retained_orders_count(self) -> int:
        return self.inventory_order_count

    def __post_init__(self):
        if self.outcome == "prepared" and self.reverted_to is None:
            raise ValueError("a prepared cutback has a committed target stage")


class RecoveryManager:
    """Prepares a code/config cutback while preserving current economic state."""

    def __init__(self, ledger: Ledger | None = None):
        self.ledger = ledger or Ledger()

    def execute_safe_rollback(
        self,
        graft_id: str,
        current_stage: str = Stage.LIVE_100.value,
        *,
        reason: str,
        idempotency_key: str,
        processed_orders: list[str] | None = None,
        export_manifest_ref: str | None = None,
        restore_verified_ref: str | None = None,
        pending_effect_refs: list[str] | None = None,
        financial_undo: bool = False,
    ) -> RollbackReceipt:
        if financial_undo:
            raise ValueError(
                "Restoring prior financial state is not a supported rollback; it needs its own "
                "separate financial compensation authority"
            )
        orders = list(processed_orders or [])
        rollback_id = f"rb-{hashlib.sha256(f'{graft_id}:{reason}'.encode()).hexdigest()[:12]}"
        now = datetime.now(UTC).isoformat()

        holds: list[str] = []
        if not export_manifest_ref:
            holds.append("no consistent state export; a cutback would lose state")
        if not restore_verified_ref:
            holds.append("restore into a disposable copy was not verified")
        if pending_effect_refs:
            holds.extend(f"unresolved effect: {ref}" for ref in pending_effect_refs)
        if holds:
            return RollbackReceipt(
                rollback_id=rollback_id,
                graft_id=graft_id,
                prior_stage=current_stage,
                reverted_to=None,
                reason=reason,
                inventory_order_count=len(orders),
                timestamp=now,
                outcome="held",
                holds=holds,
            )

        producer = Producer(kind=ProducerKind.SERVICE, name="RecoveryManager", version="2.0.0")
        entry = self.ledger.append(
            graft_id=graft_id,
            type=EntryType.STAGE.value,
            producer=producer.model_dump(),
            schema="StageChange/1",
            payload={
                "graft_id": graft_id,
                "from_stage": current_stage,
                "to_stage": Stage.CUTBACK.value,
                "attempt": 1,
                "reason": (
                    f"Code cutback prepared: {reason}. State preserved via "
                    f"{export_manifest_ref}; no financial effect was undone."
                ),
                "actor": {"kind": producer.kind.value, "name": producer.name},
                "evidence_refs": [export_manifest_ref, restore_verified_ref],
            },
            idempotency_key=idempotency_key,
        )
        return RollbackReceipt(
            rollback_id=rollback_id,
            graft_id=graft_id,
            prior_stage=current_stage,
            reverted_to=Stage.CUTBACK.value,
            reason=reason,
            inventory_order_count=len(orders),
            timestamp=now,
            outcome="prepared",
            state_preservation_ref=export_manifest_ref,
            holds=["cutback prepared; restored-state verification remains a separate gate"],
            ledger_seq=entry.seq,
        )
