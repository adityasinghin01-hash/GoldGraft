"""Lifecycle package for GoldGraft backend (GU01, GU02, GU04, GU05).

Provides:
- engine.py: Core JobLifecycleState machine, transitions, and stage ledger commits (GU01/GU02).
- approvals.py: Exact approval slots, target resource locks, and deployment gates (GU04).
- recovery.py: Safe zero-downtime rollback and financial state preservation (GU05).
- exit.py: Verifiable merchant exit, token revocation, and resource cleanup (GU05).
"""

from .approvals import (
    ApprovalGate,
    ApprovalSlot,
    AuthorizationEscalationError,
    TargetLockError,
)
from .engine import (
    STAGE_MAP,
    VALID_TRANSITIONS,
    InvalidStateTransitionError,
    JobLifecycleState,
    LifecycleEngine,
)
from .exit import ExitController, ExitReceipt
from .recovery import RecoveryManager, RollbackReceipt

__all__ = [
    "STAGE_MAP",
    "VALID_TRANSITIONS",
    "ApprovalGate",
    "ApprovalSlot",
    "AuthorizationEscalationError",
    "ExitController",
    "ExitReceipt",
    "InvalidStateTransitionError",
    "JobLifecycleState",
    "LifecycleEngine",
    "RecoveryManager",
    "RollbackReceipt",
    "TargetLockError",
]
