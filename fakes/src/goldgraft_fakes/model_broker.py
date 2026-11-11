"""Deterministic scripted ModelPort; cannot contact a model SDK or incur spend."""

import json

from goldgraft_contracts.agent_runtime import (
    ModelTurnRequest,
    ModelTurnResult,
    ModelTurnStatus,
    ToolCall,
)
from goldgraft_contracts.plan5_common import Issue, content_digest

from .offline_store import encoded, fail


def unknown_issue():
    return Issue(
        code="SCRIPTED_UNKNOWN",
        input_ref=None,
        owner_role="offline-counterpart",
        recovery="reconcile",
        evidence_refs=[],
    )


class ScriptedModelBroker:
    def __init__(self, control, *, fault=None):
        self.control = control
        self.store = control.store
        self.fault = fault or (lambda boundary: None)

    def script(self, turn_id, value):
        with self.store.transaction() as db:
            db.execute("INSERT INTO scripts VALUES(?,?,?)", ("model", turn_id, encoded(value)))

    def _validate(self, db, request):
        task = self.control._active(db, request.task_id)
        context = db.execute(
            "SELECT body FROM contexts WHERE ref=?", (request.context_ref,)
        ).fetchone()
        if context is None or content_digest(json.loads(context["body"])) != request.context_digest:
            fail("DENIED context")
        ctx = json.loads(context["body"])
        ctx = ctx.get('task_context', ctx)
        if (request.generation, request.lease_epoch, ctx["lease_epoch"]) != (
            task.generation,
            task.lease_epoch,
            task.lease_epoch,
        ):
            fail("STALE")
        if ctx["task_ref"] != "fake:task:" + task.task.task_id:
            fail("DENIED")
        if (
            not set(request.allowed_tool_ids) <= set(task.task.allowed_tool_ids)
            or request.output_schema not in task.task.expected_schemas
            or request.model_profile_ref != "fake:scripted"
            or request.budget_reservation_ref != "fake:zero-budget"
            or request.deadline > task.deadline
            or request.deadline <= self.store.clock()
        ):
            fail("DENIED unqualified model/budget/scope")
        return task

    def turn(self, request):
        request = ModelTurnRequest.model_validate(request.model_dump(mode="json"))
        with self.store.transaction() as db:
            self._validate(db, request)
            fingerprint = content_digest(request)
            prior = db.execute(
                "SELECT * FROM model_turns WHERE id=?", (request.turn_id,)
            ).fetchone()
            if prior:
                if prior["fingerprint"] != fingerprint:
                    fail("CONFLICT")
                if prior["result"]:
                    return ModelTurnResult.model_validate_json(prior["result"])
                if prior["dispatch_count"]:
                    fail("UNKNOWN reconcile original turn")
            else:
                if db.execute(
                    "SELECT 1 FROM model_turns WHERE task_id=? "
                    "AND json_extract(status,'$.state') IN ('intended','submitted','unknown')",
                    (request.task_id,),
                ).fetchone():
                    fail("UNKNOWN original reservation retained")
                status = ModelTurnStatus(
                    turn_id=request.turn_id,
                    task_id=request.task_id,
                    state="intended",
                    result_ref=None,
                    usage_receipt_ref=None,
                    checked_at=self.store.clock(),
                    issue=None,
                )
                db.execute(
                    "INSERT INTO model_turns VALUES(?,?,?,?,?,?,0)",
                    (
                        request.turn_id,
                        fingerprint,
                        request.task_id,
                        encoded(request),
                        None,
                        encoded(status),
                    ),
                )
        self.fault("model_intent_committed")
        with self.store.transaction() as db:
            self._validate(db, request)
            prior = db.execute(
                "SELECT * FROM model_turns WHERE id=?", (request.turn_id,)
            ).fetchone()
            if prior["dispatch_count"]:
                fail("UNKNOWN")
            status = ModelTurnStatus(
                turn_id=request.turn_id,
                task_id=request.task_id,
                state="submitted",
                result_ref=None,
                usage_receipt_ref="fake:reserved-zero:" + request.turn_id,
                checked_at=self.store.clock(),
                issue=None,
            )
            db.execute(
                "UPDATE model_turns SET status=?,dispatch_count=1 WHERE id=?",
                (encoded(status), request.turn_id),
            )
        self.fault("model_dispatch_committed")
        with self.store.transaction() as db:
            self._validate(db, request)
            row = db.execute(
                "SELECT body FROM scripts WHERE namespace=? AND id=?", ("model", request.turn_id)
            ).fetchone()
            script = json.loads(row["body"]) if row else {"unknown": True}
            if script.get("unknown"):
                status = status.model_copy(update={"state": "unknown", "issue": unknown_issue()})
                db.execute(
                    "UPDATE model_turns SET status=? WHERE id=?", (encoded(status), request.turn_id)
                )
                result = None
            else:
                calls, final_ref, issue = [], None, None
                kind = script["kind"]
                if kind == "final":
                    final_ref = self.store.blob(db, request.task_id, script["payload"])
                elif kind == "tool_calls":
                    for index, call in enumerate(script["calls"]):
                        ref = self.store.blob(db, request.task_id, call["arguments"])
                        calls.append(
                            ToolCall(
                                call_id=f"call-{index}",
                                tool=call["tool"],
                                arguments_ref=ref,
                                arguments_digest=content_digest(call["arguments"]),
                            )
                        )
                elif kind == "blocked":
                    issue = Issue.model_validate(script["issue"])
                result = ModelTurnResult(
                    turn_id=request.turn_id,
                    task_id=request.task_id,
                    kind=kind,
                    calls=calls,
                    final_artifact_ref=final_ref,
                    issue=issue,
                    usage_receipt_ref="fake:zero-usage:" + request.turn_id,
                    provider_receipt_ref=None,
                )
                result_ref = self.store.blob(db, request.task_id, result.model_dump(mode="json"))
                status = status.model_copy(
                    update={
                        "state": "observed",
                        "result_ref": result_ref,
                        "usage_receipt_ref": result.usage_receipt_ref,
                    }
                )
                db.execute(
                    "UPDATE model_turns SET result=?,status=? WHERE id=?",
                    (encoded(result), encoded(status), request.turn_id),
                )
        if result is None:
            fail("UNKNOWN")
        return result

    def reconcile(self, turn_id):
        with self.store.transaction() as db:
            row = db.execute("SELECT status FROM model_turns WHERE id=?", (turn_id,)).fetchone()
            if row is None:
                fail("NOT_FOUND")
            return ModelTurnStatus.model_validate_json(row["status"])

    def dispatch_count(self, turn_id):
        with self.store.transaction() as db:
            row = db.execute(
                "SELECT dispatch_count FROM model_turns WHERE id=?", (turn_id,)
            ).fetchone()
            return row[0] if row else 0
