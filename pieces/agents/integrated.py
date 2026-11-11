"""Integrated thirteen-role run policy (Plan5 phase 1 of the 12 Nov integration plan).

One run, two linked durable stores, every edge carried by a committed predecessor output:

  Store A (existing Surveyor→Herald collaboration graph):
      Surveyor (survey the submitted source) → Herald (grounded summary of that inventory)
  Store B (this module, over the existing component profile):
      Gardener admits the survey stage ─(admission checked here)→ Store A runs
      → Builder baseline of the *surveyed* source (root_map_ref + source digest from Surveyor)
      → the existing component chain (workflow.STAGES): Explorer OLD/OLD_TWIN → Scribe draft
        → Explorer followup → Scribe final → Architect → Grafter → Builder NEW → Explorer NEW
        → Adversary guards → Adversary mutant
      side branches on the same run: Healer (controlled go-live fault on the NEW capture),
      Sentinel (this run's audit events + one controlled hostile event), Librarian (the
      finished candidate, under the stated consent), Orchard Analyst (aggregate of finished runs).

Runner, recorder, collector and mutation tools stay the existing labelled counterparts
("scripted runner"); model calls are whatever ModelPort the driver binds. This module never
calls a model, a provider or the network; it only decides which task is next and with what data.
"""

from goldgraft_contracts.agent_runtime import PlanProposal
from goldgraft_contracts.plan5_common import content_digest

from .component import implementation
from .component_cli import create as create_component
from .roles import component_configuration
from .workflow import BASE, STAGES, candidate, committed, execution, payload
from .workflow import stage_data as chain_data

GARDENER = "gardener:propose_plan"
SURVEY = "survey"
CHAIN = ((BASE, "Builder", "build_baseline", (GARDENER,)),) + STAGES
SIDE = (
    ("healer-golive", "Healer", "diagnose", ("candidate-new",)),
    ("sentinel-audit", "Sentinel", "audit", ("adversary-mutant",)),
    ("librarian-recipe", "Librarian", "learn", ("adversary-mutant",)),
    ("orchard-aggregate", "Orchard Analyst", "aggregate", ("librarian-recipe",)),
)
ALL_STAGES = CHAIN + SIDE
# Roles that take part, in lifecycle order (Surveyor and Herald run in the linked Store A).
ROLES = (
    "Gardener",
    "Surveyor",
    "Herald",
    "Builder",
    "Explorer",
    "Scribe",
    "Architect",
    "Grafter",
    "Adversary",
    "Healer",
    "Sentinel",
    "Librarian",
    "Orchard Analyst",
)


def gardener_input():
    """Intake accepted and the source package verified (digest-bound) before any plan."""
    return {
        "accepted": True,
        "baseline_verified": True,
        "max_tasks": 32,
        "budget_micro_usd": 0,
        "required_task_ids": [SURVEY],
        "allowed_roles": ["Surveyor"],
    }


def create(path, *, clock=None):
    from dataclasses import replace

    p = create_component("Gardener", path, data=gardener_input(), clock=clock)
    return replace(p, program="integrated")


def admitted_survey(p):
    """The Gardener's committed plan must admit exactly the survey stage before Store A runs."""
    t, _, _ = committed(p, GARDENER)
    if t.state != "succeeded":
        raise ValueError("MISSING_EVIDENCE committed Gardener plan")
    plan = PlanProposal.model_validate(payload(p, GARDENER, "PlanProposal/1"))
    nodes = [n for n in plan.tasks if n.required]
    if [(n.task_id, n.role, n.operation) for n in nodes] != [(SURVEY, "Surveyor", "survey")]:
        raise ValueError("DENIED plan does not admit exactly the survey stage")
    return {"plan_ref": t.output_refs[0], "node": nodes[0].model_dump(mode="json")}


def _side_data(p, task_id, role, operation, run):
    data = implementation(role).sample(operation)
    if task_id == "healer-golive":
        # Controlled go-live fault on the actual NEW capture; the observation says it is synthetic.
        ref = committed(p, "candidate-new")[0].output_refs[0]
        data["evidence"] = {ref: {"new_economic_state": True, "legacy_restore_safe": False}}
        data["synthetic_observation"] = True
    elif task_id == "sentinel-audit":
        snapshot = p.control.snapshot(p.run_ref)
        head = next(t for t in snapshot.tasks if t.task.task_id == GARDENER)
        events = []
        for t in snapshot.tasks:
            if t.state in {"rejected", "held", "failed"}:
                events.append(("denied_tool", t.task.task_id))
        # One controlled hostile event: the submitted source asked an agent for a secret.
        events.append(("secret_attempt", run.get("hostile_fingerprint_seed", "controlled-hostile")))
        data["after_seq"] = 0
        data["events"] = [
            {
                "sequence": i + 1,
                "case_id": head.case_id,
                "run_id": head.run_id,
                "generation": head.generation,
                "kind": kind,
                "fingerprint": content_digest([kind, seed]),
            }
            for i, (kind, seed) in enumerate(events[:32])
        ]
    elif task_id == "librarian-recipe":
        c = candidate(p)
        data["source_tree_digest"] = c["tree"]
        data["origin_fixture_ref"] = c["snapshot_ref"]
        data["completed"] = True
        # Stated assumption (12 Nov): the MIT-licensed synthetic sample shop is rights-cleared.
        data["learning_consent"] = bool(run.get("learning_consent", True))
        data["source_rights"] = bool(run.get("source_rights", True))
    elif task_id == "orchard-aggregate":
        buckets = run.get("fleet_buckets")
        if buckets:
            data["buckets"] = buckets
    return data


