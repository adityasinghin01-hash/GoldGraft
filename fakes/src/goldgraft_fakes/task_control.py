"""SQLite TaskControl stand-in. Only labelled offline counterpart behavior."""

import json
from datetime import timedelta

from goldgraft_contracts.agent_runtime import (
    AgentResult,
    AgentTask,
    ArtifactDescriptor,
    PlanProposal,
    RunTaskSnapshot,
    TaskCheckpoint,
    TaskContext,
    TaskEvent,
    TaskLease,
    ToolInvocation,
    WakeCondition,
)
from goldgraft_contracts.plan5_common import content_digest
from goldgraft_contracts.plan5_validation import (
    ArtifactBinding,
    validate_artifact,
    validate_plan_admission,
)

from .offline_artifacts import OfflineArtifacts
from .offline_store import OfflineStore, encoded, fail


class OfflineTaskControl:
    def __init__(self, path, *, clock=None):
        self.store = OfflineStore(path, clock=clock)
        self.artifacts = OfflineArtifacts(self)
        self.role_configurations = {}
        self.output_context = lambda db, task: None
        self.output_subject = lambda db, task, descriptor: task.task.expected_subject

    def _run(self, db, ref):
        row = db.execute("SELECT * FROM runs WHERE ref=?", (ref,)).fetchone()
        if row is None:
            fail("NOT_FOUND")
        return json.loads(row["body"]), bool(row["authority"])

    def _snapshot(self, db, ref):
        run, _ = self._run(db, ref)
        tasks = [
            AgentTask.model_validate_json(r["body"])
            for r in db.execute("SELECT body FROM tasks WHERE run_ref=? ORDER BY rowid", (ref,))
        ]
        return RunTaskSnapshot(**run, tasks=tasks)

    def snapshot(self, run_ref):
        with self.store.transaction() as db:
            return self._snapshot(db, run_ref)

    def _save_task(self, db, task):
        db.execute("UPDATE tasks SET body=? WHERE id=?", (encoded(task), task.task.task_id))

    def _event(self, db, ref, kind, task_id=None):
        run, _ = self._run(db, ref)
        run["last_event_seq"] += 1
        run["state_version"] += 1
        payload = {"kind": kind, "task_id": task_id, "state_version": run["state_version"]}
        payload_ref = self.store.blob(db, ref, payload)
        event_id = "fake:event:" + content_digest({"run": ref, "sequence": run["last_event_seq"]})
        event = TaskEvent(
            event_id=event_id,
            case_id=run["case_id"],
            run_id=run["run_id"],
            generation=run["generation"],
            task_id=task_id,
            sequence=run["last_event_seq"],
            kind=kind,
            payload_ref=payload_ref,
            payload_digest=content_digest(payload),
            causation_id=event_id,
            correlation_id=ref,
            occurred_at=self.store.clock(),
        )
        db.execute("UPDATE runs SET body=? WHERE ref=?", (encoded(run), ref))
        db.execute(
            "INSERT INTO outbox(id,run_ref,sequence,body) VALUES(?,?,?,?)",
            (event_id, ref, event.sequence, encoded(event)),
        )

    def seed(self, run_ref, proposal, key):
        return self._admit(run_ref, None, proposal, key)

    def extend(self, run_ref, expected_run_version, proposal, key):
        return self._admit(run_ref, expected_run_version, proposal, key)

    def _admit(self, ref, expected, proposal, key):
        proposal = PlanProposal.model_validate(proposal.model_dump(mode="json"))
        with self.store.transaction() as db:
            fingerprint = {
                "ref": ref,
                "expected": expected,
                "proposal": proposal.model_dump(mode="json"),
            }
            prior = self.store.key(db, "admit:" + ref, key, fingerprint)
            if prior is not None:
                return [AgentTask.model_validate(x) for x in prior]
            exists = db.execute("SELECT 1 FROM runs WHERE ref=?", (ref,)).fetchone()
            if not exists and db.execute("SELECT 1 FROM runs").fetchone():
                fail("UNSUPPORTED one synthetic run per offline database")
            old = self._snapshot(db, ref) if exists else None
            if exists and expected is None:
                fail("CONFLICT")
            if expected is not None and (old is None or old.state_version != expected):
                fail("STALE")
            if exists and not self._run(db, ref)[1]:
                fail("DENIED")
            validate_plan_admission(proposal, existing=old, required_task_ids=set())
            if not exists:
                run = dict(
                    case_id=proposal.case_id,
                    run_id=proposal.run_id,
                    generation=proposal.generation,
                    state_version=1,
                    last_event_seq=0,
                    cancellation_ref=None,
                )
                db.execute("INSERT INTO runs VALUES(?,?,1)", (ref, encoded(run)))
            done = {t.task.task_id for t in old.tasks if t.state == "succeeded"} if old else set()
            added = []
            now = self.store.clock()
            for spec in proposal.tasks:
                config = self.role_configurations.get(spec.role, {})
                if db.execute("SELECT 1 FROM tasks WHERE id=?", (spec.task_id,)).fetchone():
                    fail("CONFLICT globally unique synthetic task ID required")
                task = AgentTask(
                    task=spec,
                    case_id=proposal.case_id,
                    run_id=proposal.run_id,
                    generation=proposal.generation,
                    request_id="fake:request:" + spec.task_id,
                    input_digest=content_digest(spec.input_refs),
                    policy_ref=config.get("policy_ref", "fake:offline-policy"),
                    policy_digest=config.get("policy_digest", content_digest("offline-policy")),
                    prompt_ref=config.get("prompt_ref", "fake:no-agent-prompt"),
                    prompt_digest=config.get(
                        "prompt_digest", content_digest("scripted-counterpart-only")
                    ),
                    model_profile_ref=None,
                    state="ready" if set(spec.dependencies) <= done else "pending",
                    state_version=1,
                    attempt=1,
                    created_at=now,
                    deadline=now + timedelta(minutes=10),
                    next_wake_at=None,
                    wake_condition_ref=None,
                    lease_owner=None,
                    lease_epoch=0,
                    lease_until=None,
                    checkpoint_ref=None,
                    output_refs=[],
                    issue=None,
                )
                db.execute(
                    "INSERT INTO tasks VALUES(?,?,?,NULL)", (spec.task_id, ref, encoded(task))
                )
                self._event(
                    db, ref, "task_ready" if task.state == "ready" else "task_changed", spec.task_id
                )
                added.append(task)
            self.store.key(
                db, "admit:" + ref, key, fingerprint, [t.model_dump(mode="json") for t in added]
            )
            return added

    def _active(self, db, task_id):
        row = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            fail("NOT_FOUND")
        task = AgentTask.model_validate_json(row["body"])
        run, authority = self._run(db, row["run_ref"])
        if not authority:
            fail("DENIED")
        if run["cancellation_ref"] is not None:
            fail("CANCELLED")
        if task.generation != run["generation"] or task.state not in {"leased", "running"}:
            fail("STALE")
        if task.lease_until <= self.store.clock() or task.deadline <= self.store.clock():
            fail("STALE expired lease/deadline")
        return task

    def _lease(self, db, lease):
        task = self._active(db, lease.task_id)
        row = db.execute("SELECT claim_version FROM tasks WHERE id=?", (lease.task_id,)).fetchone()
        if (
            task.run_id,
            task.generation,
            task.lease_epoch,
            task.lease_owner,
            row["claim_version"],
        ) != (
            lease.run_id,
            lease.generation,
            lease.lease_epoch,
            lease.worker_id,
            lease.task_version,
        ):
            fail("STALE")
        return task

    def claim(self, worker_id, now):
        authoritative_now = self.store.clock()
        if abs((now - authoritative_now).total_seconds()) > 1:
            fail("INVALID authoritative clock mismatch")
        now = authoritative_now
        with self.store.transaction() as db:
            rows = list(db.execute("SELECT * FROM tasks ORDER BY rowid"))
            for row in rows:
                t = AgentTask.model_validate_json(row["body"])
                run, authority = self._run(db, row["run_ref"])
                if not authority or run["cancellation_ref"] or t.deadline <= now:
                    continue
                eligible = t.state == "ready" or (t.state == "retry_due" and t.next_wake_at <= now)
                eligible |= t.state in {"leased", "running"} and t.lease_until <= now
                if not eligible:
                    continue
                t = t.model_copy(
                    update=dict(
                        state="leased",
                        state_version=t.state_version + 1,
                        lease_owner=worker_id,
                        lease_epoch=t.lease_epoch + 1,
                        lease_until=min(now + timedelta(seconds=60), t.deadline),
                    )
                )
                context_ref = "fake:context:" + content_digest(
                    {"task": t.task.task_id, "epoch": t.lease_epoch}
                )
                ctx = TaskContext(
                    task_ref="fake:task:" + t.task.task_id,
                    case_id=t.case_id,
                    run_id=t.run_id,
                    generation=t.generation,
                    lease_epoch=t.lease_epoch,
                    role=t.task.role,
                    operation=t.task.operation,
                    input_refs=t.task.input_refs,
                    expected_subject=t.task.expected_subject,
                    policy_ref=t.policy_ref,
                    prompt_ref=t.prompt_ref,
                    allowed_tool_ids=t.task.allowed_tool_ids,
                    expected_schemas=t.task.expected_schemas,
                    budget_ref="fake:zero-budget",
                    deadline=t.deadline,
                    checkpoint_ref=t.checkpoint_ref,
                )
                db.execute("INSERT INTO contexts VALUES(?,?)", (context_ref, encoded(ctx)))
                self._save_task(db, t)
                db.execute(
                    "UPDATE tasks SET claim_version=? WHERE id=?", (t.state_version, t.task.task_id)
                )
                self._event(db, row["run_ref"], "task_changed", t.task.task_id)
                return TaskLease(
                    task_id=t.task.task_id,
                    run_id=t.run_id,
                    generation=t.generation,
                    worker_id=worker_id,
                    lease_epoch=t.lease_epoch,
                    task_version=t.state_version,
                    lease_until=t.lease_until,
                    context_ref=context_ref,
                )
            return None

    def load(self, lease):
        with self.store.transaction() as db:
            return self._lease(db, lease)

    def context(self, ref):
        with self.store.transaction() as db:
            row = db.execute("SELECT body FROM contexts WHERE ref=?", (ref,)).fetchone()
            if row is None:
                fail("NOT_FOUND")
            return json.loads(row["body"])

    def stage_untrusted(self, lease, value):
        with self.store.transaction() as db:
            task = self._lease(db, lease)
            return self.store.blob(db, task.task.task_id, value)

    def artifact_count(self):
        with self.store.transaction() as db:
            return db.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]

    def renew(self, lease, now):
        authoritative_now = self.store.clock()
        if abs((now - authoritative_now).total_seconds()) > 1:
            fail("INVALID clock")
        now = authoritative_now
        with self.store.transaction() as db:
            t = self._lease(db, lease)
            until = min(now + timedelta(seconds=60), t.deadline)
            self._save_task(db, t.model_copy(update={"lease_until": until}))
            return lease.model_copy(update={"lease_until": until})

    def checkpoint(self, lease, value):
        value = TaskCheckpoint.model_validate(value.model_dump(mode="json"))
        with self.store.transaction() as db:
            t = self._lease(db, lease)
            if (value.task_id, value.generation, value.lease_epoch, value.policy_digest) != (
                t.task.task_id,
                t.generation,
                t.lease_epoch,
                t.policy_digest,
            ):
                fail("INVALID checkpoint binding")
            ref = "fake:checkpoint:" + content_digest(value)
            db.execute("INSERT OR IGNORE INTO checkpoints VALUES(?,?)", (ref, encoded(value)))
            self._save_task(db, t.model_copy(update={"checkpoint_ref": ref}))
            return ref

    def begin_tool(self, lease, value):
        value = ToolInvocation.model_validate(value.model_dump(mode="json"))
        with self.store.transaction() as db:
            t = self._lease(db, lease)
            self.check_invocation(t, value)
            if value.state != "intended":
                fail("INVALID intent required")
            row = db.execute(
                "SELECT * FROM invocations WHERE id=?", (value.invocation_id,)
            ).fetchone()
            fingerprint = content_digest(value)
            if row:
                if row["fingerprint"] != fingerprint:
                    fail("CONFLICT")
                return ToolInvocation.model_validate_json(row["body"])
            if db.execute(
                "SELECT 1 FROM invocations WHERE json_extract(body,'$.task_id')=? "
                "AND json_extract(body,'$.state') IN ('submitted','unknown')",
                (value.task_id,),
            ).fetchone():
                fail("UNKNOWN reconcile original invocation")
            db.execute(
                "INSERT INTO invocations VALUES(?,?,?)",
                (value.invocation_id, fingerprint, encoded(value)),
            )
            return value

    @staticmethod
    def check_invocation(task, value):
        if (
            value.task_id,
            value.case_id,
            value.run_id,
            value.generation,
            value.lease_epoch,
            value.input_digest,
        ) != (
            task.task.task_id,
            task.case_id,
            task.run_id,
            task.generation,
            task.lease_epoch,
            task.input_digest,
        ) or value.tool_id not in task.task.allowed_tool_ids:
            fail("DENIED invocation scope")

    def observe_tool(self, lease, invocation_id, result_ref):
        with self.store.transaction() as db:
            t = self._lease(db, lease)
            row = db.execute("SELECT body FROM tools WHERE id=?", (invocation_id,)).fetchone()
            if row is None:
                fail("MISSING_EVIDENCE")
            observed = ToolInvocation.model_validate_json(row["body"])
            self.check_invocation(t, observed)
            if observed.state != "observed" or result_ref not in observed.result_refs:
                fail("MISSING_EVIDENCE")
            db.execute(
                "UPDATE invocations SET body=? WHERE id=?", (encoded(observed), invocation_id)
            )
            return observed

    def finish(self, lease, result):
        result = AgentResult.model_validate(result.model_dump(mode="json"))
        with self.store.transaction() as db:
            previous = db.execute(
                "SELECT body FROM results WHERE task_id=?", (lease.task_id,)
            ).fetchone()
            if previous:
                if previous["body"] != encoded(result):
                    fail("CONFLICT")
                row = db.execute("SELECT body FROM tasks WHERE id=?", (lease.task_id,)).fetchone()
                return AgentTask.model_validate_json(row["body"])
            t = self._lease(db, lease)
            if result.outcome == "completed":
                unresolved_tool = db.execute(
                    "SELECT 1 FROM invocations WHERE json_extract(body,'$.task_id')=? "
                    "AND json_extract(body,'$.state') IN ('intended','submitted','unknown')",
                    (t.task.task_id,),
                ).fetchone()
                unresolved_model = db.execute(
                    "SELECT 1 FROM model_turns WHERE task_id=? "
                    "AND json_extract(status,'$.state') IN ('intended','submitted','unknown')",
                    (t.task.task_id,),
                ).fetchone()
                if unresolved_tool or unresolved_model:
                    fail("UNKNOWN unresolved dispatch/reservation")
            if (
                result.task_id,
                result.request_id,
                result.case_id,
                result.run_id,
                result.generation,
                result.lease_epoch,
                result.input_digest,
            ) != (
                t.task.task_id,
                t.request_id,
                t.case_id,
                t.run_id,
                t.generation,
                t.lease_epoch,
                t.input_digest,
            ):
                fail("STALE result binding")
            if not result.authenticity_ref.startswith("fake:"):
                fail("DENIED nonfake authenticity")
            if result.outcome == "completed":
                schemas = set()
                for ref in result.output_refs:
                    row = db.execute("SELECT * FROM artifacts WHERE ref=?", (ref,)).fetchone()
                    if row is None:
                        fail("MISSING_EVIDENCE")
                    d = ArtifactDescriptor.model_validate_json(row["descriptor"])
                    identity = "fake:role:" + t.task.role.replace(" ", "_")
                    if d.evidence_class != "scripted" or d.schema_id not in t.task.expected_schemas:
                        fail("DENIED output/evidence class")
                    binding = ArtifactBinding(
                        "offline",
                        t.case_id,
                        t.run_id,
                        t.generation,
                        self.output_subject(db, t, d),
                        t.input_digest,
                        d.schema_id,
                        identity,
                        t.task.role,
                        frozenset({"model_proposal", "collector_observed"}),
                    )
                    validate_artifact(
                        d,
                        bytes(row["payload"]),
                        binding,
                        authenticated_tenant="offline",
                        authenticated_producer=identity,
                        now=self.store.clock(),
                        validation_context=self.output_context(db, t),
                    )
                    schemas.add(d.schema_id)
                if schemas != set(t.task.expected_schemas):
                    fail("MISSING_EVIDENCE required outputs")
            state = {
                "completed": "succeeded",
                "blocked": "held",
                "failed": "failed",
                "unknown": "unknown",
            }[result.outcome]
            t = t.model_copy(
                update=dict(
                    state=state,
                    output_refs=result.output_refs,
                    issue=result.issue,
                    state_version=t.state_version + 1,
                )
            )
            self._save_task(db, t)
            db.execute("INSERT INTO results VALUES(?,?)", (t.task.task_id, encoded(result)))
            run_ref = db.execute(
                "SELECT run_ref FROM tasks WHERE id=?", (t.task.task_id,)
            ).fetchone()[0]
            self._event(db, run_ref, "task_changed", t.task.task_id)
            snapshot = self._snapshot(db, run_ref)
            done = {x.task.task_id for x in snapshot.tasks if x.state == "succeeded"}
            for item in snapshot.tasks:
                if item.state == "pending" and set(item.task.dependencies) <= done:
                    self._save_task(
                        db,
                        item.model_copy(
                            update={"state": "ready", "state_version": item.state_version + 1}
                        ),
                    )
                    self._event(db, run_ref, "task_ready", item.task.task_id)
            return t

    def wait(self, lease, issue, condition):
        condition = WakeCondition.model_validate(condition.model_dump(mode="json"))
        with self.store.transaction() as db:
            t = self._lease(db, lease)
            if (condition.case_id, condition.run_id, condition.generation) != (
                t.case_id,
                t.run_id,
                t.generation,
            ):
                fail("DENIED wake scope")
            ref = "fake:wake:" + content_digest(condition)
            db.execute(
                "INSERT OR REPLACE INTO wakes VALUES(?,?)", (t.task.task_id, encoded(condition))
            )
            t = t.model_copy(update={"state": "waiting", "issue": issue, "wake_condition_ref": ref})
            self._save_task(db, t)
            run_ref = db.execute(
                "SELECT run_ref FROM tasks WHERE id=?", (t.task.task_id,)
            ).fetchone()[0]
            self._event(db, run_ref, "task_changed", t.task.task_id)
            return t

    def wake(self, run_ref, subject_ref, *, digest, version):
        with self.store.transaction() as db:
            run, authority = self._run(db, run_ref)
            if not authority or run["cancellation_ref"]:
                return False
            woke = False
            for t in self._snapshot(db, run_ref).tasks:
                if t.state != "waiting":
                    continue
                row = db.execute(
                    "SELECT body FROM wakes WHERE task_id=?", (t.task.task_id,)
                ).fetchone()
                condition = WakeCondition.model_validate_json(row["body"])
                if condition.expires_at <= self.store.clock() or t.deadline <= self.store.clock():
                    self._save_task(db, t.model_copy(update={"state": "held"}))
                    continue
                if (
                    condition.subject_ref == subject_ref
                    and condition.minimum_version <= version
                    and condition.generation == run["generation"]
                    and (condition.expected_digest is None or condition.expected_digest == digest)
                    and (condition.due_at is None or condition.due_at <= self.store.clock())
                ):
                    self._save_task(
                        db,
                        t.model_copy(
                            update={"state": "ready", "issue": None, "wake_condition_ref": None}
                        ),
                    )
                    self._event(db, run_ref, "task_ready", t.task.task_id)
                    woke = True
            return woke

    def recover_due(self, run_ref, now):
        """Offline timer scan only; authority/approval/counterpart waits require observations."""
        with self.store.transaction() as db:
            run, authority = self._run(db, run_ref)
            if not authority or run["cancellation_ref"]:
                return 0
            conditions = [
                WakeCondition.model_validate_json(row[0])
                for row in db.execute(
                    "SELECT wakes.body FROM wakes JOIN tasks ON wakes.task_id=tasks.id "
                    "WHERE tasks.run_ref=? AND json_extract(tasks.body,'$.state')='waiting'",
                    (run_ref,),
                )
            ]
        return sum(
            self.wake(run_ref, c.subject_ref, digest=c.expected_digest, version=c.minimum_version)
            for c in conditions
            if c.kind == "timer" and c.due_at <= now
        )

    def cancel(self, run_ref, cancellation_ref):
        with self.store.transaction() as db:
            run, _ = self._run(db, run_ref)
            if run["cancellation_ref"] and run["cancellation_ref"] != cancellation_ref:
                fail("CONFLICT")
            if run["cancellation_ref"] == cancellation_ref:
                return self._snapshot(db, run_ref)
            run["cancellation_ref"] = cancellation_ref
            db.execute("UPDATE runs SET body=? WHERE ref=?", (encoded(run), run_ref))
            for t in self._snapshot(db, run_ref).tasks:
                if t.state not in {"succeeded", "failed", "held", "unknown"}:
                    self._save_task(db, t.model_copy(update={"state": "cancelled"}))
            self._event(db, run_ref, "cancellation_changed")
            return self._snapshot(db, run_ref)

    def set_authority(self, run_ref, allowed):
        with self.store.transaction() as db:
            self._run(db, run_ref)
            db.execute("UPDATE runs SET authority=? WHERE ref=?", (int(allowed), run_ref))

    def outbox(self, run_ref):
        with self.store.transaction() as db:
            self._run(db, run_ref)
            return [
                TaskEvent.model_validate_json(r["body"])
                for r in db.execute(
                    "SELECT body FROM outbox WHERE run_ref=? AND ack=0 ORDER BY sequence",
                    (run_ref,),
                )
            ]

    def ack_event(self, event_id):
        with self.store.transaction() as db:
            db.execute("UPDATE outbox SET ack=1 WHERE id=?", (event_id,))

    def result(self, task_id):
        with self.store.transaction() as db:
            row = db.execute("SELECT body FROM results WHERE task_id=?", (task_id,)).fetchone()
            if row is None:
                fail("NOT_FOUND")
            return AgentResult.model_validate_json(row["body"])

    def accepted_result_count(self):
        with self.store.transaction() as db:
            return db.execute("SELECT COUNT(*) FROM results").fetchone()[0]
