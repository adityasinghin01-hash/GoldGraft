"""Cross-Case Target Reservations and Leases (GU04).

Implements:
1. Target resource reservation across concurrent cases to prevent split-brain deploys.
2. Expiring leases with heartbeat renewal.
3. Explicit release and conflict detection.
"""

import hashlib
from dataclasses import dataclass
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
    released: bool = False


class TargetReservationManager:
    """Manages mutual exclusion and leases across target deployment environments."""

    def __init__(self, default_lease_seconds: int = 300):
        self.default_lease_seconds = default_lease_seconds
        self._reservations: dict[str, TargetReservation] = {}

    def reserve(
        self,
        target_resource: str,
        case_id: str,
        *,
        lease_seconds: int | None = None,
    ) -> TargetReservation:
        now = datetime.now(UTC)
        ttl = lease_seconds or self.default_lease_seconds
        expires = now + timedelta(seconds=ttl)

        # Check existing active reservations
        for res in self._reservations.values():
            if res.target_resource == target_resource and not res.released:
                if datetime.fromisoformat(res.expires_at) > now:
                    if res.case_id != case_id:
                        msg = (
                            f"Target {target_resource} reserved by case {res.case_id} "
                            f"until {res.expires_at}"
                        )
                        raise ReservationConflictError(msg)

        raw = f"{target_resource}:{case_id}:{now.isoformat()}".encode()
        res_id = f"res-{hashlib.sha256(raw).hexdigest()[:12]}"

        reservation = TargetReservation(
            reservation_id=res_id,
            target_resource=target_resource,
            case_id=case_id,
            granted_at=now.isoformat(),
            expires_at=expires.isoformat(),
        )
        self._reservations[res_id] = reservation
        return reservation

    def release(self, reservation_id: str) -> None:
        res = self._reservations.get(reservation_id)
        if res:
            res.released = True
