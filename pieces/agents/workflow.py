"""Incremental offline B4 dependency policy over the existing scheduler and ports.

Synthetic input/runner/mapping counterparts remain explicit. This is not a GU
service implementation, SH proof engine, VJ recipe implementation or new scheduler.
"""

from dataclasses import replace

from goldgraft_contracts.plan5_common import content_digest

from .component import implementation
from .component_cli import create as create_component
from .roles import component_configuration

BASE = "builder:build_baseline"
STAGES = (
    ("baseline-old", "Explorer", "run_scenario", (BASE,)),
    ("baseline-old-twin", "Explorer", "run_scenario", (BASE,)),
    ("scribe-draft", "Scribe", "scribe_draft", ("baseline-old", "baseline-old-twin")),
    ("followup-0", "Explorer", "run_scenario", ("scribe-draft", BASE)),
    ("scribe-final", "Scribe", "scribe_final", ("scribe-draft", "followup-0")),
    ("architect", "Architect", "architect", ("scribe-final",)),
    ("grafter", "Grafter", "candidate_patch", ("architect",)),
    ("candidate-build", "Builder", "build_candidate", ("grafter",)),
    ("candidate-new", "Explorer", "run_scenario", ("candidate-build", "scribe-final")),
    ("adversary-guards", "Adversary", "derive_guards", ("candidate-build", "scribe-final")),
    ("adversary-mutant", "Adversary", "run_mutant", ("adversary-guards", "candidate-build")),
)


def create(path, *, clock=None):
    return replace(create_component("Builder", path, clock=clock), program="component_workflow")


def committed(p, task_id):
    return p.artifacts.committed(task_id)


def payload(p, task_id, schema):
    _, outputs, _ = committed(p, task_id)
    found = [o["payload"] for o in outputs if o["schema"] == schema]
    if len(found) != 1:
        raise ValueError("MISSING_EVIDENCE exact predecessor schema")
    return found[0]


def execution(p, task_id):
    t, _, observations = committed(p, task_id)
    values = [
        o["value"]["payload"] for o in observations if o["value"]["tool"] == "execution.status"
    ]
    if (
        len(values) != 1
        or values[0]["state"] != "observed"
        or values[0]["subject"] != t.task.expected_subject
    ):
        raise ValueError("MISSING_EVIDENCE exact observed execution")
    return values[0]["result"]


def candidate(p, task_id="grafter"):
    _, _, observations = committed(p, task_id)
    receipts = [
        o["value"]["payload"] for o in observations if o["value"]["tool"] == "candidate.patch"
    ]
    if len(receipts) != 1:
        raise ValueError("MISSING_EVIDENCE candidate collector receipt")
    return receipts[0]


def stage_data(p, task_id, role, operation):
    data = implementation(role).sample(operation)
    if task_id in {"baseline-old", "baseline-old-twin", "followup-0", "candidate-new"}:
        variant = (
            "OLD_TWIN"
            if task_id == "baseline-old-twin"
            else "NEW"
            if task_id == "candidate-new"
            else "OLD"
        )
        data["variant"] = variant
        data["execution_result"]["variant"] = variant
        data["execution_result"]["capture_ref"] = "fixture:capture:" + variant
        build_id = "candidate-build" if variant == "NEW" else BASE
        build = execution(p, build_id)
        bt, _, _ = committed(p, build_id)
        data["subject_ref"] = payload(p, build_id, "ExecutionProposal/1")["subject_ref"]
        data["driver_ref"] = bt.output_refs[0]
        data["source_tree_digest"] = build["source_tree_digest"]
        data["execution_result"]["source_tree_digest"] = build["source_tree_digest"]
        if variant == "NEW":
            data["final_contract_ref"] = committed(p, "scribe-final")[0].output_refs[0]
        if task_id == "followup-0":
            _, drafts, _ = committed(p, "scribe-draft")
            triangles = [x for x in drafts if x["schema"] == "TriangleRequest/1"]
            if not 1 <= len(triangles) <= 4:
                raise ValueError("DENIED bounded Triangle followup")
            data["scenario_ref"] = "fixture:pending-rule-followup"
    elif task_id == "scribe-final":
        draft = payload(p, "scribe-draft", "Contract/1")
        capture = execution(p, "followup-0")
        if not capture.get("complete") or capture.get("recorder") != "fixture:recorder":
            raise ValueError("MISSING_EVIDENCE mapped followup input")
        # Explicit injected SH mapping counterpart; no CMEL/proof is model-authored.
        trace_ref = committed(p, "followup-0")[0].output_refs[0]
        data["normative_rules"] = draft["rules"]
        data["evidence"] = {
            trace_ref: {
                "mapper": "fixture:SH",
                "rule_id": draft["rules"][0]["id"],
                "variant": "OLD",
                "old_defect": True,
            }
        }
        data["trace_rules"] = {draft["rules"][0]["id"]: [trace_ref]}
        data["followups_used"] = 1
    elif task_id == "architect":
        data["contract"] = payload(p, "scribe-final", "Contract/1")
        data["evidence"] = {committed(p, "scribe-final")[0].output_refs[0]: {"final": True}}
    elif task_id == "grafter":
        data["target_plan"] = payload(p, "architect", "TargetPlan/1")
    elif task_id == "candidate-build":
        c = candidate(p)
        data["subject_ref"] = data["candidate_snapshot_ref"] = c["snapshot_ref"]
        data["source_tree_digest"] = c["tree"]
        data["execution_result"]["source_tree_digest"] = c["tree"]
        manifest = {"fixture": "offline-candidate", "tree": c["tree"]}
        data["execution_result"]["synthetic_manifest"] = manifest
        data["execution_result"]["image_digest"] = "sha256:" + content_digest(manifest)
    elif task_id in {"adversary-guards", "adversary-mutant"}:
        c = candidate(p)
        data["contract"] = payload(p, "scribe-final", "Contract/1")
        data["candidate_ref"] = c["snapshot_ref"]
        data["source_ref"] = c["snapshot_ref"]
        data["source_tree_digest"] = c["tree"]
        data["subject_ref"] = (
            c["snapshot_ref"] if task_id == "adversary-guards" else "fixture:fork:" + c["tree"]
        )
        if task_id == "adversary-mutant":
            data["fork_ref"] = data["subject_ref"]
            data["execution_result"]["fork_ref"] = data["fork_ref"]
    return data


