"""Ledger-Driven State Reconciliation and Crash Recovery (GU05).

Implements:
1. Reconstructs in-memory lifecycle state directly from cryptographic ledger entries.
2. Identifies interrupted operations (e.g. crash after Start before capture).
3. Reconciles state to a safe boundary (CUTBACK or FAILED) without data loss.
"""

from dataclasses import dataclass

from goldgraft_contracts.common import Producer, ProducerKind, Stage
from goldgraft_contracts.ledger import EntryType
from goldgraft_foundation.ledger import Ledger


@dataclass
class ReconciliationReport:
    graft_id: str
    last_known_stage: str
    reconciled_stage: str
    total_entries_inspected: int
    clean: bool
    reconciled_entry_seq: int | None = None
    reason: str | None = None


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
    """Audits ledger history and restores deterministic state after interruptions."""

    def __init__(self, ledger: Ledger | None = None):
        self.ledger = ledger or Ledger()

    def reconcile_graft(self, graft_id: str) -> ReconciliationReport:
        entries = self.ledger.read(graft_id)
        if not entries:
            return ReconciliationReport(
                graft_id=graft_id,
                last_known_stage="NONE",
                reconciled_stage=Stage.CREATED.value,
                total_entries_inspected=0,
                clean=True,
            )

        last_stage = Stage.CREATED.value
        for entry in entries:
            if entry.payload and isinstance(entry.payload, dict) and "to_stage" in entry.payload:
                last_stage = entry.payload["to_stage"]

        return ReconciliationReport(
            graft_id=graft_id,
            last_known_stage=last_stage,
            reconciled_stage=last_stage,
            total_entries_inspected=len(entries),
            clean=True,
        )

    def reconcile_interrupted_operation(
        self,
        graft_id: str,
        operation_id: str | None = None,
        *,
        auto_cutback: bool = True,
        target_stage: Stage = Stage.CUTBACK,
    ) -> ReconciliationReport:
        """Audits ledger for incomplete in-flight operations and safely rolls back to safe stage."""
        entries = self.ledger.read(graft_id)
        if not entries:
            return ReconciliationReport(
                graft_id=graft_id,
                last_known_stage="NONE",
                reconciled_stage=Stage.CREATED.value,
                total_entries_inspected=0,
                clean=True,
                reason="No ledger history found; clean initial state",
            )

        last_stage = Stage.CREATED.value
        for entry in entries:
            if entry.payload and isinstance(entry.payload, dict) and "to_stage" in entry.payload:
                last_stage = entry.payload["to_stage"]

        is_interrupted = last_stage in INTERMEDIATE_IN_FLIGHT_STAGES

        if not is_interrupted:
            return ReconciliationReport(
                graft_id=graft_id,
                last_known_stage=last_stage,
                reconciled_stage=last_stage,
                total_entries_inspected=len(entries),
                clean=True,
                reason=f"Ledger is at stable stage {last_stage}",
            )

        # Interrupted operation detected: commit safe reconciliation entry
        producer = Producer(
            kind=ProducerKind.SERVICE,
            name="LedgerReconciler",
            version="1.0.0",
        )
        reason_msg = f"Reconciled interrupted stage {last_stage} -> {target_stage.value}"
        if operation_id:
            reason_msg += f" for op {operation_id}"

        new_entry_seq = None
        reconciled_stage = last_stage
        if auto_cutback:
            reconciled_stage = target_stage.value
            entry = self.ledger.append(
                graft_id=graft_id,
                type=EntryType.STAGE.value,
                producer=producer.model_dump(),
                schema="StageChange/1",
                payload={
                    "graft_id": graft_id,
                    "from_stage": last_stage,
                    "to_stage": reconciled_stage,
                    "attempt": 1,
                    "reason": reason_msg,
                    "actor": {"kind": producer.kind.value, "name": producer.name},
                    "evidence_refs": [],
                },
                idempotency_key=f"reconcile-{graft_id}-{len(entries) + 1}",
            )
            new_entry_seq = entry.seq

        return ReconciliationReport(
            graft_id=graft_id,
            last_known_stage=last_stage,
            reconciled_stage=reconciled_stage,
            total_entries_inspected=len(entries) + (1 if new_entry_seq is not None else 0),
            clean=False,
            reconciled_entry_seq=new_entry_seq,
            reason=reason_msg,
        )
