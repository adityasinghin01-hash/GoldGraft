"""Offline-testable durable acceptance/outbox, cancellation and worker fencing.

Host adapters supply CURRENT readiness and authenticate supervisor observations.
There is no default readiness, allocator, supervisor or termination verifier.
This component commits intent; it never provisions or executes a guest.
"""

from datetime import timedelta
from uuid import uuid4

from goldgraft_contracts.connection_control import (
    ActionIntent,
    ActionStatusView,
    CaseEvent,
    CollectorAcceptance,
    ConnectionReadiness,
    WorkAcceptance,
    WorkCancellation,
    WorkerOperation,
    WorkStatus,
)
from goldgraft_contracts.plan5_common import content_digest
from sqlalchemy import Column, Integer, MetaData, String, Table, Text, select

from .service import PRODUCER, ServiceError

metadata = MetaData()
intents = Table(
    "gu_work_intents",
    metadata,
    Column("action_id", String, primary_key=True),
    Column("case_id", String, nullable=False),
    Column("actor_id", String, nullable=False),
    Column("request_key", String, nullable=False),
    Column("request_digest", String, nullable=False),
    Column("body", Text, nullable=False),
    Column("readiness", Text, nullable=False),
)
work = Table(
    "gu_work",
    metadata,
    Column("work_id", String, primary_key=True),
    Column("action_id", String, nullable=False, unique=True),
    Column("case_id", String, nullable=False),
    Column("request_digest", String, nullable=False),
    Column("acceptance", Text, nullable=False),
    Column("state", String, nullable=False),
    Column("generation", Integer, nullable=False),
    Column("lease_until", String),
    Column("worker_id", String),
    Column("assignment_digest", String),
    Column("operation_digest", String),
    Column("evidence", Text, nullable=False, default="[]"),
)
cancellations = Table(
    "gu_work_cancellations",
    metadata,
    Column("action_id", String, primary_key=True),
    Column("body", Text, nullable=False),
)


