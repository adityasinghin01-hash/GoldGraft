"""Durable draft claims require verified identity AND a separate bounded capability."""

import hashlib
from datetime import timedelta
from secrets import compare_digest, token_bytes
from uuid import uuid4

from goldgraft_contracts.connection_control import ClaimDraft, CreateDraft, DraftCase
from goldgraft_contracts.plan5_common import Id, content_digest, reject_secret
from goldgraft_contracts.plan5_validation import validate_draft_claim
from goldgraft_foundation.ledger import LedgerTransaction
from pydantic import TypeAdapter, ValidationError
from sqlalchemy import Column, MetaData, String, Table, select

from .service import PRODUCER, ServiceError, requests

metadata = MetaData()
drafts = Table(
    "case_service_drafts",
    metadata,
    Column("draft_id", String, primary_key=True),
    Column("creator_actor", String, nullable=False),
    Column("creator_tenant", String, nullable=False),
    Column("creator_kind", String, nullable=False),
    Column("capability_digest", String, nullable=False),
    Column("claimed_actor", String),
    Column("claimed_tenant", String),
    Column("case_id", String),
)


class DraftService:
    def __init__(self, service):
        self.service = service
        self.ledger = service.ledger
        metadata.create_all(self.ledger.engine)

    @staticmethod
    def _request(principal, operation, body, key):
        TypeAdapter(Id).validate_python(key)
        reject_secret(key)
        namespace = (
            operation
            + ":"
            + content_digest({"tenant": principal.tenant_id, "actor": principal.actor_id})
        )
        return (
            namespace,
            content_digest(body),
            content_digest(
                {"namespace": namespace, "key": key, "request": body.model_dump(mode="json")}
            ),
        )

    def _verified(self, draft_id, capability_digest):
        if not self.ledger.verify_chain(draft_id).ok:
            raise ServiceError("INTEGRITY_FAILURE", 503)
        entries = [r for r in self.ledger.read(draft_id) if r.schema_ == "DraftCase/1"]
        if not entries or capability_digest not in entries[0].inputs:
            raise ServiceError("INTEGRITY_FAILURE", 503)
        draft = DraftCase.model_validate(self.ledger.payload(entries[-1]))
        if draft.draft_id != draft_id:
            raise ServiceError("INTEGRITY_FAILURE", 503)
        return draft, entries

    def create(self, principal, body, key):
        self.service.check_principal(principal)
        if principal.kind not in {"draft", "session"}:
            raise ServiceError("SESSION_REQUIRED", 403)
        body = CreateDraft.model_validate(body.model_dump(mode="json"))
        try:
            reject_secret(body.shop_url)
        except ValueError:
            raise ServiceError("INVALID_BODY", 422) from None
        namespace, fingerprint, request_digest = self._request(principal, "draft-create", body, key)
        with self.ledger.transaction(namespace) as transaction:
            prior = (
                transaction.conn.execute(
                    select(requests).where(
                        requests.c.namespace == namespace,
                        requests.c.key == key,
                    )
                )
                .mappings()
                .first()
            )
            if prior:
                if prior["fingerprint"] != fingerprint:
                    raise ServiceError("IDEMPOTENCY_CONFLICT")
                try:
                    original = DraftCase.model_validate_json(prior["response"])
                except ValidationError:
                    raise ServiceError("INTEGRITY_FAILURE", 503) from None
                row = (
                    transaction.conn.execute(
                        select(drafts).where(
                            drafts.c.draft_id == original.draft_id,
                            drafts.c.creator_actor == principal.actor_id,
                            drafts.c.creator_tenant == principal.tenant_id,
                        )
                    )
                    .mappings()
                    .first()
                )
                if row is None:
                    raise ServiceError("INTEGRITY_FAILURE", 503)
                _, entries = self._verified(original.draft_id, row["capability_digest"])
                if entries[0].inputs != [
                    request_digest,
                    row["capability_digest"],
                ] or self.ledger.payload(entries[0]) != original.model_dump(mode="json"):
                    raise ServiceError("INTEGRITY_FAILURE", 503)
                # Never persist/recover raw capability bytes from a database or log.
                # A retry preserves the original HTTP-only cookie if it was received.
                return original, None
            capability = token_bytes(32)
            capability_digest = hashlib.sha256(capability).hexdigest()
            draft = DraftCase(
                draft_id="draft-" + uuid4().hex,
                shop_url=body.shop_url,
                created_at=self.service.clock(),
                expires_at=self.service.clock() + timedelta(minutes=30),
                continuation_ref="draft-continuation:" + uuid4().hex,
                state="unclaimed",
            )
            draft_tx = LedgerTransaction(self.ledger, transaction.conn, draft.draft_id)
            draft_tx.append(
                "ARTIFACT",
                PRODUCER,
                "DraftCase/1",
                payload=draft.model_dump(mode="json"),
                inputs=[request_digest, capability_digest],
            )
            transaction.conn.execute(
                drafts.insert().values(
                    draft_id=draft.draft_id,
                    creator_actor=principal.actor_id,
                    creator_tenant=principal.tenant_id,
                    creator_kind=principal.kind,
                    capability_digest=capability_digest,
                )
            )
            transaction.conn.execute(
                requests.insert().values(
                    namespace=namespace,
                    key=key,
                    fingerprint=fingerprint,
                    response=draft.model_dump_json(),
                )
            )
            return draft, capability

    def claim(self, principal, draft_id, body, key, capability):
        self.service.check_principal(principal)
        if principal.kind != "session":
            raise ServiceError("SESSION_REQUIRED", 403)
        if type(capability) is not bytes or len(capability) != 32:
            raise ServiceError("DRAFT_CAPABILITY_REQUIRED", 403)
        body = ClaimDraft.model_validate(body.model_dump(mode="json"))
        namespace, fingerprint, _ = self._request(principal, "draft-claim-" + draft_id, body, key)
        with self.ledger.transaction(draft_id) as transaction:
            row = (
                transaction.conn.execute(
                    select(drafts).where(
                        drafts.c.draft_id == draft_id,
                    )
                )
                .mappings()
                .first()
            )
            if row is None or not compare_digest(
                hashlib.sha256(capability).hexdigest(), row["capability_digest"]
            ):
                raise ServiceError("DRAFT_CAPABILITY_REQUIRED", 403)
            draft, entries = self._verified(draft_id, row["capability_digest"])
            original_actor = row["claimed_actor"] or (
                row["creator_actor"] if row["creator_kind"] == "session" else None
            )
            expected_tenant = row["claimed_tenant"] or (
                row["creator_tenant"] if row["creator_kind"] == "session" else None
            )
            if expected_tenant is not None and expected_tenant != principal.tenant_id:
                raise ServiceError("DRAFT_CAPABILITY_REQUIRED", 403)
            try:
                validate_draft_claim(
                    draft=draft,
                    principal_id=principal.actor_id,
                    capability=capability,
                    expected_capability_digest=row["capability_digest"],
                    continuation_ref=body.continuation_ref,
                    now=self.service.clock(),
                    original_requester=original_actor,
                )
            except ValueError:
                raise ServiceError("DRAFT_CAPABILITY_REQUIRED", 403) from None
            prior = (
                transaction.conn.execute(
                    select(requests).where(
                        requests.c.namespace == namespace,
                        requests.c.key == key,
                    )
                )
                .mappings()
                .first()
            )
            if prior and prior["fingerprint"] != fingerprint:
                raise ServiceError("IDEMPOTENCY_CONFLICT")
            if draft.state == "claimed":
                expected = content_digest(
                    {
                        "draft": draft_id,
                        "case": row["case_id"],
                        "actor": principal.actor_id,
                        "tenant": principal.tenant_id,
                    }
                )
                if entries[-1].inputs != [expected] or row["case_id"] is None:
                    raise ServiceError("INTEGRITY_FAILURE", 503)
                return self.service.get_case(principal, row["case_id"])
            if row["case_id"] is not None or row["claimed_actor"] is not None:
                raise ServiceError("INTEGRITY_FAILURE", 503)
            request_digest = content_digest(
                {
                    "draft": draft_id,
                    "actor": principal.actor_id,
                    "tenant": principal.tenant_id,
                    "continuation": body.continuation_ref,
                }
            )
            case = self.service._write_case(
                transaction.conn, principal, draft.shop_url, request_digest
            )
            claimed = draft.model_copy(update={"state": "claimed"})
            link_digest = content_digest(
                {
                    "draft": draft_id,
                    "case": case.case_id,
                    "actor": principal.actor_id,
                    "tenant": principal.tenant_id,
                }
            )
            transaction.append(
                "ARTIFACT",
                PRODUCER,
                "DraftCase/1",
                payload=claimed.model_dump(mode="json"),
                inputs=[link_digest],
            )
            transaction.conn.execute(
                drafts.update()
                .where(drafts.c.draft_id == draft_id)
                .values(
                    claimed_actor=principal.actor_id,
                    claimed_tenant=principal.tenant_id,
                    case_id=case.case_id,
                )
            )
            transaction.conn.execute(
                requests.insert().values(
                    namespace=namespace,
                    key=key,
                    fingerprint=fingerprint,
                    response=case.model_dump_json(),
                )
            )
            return case
