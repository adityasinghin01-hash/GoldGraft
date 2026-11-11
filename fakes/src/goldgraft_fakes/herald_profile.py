"""Explicit persistent Surveyor/Herald counterpart, not real GU projection or ledger.

Numeric journal rows are derived from actually committed predecessor bytes. This
fake stores no merchant data and has no external notification/provider operation.
"""

import hashlib
import json
from dataclasses import dataclass

from goldgraft_contracts.agent_runtime import AgentTask, ArtifactDescriptor
from goldgraft_contracts.plan5_common import content_digest, reject_secret

from .guarded_tools import GuardedOfflineTools
from .model_broker import ScriptedModelBroker
from .offline_store import encoded, fail
from .plan5_profile import RUN, OfflineProfile
from .surveyor_profile import (
    SurveyArtifacts,
    SurveyModel,
    SurveyTools,
    authorize,
    create_surveyor_profile,
)


def projection(control, db, task, config, *, create=False):
    if task.task.role == "Surveyor":
        source = task
    else:
        row = db.execute("SELECT body FROM tasks WHERE id='survey'").fetchone()
        if row is None:
            fail("MISSING_EVIDENCE predecessor")
        source = AgentTask.model_validate_json(row[0])
    if source.state != "succeeded" or len(source.output_refs) != 1:
        fail("MISSING_EVIDENCE committed inventory")
    ref = source.output_refs[0]
    row = db.execute("SELECT * FROM artifacts WHERE ref=?", (ref,)).fetchone()
    if row is None:
        fail("MISSING_EVIDENCE inventory bytes")
    descriptor = ArtifactDescriptor.model_validate_json(row["descriptor"])
    if (
        (
            descriptor.case_id,
            descriptor.run_id,
            descriptor.generation,
            descriptor.subject_digest,
            descriptor.producer_identity_ref,
            descriptor.schema_id,
        )
        != (
            task.case_id,
            task.run_id,
            task.generation,
            task.task.expected_subject,
            "fake:role:Surveyor",
            "RootMap/1",
        )
        or descriptor.ref != ref
        or descriptor.input_digest != source.input_digest
    ):
        fail("DENIED predecessor binding")
    raw = bytes(row["payload"])
    if (len(raw), hashlib.sha256(raw).hexdigest()) != (
        descriptor.byte_count,
        descriptor.payload_digest,
    ):
        fail("DENIED predecessor bytes")
    if descriptor.expires_at is not None and descriptor.expires_at <= control.store.clock():
        fail("EXPIRED predecessor custody")
    if task.task.role == "Herald" and task.task.input_refs != [ref]:
        fail("DENIED projection input binding")
    entry = {
        "case_id": source.case_id,
        "run_id": source.run_id,
        "generation": source.generation,
        "subject_digest": descriptor.subject_digest,
        "source_ref": ref,
        "source_payload_digest": descriptor.payload_digest,
        "source_version": source.state_version,
        "payload": {"source_indicators": len(json.loads(raw)["touchpoints"])},
    }
    digest = content_digest(entry)
    journal = db.execute(
        "SELECT body FROM scripts WHERE namespace='herald-journal' AND id=?", (digest,)
    ).fetchone()
    if journal is None:
        if not create:
            fail("MISSING_EVIDENCE committed projection journal")
        db.execute("INSERT INTO scripts VALUES('herald-journal',?,?)", (digest, encoded(entry)))
    elif json.loads(journal[0]) != entry:
        fail("DENIED projection journal bytes")
    result = db.execute("SELECT body FROM results WHERE task_id='survey'").fetchone()
    if result is None or json.loads(result[0])["outcome"] != "completed":
        fail("MISSING_EVIDENCE accepted predecessor result")
    facts = {
        "case_id": task.case_id,
        "run_id": task.run_id,
        "generation": task.generation,
        "subject_digest": task.task.expected_subject,
        "run_ref": RUN,
        "input_refs": [ref],
        "projection": config["projection"],
        "status": config.get("status", "inventory_ready"),
        "observed_at": json.loads(result[0])["completed_at"],
        "projection_version": source.state_version,
        "ledger_entries": {digest: entry},
        "evidence_refs": [ref, "fake:projection-journal:" + digest],
        "proof_complete": False,
        "proof_subject": None,
        "kind": config.get("kind", "GRAFT_CARD"),
        "reason_code": config.get("reason_code", "NONE"),
        "retained": config.get("retained", []),
        "removed": config.get("removed", []),
        "pending": config.get("pending", []),
    }
    reject_secret(encoded(facts))
    return facts


