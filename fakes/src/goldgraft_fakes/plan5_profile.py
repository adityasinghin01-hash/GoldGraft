"""Explicit synthetic runtime composition. No SDK, shell, network or merchant data."""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime

from goldgraft_contracts.agent_runtime import ArtifactDescriptor, TaskCheckpoint, TaskContext
from goldgraft_contracts.plan5_common import content_digest, reject_secret
from goldgraft_contracts.registry import validate

from ._fixtures import example
from .guarded_tools import GuardedOfflineTools
from .model_broker import ScriptedModelBroker
from .offline_artifacts import OfflineArtifacts
from .offline_store import encoded, fail
from .task_control import OfflineTaskControl

RUN = "fake:runtime-run"
SCENARIOS = frozenset(
    {
        "two_task_read",
        "missing_operation",
        "invalid_output",
        "prohibited_tool",
        "model_unknown",
        "tool_unknown",
        "missing_input",
        "zero_budget_missing",
    }
)


def authorize_synthetic_refs(control, db, task, tool_id, arguments):
    if tool_id == "source.read":
        if arguments.snapshot_ref not in task.task.input_refs or arguments.path != "checkout.php":
            fail("DENIED source scope/path")
        row = db.execute(
            "SELECT descriptor FROM artifacts WHERE ref=?", (arguments.snapshot_ref,)
        ).fetchone()
        if row is None:
            fail("MISSING_EVIDENCE snapshot")
        descriptor = ArtifactDescriptor.model_validate_json(row["descriptor"])
        if (
            descriptor.case_id,
            descriptor.run_id,
            descriptor.generation,
            descriptor.subject_digest,
        ) != (task.case_id, task.run_id, task.generation, task.task.expected_subject):
            fail("DENIED source binding")
    elif tool_id == "status.read":
        if arguments.run_ref != RUN:
            fail("DENIED run scope")
        run, authority = control._run(db, arguments.run_ref)
        if not authority or (run["case_id"], run["run_id"], run["generation"]) != (
            task.case_id,
            task.run_id,
            task.generation,
        ):
            fail("DENIED status scope")
    else:
        fail("UNSUPPORTED this offline slice admits only source.read/status.read")


@dataclass(frozen=True)
class FakeAdmission:
    task_id: str
    context: TaskContext
    acceptance: object
    operation: object
    policy_digest: str
    prompt_digest: str
    budget: object
    authority_current: bool
    evidence_class: str = "scripted"


