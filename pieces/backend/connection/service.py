"""Durable, tenant-scoped case intake; readiness requires separate trusted evidence.

The foundation ledger owns case/event truth. SQL tables below are coordination
indexes and idempotency records committed in the same transaction as the ledger.
No provider, model, payment or shop execution occurs during case intake.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from goldgraft_contracts.connection_control import (
    CaseEvent,
    CaseList,
    CaseSummary,
    CaseView,
    ConnectionCase,
    CreateCase,
    RequiredAction,
)
from goldgraft_contracts.plan5_common import Id, content_digest, reject_secret
from goldgraft_foundation.ledger import Ledger, LedgerTransaction
from pydantic import TypeAdapter, ValidationError
from sqlalchemy import Column, Index, MetaData, String, Table, Text, and_, select

metadata = MetaData()
cases = Table(
    "case_service_cases",
    metadata,
    Column("case_id", String, primary_key=True),
    Column("tenant_id", String, nullable=False),
    Column("requester_id", String, nullable=False),
    Index("ix_case_service_owner", "tenant_id", "requester_id"),
)
requests = Table(
    "case_service_requests",
    metadata,
    Column("namespace", String, primary_key=True),
    Column("key", String, primary_key=True),
    Column("fingerprint", String, nullable=False),
    Column("response", Text, nullable=False),
)
cursors = Table(
    "case_service_cursors",
    metadata,
    Column("cursor", String, primary_key=True),
    Column("tenant_id", String, nullable=False),
    Column("actor_id", String, nullable=False),
    Column("last_case_id", String, nullable=False),
    Column("expires_at", String, nullable=False),
)
PRODUCER = {"kind": "service", "name": "case-service", "version": "1"}


class ServiceError(ValueError):
    """Closed reason codes only; never echo a request or credential-bearing error."""

    def __init__(self, code: str, status: int = 409):
        self.code, self.status = code, status
        super().__init__(code)


@dataclass(frozen=True)
class Principal:
    """Produced by the host's verified session/worker adapter, never from body/header IDs."""

    actor_id: str
    tenant_id: str
    expires_at: datetime
    csrf_token: str = field(repr=False)
    kind: str = "session"

    def __post_init__(self):
        for value in (self.actor_id, self.tenant_id):
            TypeAdapter(Id).validate_python(value)
            reject_secret(value)
        if (
            self.expires_at.tzinfo is None
            or self.expires_at.utcoffset() != timedelta(0)
            or not isinstance(self.csrf_token, str)
            or not 1 <= len(self.csrf_token) <= 256
            or not self.csrf_token.isascii()
            or self.kind not in {"session", "draft", "service"}
        ):
            raise ValueError("INVALID principal configuration")