class CollaborationArtifacts(SurveyArtifacts):
    def __init__(self, control, config, bundle, herald_config):
        super().__init__(control, config, bundle)
        self.herald_config = herald_config

    def prepare_herald_projection(self, source):
        with self.store.transaction() as db:
            current = AgentTask.model_validate_json(
                db.execute("SELECT body FROM tasks WHERE id=?", (source.task.task_id,)).fetchone()[
                    0
                ]
            )
            run, authority = self.control._run(db, RUN)
            if not authority or run["cancellation_ref"] or current.generation != run["generation"]:
                fail("DENIED current projection authority")
            projection(self.control, db, current, self.herald_config, create=True)

    def role_inputs(self, lease):
        task = self.control.load(lease)
        if task.task.role == "Surveyor":
            return super().role_inputs(lease)
        with self.store.transaction() as db:
            task = self.control._lease(db, lease)
            return projection(self.control, db, task, self.herald_config)

    def authorize_tool(self, lease, tool_id, arguments):
        task = self.control.load(lease)
        if task.task.role == "Surveyor":
            return super().authorize_tool(lease, tool_id, arguments)
        facts = self.role_inputs(lease)
        authorize_herald(task, facts, tool_id, arguments)

    def model_context(self, lease, context, observation_refs):
        task = self.control.load(lease)
        if task.task.role == "Surveyor":
            return super().model_context(lease, context, observation_refs)
        facts = self.role_inputs(lease)
        config = self.herald_config
        envelope = {
            "task_context": context.model_dump(mode="json"),
            "facts": facts,
            "prompt": config["prompt"],
            "policy": config["policy"],
            "observations": [
                {
                    "ref": ref,
                    "trust": "untrusted_tool_observation",
                    "digest": hashlib.sha256(self.raw(ref, lease)).hexdigest(),
                    "value": json.loads(self.raw(ref, lease)),
                }
                for ref in observation_refs
            ],
        }
        if (content_digest(envelope["prompt"]), content_digest(envelope["policy"])) != (
            task.prompt_digest,
            task.policy_digest,
        ):
            fail("DENIED Herald prompt/policy")
        raw = encoded(envelope)
        reject_secret(raw)
        if len(raw.encode()) > 24000:
            fail("MISSING_EVIDENCE bounded Herald context")
        digest = hashlib.sha256(raw.encode()).hexdigest()
        ref = "fake:model-context:" + digest
        with self.store.transaction() as db:
            self.control._lease(db, lease)
            db.execute("INSERT OR IGNORE INTO contexts VALUES(?,?)", (ref, raw))
        return ref, digest

    def inspect_herald(self, task, context_ref):
        if task.state != "succeeded" or len(task.output_refs) != 1:
            fail("MISSING_EVIDENCE accepted Herald output")
        descriptor = self.resolve(task.output_refs[0], context_ref)
        if (
            descriptor.schema_id,
            descriptor.producer_identity_ref,
            descriptor.subject_digest,
            descriptor.input_digest,
        ) != (
            "HeraldText/1",
            "fake:role:Herald",
            task.task.expected_subject,
            task.input_digest,
        ):
            fail("DENIED inspected Herald binding")
        if descriptor.expires_at is not None and descriptor.expires_at <= self.clock():
            fail("EXPIRED text custody")
        with self.store.transaction() as db:
            facts = projection(self.control, db, task, self.herald_config)
            row = db.execute(
                "SELECT payload FROM artifacts WHERE ref=?", (descriptor.ref,)
            ).fetchone()
            return json.loads(bytes(row[0])), facts


def authorize_herald(task, facts, tool_id, args):
    if task.task.role != "Herald" or tool_id not in task.task.allowed_tool_ids:
        fail("DENIED Herald tool")
    if tool_id not in {"status.read", "evidence.summary"} or args.run_ref != facts["run_ref"]:
        fail("DENIED Herald run scope")
    if tool_id == "evidence.summary" and args.projection != facts["projection"]:
        fail("DENIED projection capability")