class RuntimeArtifacts(OfflineArtifacts):
    def __init__(self, control, scenario):
        super().__init__(control)
        self.scenario = scenario
        self.clock = self.store.clock

    def authorize_tool(self, lease, tool_id, arguments):
        with self.store.transaction() as db:
            task = self.control._lease(db, lease)
            authorize_synthetic_refs(self.control, db, task, tool_id, arguments)

    def model_context(self, lease, context, observation_refs):
        task = self.control.load(lease)
        observations = []
        for ref in observation_refs:
            raw = self.raw(ref, lease)
            value = json.loads(raw)
            observations.append(
                {
                    "ref": ref,
                    "digest": hashlib.sha256(raw).hexdigest(),
                    "trust": "untrusted_tool_observation",
                    "value": value,
                }
            )
        envelope = {
            "task_context": context.model_dump(mode="json"),
            "policy": "offline-policy",
            "prompt": "scripted-counterpart-only",
            "observations": observations,
        }
        if (content_digest(envelope["policy"]), content_digest(envelope["prompt"])) != (
            task.policy_digest,
            task.prompt_digest,
        ):
            fail("DENIED prompt/policy digest")
        raw = encoded(envelope).encode()
        reject_secret(raw.decode())
        if len(raw) > 24000:
            fail("INVALID context cap")
        digest = hashlib.sha256(raw).hexdigest()
        ref = "fake:model-context:" + digest
        with self.store.transaction() as db:
            self.control._lease(db, lease)
            db.execute("INSERT OR IGNORE INTO contexts VALUES(?,?)", (ref, raw.decode()))
        return ref, digest

    def ticket(self, lease):
        task = self.control.load(lease)
        accepted = validate("WorkAcceptance/1", example("WorkAcceptance/1"))
        operation = validate("WorkerOperation/1", example("WorkerOperation/1"))
        budget = example("ModelBudget/1")
        budget.update(budget_id="fake:zero-budget", ceiling_micro_usd=0, target_micro_usd=0)
        return FakeAdmission(
            task.task.task_id,
            TaskContext.model_validate(self.control.context(lease.context_ref)),
            accepted,
            None if self.scenario == "missing_operation" else operation,
            task.policy_digest,
            task.prompt_digest,
            None if self.scenario == "zero_budget_missing" else validate("ModelBudget/1", budget),
            True,
        )

    def resolve(self, ref, task_context):
        # Inspection after completion is allowed; execution/staging still requires a live lease.
        with self.store.transaction() as db:
            ctxrow = db.execute("SELECT body FROM contexts WHERE ref=?", (task_context,)).fetchone()
            row = db.execute("SELECT * FROM artifacts WHERE ref=?", (ref,)).fetchone()
            if ctxrow is None or row is None:
                fail("MISSING_EVIDENCE scoped artifact")
            ctx = TaskContext.model_validate_json(ctxrow["body"])
            run, authority = self.control._run(db, RUN)
            descriptor = ArtifactDescriptor.model_validate_json(row["descriptor"])
            if not authority or (descriptor.case_id, descriptor.run_id, descriptor.generation) != (
                ctx.case_id,
                ctx.run_id,
                run["generation"],
            ):
                fail("DENIED artifact scope")
            if descriptor.ref != ref or (
                len(row["payload"]),
                hashlib.sha256(row["payload"]).hexdigest(),
            ) != (descriptor.byte_count, descriptor.payload_digest):
                fail("INVALID artifact bytes")
            return descriptor

    def raw(self, ref, lease):
        self.control.load(lease)
        return self.store.raw(ref, scope=lease.task_id)

    def read_artifact(self, ref, lease):
        """Authenticated artifact bytes, distinct from model/tool staging blobs."""
        task = self.control.load(lease)
        descriptor = self.resolve(ref, lease.context_ref)
        if descriptor.expires_at is not None and descriptor.expires_at <= self.clock():
            fail("EXPIRED artifact custody")
        if descriptor.subject_digest != task.task.expected_subject:
            fail("DENIED artifact subject")
        with self.store.transaction() as db:
            self.control._lease(db, lease)
            row = db.execute("SELECT payload FROM artifacts WHERE ref=?", (ref,)).fetchone()
            return bytes(row[0])

    def save_state(self, lease, state):
        return self.control.stage_untrusted(lease, state)

    def checkpoint_value(self, ref, lease):
        task = self.control.load(lease)
        with self.store.transaction() as db:
            row = db.execute("SELECT body FROM checkpoints WHERE ref=?", (ref,)).fetchone()
            if row is None:
                fail("MISSING_EVIDENCE checkpoint")
            value = TaskCheckpoint.model_validate_json(row["body"])
            if (value.task_id, value.generation, value.policy_digest) != (
                lease.task_id,
                lease.generation,
                task.policy_digest,
            ) or value.lease_epoch > lease.lease_epoch:
                fail("DENIED checkpoint")
            if ref != "fake:checkpoint:" + content_digest(value):
                fail("DENIED checkpoint bytes")
            contexts = [
                TaskContext.model_validate_json(row[0])
                for row in db.execute(
                    "SELECT body FROM contexts WHERE json_extract(body,'$.task_ref')=?",
                    ("fake:task:" + lease.task_id,),
                )
            ]
            pinned = next(
                (ctx for ctx in contexts if content_digest(ctx) == value.context_digest), None
            )
            if pinned is None or (
                pinned.case_id,
                pinned.run_id,
                pinned.generation,
                pinned.lease_epoch,
                pinned.input_refs,
                pinned.expected_subject,
            ) != (
                task.case_id,
                task.run_id,
                task.generation,
                value.lease_epoch,
                task.task.input_refs,
                task.task.expected_subject,
            ):
                fail("DENIED checkpoint context")
            return value

    def result_authenticity(self, lease):
        self.control.load(lease)
        return "fake:runtime-result"


class RuntimeModel(ScriptedModelBroker):
    def __init__(self, control, scenario):
        super().__init__(control)
        self.scenario = scenario

    def turn(self, request):
        task = self.control.snapshot(RUN).tasks
        task = next(t for t in task if t.task.task_id == request.task_id)
        with self.store.transaction() as db:
            turn = db.execute(
                "SELECT COUNT(*) FROM model_turns WHERE task_id=?", (request.task_id,)
            ).fetchone()[0]
            exists = db.execute(
                "SELECT 1 FROM scripts WHERE namespace=? AND id=?", ("model", request.turn_id)
            ).fetchone()
        if not exists:
            if self.scenario == "model_unknown":
                script = {"unknown": True}
            elif self.scenario == "invalid_output":
                script = {"kind": "final", "payload": {"invalid": True}}
            elif self.scenario == "prohibited_tool":
                script = {
                    "kind": "tool_calls",
                    "calls": [{"tool": "host.shell", "arguments": {"command": "echo unsafe"}}],
                }
            elif turn == 0:
                tool, args = (
                    (
                        "source.read",
                        {
                            "snapshot_ref": "fixture:input",
                            "path": "checkout.php",
                            "max_bytes": 4096,
                        },
                    )
                    if task.task.role == "Surveyor"
                    else ("status.read", {"run_ref": RUN})
                )
                script = {"kind": "tool_calls", "calls": [{"tool": tool, "arguments": args}]}
            else:
                payload = example(task.task.expected_schemas[0])
                if task.task.role == "Herald":
                    payload["producer"]["name"] = "Herald"
                    payload["text"] = (
                        "Scripted inventory was accepted; merchant readiness is unqualified."
                    )
                script = {"kind": "final", "payload": payload}
            self.script(request.turn_id, script)
        return super().turn(request)

    def total_dispatches(self):
        with self.store.transaction() as db:
            return db.execute("SELECT COALESCE(SUM(dispatch_count),0) FROM model_turns").fetchone()[
                0
            ]