class CaseService:
    """Actual persistent intake component, without claiming external qualification."""

    evidence_class = "component_offline"

    def __init__(self, ledger: Ledger, *, clock: Callable[[], datetime] | None = None):
        if ledger.engine.url.database in (None, "", ":memory:"):
            raise ValueError("DURABLE case ledger required")
        self.ledger = ledger
        self.clock = clock or (lambda: datetime.now(UTC))
        metadata.create_all(ledger.engine)

    def check_principal(self, principal):
        if not isinstance(principal, Principal) or principal.expires_at <= self.clock():
            raise ServiceError("AUTHENTICATION_REQUIRED", 401)
        return principal

    def create_case(self, principal, body: CreateCase, key: str) -> ConnectionCase:
        self.check_principal(principal)
        if principal.kind != "session":
            raise ServiceError("SESSION_REQUIRED", 403)
        TypeAdapter(Id).validate_python(key)
        reject_secret(key)
        body = CreateCase.model_validate(body.model_dump(mode="json"))
        try:
            reject_secret(body.shop_url)
        except ValueError:
            raise ServiceError("INVALID_BODY", 422) from None
        namespace = "case-create:" + content_digest(
            {"tenant": principal.tenant_id, "actor": principal.actor_id}
        )
        fingerprint = content_digest(body)
        request_digest = content_digest(
            {"namespace": namespace, "key": key, "request": body.model_dump(mode="json")}
        )
        with self.ledger.transaction(namespace) as transaction:
            prior = (
                transaction.conn.execute(
                    select(requests).where(requests.c.namespace == namespace, requests.c.key == key)
                )
                .mappings()
                .first()
            )
            if prior is not None:
                if prior["fingerprint"] != fingerprint:
                    raise ServiceError("IDEMPOTENCY_CONFLICT")
                try:
                    cached = ConnectionCase.model_validate_json(prior["response"])
                except ValidationError:
                    raise ServiceError("INTEGRITY_FAILURE", 503) from None
                rows = self._owned_rows(principal, cached.case_id)
                if not any(
                    row.schema_ == "ConnectionCase/1"
                    and row.inputs == [request_digest]
                    and self.ledger.payload(row) == cached.model_dump(mode="json")
                    for row in rows
                ):
                    raise ServiceError("INTEGRITY_FAILURE", 503)
                return cached
            case = self._write_case(transaction.conn, principal, body.shop_url, request_digest)
            transaction.conn.execute(
                requests.insert().values(
                    namespace=namespace,
                    key=key,
                    fingerprint=fingerprint,
                    response=case.model_dump_json(),
                )
            )
            return case

    def _write_case(self, connection, principal, shop_url, request_digest):
        case = ConnectionCase(
            case_id="case-" + uuid4().hex,
            tenant_id=principal.tenant_id,
            requester_id=principal.actor_id,
            shop_url=shop_url,
            created_at=self.clock(),
            graph_ref=None,
            binding_refs=[],
            status="setup_needed",
        )
        transaction = LedgerTransaction(self.ledger, connection, case.case_id)
        entry = transaction.append(
            "ARTIFACT",
            PRODUCER,
            "ConnectionCase/1",
            payload=case.model_dump(mode="json"),
            inputs=[request_digest],
        )
        event = CaseEvent(
            event_id="case-event-" + uuid4().hex,
            case_id=case.case_id,
            sequence=1,
            state_version=1,
            kind="case_changed",
            payload_ref="ledger:" + entry.entry_hash,
            payload_digest=entry.payload_hash,
            occurred_at=self.clock(),
        )
        transaction.append(
            "ARTIFACT", PRODUCER, "CaseEvent/1", payload=event.model_dump(mode="json")
        )
        connection.execute(
            cases.insert().values(
                case_id=case.case_id,
                tenant_id=case.tenant_id,
                requester_id=case.requester_id,
            )
        )
        return case

    @property
    def drafts(self):
        from .drafts import DraftService

        return DraftService(self)

    def create_draft(self, principal, body, key):
        return self.drafts.create(principal, body, key)

    def claim_draft(self, principal, draft_id, body, key, capability):
        return self.drafts.claim(principal, draft_id, body, key, capability)

    def _owned_rows(self, principal, case_id):
        self.check_principal(principal)
        if principal.kind != "session":
            raise ServiceError("CASE_UNAVAILABLE", 404)
        with self.ledger.engine.connect() as db:
            allowed = db.execute(
                select(cases.c.case_id).where(
                    cases.c.case_id == case_id,
                    cases.c.tenant_id == principal.tenant_id,
                    cases.c.requester_id == principal.actor_id,
                )
            ).first()
        if allowed is None:
            raise ServiceError("CASE_UNAVAILABLE", 404)
        # Access is checked before loading the private ledger body.
        if not self.ledger.verify_chain(case_id).ok:
            raise ServiceError("INTEGRITY_FAILURE", 503)
        return self.ledger.read(case_id)

    def get_case(self, principal, case_id) -> ConnectionCase:
        rows = self._owned_rows(principal, case_id)
        matches = [r for r in rows if r.schema_ == "ConnectionCase/1"]
        if not matches:
            raise ServiceError("INTEGRITY_FAILURE", 503)
        case = ConnectionCase.model_validate(self.ledger.payload(matches[-1]))
        if case.case_id != case_id:
            raise ServiceError("INTEGRITY_FAILURE", 503)
        if (case.tenant_id, case.requester_id) != (principal.tenant_id, principal.actor_id):
            raise ServiceError("CASE_UNAVAILABLE", 404)
        return case

    def list_cases(self, principal, *, cursor=None, limit=20) -> CaseList:
        self.check_principal(principal)
        if principal.kind != "session":
            raise ServiceError("SESSION_REQUIRED", 403)
        if type(limit) is not int or not 1 <= limit <= 50:
            raise ServiceError("INVALID_QUERY", 422)
        condition = and_(
            cases.c.tenant_id == principal.tenant_id,
            cases.c.requester_id == principal.actor_id,
        )
        with self.ledger.engine.begin() as db:
            if cursor is not None:
                position = (
                    db.execute(
                        select(cursors).where(
                            cursors.c.cursor == cursor,
                            cursors.c.tenant_id == principal.tenant_id,
                            cursors.c.actor_id == principal.actor_id,
                        )
                    )
                    .mappings()
                    .first()
                )
                if (
                    position is None
                    or datetime.fromisoformat(position["expires_at"]) <= self.clock()
                ):
                    raise ServiceError("CURSOR_INVALID", 400)
                condition = and_(condition, cases.c.case_id > position["last_case_id"])
            ids = list(
                db.execute(
                    select(cases.c.case_id)
                    .where(condition)
                    .order_by(cases.c.case_id)
                    .limit(limit + 1)
                ).scalars()
            )
            next_cursor = None
            if len(ids) > limit:
                next_cursor = "cursor-" + uuid4().hex
                db.execute(
                    cursors.insert().values(
                        cursor=next_cursor,
                        tenant_id=principal.tenant_id,
                        actor_id=principal.actor_id,
                        last_case_id=ids[limit - 1],
                        expires_at=(self.clock() + timedelta(minutes=15)).isoformat(),
                    )
                )
        values = [self.get_case(principal, case_id) for case_id in ids[:limit]]
        return CaseList(
            items=[
                CaseSummary(
                    case_id=case.case_id,
                    shop_url=case.shop_url,
                    status=case.status,
                    updated_at=case.created_at,
                )
                for case in values
            ],
            next_cursor=next_cursor,
        )

    def events(self, principal, case_id, *, after=0) -> list[CaseEvent]:
        rows = self._owned_rows(principal, case_id)
        values = [
            CaseEvent.model_validate(self.ledger.payload(row))
            for row in rows
            if row.schema_ == "CaseEvent/1"
        ]
        if (
            [v.sequence for v in values] != list(range(1, len(values) + 1))
            or any(v.case_id != case_id for v in values)
            or any(
                b.state_version < a.state_version for a, b in zip(values, values[1:], strict=False)
            )
        ):
            raise ServiceError("INTEGRITY_FAILURE", 503)
        if (
            type(after) is not int
            or after < 0
            or after > max((v.sequence for v in values), default=0)
        ):
            raise ServiceError("INVALID_EVENT_CURSOR")
        return [v for v in values if v.sequence > after]

    def view(self, principal, case_id) -> CaseView:
        case = self.get_case(principal, case_id)
        events = self.events(principal, case_id)
        return CaseView(
            case=case,
            state_version=events[-1].state_version,
            last_event_seq=events[-1].sequence,
            resources=[],
            processing=None,
            readiness=None,
            pending_action_id=None,
            action=None,
            lifecycle=None,
            delivery_ref=None,
            required_actions=[
                RequiredAction(
                    kind="connect",
                    resource_ids=[],
                    enabled=True,
                    reason_code="RESOURCE_AUTHORITY_REQUIRED",
                )
            ],
            evidence_class=self.evidence_class,
            checked_at=self.clock(),
        )
