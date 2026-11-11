"""Persistent generic counterpart for own role implementations; no external execution.

Role planners/renderers are injected by the owning piece. This module implements
scoped fake tool behaviour, not agent decisions or a second scheduler.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime

from goldgraft_contracts.agent_runtime import (
    ArtifactDescriptor,
    ExecutionProposal,
    PlanProposal,
    SubjectDerivation,
    SubjectManifest,
    TaskSpec,
)
from goldgraft_contracts.plan5_common import content_digest, reject_secret
from goldgraft_contracts.plan5_tools import TOOL_CATALOG
from goldgraft_contracts.plan5_validation import validate_subject_lineage
from goldgraft_contracts.registry import validate

from ._fixtures import example
from .guarded_tools import GuardedOfflineTools
from .model_broker import ScriptedModelBroker
from .offline_store import encoded, fail
from .plan5_profile import RUN, RuntimeArtifacts
from .task_control import OfflineTaskControl


def packet_for(control, db, task):
    ref = task.task.input_refs[0]
    row = db.execute("SELECT * FROM artifacts WHERE ref=?", (ref,)).fetchone()
    if row is None:
        fail("MISSING_EVIDENCE role input")
    d = ArtifactDescriptor.model_validate_json(row["descriptor"])
    if (
        d.ref,
        d.case_id,
        d.run_id,
        d.generation,
        d.subject_digest,
        d.schema_id,
        d.trust,
        d.producer_identity_ref,
    ) != (
        ref,
        task.case_id,
        task.run_id,
        task.generation,
        task.task.expected_subject,
        "TaskEvent/1",
        "collector_observed",
        "fake:collector",
    ):
        fail("DENIED role input binding")
    raw = bytes(row["payload"])
    if (len(raw), hashlib.sha256(raw).hexdigest()) != (d.byte_count, d.payload_digest):
        fail("DENIED input bytes")
    if d.expires_at is not None and d.expires_at <= control.store.clock():
        fail("EXPIRED role input")
    event = validate("TaskEvent/1", json.loads(raw))
    blob = db.execute("SELECT * FROM blobs WHERE ref=?", (event.payload_ref,)).fetchone()
    if blob is None or blob["scope"] != task.task.task_id:
        fail("DENIED input payload scope")
    raw = bytes(blob["body"])
    if hashlib.sha256(raw).hexdigest() != event.payload_digest:
        fail("DENIED scoped input digest")
    return json.loads(raw)


def authorize(task, packet, tool, args):
    data = packet["data"]
    if tool not in task.task.allowed_tool_ids:
        fail("DENIED role capability")
    if tool in {"status.read", "audit.summary", "safety.request_hold", "evidence.summary"}:
        if args.run_ref != RUN:
            fail("DENIED run scope")
        if tool == "audit.summary" and args.after_seq != data["after_seq"]:
            fail("DENIED audit window")
        if tool == "safety.request_hold":
            if args.evidence_refs != task.task.input_refs:
                fail("DENIED hold evidence")
            if task.task.role == "Sentinel" and (
                args.reason_code != "AUDIT_POLICY_BREACH"
                or not any(e["kind"] in {"denied_tool", "secret_attempt"} for e in data["events"])
            ):
                fail("DENIED ungrounded hold")
    elif tool == "evidence.read":
        if args.ref not in data.get("evidence", {}) and args.ref not in task.task.input_refs:
            fail("DENIED evidence ref")
    elif tool == "source.read":
        if args.snapshot_ref != data.get("source_ref") or args.path not in data.get("files", {}):
            fail("DENIED source scope")
    elif tool in {"recipe.lookup", "docs.lookup", "dependency.inspect"}:
        catalog = data.get("catalog", {})
        expected = {
            "recipe.lookup": {
                "catalog_ref": catalog.get("ref"),
                "fingerprint": catalog.get("fingerprint"),
            },
            "docs.lookup": {
                "catalog_ref": catalog.get("ref"),
                "topic": catalog.get("topic"),
                "version": catalog.get("version"),
            },
            "dependency.inspect": {
                "recipe_ref": catalog.get("recipe_ref"),
                "package": catalog.get("package"),
                "version": catalog.get("version"),
            },
        }[tool]
        if args.model_dump(mode="json") != expected:
            fail("DENIED pinned catalog scope")
    elif tool == "execution.status" and args.request_id != task.request_id:
        fail("DENIED execution request identity")
    elif tool == "candidate.patch":
        if (
            task.task.role != "Grafter"
            or args.workspace_ref != task.task.workspace_ref
            or args.expected_tree != data.get("expected_tree")
        ):
            fail("DENIED candidate writer/workspace/tree")
    elif tool == "aggregate.read":
        if (args.query_ref, args.projection_ref) != (
            data.get("query_ref"),
            data.get("projection_ref"),
        ):
            fail("DENIED aggregate query/projection ACL")
    # Remaining catalog operations get their own closed handlers as roles are built.


def tool_value(control, db, task, packet, invocation, args):
    data = packet["data"]
    tool = invocation.tool_id
    if tool == "audit.summary":
        return {"events": data["events"], "after_seq": args.after_seq}
    if tool == "status.read":
        return data.get("status", {"generation": task.generation, "state": "component_offline"})
    if tool == "safety.request_hold":
        receipt = {
            "request_id": "fake:hold:" + invocation.invocation_id,
            "run_ref": RUN,
            "requested": True,
            "termination": "pending",
        }
        db.execute(
            "INSERT OR IGNORE INTO scripts VALUES('component-hold',?,?)",
            (invocation.invocation_id, encoded(receipt)),
        )
        return receipt
    if tool == "source.read":
        text = data["files"][args.path]
        if len(text.encode()) > args.max_bytes:
            fail("MISSING_EVIDENCE source bound")
        return {
            "path": args.path,
            "excerpt": text,
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "provenance": "untrusted_source",
        }
    if tool == "evidence.read":
        value = data.get("evidence", {}).get(args.ref, {"ref": task.task.input_refs[0]})
        if len(encoded(value).encode()) > args.max_bytes:
            fail("MISSING_EVIDENCE evidence bound")
        return value
    if tool in {"recipe.lookup", "docs.lookup", "dependency.inspect"}:
        return {"catalog": data["catalog"], "qualification": "synthetic_only"}
    if tool == "execution.request":
        row = db.execute(
            "SELECT scope,body FROM blobs WHERE ref=?", (args.proposal_ref,)
        ).fetchone()
        if row is None or row["scope"] != task.task.task_id:
            fail("DENIED execution proposal custody")
        proposal = ExecutionProposal.model_validate_json(bytes(row["body"]))
        if (
            proposal.task_id,
            proposal.expected_subject,
            proposal.operation,
            proposal.evidence_refs,
        ) != (
            task.task.task_id,
            task.task.expected_subject,
            task.task.operation,
            task.task.input_refs,
        ):
            fail("DENIED execution proposal scope")
        if proposal.subject_ref != data.get("subject_ref") or proposal.recipe_ref != data.get(
            "catalog", {}
        ).get("recipe_ref", data.get("recipe_ref")):
            fail("DENIED execution subject/recipe")
        if proposal.scenario_ref != data.get("scenario_ref") or proposal.variant != data.get(
            "variant"
        ):
            fail("DENIED scenario variant")
        receipt = {
            "proposal": proposal.model_dump(mode="json"),
            "request_id": task.request_id,
            "state": data.get("execution_state", "observed"),
            "subject": task.task.expected_subject,
            "result": data.get("execution_result", {}),
            "synthetic_only": True,
        }
        old = db.execute(
            "SELECT body FROM scripts WHERE namespace='component-job' AND id=?", (task.request_id,)
        ).fetchone()
        if old and json.loads(old[0]) != receipt:
            fail("CONFLICT existing execution identity")
        db.execute(
            "INSERT OR IGNORE INTO scripts VALUES('component-job',?,?)",
            (task.request_id, encoded(receipt)),
        )
        return receipt
    if tool == "execution.status":
        row = db.execute(
            "SELECT body FROM scripts WHERE namespace='component-job' AND id=?", (args.request_id,)
        ).fetchone()
        if row is None:
            fail("MISSING_EVIDENCE execution request")
        return json.loads(row[0])
    if tool == "candidate.patch":
        row = db.execute("SELECT scope,body FROM blobs WHERE ref=?", (args.patch_ref,)).fetchone()
        if row is None or row["scope"] != task.task.task_id:
            fail("DENIED candidate patch custody")
        patch = json.loads(bytes(row["body"]))
        if not isinstance(patch, dict) or not patch or set(patch) - set(data["allowed_paths"]):
            fail("DENIED candidate path scope")
        if any(not isinstance(v, str) for v in patch.values()):
            fail("DENIED patch content")
        current = db.execute(
            "SELECT body FROM scripts WHERE namespace='candidate-tree' AND id=?",
            (args.workspace_ref,),
        ).fetchone()
        current = (
            json.loads(current[0])
            if current
            else {"files": data["files"], "owner": task.task.task_id}
        )
        prior_writer = db.execute(
            "SELECT body FROM tasks WHERE id=?", (current["owner"],)
        ).fetchone()
        transfer = (
            prior_writer is not None
            and json.loads(prior_writer[0])["state"] == "succeeded"
            and current["owner"] in task.task.dependencies
        )
        if (current["owner"] != task.task.task_id and not transfer) or content_digest(
            current["files"]
        ) != args.expected_tree:
            fail("CONFLICT candidate CAS or writer")
        files = {**current["files"], **patch}
        tree = content_digest(files)
        snapshot_ref = control.store.blob(
            db,
            task.task.task_id,
            {"kind": "synthetic_candidate_snapshot", "files": files, "tree": tree},
        )
        manifest = SubjectManifest(
            source_snapshot_refs=[snapshot_ref],
            source_tree_digest=tree,
            oci_manifest_digest=None,
            config_digest=None,
            runtime_profile_digest=content_digest("offline-component-profile:1"),
            scope_digest=task.task.expected_subject,
        )
        receipt = {
            "patch": patch,
            "patch_digest": content_digest(patch),
            "snapshot_ref": snapshot_ref,
            "tree": tree,
            "manifest": manifest.model_dump(mode="json"),
            "subject": content_digest(manifest),
            "synthetic_only": True,
        }
        # Explicit fault injection for original synthetic Grafter cases only;
        # candidate bytes and the independently built manifest remain unchanged.
        if data.get("collector_receipt_fault") == "wrong_tree":
            receipt["tree"] = "0" * 64
        elif data.get("collector_receipt_fault") == "missing_snapshot":
            receipt.pop("snapshot_ref")
        db.execute(
            "INSERT OR REPLACE INTO scripts VALUES('candidate-tree',?,?)",
            (args.workspace_ref, encoded({"files": files, "owner": task.task.task_id})),
        )
        db.execute(
            "INSERT INTO scripts VALUES('candidate-receipt',?,?)",
            (task.request_id, encoded(receipt)),
        )
        return receipt
    if tool == "scenario.stage":
        result = {}
        for name, schema in [
            ("scenario_set_ref", "ScenarioSet/1"),
            ("mutant_set_ref", "MutantSet/1"),
        ]:
            ref = getattr(args, name)
            row = db.execute("SELECT scope,body FROM blobs WHERE ref=?", (ref,)).fetchone()
            if row is None or row["scope"] != task.task.task_id:
                fail("DENIED guard draft custody")
            value = json.loads(bytes(row["body"]))
            parsed = validate(schema, value)
            if parsed.producer.name != "Adversary" or parsed.graft_id != task.run_id:
                fail("DENIED guard draft owner")
            result[schema] = value
        return {"drafts": result, "status": "QUARANTINE", "candidate_mutated": False}
    if tool == "recipe.stage":
        result = {}
        for name, schema in [("recipe_ref", "Recipe/1"), ("detection_rule_ref", "DetectionRule/1")]:
            ref = getattr(args, name)
            if ref is None:
                continue
            row = db.execute("SELECT scope,body FROM blobs WHERE ref=?", (ref,)).fetchone()
            if row is None or row["scope"] != task.task.task_id:
                fail("DENIED recipe proposal custody")
            value = json.loads(bytes(row["body"]))
            parsed = validate(schema, value)
            if schema == "Recipe/1" and (
                parsed.status.value != "QUARANTINE"
                or parsed.signature != "UNSIGNED_SYNTHETIC_QUARANTINE"
            ):
                fail("DENIED recipe promotion/signature")
            result[schema] = value
        return {"drafts": result, "status": "QUARANTINE", "active_promotion": False}
    if tool == "aggregate.read":
        if (
            data.get("tenant_id") != "offline"
            or data.get("purpose") != "upgrade_audit"
            or data.get("query_ref") != "catalog:upgrade-counts:1"
        ):
            fail("DENIED aggregate scope/purpose")
        if any(b["cases"] < data["minimum_cohort"] for b in data["buckets"]):
            fail("DENIED minimum disclosure cohort")
        return {
            "tenant_id": "other"
            if data.get("aggregate_receipt_fault") == "wrong_tenant"
            else "offline",
            "purpose": "upgrade_audit",
            "buckets": data["buckets"],
            "projection_ref": args.projection_ref,
            "raw_rows": data.get("aggregate_receipt_fault") == "raw_rows",
        }
    fail("UNSUPPORTED tool handler not implemented")


def accepted_output_subject(control, db, task, descriptor):
    if task.task.output_subject_policy == "same_subject":
        return task.task.expected_subject
    if task.task.role != "Grafter" or task.task.output_subject_policy != "candidate_child":
        fail("DENIED output transformation")
    row = db.execute(
        "SELECT body FROM scripts WHERE namespace='candidate-receipt' AND id=?", (task.request_id,)
    ).fetchone()
    blob = db.execute(
        "SELECT scope,body FROM blobs WHERE ref=?", (descriptor.derivation_ref,)
    ).fetchone()
    if row is None or blob is None or blob["scope"] != task.task.task_id:
        fail("MISSING_EVIDENCE candidate lineage")
    receipt = json.loads(row[0])
    manifest = SubjectManifest.model_validate(receipt["manifest"])
    derivation = SubjectDerivation.model_validate_json(bytes(blob["body"]))
    if descriptor.derivation_ref != "fake:blob:" + content_digest(
        {"scope": task.task.task_id, "body": derivation.model_dump(mode="json")}
    ):
        fail("DENIED derivation bytes")
    if derivation.recipe_or_patch_digest != receipt[
        "patch_digest"
    ] or manifest.source_snapshot_refs != [receipt["snapshot_ref"]]:
        fail("DENIED patch/source lineage")
    snapshot = db.execute(
        "SELECT scope,body FROM blobs WHERE ref=?", (receipt["snapshot_ref"],)
    ).fetchone()
    if snapshot is None or snapshot["scope"] != task.task.task_id:
        fail("DENIED candidate snapshot custody")
    snapshot = json.loads(bytes(snapshot["body"]))
    if (
        content_digest(snapshot["files"]) != manifest.source_tree_digest
        or manifest.source_tree_digest != receipt["tree"]
    ):
        fail("DENIED candidate tree bytes")
    validate_subject_lineage(
        task,
        descriptor,
        manifest,
        derivation=derivation,
        derivation_ref=descriptor.derivation_ref,
        authenticated_collector="fake:collector",
    )
    return descriptor.subject_digest


class ComponentArtifacts(RuntimeArtifacts):
    def __init__(self, control, configuration):
        super().__init__(control, "role_component")
        self.configuration = configuration

    def validate_input_subject(self, lease, descriptor):
        with self.store.transaction() as db:
            task = self.control._lease(db, lease)
            row = db.execute(
                "SELECT body FROM scripts WHERE namespace='prepared-component' AND id=?",
                (task.task.task_id,),
            ).fetchone()
            if row is None:
                return False
            prepared = json.loads(row[0])
            bindings = prepared["bindings"]
            manifest = SubjectManifest.model_validate(prepared["manifest"])
            if content_digest(manifest) != task.task.expected_subject:
                fail("DENIED composite subject manifest")
            if manifest.scope_digest != content_digest(bindings):
                fail("DENIED composite input manifest")
            bound = next((d for d in bindings if d["ref"] == descriptor.ref), None)
            return bound == descriptor.model_dump(mode="json", by_alias=True)

    def input_data(self, task_id):
        with self.store.transaction() as db:
            task = next(
                (t for t in self.control._snapshot(db, RUN).tasks if t.task.task_id == task_id),
                None,
            )
            if task is None:
                fail("MISSING_EVIDENCE task data")
            return packet_for(self.control, db, task)["data"]

    def candidate_files(self, task_id):
        task, _, observations = self.committed(task_id)
        receipt = next(
            o["value"]["payload"] for o in observations if o["value"]["tool"] == "candidate.patch"
        )
        with self.store.transaction() as db:
            row = db.execute(
                "SELECT scope,body FROM blobs WHERE ref=?", (receipt["snapshot_ref"],)
            ).fetchone()
            if row is None or row["scope"] != task_id:
                fail("DENIED candidate file custody")
            value = json.loads(bytes(row["body"]))
            if content_digest(value["files"]) != receipt["tree"]:
                fail("DENIED candidate tree")
            return value["files"]

    def committed(self, task_id):
        with self.store.transaction() as db:
            task = self.control._snapshot(db, RUN).tasks
            task = next((t for t in task if t.task.task_id == task_id), None)
        if task is None or task.state != "succeeded":
            fail("MISSING_EVIDENCE committed predecessor")
        outputs = self.inspect_outputs(task, self.context_for_task(task_id))
        with self.store.transaction() as db:
            row = db.execute("SELECT body FROM results WHERE task_id=?", (task_id,)).fetchone()
            result = json.loads(row[0])
            observations = [
                json.loads(
                    bytes(db.execute("SELECT body FROM blobs WHERE ref=?", (r,)).fetchone()[0])
                )
                for r in result["evidence_refs"]
            ]
        return task, outputs, observations

    def context_for_task(self, task_id):
        with self.store.transaction() as db:
            for row in db.execute("SELECT ref,body FROM contexts ORDER BY rowid DESC"):
                if json.loads(row[1]).get("task_ref") == "fake:task:" + task_id:
                    return row[0]
        fail("MISSING_EVIDENCE task context")

    def append_task(
        self,
        *,
        task_id,
        configuration,
        operation,
        data,
        schemas,
        dependencies,
        output_policy="same_subject",
        workspace_ref=None,
    ):
        snapshot = self.control.snapshot(RUN)
        if any(t.task.task_id == task_id for t in snapshot.tasks):
            hydrate_components(self.control)
            return
        refs = []
        bindings = []
        for dependency in dependencies:
            task, _, _ = self.committed(dependency)
            for ref in task.output_refs:
                d = self.resolve(ref, self.context_for_task(dependency))
                if d.producer_identity_ref != "fake:role:" + task.task.role.replace(" ", "_"):
                    fail("DENIED predecessor owner")
                refs.append(ref)
                bindings.append(d.model_dump(mode="json", by_alias=True))
        manifest = SubjectManifest(
            source_snapshot_refs=[],
            source_tree_digest=None,
            oci_manifest_digest=None,
            config_digest=None,
            runtime_profile_digest=content_digest("offline-component-composite:1"),
            scope_digest=content_digest(bindings),
        )
        carrier = "fake:input:" + task_id
        spec = TaskSpec(
            task_id=task_id,
            role=configuration["role"],
            operation=operation,
            dependencies=dependencies,
            input_refs=[carrier, *refs],
            expected_schemas=schemas,
            output_slot="component:" + task_id,
            workspace_ref=workspace_ref,
            expected_subject=content_digest(manifest),
            allowed_tool_ids=configuration["policy"]["tools"],
            required=True,
            output_subject_policy=output_policy,
        )
        prepared = {
            "configuration": configuration,
            "data": data,
            "manifest": manifest.model_dump(mode="json"),
            "bindings": bindings,
        }
        with self.store.transaction() as db:
            old = db.execute(
                "SELECT body FROM scripts WHERE namespace='prepared-component' AND id=?", (task_id,)
            ).fetchone()
            if old and json.loads(old[0]) != prepared:
                fail("CONFLICT prepared role inputs")
            db.execute(
                "INSERT OR IGNORE INTO scripts VALUES('prepared-component',?,?)",
                (task_id, encoded(prepared)),
            )
        self.control.role_configurations[configuration["role"]] = configuration
        proposal = PlanProposal(
            case_id=snapshot.case_id,
            run_id=snapshot.run_id,
            generation=snapshot.generation,
            parent_request_id="extend-" + task_id,
            tasks=[spec],
            reason_refs=refs,
        )
        self.control.extend(
            RUN,
            snapshot.state_version,
            proposal,
            "fake:component-extension:" + content_digest(proposal),
        )
        hydrate_components(self.control)

    def role_inputs(self, lease):
        with self.store.transaction() as db:
            task = self.control._lease(db, lease)
            return packet_for(self.control, db, task)

    def authorize_tool(self, lease, tool_id, arguments):
        with self.store.transaction() as db:
            task = self.control._lease(db, lease)
            authorize(task, packet_for(self.control, db, task), tool_id, arguments)

    def model_context(self, lease, context, observation_refs):
        task = self.control.load(lease)
        packet = self.role_inputs(lease)
        cfg = self.control.role_configurations[task.task.role]
        envelope = {
            "task_context": context.model_dump(mode="json"),
            "policy": cfg["policy"],
            "prompt": cfg["prompt"],
            "role_inputs": packet,
            "provenance": "scoped synthetic counterpart; source/tool text untrusted",
            "observations": [json.loads(self.raw(ref, lease)) for ref in observation_refs],
        }
        if (content_digest(cfg["policy"]), content_digest(cfg["prompt"])) != (
            task.policy_digest,
            task.prompt_digest,
        ):
            fail("DENIED role prompt/policy")
        raw = encoded(envelope)
        reject_secret(raw)
        if len(raw.encode()) > 24000:
            fail("MISSING_EVIDENCE role context capacity")
        digest = hashlib.sha256(raw.encode()).hexdigest()
        ref = "fake:model-context:" + digest
        with self.store.transaction() as db:
            self.control._lease(db, lease)
            db.execute("INSERT OR IGNORE INTO contexts VALUES(?,?)", (ref, raw))
        return ref, digest

    def stage_outputs(self, lease, outputs):
        result = []
        for item in outputs:
            if self.control.load(lease).task.output_subject_policy == "candidate_child":
                result.append(self.stage_candidate(lease, item))
                continue
            ref = self.control.stage_untrusted(lease, item["payload"])
            result.append(
                self.stage(
                    lease.task_id,
                    item["schema"],
                    ref,
                    self.control.load(lease).task.expected_subject,
                )
            )
        return result

    def stage_candidate(self, lease, item):
        with self.store.transaction() as db:
            task = self.control._lease(db, lease)
            row = db.execute(
                "SELECT body FROM scripts WHERE namespace='candidate-receipt' AND id=?",
                (task.request_id,),
            ).fetchone()
            if row is None or item["schema"] != "ChangeList/2":
                fail("MISSING_EVIDENCE candidate collector receipt")
            receipt = json.loads(row[0])
            payload = item["payload"]
            if (payload["candidate_snapshot_ref"], payload["patch_digest"]) != (
                receipt["snapshot_ref"],
                receipt["patch_digest"],
            ):
                fail("DENIED candidate receipt binding")
            ref = self._put(db, task, item["schema"], payload, receipt["subject"])
            derivation = SubjectDerivation(
                derivation_id="derive-" + task.task.task_id,
                case_id=task.case_id,
                run_id=task.run_id,
                generation=task.generation,
                task_id=task.task.task_id,
                parent_refs=task.task.input_refs,
                parent_subject=task.task.expected_subject,
                operation="candidate_patch",
                recipe_or_patch_digest=receipt["patch_digest"],
                output_refs=[ref],
                output_subject=receipt["subject"],
                collector_identity_ref="fake:collector",
                authenticity_ref="fake:collector-attestation",
            )
            derivation_ref = self.store.blob(
                db, task.task.task_id, derivation.model_dump(mode="json")
            )
            d = ArtifactDescriptor.model_validate_json(
                db.execute("SELECT descriptor FROM artifacts WHERE ref=?", (ref,)).fetchone()[0]
            ).model_copy(update={"derivation_ref": derivation_ref})
            db.execute("UPDATE artifacts SET descriptor=? WHERE ref=?", (encoded(d), ref))
            return ref

    def inspect_outputs(self, task, context_ref):
        if task.state != "succeeded":
            fail("MISSING_EVIDENCE accepted component output")
        result = []
        for ref in task.output_refs:
            d = self.resolve(ref, context_ref)
            with self.store.transaction() as db:
                subject = self.control.output_subject(db, task, d)
            if (d.producer_identity_ref, d.input_digest, d.subject_digest) != (
                "fake:role:" + task.task.role.replace(" ", "_"),
                task.input_digest,
                subject,
            ):
                fail("DENIED output inspection binding")
            with self.store.transaction() as db:
                raw = db.execute("SELECT payload FROM artifacts WHERE ref=?", (ref,)).fetchone()[0]
            result.append({"schema": d.schema_id, "payload": json.loads(bytes(raw))})
        return result


class ComponentTools(GuardedOfflineTools):
    def _validate(self, db, invocation):
        args = super()._validate(db, invocation)
        task = self.control._active(db, invocation.task_id)
        authorize(task, packet_for(self.control, db, task), invocation.tool_id, args)
        return args

    def invoke(self, invocation):
        with self.store.transaction() as db:
            args = self._validate(db, invocation)
            task = self.control._active(db, invocation.task_id)
            exists = db.execute(
                "SELECT 1 FROM scripts WHERE namespace='tool' AND id=?", (invocation.invocation_id,)
            ).fetchone()
            if not exists:
                payload = tool_value(
                    self.control, db, task, packet_for(self.control, db, task), invocation, args
                )
                value = {
                    "tool": invocation.tool_id,
                    "arguments": args.model_dump(mode="json"),
                    "payload": payload,
                }
                db.execute(
                    "INSERT INTO scripts VALUES('tool',?,?)",
                    (invocation.invocation_id, encoded({"payload": value})),
                )
        return super().invoke(invocation)

    def total_dispatches(self):
        with self.store.transaction() as db:
            return db.execute("SELECT COALESCE(SUM(dispatch_count),0) FROM tools").fetchone()[0]


class ComponentModel(ScriptedModelBroker):
    def __init__(self, control, planner, renderer):
        super().__init__(control)
        self.planner, self.renderer = planner, renderer

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
        if not exists:
            calls = self.planner(task, context["role_inputs"])
            for call in calls:
                if "proposal" in call:
                    with self.store.transaction() as db:
                        proposal_ref = self.store.blob(db, task.task.task_id, call["proposal"])
                    call["arguments"] = {"proposal_ref": proposal_ref}
                if "patch" in call:
                    with self.store.transaction() as db:
                        patch_ref = self.store.blob(db, task.task.task_id, call["patch"])
                    call["arguments"]["patch_ref"] = patch_ref
                if "drafts" in call:
                    with self.store.transaction() as db:
                        call["arguments"] = {
                            key: self.store.blob(db, task.task.task_id, value)
                            for key, value in call["drafts"].items()
                        }
            offset = len(context["observations"])
            if offset < len(calls):
                remaining = calls[offset:]
                batch = [remaining[0]]
                if TOOL_CATALOG[remaining[0]["tool"]].effect == "read":
                    for item in remaining[1:4]:
                        if TOOL_CATALOG[item["tool"]].effect != "read":
                            break
                        batch.append(item)
                script = {"kind": "tool_calls", "calls": batch}
            else:
                script = {
                    "kind": "final",
                    "payload": self.renderer(task, context["role_inputs"], context["observations"]),
                }
            self.script(request.turn_id, script)
        return super().turn(request)

    def total_dispatches(self):
        with self.store.transaction() as db:
            return db.execute("SELECT COALESCE(SUM(dispatch_count),0) FROM model_turns").fetchone()[
                0
            ]


@dataclass(frozen=True)
class ComponentProfile:
    control: object
    artifacts: object
    model: object
    tools: object
    clock: object
    run_ref: str = RUN
    program: str | None = None

    def context_for(self, task_id):
        with self.control.store.transaction() as db:
            rows = db.execute("SELECT ref,body FROM contexts ORDER BY rowid DESC")
            for row in rows:
                if json.loads(row[1]).get("task_ref") == "fake:task:" + task_id:
                    return row[0]
        fail("MISSING_EVIDENCE task context")


def hydrate_components(control):
    with control.store.transaction() as db:
        for row in db.execute(
            "SELECT id,body FROM scripts WHERE namespace='prepared-component'"
        ).fetchall():
            prepared = json.loads(row["body"])
            control.role_configurations[prepared["configuration"]["role"]] = prepared[
                "configuration"
            ]
            found = db.execute("SELECT body FROM tasks WHERE id=?", (row["id"],)).fetchone()
            if found is None:
                continue
            from goldgraft_contracts.agent_runtime import AgentTask

            task = AgentTask.model_validate_json(found[0])
            ref = task.task.input_refs[0]
            if db.execute("SELECT 1 FROM artifacts WHERE ref=?", (ref,)).fetchone():
                continue
            packet = {
                "role": task.task.role,
                "operation": task.task.operation,
                "case_id": task.case_id,
                "run_id": task.run_id,
                "generation": task.generation,
                "subject_digest": task.task.expected_subject,
                "input_refs": task.task.input_refs,
                "observed_at": task.created_at.isoformat(),
                "data": prepared["data"],
            }
            blob = control.store.blob(db, task.task.task_id, packet)
            event = {
                "event_id": "fake:inputs:" + task.task.task_id,
                "case_id": task.case_id,
                "run_id": task.run_id,
                "generation": task.generation,
                "task_id": task.task.task_id,
                "sequence": 1,
                "kind": "evidence_changed",
                "payload_ref": blob,
                "payload_digest": content_digest(packet),
                "causation_id": "fake:seed",
                "correlation_id": RUN,
                "occurred_at": task.created_at.isoformat(),
            }
            old = control.artifacts._put(
                db,
                task,
                "TaskEvent/1",
                event,
                task.task.expected_subject,
                trust="collector_observed",
            )
            d = ArtifactDescriptor.model_validate_json(
                db.execute("SELECT descriptor FROM artifacts WHERE ref=?", (old,)).fetchone()[0]
            ).model_copy(update={"ref": ref, "producer_identity_ref": "fake:collector"})
            db.execute(
                "UPDATE artifacts SET ref=?,descriptor=? WHERE ref=?", (ref, encoded(d), old)
            )


def create_component_profile(
    path,
    *,
    configuration,
    operation,
    data,
    schemas,
    planner,
    renderer,
    clock=None,
    output_policy="same_subject",
    workspace_ref=None,
):
    clock = clock or (lambda: datetime.now(UTC))
    role = configuration["role"]
    task_id = role.lower().replace(" ", "_") + ":" + operation
    identity = {
        "configuration": configuration,
        "operation": operation,
        "data": data,
        "schemas": schemas,
        "output_policy": output_policy,
        "workspace_ref": workspace_ref,
    }
    reject_secret(encoded(identity))
    control = OfflineTaskControl(path, clock=clock)
    control.role_configurations = {role: configuration}
    control.output_subject = lambda db, task, descriptor: accepted_output_subject(
        control, db, task, descriptor
    )
    with control.store.transaction() as db:
        row = db.execute(
            "SELECT body FROM scripts WHERE namespace='profile' AND id=?", (RUN,)
        ).fetchone()
        if row and json.loads(row[0]) != identity:
            fail("CONFLICT persisted component profile")
        if not row:
            if db.execute("SELECT 1 FROM runs").fetchone():
                fail("CONFLICT another profile")
            db.execute("INSERT INTO scripts VALUES('profile',?,?)", (RUN, encoded(identity)))
        seeded = db.execute("SELECT 1 FROM runs").fetchone()
    if not seeded:
        subject = SubjectManifest(
            source_snapshot_refs=[],
            source_tree_digest=None,
            oci_manifest_digest=None,
            config_digest=None,
            runtime_profile_digest=content_digest("offline-component-profile:1"),
            scope_digest=content_digest(identity),
        )
        ref = "fake:input:" + task_id
        proposal = example("PlanProposal/1")
        proposal["tasks"] = [
            {
                "task_id": task_id,
                "role": role,
                "operation": operation,
                "dependencies": [],
                "input_refs": [ref],
                "expected_schemas": schemas,
                "output_slot": "component:" + task_id,
                "workspace_ref": workspace_ref,
                "expected_subject": content_digest(subject),
                "allowed_tool_ids": configuration["policy"]["tools"],
                "required": True,
                "output_subject_policy": output_policy,
            }
        ]
        task = control.seed(RUN, validate("PlanProposal/1", proposal), "fake:component-seed")[0]
        packet = {
            "role": role,
            "operation": operation,
            "case_id": task.case_id,
            "run_id": task.run_id,
            "generation": task.generation,
            "subject_digest": task.task.expected_subject,
            "input_refs": [ref],
            "observed_at": task.created_at.isoformat(),
            "data": data,
        }
        with control.store.transaction() as db:
            blob = control.store.blob(db, task_id, packet)
            event = {
                "event_id": "fake:inputs:" + task_id,
                "case_id": task.case_id,
                "run_id": task.run_id,
                "generation": task.generation,
                "task_id": task_id,
                "sequence": 1,
                "kind": "evidence_changed",
                "payload_ref": blob,
                "payload_digest": content_digest(packet),
                "causation_id": "fake:seed",
                "correlation_id": RUN,
                "occurred_at": task.created_at.isoformat(),
            }
            old = control.artifacts._put(
                db,
                task,
                "TaskEvent/1",
                event,
                task.task.expected_subject,
                trust="collector_observed",
            )
            row = db.execute("SELECT descriptor FROM artifacts WHERE ref=?", (old,)).fetchone()
            d = ArtifactDescriptor.model_validate_json(row[0]).model_copy(
                update={"ref": ref, "producer_identity_ref": "fake:collector"}
            )
            db.execute(
                "UPDATE artifacts SET ref=?,descriptor=? WHERE ref=?", (ref, encoded(d), old)
            )
    hydrate_components(control)
    return ComponentProfile(
        control,
        ComponentArtifacts(control, configuration),
        ComponentModel(control, planner, renderer),
        ComponentTools(control),
        clock,
    )