class RuntimeTools(GuardedOfflineTools):
    def __init__(self, control, scenario):
        super().__init__(control)
        self.scenario = scenario

    def _validate(self, db, invocation):
        args = super()._validate(db, invocation)
        task = self.control._active(db, invocation.task_id)
        authorize_synthetic_refs(self.control, db, task, invocation.tool_id, args)
        return args

    def invoke(self, invocation):
        with self.store.transaction() as db:
            exists = db.execute(
                "SELECT 1 FROM scripts WHERE namespace=? AND id=?",
                ("tool", invocation.invocation_id),
            ).fetchone()
        if not exists:
            if self.scenario == "tool_unknown":
                script = {"unknown": True}
            elif invocation.tool_id == "status.read":
                # These refs come from committed predecessor results, never a scripted success flag.
                snapshot = self.control.snapshot(RUN)
                refs = [
                    ref
                    for task in snapshot.tasks
                    if task.state == "succeeded"
                    for ref in task.output_refs
                ]
                if not refs:
                    fail("MISSING_EVIDENCE predecessor output")
                script = {"payload": {"accepted_inventory_refs": refs}}
            else:
                script = {
                    "payload": {
                        "snapshot_ref": "fixture:input",
                        "path": "checkout.php",
                        "trust": "untrusted_source",
                        "excerpt": "<?php // synthetic licensed test source",
                    }
                }
            self.script(invocation.invocation_id, script)
        return super().invoke(invocation)

    def total_dispatches(self):
        with self.store.transaction() as db:
            return db.execute("SELECT COALESCE(SUM(dispatch_count),0) FROM tools").fetchone()[0]


@dataclass(frozen=True)
class OfflineProfile:
    control: OfflineTaskControl
    artifacts: RuntimeArtifacts
    model: RuntimeModel
    tools: RuntimeTools
    clock: object

    def context_for(self, task_id):
        with self.control.store.transaction() as db:
            for row in db.execute("SELECT ref,body FROM contexts ORDER BY rowid DESC"):
                if json.loads(row["body"]).get("task_ref") == "fake:task:" + task_id:
                    return row["ref"]
        fail("NOT_FOUND context")


def create_profile(path, *, scenario="two_task_read", clock=None):
    if scenario not in SCENARIOS:
        fail("UNSUPPORTED synthetic scenario")
    clock = clock or (lambda: datetime.now(UTC))
    control = OfflineTaskControl(path, clock=clock)
    with control.store.transaction() as db:
        existing = db.execute(
            "SELECT body FROM scripts WHERE namespace=? AND id=?", ("profile", RUN)
        ).fetchone()
        if existing and json.loads(existing["body"]) != {"scenario": scenario}:
            fail("CONFLICT existing profile")
        seeded = db.execute("SELECT 1 FROM runs").fetchone()
        if not existing:
            db.execute(
                "INSERT INTO scripts VALUES(?,?,?)",
                ("profile", RUN, encoded({"scenario": scenario})),
            )
    if not seeded:
        proposal = example("PlanProposal/1")
        first = proposal["tasks"][0]
        first.update(task_id="survey", output_slot="inventory")
        second = dict(
            first,
            task_id="herald",
            role="Herald",
            operation="explain_status",
            dependencies=["survey"],
            expected_schemas=["HeraldText/1"],
            allowed_tool_ids=["status.read"],
            output_slot="text",
        )
        proposal["tasks"] = [first, second]
        tasks = control.seed(RUN, validate("PlanProposal/1", proposal), "fake:seed")
        if scenario != "missing_input":
            with control.store.transaction() as db:
                ref = control.artifacts._put(
                    db, tasks[0], "RootMap/1", example("RootMap/1"), first["expected_subject"]
                )
                db.execute(
                    "UPDATE artifacts SET ref=?,"
                    "descriptor=json_set(descriptor,'$.ref',?) WHERE ref=?",
                    ("fixture:input", "fixture:input", ref),
                )
    artifacts = RuntimeArtifacts(control, scenario)
    return OfflineProfile(
        control, artifacts, RuntimeModel(control, scenario), RuntimeTools(control, scenario), clock
    )
