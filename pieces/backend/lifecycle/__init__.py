"""Lifecycle package for GoldGraft backend (GU01, GU02, GU04, GU05).

Provides:
- engine.py: Core JobLifecycleState machine, transitions, and stage ledger commits (GU01/GU02).
- approvals.py: Exact approval slots, target resource locks, and deployment gates (GU04).
- reservations.py: Cross-case target reservations and leases (GU04).
- effects.py: Effect intents and unknown state reconciliation (GU04).
- state_plan.py: State cutover planning and economic data preservation rules (GU05).
- recovery.py: Safe zero-downtime rollback and financial state preservation (GU05).
- reconcile.py: Crash/failure state reconciliation against foundation ledger (GU05).
- exit.py: Verifiable merchant exit, token revocation, and resource cleanup (GU05).
"""

from .approvals import (
    ApprovalGate,
    ApprovalSlot,
    AuthorizationEscalationError,
    TargetLockError,
)
from .effects import EffectManager, EffectSlot, EffectStatus
from .engine import (
    STAGE_MAP,
    VALID_TRANSITIONS,
    InvalidStateTransitionError,
    JobLifecycleState,
    LifecycleEngine,
)
from .exit import ExitController, ExitReceipt
from .reconcile import LedgerReconciler, ReconciliationReport
from .recovery import RecoveryManager, RollbackReceipt
from .reservations import ReservationConflictError, TargetReservation, TargetReservationManager
from .state_plan import StateCutoverPlan, StatePlanner

__all__ = [
    "STAGE_MAP",
    "VALID_TRANSITIONS",
    "ApprovalGate",
    "ApprovalSlot",
    "AuthorizationEscalationError",
    "EffectManager",
    "EffectSlot",
    "EffectStatus",
    "ExitController",
    "ExitReceipt",
    "InvalidStateTransitionError",
    "JobLifecycleState",
    "LedgerReconciler",
    "LifecycleEngine",
    "ReconciliationReport",
    "RecoveryManager",
    "ReservationConflictError",
    "RollbackReceipt",
    "StateCutoverPlan",
    "StatePlanner",
    "TargetLockError",
    "TargetReservation",
    "TargetReservationManager",
]