class WorkControl:
    """Ledger and coordination rows share the same real database transaction."""

    def __init__(
        self,
        cases,
        *,
        readiness_resolver,
        required_checks,
        authenticate_operation=None,
        authenticate_termination=None,
    ):
        if not required_checks or not callable(readiness_resolver):
            raise ValueError("Current readiness resolver and required check inventory required")
        self.cases, self.ledger, self.clock = cases, cases.ledger, cases.clock
        self.resolve_readiness = readiness_resolver
        self.required_checks = frozenset(required_checks)
        self.authenticate_operation = authenticate_operation
        self.authenticate_termination = authenticate_termination
        metadata.create_all(self.ledger.engine)

    def _readiness(self, case_id, actor_id):
        try:
            value = self.resolve_readiness(case_id, actor_id)
            value = ConnectionReadiness.model_validate(value.model_dump(mode="json"))
        except Exception:
            raise ServiceError("READINESS_UNAVAILABLE", 503) from None
        now = self.clock()
        checks = {c.check_id: c for c in value.checks}
        if (
            value.case_id != case_id
            or value.actor_id != actor_id
            or not value.issued_at <= now < value.expires_at
            or not self.required_checks <= checks.keys()
            or any(
                c.status != "pass"
                or c.checked_at > now
                or c.expires_at is None
                or c.expires_at <= now
                for c in value.checks
            )
            or not value.binding_epochs
            or not value.source_snapshot_refs
        ):
            raise ServiceError("READINESS_STALE")
        return value

    def _append(self, tx, record):
        entry = tx.append(
            "ARTIFACT",
            PRODUCER,
            type(record).__name__ + "/1",
            payload=record.model_dump(mode="json"),
        )
        events = [r for r in tx.read() if r.schema_ == "CaseEvent/1"]
        version = self.ledger.payload(events[-1])["state_version"] + 1 if events else 1
        event = CaseEvent(
            event_id="event-" + uuid4().hex,
            case_id=tx.graft_id,
            sequence=len(events) + 1,
            state_version=version,
            kind="work_changed",
            payload_ref="ledger:" + entry.entry_hash,
            payload_digest=entry.payload_hash,
            occurred_at=self.clock(),
        )
        tx.append("ARTIFACT", PRODUCER, "CaseEvent/1", payload=event.model_dump(mode="json"))
        return entry

    def _intent(self, tx, case_id, action_id):
        row = (
            tx.conn.execute(
                select(intents).where(
                    intents.c.case_id == case_id, intents.c.action_id == action_id
                )
            )
            .mappings()
            .first()
        )
        if row is None:
            raise ServiceError("ACTION_UNAVAILABLE", 404)
        return row

    def create_intent(self, principal, case_id, body, key):
        self.cases.get_case(principal, case_id)
        with self.ledger.transaction(case_id) as tx:
            previous = (
                tx.conn.execute(
                    select(intents).where(
                        intents.c.case_id == case_id,
                        intents.c.actor_id == principal.actor_id,
                        intents.c.request_key == key,
                    )
                )
                .mappings()
                .first()
            )
            if previous:
                if previous["request_digest"] != content_digest(body):
                    raise ServiceError("IDEMPOTENCY_CONFLICT")
                return ActionIntent.model_validate_json(previous["body"])
            ready = self._readiness(case_id, principal.actor_id)
            if (body.readiness_id, body.readiness_digest) != (
                ready.readiness_id,
                ready.readiness_digest,
            ):
                raise ServiceError("READINESS_STALE")
            result = ActionIntent(
                action_id="action-" + uuid4().hex,
                case_id=case_id,
                actor_id=principal.actor_id,
                readiness_id=ready.readiness_id,
                readiness_digest=ready.readiness_digest,
                created_at=self.clock(),
                expires_at=min(ready.expires_at, self.clock() + timedelta(minutes=5)),
            )
            self._append(tx, result)
            tx.conn.execute(
                intents.insert().values(
                    action_id=result.action_id,
                    case_id=case_id,
                    actor_id=principal.actor_id,
                    request_key=key,
                    request_digest=content_digest(body),
                    body=result.model_dump_json(),
                    readiness=ready.model_dump_json(),
                )
            )
            return result

    def start(self, principal, case_id, body, key):
        self.cases.get_case(principal, case_id)
        fingerprint = content_digest({"key": key, "body": body.model_dump(mode="json")})
        with self.ledger.transaction(case_id) as tx:
            intent = self._intent(tx, case_id, body.action_id)
            if intent["actor_id"] != principal.actor_id:
                raise ServiceError("ACTION_UNAVAILABLE", 404)
            existing = (
                tx.conn.execute(select(work).where(work.c.action_id == body.action_id))
                .mappings()
                .first()
            )
            if existing:
                if existing["request_digest"] != fingerprint:
                    raise ServiceError("IDEMPOTENCY_CONFLICT")
                return WorkAcceptance.model_validate_json(existing["acceptance"])
            if tx.conn.execute(
                select(cancellations).where(cancellations.c.action_id == body.action_id)
            ).first():
                raise ServiceError("ACTION_CANCELLED")
            action = ActionIntent.model_validate_json(intent["body"])
            ready = self._readiness(case_id, principal.actor_id)
            stored = ConnectionReadiness.model_validate_json(intent["readiness"])
            if (
                action.expires_at <= self.clock()
                or ready != stored
                or (body.readiness_id, body.readiness_digest)
                != (action.readiness_id, action.readiness_digest)
            ):
                raise ServiceError("READINESS_STALE")
            if tx.conn.execute(
                select(work.c.work_id).where(
                    work.c.case_id == case_id,
                    work.c.state.not_in(["cancelled", "stopped", "failed"]),
                )
            ).first():
                raise ServiceError("ACTIVE_WORK_CONFLICT")
            result = WorkAcceptance(
                action_id=action.action_id,
                case_id=case_id,
                work_id="work-" + uuid4().hex,
                accepted_at=self.clock(),
                readiness_digest=ready.readiness_digest,
                work_package_digest=ready.work_package_digest,
                resource_graph_digest=ready.resource_graph_digest,
                scope_digest=ready.scope_digest,
                source_manifest_digest=ready.source_manifest_digest,
                receipt_ref="acceptance:" + action.action_id,
            )
            self._append(tx, result)
            # The queued row IS the durable outbox; claiming never removes it.
            tx.conn.execute(
                work.insert().values(
                    work_id=result.work_id,
                    action_id=action.action_id,
                    case_id=case_id,
                    request_digest=fingerprint,
                    acceptance=result.model_dump_json(),
                    state="queued",
                    generation=1,
                    evidence="[]",
                )
            )
            return result

    def status(self, principal, case_id, action_id):
        import json

        self.cases.get_case(principal, case_id)
        with self.ledger.transaction(case_id) as tx:
            self._intent(tx, case_id, action_id)
            row = (
                tx.conn.execute(select(work).where(work.c.action_id == action_id))
                .mappings()
                .first()
            )
            cancel = tx.conn.execute(
                select(cancellations).where(cancellations.c.action_id == action_id)
            ).first()
            status = WorkStatus(
                case_id=case_id,
                action_id=action_id,
                work_id=row["work_id"] if row else None,
                state=row["state"] if row else ("cancelled" if cancel else "submitting"),
                generation=row["generation"] if row else None,
                last_event_seq=sum(r.schema_ == "CaseEvent/1" for r in tx.read()),
                checked_at=self.clock(),
                evidence_refs=json.loads(row["evidence"]) if row else [],
            )
            return ActionStatusView(
                status=status, acceptance_ref="acceptance:" + action_id if row else None
            )

    def cancel(self, principal, case_id, action_id, cancel_id):
        self.cases.get_case(principal, case_id)
        with self.ledger.transaction(case_id) as tx:
            self._intent(tx, case_id, action_id)
            prior = tx.conn.execute(
                select(cancellations.c.body).where(cancellations.c.action_id == action_id)
            ).scalar_one_or_none()
            if prior:
                return WorkCancellation.model_validate_json(prior)
            row = (
                tx.conn.execute(select(work).where(work.c.action_id == action_id))
                .mappings()
                .first()
            )
            result = WorkCancellation(
                cancel_id=cancel_id,
                case_id=case_id,
                action_id=action_id,
                requested_by=principal.actor_id,
                requested_at=self.clock(),
                state="termination_pending" if row else "confirmed",
                work_id=row["work_id"] if row else None,
                generation=row["generation"] + 1 if row else None,
                termination_evidence_refs=[],
            )
            self._append(tx, result)
            tx.conn.execute(
                cancellations.insert().values(action_id=action_id, body=result.model_dump_json())
            )
            if row:
                tx.conn.execute(
                    work.update()
                    .where(work.c.work_id == row["work_id"])
                    .values(
                        state="cancellation_pending", generation=result.generation, lease_until=None
                    )
                )
            return result

    def _worker(self, tx, work_id):
        row = tx.conn.execute(select(work).where(work.c.work_id == work_id)).mappings().first()
        if row is None:
            raise ServiceError("WORK_UNAVAILABLE", 404)
        return row

    def claim(self, case_id, work_id, *, worker_id, assignment_digest, lease_seconds=60):
        """Trusted allocator only; expiry holds for reconciliation without redispatch."""
        if type(lease_seconds) is not int or lease_seconds <= 0:
            raise ServiceError("INVALID_LEASE")
        from goldgraft_contracts.plan5_common import Digest, Id
        from pydantic import TypeAdapter

        TypeAdapter(Digest).validate_python(assignment_digest)
        TypeAdapter(Id).validate_python(worker_id)
        with self.ledger.transaction(case_id) as tx:
            row = self._worker(tx, work_id)
            if row["case_id"] != case_id or row["state"] != "queued":
                raise ServiceError("WORK_NOT_QUEUED")
            intent = self._intent(tx, case_id, row["action_id"])
            if self._readiness(case_id, intent["actor_id"]) != (
                ConnectionReadiness.model_validate_json(intent["readiness"])
            ):
                raise ServiceError("READINESS_STALE")
            tx.conn.execute(
                work.update()
                .where(work.c.work_id == work_id)
                .values(
                    state="provisioning",
                    worker_id=worker_id,
                    assignment_digest=assignment_digest,
                    lease_until=(self.clock() + timedelta(seconds=lease_seconds)).isoformat(),
                )
            )
            self._append(
                tx,
                WorkStatus(
                    action_id=row["action_id"],
                    case_id=case_id,
                    work_id=work_id,
                    state="provisioning",
                    generation=row["generation"],
                    last_event_seq=sum(r.schema_ == "CaseEvent/1" for r in tx.read()),
                    checked_at=self.clock(),
                    evidence_refs=[],
                ),
            )
            return row["generation"]

    def operation(self, principal, value: WorkerOperation):
        """Authenticates the actual supervisor, assignment, manifest and current lease."""
        self.cases.check_principal(principal)
        if principal.kind != "service" or self.authenticate_operation is None:
            raise ServiceError("SUPERVISOR_AUTHORITY_REQUIRED", 403)
        value = WorkerOperation.model_validate(value.model_dump(mode="json"))
        with self.ledger.engine.connect() as db:
            row = db.execute(select(work).where(work.c.work_id == value.work_id)).mappings().first()
        if row is None:
            raise ServiceError("WORK_UNAVAILABLE", 404)
        with self.ledger.transaction(row["case_id"]) as tx:
            row = self._worker(tx, value.work_id)
            intent = self._intent(tx, row["case_id"], row["action_id"])
            from .service import cases

            tenant = tx.conn.execute(
                select(cases.c.tenant_id).where(cases.c.case_id == row["case_id"])
            ).scalar_one()
            if principal.tenant_id != tenant:
                raise ServiceError("WORK_UNAVAILABLE", 404)
            ready = self._readiness(row["case_id"], intent["actor_id"])
            if ready != ConnectionReadiness.model_validate_json(intent["readiness"]):
                raise ServiceError("READINESS_STALE")
            from datetime import datetime

            if (
                row["state"] not in {"provisioning", "operation_started"}
                or row["generation"] != value.generation
                or row["worker_id"] != value.worker_id
                or row["assignment_digest"] != value.assignment_digest
                or not row["lease_until"]
                or datetime.fromisoformat(row["lease_until"]) <= self.clock()
                or value.finished_at > self.clock()
                or value.started_at
                < WorkAcceptance.model_validate_json(row["acceptance"]).accepted_at
                or any(
                    getattr(value, name) != getattr(ready, name)
                    for name in (
                        "work_package_digest",
                        "resource_graph_digest",
                        "source_manifest_digest",
                        "scope_digest",
                        "runtime_profile_digest",
                    )
                )
            ):
                raise ServiceError("STALE_WORKER")
            try:
                authenticated = self.authenticate_operation(principal, value) is True
            except Exception:
                authenticated = False
            if not authenticated:
                raise ServiceError("OPERATION_UNAUTHENTICATED", 403)
            digest = content_digest(value)
            if row["operation_digest"] and row["operation_digest"] != digest:
                raise ServiceError("OPERATION_CONFLICT")
            if row["operation_digest"]:
                for entry in tx.read():
                    if entry.schema_ == "CollectorAcceptance/1":
                        recorded = CollectorAcceptance.model_validate(self.ledger.payload(entry))
                        if recorded.operation_id == value.operation_id:
                            return recorded
                raise ServiceError("INTEGRITY_FAILURE", 503)
            receipt = CollectorAcceptance(
                operation_id=value.operation_id,
                work_id=value.work_id,
                generation=value.generation,
                accepted_at=self.clock(),
                receipt_ref="operation:" + value.operation_id,
            )
            if not row["operation_digest"]:
                import json

                self._append(tx, value)
                self._append(tx, receipt)
                tx.conn.execute(
                    work.update()
                    .where(work.c.work_id == value.work_id)
                    .values(
                        state="operation_started" if value.result == "verified" else "held",
                        operation_digest=digest,
                        evidence=json.dumps(value.evidence_refs),
                    )
                )
            return receipt

    def confirm_termination(self, case_id, action_id, evidence_refs):
        """Internal trusted observer; timeout/acknowledged request is not termination."""
        import json

        if not evidence_refs or self.authenticate_termination is None:
            raise ServiceError("TERMINATION_UNVERIFIED")
        with self.ledger.transaction(case_id) as tx:
            raw = tx.conn.execute(
                select(cancellations.c.body).where(cancellations.c.action_id == action_id)
            ).scalar_one_or_none()
            if raw is None:
                raise ServiceError("CANCELLATION_UNAVAILABLE", 404)
            result = WorkCancellation.model_validate_json(raw)
            if result.case_id != case_id or not result.work_id:
                raise ServiceError("CANCELLATION_UNAVAILABLE", 404)
            try:
                verified = self.authenticate_termination(result, evidence_refs) is True
            except Exception:
                verified = False
            if not verified:
                raise ServiceError("TERMINATION_UNVERIFIED")
            if result.state == "confirmed":
                return result
            result = WorkCancellation.model_validate(
                {
                    **result.model_dump(),
                    "state": "confirmed",
                    "termination_evidence_refs": evidence_refs,
                }
            )
            self._append(tx, result)
            tx.conn.execute(
                cancellations.update()
                .where(cancellations.c.action_id == action_id)
                .values(body=result.model_dump_json())
            )
            tx.conn.execute(
                work.update()
                .where(work.c.action_id == action_id)
                .values(state="stopped", evidence=json.dumps(evidence_refs))
            )
            return result
