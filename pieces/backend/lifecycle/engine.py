"""Lifecycle state machine for GoldGraft jobs and grafts (GU01 & GU02).

Manages state transitions:
    PENDING ➔ BASELINE_TESTED ➔ UPGRADED_IN_SANDBOX ➔ PROVED ➔ READY_TO_DEPLOY
and integrates with foundation.ledger for cryptographic audit trails.
"""

from enum import StrEnum
from typing import Any

from goldgraft_contracts.common import Producer, ProducerKind, Stage
from goldgraft_contracts.ledger import EntryType
from goldgraft_foundation.ledger import Ledger


class JobLifecycleState(StrEnum):
    PENDING = "PENDING"
    BASELINE_TESTED = "BASELINE_TESTED"
    UPGRADED_IN_SANDBOX = "UPGRADED_IN_SANDBOX"
    PROVED = "PROVED"
    READY_TO_DEPLOY = "READY_TO_DEPLOY"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


VALID_TRANSITIONS: dict[JobLifecycleState, set[JobLifecycleState]] = {
    JobLifecycleState.PENDING: {
        JobLifecycleState.BASELINE_TESTED,
        JobLifecycleState.CANCELLED,
        JobLifecycleState.FAILED,
    },
    JobLifecycleState.BASELINE_TESTED: {
        JobLifecycleState.UPGRADED_IN_SANDBOX,
        JobLifecycleState.CANCELLED,
        JobLifecycleState.FAILED,
    },
    JobLifecycleState.UPGRADED_IN_SANDBOX: {
        JobLifecycleState.PROVED,
        JobLifecycleState.CANCELLED,
        JobLifecycleState.FAILED,
    },
    JobLifecycleState.PROVED: {
        JobLifecycleState.READY_TO_DEPLOY,
        JobLifecycleState.CANCELLED,
        JobLifecycleState.FAILED,
    },
    JobLifecycleState.READY_TO_DEPLOY: {JobLifecycleState.CANCELLED},
    JobLifecycleState.CANCELLED: set(),
    JobLifecycleState.FAILED: set(),
}

STAGE_MAP: dict[JobLifecycleState, Stage] = {
    JobLifecycleState.PENDING: Stage.CREATED,
    JobLifecycleState.BASELINE_TESTED: Stage.SURVEYED,
    JobLifecycleState.UPGRADED_IN_SANDBOX: Stage.GRAFTED,
    JobLifecycleState.PROVED: Stage.CERTIFIED,
    JobLifecycleState.READY_TO_DEPLOY: Stage.PR_OPEN,
    JobLifecycleState.CANCELLED: Stage.FAILED,
    JobLifecycleState.FAILED: Stage.FAILED,
}


class InvalidStateTransitionError(Exception):
    """Raised when an invalid state transition is requested."""

    def __init__(self, current: JobLifecycleState, target: JobLifecycleState):
        super().__init__(f"Invalid state transition from {current.value} to {target.value}")
        self.current = current
        self.target = target


class LifecycleEngine:
    """Orchestrates job lifecycle progression and audit trails in foundation.ledger."""

    def __init__(self, ledger: Ledger | None = None):
        self.ledger = ledger or Ledger()
        self._states: dict[str, JobLifecycleState] = {}
        self._attempts: dict[str, dict[str, int]] = {}
        self._history: dict[str, list[dict[str, Any]]] = {}

    def get_state(self, graft_id: str) -> JobLifecycleState:
        return self._states.get(graft_id, JobLifecycleState.PENDING)

    def transition(
        self,
        graft_id: str,
        target_state: JobLifecycleState,
        *,
        idempotency_key: str,
        reason: str | None = None,
        evidence_refs: list[str] | None = None,
        producer: Producer | None = None,
    ) -> dict[str, Any]:
        current = self.get_state(graft_id)

        # Allow no-op idempotent re-transition
        if current == target_state:
            return {
                "graft_id": graft_id,
                "previous_state": current.value,
                "current_state": target_state.value,
                "idempotent": True,
            }

        allowed = VALID_TRANSITIONS.get(current, set())
        if target_state not in allowed:
            raise InvalidStateTransitionError(current, target_state)

        from_stage = STAGE_MAP[current] if graft_id in self._states else None
        to_stage = STAGE_MAP[target_state]

        attempts = self._attempts.setdefault(graft_id, {})
        attempts[to_stage.value] = attempts.get(to_stage.value, 0) + 1

        service_producer = producer or Producer(
            kind=ProducerKind.SERVICE, name="LifecycleEngine", version="1.0.0"
        )
        stage_actor = {"kind": service_producer.kind.value, "name": service_producer.name}

        payload = {
            "graft_id": graft_id,
            "from_stage": from_stage.value if from_stage else None,
            "to_stage": to_stage.value,
            "attempt": attempts[to_stage.value],
            "reason": reason or f"Transitioned to {target_state.value}",
            "actor": stage_actor,
            "evidence_refs": evidence_refs or [],
        }

        # Commit state change to append-only ledger
        self.ledger.append(
            graft_id=graft_id,
            type=EntryType.STAGE.value,
            producer=service_producer.model_dump(),
            schema="StageChange/1",
            payload=payload,
            idempotency_key=idempotency_key,
        )

        self._states[graft_id] = target_state
        self._history.setdefault(graft_id, []).append(payload)

        return {
            "graft_id": graft_id,
            "previous_state": current.value,
            "current_state": target_state.value,
            "idempotent": False,
        }

    def cancel(
        self, graft_id: str, idempotency_key: str, reason: str = "User requested cancellation"
    ) -> dict[str, Any]:
        return self.transition(
            graft_id=graft_id,
            target_state=JobLifecycleState.CANCELLED,
            idempotency_key=idempotency_key,
            reason=reason,
        )

    def rollback(
        self,
        graft_id: str,
        target_state: JobLifecycleState,
        idempotency_key: str,
        reason: str = "Rollback triggered",
    ) -> dict[str, Any]:
        """Rolls back safely to an earlier valid state by recording an audit record."""
        current = self.get_state(graft_id)
        service_producer = Producer(
            kind=ProducerKind.SERVICE, name="LifecycleEngine", version="1.0.0"
        )
        to_stage = STAGE_MAP.get(target_state, Stage.CREATED)

        payload = {
            "graft_id": graft_id,
            "from_stage": STAGE_MAP.get(current, Stage.CREATED).value,
            "to_stage": to_stage.value,
            "attempt": 1,
            "reason": reason,
            "actor": {"kind": service_producer.kind.value, "name": service_producer.name},
            "evidence_refs": [],
        }
        self.ledger.append(
            graft_id=graft_id,
            type=EntryType.STAGE.value,
            producer=service_producer.model_dump(),
            schema="StageChange/1",
            payload=payload,
            idempotency_key=idempotency_key,
        )
        self._states[graft_id] = target_state
        return payload
