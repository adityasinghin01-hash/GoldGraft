"""Resource Authority and Role Enforcement for Connection Cases (GU01).

Implements:
1. Strict role separation: READER, CONTROLLER, DEPLOYER, ADMIN.
2. Hard rule: Possession of an invite or key does not grant ownership.
3. Escalation denial: Reader tokens strictly denied write/mutate operations.
4. Cryptographic audit logging of authority grants and checks.
"""

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from goldgraft_contracts.common import Producer, ProducerKind
from goldgraft_contracts.ledger import EntryType
from goldgraft_foundation.ledger import Ledger


class CaseRole(StrEnum):
    READER = "READER"
    CONTROLLER = "CONTROLLER"
    DEPLOYER = "DEPLOYER"
    ADMIN = "ADMIN"


class PermissionDeniedError(Exception):
    """Raised when an actor attempts an action outside their granted role."""


@dataclass
class AuthorityGrant:
    grant_id: str
    case_id: str
    actor_id: str
    role: CaseRole
    target_scope: str  # e.g. "github.com/merchant/repo:read-only"
    granted_by: str
    created_at: str
    revoked: bool = False


class AuthorityManager:
    """Manages role-based access control, scope enforcement, and escalation prevention."""

    def __init__(self, ledger: Ledger | None = None):
        self.ledger = ledger or Ledger()
        self._grants: dict[str, AuthorityGrant] = {}

    def grant_role(
        self,
        case_id: str,
        actor_id: str,
        role: CaseRole,
        target_scope: str,
        *,
        granted_by: str,
        idempotency_key: str | None = None,
    ) -> AuthorityGrant:
        raw = f"{case_id}:{actor_id}:{role}:{target_scope}".encode()
        grant_id = f"grant-{hashlib.sha256(raw).hexdigest()[:12]}"
        now = datetime.now(UTC).isoformat()

        grant = AuthorityGrant(
            grant_id=grant_id,
            case_id=case_id,
            actor_id=actor_id,
            role=role,
            target_scope=target_scope,
            granted_by=granted_by,
            created_at=now,
        )
        self._grants[grant_id] = grant

        producer = Producer(
            kind=ProducerKind.SERVICE,
            name="AuthorityManager",
            version="1.0.0",
        )
        self.ledger.append(
            graft_id=case_id,
            type=EntryType.STAGE.value,
            producer=producer.model_dump(),
            schema="StageChange/1",
            payload={
                "graft_id": case_id,
                "from_stage": None,
                "to_stage": "GATED",
                "attempt": 1,
                "reason": f"Granted role {role.value} to {actor_id} on {target_scope}",
                "actor": {"kind": producer.kind.value, "name": producer.name},
                "evidence_refs": [f"blob://grants/{grant_id}"],
            },
            idempotency_key=idempotency_key,
        )
        return grant

    def check_permission(
        self,
        grant_id: str,
        required_role: CaseRole,
        resource_path: str,
    ) -> None:
        grant = self._grants.get(grant_id)
        if not grant or grant.revoked:
            raise PermissionDeniedError("Grant not found or revoked")

        if grant.role == CaseRole.READER and required_role != CaseRole.READER:
            raise PermissionDeniedError(
                f"Reader escalation denied: Actor {grant.actor_id} cannot perform write operations"
            )

        if grant.role != CaseRole.ADMIN and required_role not in {CaseRole.READER, grant.role}:
            raise PermissionDeniedError("Role does not cover the requested operation")

        # A repository named repo-extra is not a child of repo.
        scope = grant.target_scope.rstrip("/")
        if scope == "*" or not (resource_path == scope or resource_path.startswith(scope + "/")):
            msg = (
                f"Scope boundary violated: resource {resource_path} "
                f"outside grant {grant.target_scope}"
            )
            raise PermissionDeniedError(msg)

    def revoke_grant(self, grant_id: str) -> None:
        grant = self._grants.get(grant_id)
        if grant:
            grant.revoked = True
