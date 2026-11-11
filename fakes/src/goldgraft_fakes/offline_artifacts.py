"""Synthetic scoped bytes and proposal staging; no secret/provider storage."""

import hashlib
import json

from goldgraft_contracts.agent_runtime import ArtifactDescriptor, TaskContext
from goldgraft_contracts.plan5_common import content_digest
from goldgraft_contracts.registry import validate

from .offline_store import encoded, fail


class OfflineArtifacts:
    def __init__(self, control):
        self.control = control
        self.store = control.store

    def _put(self, db, task, schema, payload, subject, trust="model_proposal"):
        validate(schema, payload, context=self.control.output_context(db, task))
        data = encoded(payload).encode()
        ref = "fake:artifact:" + content_digest(
            {"task": task.task.task_id, "schema": schema, "payload": payload, "subject": subject}
        )
        d = ArtifactDescriptor(
            ref=ref,
            case_id=task.case_id,
            run_id=task.run_id,
            generation=task.generation,
            schema=schema,
            payload_digest=hashlib.sha256(data).hexdigest(),
            byte_count=len(data),
            subject_digest=subject,
            input_digest=task.input_digest,
            derivation_ref=None,
            producer_identity_ref="fake:role:" + task.task.role.replace(" ", "_"),
            trust=trust,
            evidence_class="scripted",
            created_at=self.store.clock(),
            expires_at=None,
        )
        db.execute("INSERT OR IGNORE INTO artifacts VALUES(?,?,?)", (ref, encoded(d), data))
        return ref

    def fixture_output(self, lease, schema, payload):
        with self.store.transaction() as db:
            task = self.control._lease(db, lease)
            if schema not in task.task.expected_schemas:
                fail("DENIED")
            return self._put(db, task, schema, payload, task.task.expected_subject)

    def stage(self, task_id, schema, payload_ref, subject):
        with self.store.transaction() as db:
            task = self.control._active(db, task_id)
            row = db.execute("SELECT * FROM blobs WHERE ref=?", (payload_ref,)).fetchone()
            if row is None or row["scope"] != task_id or schema not in task.task.expected_schemas:
                fail("DENIED")
            if (
                subject != task.task.expected_subject
                or task.task.output_subject_policy != "same_subject"
            ):
                fail("UNSUPPORTED transform requires collector lineage")
            return self._put(db, task, schema, json.loads(row["body"]), subject)

    def resolve(self, ref, task_context):
        with self.store.transaction() as db:
            ctx = db.execute("SELECT body FROM contexts WHERE ref=?", (task_context,)).fetchone()
            row = db.execute("SELECT * FROM artifacts WHERE ref=?", (ref,)).fetchone()
            if ctx is None or row is None:
                fail("DENIED")
            ctx = TaskContext.model_validate_json(ctx["body"])
            task = self.control._active(db, ctx.task_ref.removeprefix("fake:task:"))
            d = ArtifactDescriptor.model_validate_json(row["descriptor"])
            if ctx.lease_epoch != task.lease_epoch or (d.case_id, d.run_id, d.generation) != (
                ctx.case_id,
                ctx.run_id,
                ctx.generation,
            ):
                fail("DENIED")
            if (
                len(row["payload"]) != d.byte_count
                or hashlib.sha256(row["payload"]).hexdigest() != d.payload_digest
            ):
                fail("INVALID bytes")
            return d
