"""Cross-case target reservations, epochs and leases (GU04 / IR02).

Tenant or case identity does not partition a physical target. A reservation
owns the canonical target for exactly one case/run, carries a monotonic fencing
epoch, and cannot be released while an external effect is unknown.

An expired lease fences the old executor. It does not hand the target to a new
case while unresolved effects exist; that requires reconciliation first.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


class ReservationConflictError(Exception):
    """Raised when a target resource is currently reserved under another case."""


@dataclass
class TargetReservation:
    reservation_id: str
    target_resource: str
    case_id: str
    granted_at: str
    expires_at: str
    owner_run_id: str | None = None
    fence_epoch: int = 1
    unresolved_effect_refs: list[str] = field(default_factory=list)
    released: bool = False

    def active(self, now: datetime) -> bool:
        return not self.released and datetime.fromisoformat(self.expires_at) > now


class TargetReservationManager:
    """Manages mutual exclusion, fencing epochs and leases across targets."""

    def __init__(self, default_lease_seconds: int = 300):
        self.default_lease_seconds = default_lease_seconds
        self._reservations: dict[str, TargetReservation] = {}

    def _active_for(self, target_resource: str, now: datetime) -> TargetReservation | None:
        for reservation in self._reservations.values():
            if reservation.target_resource == target_resource and reservation.active(now):
                return reservation
        return None

    def reserve(
        self,
        target_resource: str,
        case_id: str,
        *,
        lease_seconds: int | None = None,
        run_id: str | None = None,
    ) -> TargetReservation:
        now = datetime.now(UTC)
        ttl = lease_seconds or self.default_lease_seconds
        existing = self._active_for(target_resource, now)

        if existing is not None:
            if existing.case_id != case_id:
                raise ReservationConflictError(
                    f"Target {target_resource} reserved by case {existing.case_id} "
                    f"until {existing.expires_at}"
                )
            # Same case re-acquires its own reservation; the epoch is unchanged.
            existing.expires_at = (now + timedelta(seconds=ttl)).isoformat()
            if run_id is not None:
                existing.owner_run_id = run_id
            return existing

        # A different case may only take over when no effect is unresolved.
        for reservation in self._reservations.values():
            if reservation.target_resource == target_resource and not reservation.released:
                if reservation.unresolved_effect_refs:
                    raise ReservationConflictError(
                        f"Target {target_resource} has unresolved effects under case "
                        f"{reservation.case_id}; reconcile before transfer"
                    )

        prior_epoch = max(
            (
                r.fence_epoch
                for r in self._reservations.values()
                if r.target_resource == target_resource
            ),
            default=0,
        )
        raw = f"{target_resource}:{case_id}:{now.isoformat()}".encode()
        reservation = TargetReservation(
            reservation_id=f"res-{hashlib.sha256(raw).hexdigest()[:12]}",
            target_resource=target_resource,
            case_id=case_id,
            granted_at=now.isoformat(),
            expires_at=(now + timedelta(seconds=ttl)).isoformat(),
            owner_run_id=run_id,
            fence_epoch=prior_epoch + 1,
        )
        self._reservations[reservation.reservation_id] = reservation
        return reservation

    def current_epoch(self, reservation_id: str) -> int:
        reservation = self._reservations.get(reservation_id)
        if reservation is None or reservation.released:
            raise ReservationConflictError(f"Reservation {reservation_id} is not active")
        return reservation.fence_epoch

    def require_current(self, reservation_id: str, *, case_id: str, epoch: int) -> None:
        """Fence a stale executor before it touches the target."""
        reservation = self._reservations.get(reservation_id)
        if reservation is None or reservation.released:
            raise ReservationConflictError(f"Reservation {reservation_id} is not active")
        if reservation.case_id != case_id:
            raise ReservationConflictError("Reservation belongs to another case")
        if reservation.fence_epoch != epoch:
            raise ReservationConflictError(
                f"Stale fencing epoch {epoch}; current is {reservation.fence_epoch}"
            )
        if not reservation.active(datetime.now(UTC)):
            raise ReservationConflictError("Reservation lease expired")

    def add_unresolved(self, reservation_id: str, effect_ref: str) -> None:
        reservation = self._reservations.get(reservation_id)
        if reservation is None:
            raise ReservationConflictError(f"Reservation {reservation_id} not found")
        if effect_ref not in reservation.unresolved_effect_refs:
            reservation.unresolved_effect_refs.append(effect_ref)

    def resolve_unresolved(self, reservation_id: str, effect_ref: str) -> None:
        reservation = self._reservations.get(reservation_id)
        if reservation is None:
            raise ReservationConflictError(f"Reservation {reservation_id} not found")
        if effect_ref in reservation.unresolved_effect_refs:
            reservation.unresolved_effect_refs.remove(effect_ref)

    def release(self, reservation_id: str) -> None:
        reservation = self._reservations.get(reservation_id)
        if reservation is None:
            return
        if reservation.unresolved_effect_refs:
            raise ReservationConflictError(
                "Cannot release a target reservation with unresolved effects"
            )
        reservation.released = True
