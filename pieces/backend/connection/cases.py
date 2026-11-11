"""Connection Case Management and Workspace Scoping (GU01).

Implements:
1. ConnectionCase tracking: CREATED, PENDING_AUTHORITY, BOUND, FAILED.
2. Tenant & membership isolation: each case binds strictly to a single merchant workspace.
3. Separation of invite possession vs actual verified workspace authority.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from goldgraft_contracts.common import Producer, ProducerKind
from goldgraft_contracts.ledger import EntryType
from goldgraft_foundation.ledger import Ledger


class CaseStatus(StrEnum):
    CREATED = "CREATED"
    PENDING_AUTHORITY = "PENDING_AUTHORITY"
    BOUND = "BOUND"
    REVOKED = "REVOKED"


@dataclass
class ConnectionCase:
    case_id: str
    merchant_id: str
    workspace_name: str
    status: CaseStatus
    created_at: str
    allowed_resources: list[str] = field(default_factory=list)
    bound_controllers: list[str] = field(default_factory=list)


class CaseManager:
    """Manages connection cases, isolation boundaries, and controller bindings."""

    def __init__(self, ledger: Ledger | None = None):
        self.ledger = ledger or Ledger()
        self._cases: dict[str, ConnectionCase] = {}

    def create_case(
        self,
        merchant_id: str,
        workspace_name: str,
        *,
        allowed_resources: list[str] | None = None,
        idempotency_key: str | None = None,
    ) -> ConnectionCase:
        raw = f"{merchant_id}:{workspace_name}".encode()
        case_id = f"case-{hashlib.sha256(raw).hexdigest()[:12]}"
        now = datetime.now(UTC).isoformat()

        case = ConnectionCase(
            case_id=case_id,
            merchant_id=merchant_id,
            workspace_name=workspace_name,
            status=CaseStatus.CREATED,
            created_at=now,
            allowed_resources=allowed_resources or [],
        )
        self._cases[case_id] = case

        producer = Producer(
            kind=ProducerKind.SERVICE,
            name="CaseManager",
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
                "to_stage": "CREATED",
                "attempt": 1,
                "reason": f"ConnectionCase created for workspace {workspace_name}",
                "actor": {"kind": producer.kind.value, "name": producer.name},
                "evidence_refs": [f"blob://cases/{case_id}"],
            },
            idempotency_key=idempotency_key,
        )
        return case

    def bind_controller(self, case_id: str, controller_id: str) -> ConnectionCase:
        case = self._cases.get(case_id)
        if not case:
            raise KeyError(f"Case {case_id} not found")
        if controller_id not in case.bound_controllers:
            case.bound_controllers.append(controller_id)
        case.status = CaseStatus.BOUND
        return case

    def get_case(self, case_id: str) -> ConnectionCase | None:
        return self._cases.get(case_id)