def stage_data(p, task_id, role, operation, run):
    if task_id == BASE:
        survey = run["survey"]
        data = implementation("Builder").sample("build_baseline")
        # Build exactly what the Surveyor mapped: its committed RootMap and the source digest.
        data["root_map_ref"] = survey["output_ref"]
        data["source_tree_digest"] = survey["source_digest"]
        data["execution_result"]["source_tree_digest"] = survey["source_digest"]
        return data
    if any(task_id == s[0] for s in STAGES):
        return chain_data(p, task_id, role, operation)
    return _side_data(p, task_id, role, operation, run)


# Model routing (lower tasks Haiku, higher tasks Sonnet). Each role's existing route() picks the
# qualified profile; a role+operation shape with two terminal, attributable Haiku failures starts
# on Sonnet next time. Holds by design, denials, missing data, budget and unknowns never escalate.
MODEL_FAILURES = frozenset({"INVALID_MODEL_OUTPUT", "TURN_LIMIT", "INVALID", "TOOL_LIMIT"})


def route(role, operation, data, routing):
    module = implementation(role)
    name = module.route(module.Input.model_validate(data)) if hasattr(module, "route") else "haiku"
    shape = f"{role}:{operation}"
    escalated = name != "sonnet" and routing.get(shape, {}).get("haiku_failures", 0) >= 2
    return ("sonnet" if escalated else name), escalated


def record_failure(routing, role, operation, profile, issue_code):
    """Count only named model failures; return True when the shape now routes to Sonnet."""
    shape = f"{role}:{operation}"
    entry = routing.setdefault(shape, {"haiku_failures": 0, "sonnet_failures": 0, "codes": []})
    if issue_code not in MODEL_FAILURES:
        return False
    entry["haiku_failures" if profile != "sonnet" else "sonnet_failures"] += 1
    entry["codes"].append(issue_code)
    return profile != "sonnet" and entry["haiku_failures"] >= 2


class WithRun:
    """Ports plus this run's linked facts (survey result, consent, fleet), read by advance()."""

    def __init__(self, ports, run):
        self._ports, self.integrated_run = ports, run

    def __getattr__(self, name):
        return getattr(self._ports, name)


def advance(run_ref, p):
    """Append the next admissible task. Waits for the linked survey before the baseline."""
    snapshot = p.control.snapshot(run_ref)
    if snapshot.cancellation_ref is not None:
        return None
    tasks = {t.task.task_id: t for t in snapshot.tasks}
    run = getattr(p, "integrated_run", None) or {}
    for task_id, role, operation, deps in ALL_STAGES:
        if task_id in tasks:
            continue
        if not all(d in tasks and tasks[d].state == "succeeded" for d in deps):
            continue
        if task_id == BASE:
            survey = run.get("survey")
            if not survey or not survey.get("accepted"):
                return None  # Store A has not produced an accepted inventory yet
        data = stage_data(p, task_id, role, operation, run)
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
        return task_id
    return None


def edges(p):
    """Per-edge evidence: each task's input refs against its predecessors' committed outputs."""
    snapshot = p.control.snapshot(p.run_ref)
    tasks = {t.task.task_id: t for t in snapshot.tasks}
    out = []
    for t in snapshot.tasks:
        preds = [d for d in t.task.dependencies if d in tasks]
        produced = [r for d in preds for r in tasks[d].output_refs]
        out.append(
            {
                "task": t.task.task_id,
                "role": t.task.role,
                "state": t.state,
                "dependencies": list(t.task.dependencies),
                "input_refs": list(t.task.input_refs),
                "predecessor_outputs_consumed": [r for r in t.task.input_refs if r in produced],
                "output_refs": list(t.output_refs),
            }
        )
    return out


__all__ = [
    "ALL_STAGES",
    "BASE",
    "GARDENER",
    "ROLES",
    "SURVEY",
    "WithRun",
    "admitted_survey",
    "advance",
    "create",
    "edges",
    "execution",
    "record_failure",
    "route",
    "stage_data",
]
