"""Scoped scripted ToolPort; no shell, HTTP, source execution or payment client."""

import hashlib
import json

from goldgraft_contracts.agent_runtime import ToolInvocation
from goldgraft_contracts.plan5_common import content_digest, reject_secret
from goldgraft_contracts.plan5_tools import validate_tool_arguments

from .model_broker import unknown_issue
from .offline_store import LABEL, encoded, fail


class GuardedOfflineTools:
    def __init__(self, control, *, fault=None):
        self.control = control
        self.store = control.store
        self.fault = fault or (lambda boundary: None)

    def script(self, invocation_id, value):
        with self.store.transaction() as db:
            db.execute("INSERT INTO scripts VALUES(?,?,?)", ("tool", invocation_id, encoded(value)))

    def _validate(self, db, invocation):
        task = self.control._active(db, invocation.task_id)
        self.control.check_invocation(task, invocation)
        row = db.execute(
            "SELECT * FROM invocations WHERE id=?", (invocation.invocation_id,)
        ).fetchone()
        if row is None:
            fail("MISSING_EVIDENCE intent not persisted")
        if row["fingerprint"] != content_digest(invocation):
            fail("CONFLICT")
        if (
            invocation.capability_ref != "fake:capability:" + invocation.task_id
            or invocation.budget_reservation_ref != "fake:zero-budget"
            or invocation.deadline <= self.store.clock()
            or invocation.deadline > task.deadline
        ):
            fail("DENIED")
        args = db.execute("SELECT * FROM blobs WHERE ref=?", (invocation.arguments_ref,)).fetchone()
        if (
            args is None
            or args["scope"] != invocation.task_id
            or hashlib.sha256(args["body"]).hexdigest() != invocation.arguments_digest
        ):
            fail("DENIED arguments binding")
        return validate_tool_arguments(task.task.role, invocation.tool_id, json.loads(args["body"]))

    def invoke(self, invocation):
        invocation = ToolInvocation.model_validate(invocation.model_dump(mode="json"))
        with self.store.transaction() as db:
            arguments = self._validate(db, invocation)
            row = db.execute(
                "SELECT * FROM tools WHERE id=?", (invocation.invocation_id,)
            ).fetchone()
            if row:
                if row["fingerprint"] != content_digest(invocation):
                    fail("CONFLICT")
                return ToolInvocation.model_validate_json(row["body"])
            if db.execute(
                "SELECT 1 FROM tools WHERE task_id=? "
                "AND json_extract(body,'$.state') IN ('submitted','unknown')",
                (invocation.task_id,),
            ).fetchone():
                fail("UNKNOWN")
            value = invocation.model_copy(update={"state": "submitted"})
            db.execute(
                "INSERT INTO tools VALUES(?,?,?,?,1)",
                (
                    invocation.invocation_id,
                    content_digest(invocation),
                    invocation.task_id,
                    encoded(value),
                ),
            )
            db.execute(
                "UPDATE invocations SET body=? WHERE id=?",
                (encoded(value), invocation.invocation_id),
            )
        self.fault("tool_dispatch_committed")
        with self.store.transaction() as db:
            arguments = self._validate(db, invocation)
            row = db.execute(
                "SELECT body FROM scripts WHERE namespace=? AND id=?",
                ("tool", invocation.invocation_id),
            ).fetchone()
            script = json.loads(row["body"]) if row else {"unknown": True}
            if script.get("unknown"):
                value = value.model_copy(update={"state": "unknown", "issue": unknown_issue()})
            else:
                data = script["payload"]

                def scan(value):
                    if isinstance(value, str):
                        reject_secret(value)
                    elif isinstance(value, dict):
                        for key, item in value.items():
                            reject_secret(key)
                            scan(item)
                    elif isinstance(value, list):
                        for item in value:
                            scan(item)

                scan(data)
                if isinstance(data, dict) and "excerpt" in data and hasattr(arguments, "max_bytes"):
                    if len(data["excerpt"].encode()) > arguments.max_bytes:
                        fail("INVALID oversized excerpt")
                if len(encoded(data).encode()) > 32768:
                    fail("INVALID oversized tool result")
                payload = {"label": LABEL, "evidence_class": "scripted", "value": script["payload"]}
                ref = self.store.blob(db, invocation.task_id, payload)
                value = value.model_copy(update={"state": "observed", "result_refs": [ref]})
            value = ToolInvocation.model_validate(value.model_dump(mode="json"))
            db.execute(
                "UPDATE tools SET body=? WHERE id=?", (encoded(value), invocation.invocation_id)
            )
            db.execute(
                "UPDATE invocations SET body=? WHERE id=?",
                (encoded(value), invocation.invocation_id),
            )
            return value

    def reconcile(self, invocation_id):
        with self.store.transaction() as db:
            row = db.execute("SELECT body FROM tools WHERE id=?", (invocation_id,)).fetchone()
            if row is None:
                fail("NOT_FOUND")
            return ToolInvocation.model_validate_json(row["body"])

    def dispatch_count(self, invocation_id):
        with self.store.transaction() as db:
            row = db.execute(
                "SELECT dispatch_count FROM tools WHERE id=?", (invocation_id,)
            ).fetchone()
            return row[0] if row else 0