def advance_repairs(p, tasks):
    for owner in [t for t in tasks.values() if t.task.task_id.startswith("repair-grafter-")]:
        n = owner.task.task_id.rsplit("-", 1)[1]
        build = "repair-build-" + n
        stages = [
            (build, "Builder", "build_candidate", (owner.task.task_id,), "candidate-build"),
            (
                "repair-new-" + n,
                "Explorer",
                "run_scenario",
                (build, "scribe-final"),
                "candidate-new",
            ),
            (
                "repair-guards-" + n,
                "Adversary",
                "derive_guards",
                (build, "scribe-final"),
                "adversary-guards",
            ),
            (
                "repair-mutant-" + n,
                "Adversary",
                "run_mutant",
                ("repair-guards-" + n, build),
                "adversary-mutant",
            ),
        ]
        for task_id, role, op, deps, template in stages:
            if task_id in tasks or not all(
                d in tasks and tasks[d].state == "succeeded" for d in deps
            ):
                continue
            data = stage_data(p, template, role, op)
            c = candidate(p, owner.task.task_id)
            data["source_tree_digest"] = c["tree"]
            if role == "Builder":
                data["subject_ref"] = data["candidate_snapshot_ref"] = c["snapshot_ref"]
                manifest = {"fixture": "offline-repair", "tree": c["tree"]}
                data["execution_result"].update(
                    source_tree_digest=c["tree"],
                    synthetic_manifest=manifest,
                    image_digest="sha256:" + content_digest(manifest),
                )
            elif role == "Explorer":
                data["subject_ref"] = c["snapshot_ref"]
                data["driver_ref"] = committed(p, build)[0].output_refs[0]
                data["execution_result"]["source_tree_digest"] = c["tree"]
            else:
                data["candidate_ref"] = data["source_ref"] = c["snapshot_ref"]
                data["files"] = p.artifacts.candidate_files(owner.task.task_id)
                data["subject_ref"] = (
                    c["snapshot_ref"] if op == "derive_guards" else "fixture:fork:" + c["tree"]
                )
                if op == "run_mutant":
                    data["fork_ref"] = data["subject_ref"]
                    data["execution_result"]["fork_ref"] = data["fork_ref"]
            module = implementation(role)
            typed = module.Input.model_validate(data)
            p.artifacts.append_task(
                task_id=task_id,
                configuration=component_configuration(role),
                operation=op,
                data=typed.model_dump(mode="json"),
                schemas=module.schemas(op, typed),
                dependencies=list(deps),
            )
            return True
    return False


def advance(run_ref, p):
    snapshot = p.control.snapshot(run_ref)
    if snapshot.cancellation_ref is not None:
        return
    tasks = {t.task.task_id: t for t in snapshot.tasks}
    if advance_repairs(p, tasks):
        return
    for task_id, role, operation, deps in STAGES:
        if task_id in tasks:
            continue
        if not all(d in tasks and tasks[d].state == "succeeded" for d in deps):
            continue
        data = stage_data(p, task_id, role, operation)
        module = implementation(role)
        typed = module.Input.model_validate(data)
        p.artifacts.append_task(
            task_id=task_id,
            configuration=component_configuration(role),
            operation=operation,
            data=typed.model_dump(mode="json"),
            schemas=module.schemas(operation, typed),
            dependencies=list(deps),
            output_policy="candidate_child" if role == "Grafter" else "same_subject",
            workspace_ref=data["workspace_ref"] if role == "Grafter" else None,
        )
        return


def inspect(p):
    snapshot = p.control.snapshot(p.run_ref)
    return {
        "evidence_class": "scripted",
        "model_api_calls": 0,
        "tasks": [
            dict(
                id=t.task.task_id,
                role=t.task.role,
                state=t.state,
                dependencies=t.task.dependencies,
                input_refs=t.task.input_refs,
                output_refs=t.output_refs,
                subject=t.task.expected_subject,
            )
            for t in snapshot.tasks
        ],
        "proof": "Independent SH evidence REQUIRED; no merchant review/apply authority",
        "real_model_evaluation": "NOT RUN",
    }