class CollaborationTools(GuardedOfflineTools):
    def __init__(self, control, bundle, herald_config):
        super().__init__(control)
        self.survey = SurveyTools(control, bundle)
        self.herald_config = herald_config

    def _validate(self, db, invocation):
        args = super()._validate(db, invocation)
        task = self.control._active(db, invocation.task_id)
        if task.task.role == "Surveyor":
            authorize(task, self.survey.bundle, invocation.tool_id, args)
        else:
            facts = projection(self.control, db, task, self.herald_config)
            authorize_herald(task, facts, invocation.tool_id, args)
        return args

    def invoke(self, invocation):
        with self.store.transaction() as db:
            task = self.control._active(db, invocation.task_id)
            if task.task.role == "Herald":
                self._validate(db, invocation)
                facts = projection(self.control, db, task, self.herald_config)
            exists = db.execute(
                "SELECT 1 FROM scripts WHERE namespace='tool' AND id=?", (invocation.invocation_id,)
            ).fetchone()
        if task.task.role == "Surveyor":
            return self.survey.invoke(invocation)
        if not exists:
            value = (
                {
                    "kind": "status_projection",
                    "status": facts["status"],
                    "projection_version": facts["projection_version"],
                }
                if invocation.tool_id == "status.read"
                else {
                    "kind": "evidence_summary",
                    "projection": facts["projection"],
                    "facts_digest": content_digest(facts),
                }
            )
            self.script(invocation.invocation_id, {"payload": value})
        return super().invoke(invocation)

    def total_dispatches(self):
        return self.survey.total_dispatches()


class CollaborationModel(ScriptedModelBroker):
    def __init__(self, control, bundle, herald_config, renderer, survey_payload=None):
        super().__init__(control)
        self.survey = SurveyModel(control, bundle, survey_payload)
        self.herald_config, self.renderer = herald_config, renderer

    def turn(self, request):
        with self.store.transaction() as db:
            task = self.control._active(db, request.task_id)
            row = db.execute(
                "SELECT body FROM contexts WHERE ref=?", (request.context_ref,)
            ).fetchone()
            context = json.loads(row[0])
            exists = db.execute(
                "SELECT 1 FROM scripts WHERE namespace='model' AND id=?", (request.turn_id,)
            ).fetchone()
        if task.task.role == "Surveyor":
            return self.survey.turn(request)
        if not exists:
            if not context["observations"]:
                script = {
                    "kind": "tool_calls",
                    "calls": [
                        {"tool": "status.read", "arguments": {"run_ref": RUN}},
                        {
                            "tool": "evidence.summary",
                            "arguments": {
                                "run_ref": RUN,
                                "projection": self.herald_config["projection"],
                            },
                        },
                    ],
                }
            else:
                script = {"kind": "final", "payload": self.renderer(task, context["facts"])}
            self.script(request.turn_id, script)
        return super().turn(request)

    def total_dispatches(self):
        return self.survey.total_dispatches()


@dataclass(frozen=True)
class CollaborationProfile(OfflineProfile):
    herald_configuration: dict
    program: str = "surveyor_herald"


def create_collaboration_profile(
    path, *, configuration, herald_configuration, renderer, clock=None, inputs=None
):
    if renderer is None:
        fail("MISSING_EVIDENCE own deterministic renderer")
    configuration = dict(configuration, herald_configuration=herald_configuration)
    original = create_surveyor_profile(
        path, configuration=configuration, clock=clock, inputs=inputs
    )
    control = original.control
    control.role_configurations = {"Herald": herald_configuration}

    def output_context(db, task):
        if task.task.role != "Herald":
            return None
        return {
            "ledger_entries": projection(control, db, task, herald_configuration)["ledger_entries"]
        }

    control.output_context = output_context
    bundle = original.artifacts.bundle
    return CollaborationProfile(
        control,
        CollaborationArtifacts(control, configuration, bundle, herald_configuration),
        CollaborationModel(
            control,
            bundle,
            herald_configuration,
            renderer,
            configuration.get("offline_final_payload"),
        ),
        CollaborationTools(control, bundle, herald_configuration),
        original.clock,
        herald_configuration,
    )
