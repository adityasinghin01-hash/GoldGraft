"""Ledger-driven reconciliation (GU05).

A last-stage lookup is not reconciliation. This module distinguishes three
things that used to be conflated:

* the ledger chain verified and the last committed stage is terminal -> clean
* the chain verified and the last stage is in flight -> interrupted
* the chain did not verify, or the terminal state depends on an effect that is
  not recorded -> unknown, and the caller must hold

Unresolved effect references block a clean verdict: a committed stage that
claims success while an effect is still unknown is not clean.
"""

from dataclasses import dataclass, field
from typing import Literal

from goldgraft_contracts.common import Producer, ProducerKind, Stage
from goldgraft_contracts.ledger import EntryType
from goldgraft_foundation.ledger import Ledger

ReconcileOutcome = Literal["clean", "interrupted", "unknown", "held"]


@dataclass
class ReconciliationReport:
    graft_id: str
    last_known_stage: str
    reconciled_stage: str
    total_entries_inspected: int
    clean: bool
    outcome: ReconcileOutcome = "clean"
    reconciled_entry_seq: int | None = None
    reason: str | None = None
    holds: list[str] = field(default_factory=list)
    chain_verified: bool = True

    def __post_init__(self):
        if self.clean != (self.outcome == "clean"):
            raise ValueError("clean must be exactly the clean outcome")


INTERMEDIATE_IN_FLIGHT_STAGES = {
    Stage.GRAFTED.value,
    Stage.PROVING.value,
    Stage.REPAIRING.value,
    Stage.SHADOW.value,
    Stage.HEAL_1.value,
    Stage.HEAL_10.value,
    Stage.HEAL_50.value,
}

TERMINAL_STAGES = {
    Stage.DONE.value,
    Stage.CUTBACK.value,
    Stage.FAILED.value,
}


class LedgerReconciler:
    """Audits ledger history and restores a deterministic, evidenced state."""

    def __init__(self, ledger: Ledger | None = None):
        self.ledger = ledger or Ledger()

    def _last_stage(self, entries) -> str:
        last_stage = Stage.CREATED.value
        for entry in entries:
            if entry.payload and isinstance(entry.payload, dict) and "to_stage" in entry.payload:
                last_stage = entry.payload["to_stage"]
        return last_stage

    def reconcile_graft(
        self, graft_id: str, *, unresolved_effect_refs: list[str] | None = None
    ) -> ReconciliationReport:
        entries = self.ledger.read(graft_id)
        chain = self.ledger.verify_chain(graft_id)
        if not entries:
            return ReconciliationReport(
                graft_id=graft_id,
                last_known_stage="NONE",
                reconciled_stage=Stage.CREATED.value,
                total_entries_inspected=0,
                clean=True,
                outcome="clean",
                reason="no ledger history; clean initial state",
            )
        last_stage = self._last_stage(entries)
        if not chain.ok:
            return ReconciliationReport(
                graft_id=graft_id,
                last_known_stage=last_stage,
                reconciled_stage=last_stage,
                total_entries_inspected=len(entries),
                clean=False,
                outcome="unknown",
                chain_verified=False,
                reason=f"ledger chain failed at seq {chain.first_bad_seq}",
                holds=["ledger integrity is not established; hold and investigate"],
            )
        pending = list(unresolved_effect_refs or [])
        if pending:
            return ReconciliationReport(
                graft_id=graft_id,
                last_known_stage=last_stage,
                reconciled_stage=last_stage,
                total_entries_inspected=len(entries),
                clean=False,
                outcome="held",
                reason="committed stage depends on unresolved external effects",
                holds=[f"unresolved effect: {ref}" for ref in pending],
            )
        if last_stage in INTERMEDIATE_IN_FLIGHT_STAGES:
            return ReconciliationReport(
                graft_id=graft_id,
                last_known_stage=last_stage,
                reconciled_stage=last_stage,
                total_entries_inspected=len(entries),
                clean=False,
                outcome="interrupted",
                reason=f"last committed stage {last_stage} is in flight",
                holds=["interrupted operation; reconcile the effect before any retry"],
            )
        if last_stage not in TERMINAL_STAGES:
            return ReconciliationReport(
                graft_id=graft_id,
                last_known_stage=last_stage,
                reconciled_stage=last_stage,
                total_entries_inspected=len(entries),
                clean=False,
                outcome="unknown",
                reason=f"last committed stage {last_stage} is not a verified terminal state",
                holds=["stage is neither terminal nor a known in-flight boundary"],
            )
        return ReconciliationReport(
            graft_id=graft_id,
            last_known_stage=last_stage,
            reconciled_stage=last_stage,
            total_entries_inspected=len(entries),
            clean=True,
            outcome="clean",
            reason=f"ledger verified and terminal at {last_stage}",
        )
    def reconcile_interrupted_operation(
        self,
        graft_id: str,
        operation_id: str | None = None,
        *,
        auto_cutback: bool = True,
        target_stage: Stage = Stage.CUTBACK,
        unresolved_effect_refs: list[str] | None = None,
    ) -> ReconciliationReport:
        """Audits an interrupted operation and commits at most a safe cutback."""
        report = self.reconcile_graft(
            graft_id, unresolved_effect_refs=unresolved_effect_refs
        )
        if report.outcome != "interrupted":
            return report
        if not auto_cutback:
            return report

        producer = Producer(kind=ProducerKind.SERVICE, name="LedgerReconciler", version="2.0.0")
        reason_msg = (
            f"Reconciled interrupted stage {report.last_known_stage} -> {target_stage.value}"
        )
        if operation_id:
            reason_msg += f" for op {operation_id}"
        entry = self.ledger.append(
            graft_id=graft_id,
            type=EntryType.STAGE.value,
            producer=producer.model_dump(),
            schema="StageChange/1",
            payload={
                "graft_id": graft_id,
                "from_stage": report.last_known_stage,
                "to_stage": target_stage.value,
                "attempt": 1,
                "reason": reason_msg,
                "actor": {"kind": producer.kind.value, "name": producer.name},
                "evidence_refs": [],
            },
            idempotency_key=f"reconcile-{graft_id}-{report.total_entries_inspected + 1}",
        )
        return ReconciliationReport(
            graft_id=graft_id,
            last_known_stage=report.last_known_stage,
            reconciled_stage=target_stage.value,
            total_entries_inspected=report.total_entries_inspected + 1,
            clean=False,
            outcome="interrupted",
            reconciled_entry_seq=entry.seq,
            reason=reason_msg,
            holds=["cutback recorded; the interrupted effect still needs reconciliation"],
        )
