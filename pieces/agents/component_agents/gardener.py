"""Bounded plan advice; only the deterministic admission policy can dispatch it."""

from goldgraft_contracts.agent_runtime import PlanProposal, TaskSpec
from goldgraft_contracts.plan5_common import Count, Id, P5Record, Positive, Role, validate_dag
from pydantic import Field, StrictBool


class Input(P5Record):
    accepted: StrictBool
    baseline_verified: StrictBool
    max_tasks: Positive = Field(le=32)
    budget_micro_usd: Count
    required_task_ids: list[Id] = Field(min_length=1, max_length=32)
    allowed_roles: list[Role] = Field(min_length=1, max_length=13)


def admit(task, data):
    if not data.accepted or not data.baseline_verified:
        raise ValueError("MISSING_EVIDENCE accepted/verified work")
    if data.budget_micro_usd != 0:
        raise ValueError("DENIED unqualified paid plan")


def route(data):
    """Pick the model before dispatch from plan size, never after a failure.

    Measured 11 Nov: a 6-node plan used 1,499 of Haiku's 1,536 output tokens and a
    9-node plan was truncated twice; Sonnet's 4,000-token cap carries the larger plans.
    """
    return "haiku" if len(data.required_task_ids) <= 5 else "sonnet"


def schemas(operation, data):
    return ["PlanProposal/1"]


def requests(task, data):
    return [{"tool": "status.read", "arguments": {"run_ref": "fake:runtime-run"}}]


def facts(task, data):
    """Scoped ids and the only admissible node shape; never the plan itself."""
    return {
        "run_ref": "fake:runtime-run",
        "parent_request_id": task.request_id,
        "case_id": task.case_id,
        "run_id": task.run_id,
        "generation": task.generation,
        "input_refs": list(task.task.input_refs),
        "expected_subject": task.task.expected_subject,
        "committed_next_stage": {
            "role": "Surveyor",
            "operation": "survey",
            "expected_schemas": ["RootMap/1"],
            "allowed_tool_ids": ["source.read"],
            "output_subject_policy": "same_subject",
            "workspace_ref": None,
        },
        "call_policy": "Call status.read once, then submit PlanProposal/1. Only the "
        "committed next stage (Surveyor survey) is admissible now, even if other roles are "
        "allowed later: later stages need committed predecessor refs. One node per "
        "required task id, required=true, input_refs and expected_subject exactly as above, "
        "a distinct output_slot per node, no dependency cycles, at most max_tasks nodes, "
        "no extra stages. reason_refs = input_refs. Hold (report_hold) if required ids "
        "exceed max_tasks.",
    }


def synthesize(task, data, packet, observations):
    nodes = [
        TaskSpec(
            task_id=task_id,
            role="Surveyor",
            operation="survey",
            dependencies=[],
            input_refs=list(task.task.input_refs),
            expected_schemas=["RootMap/1"],
            output_slot="planned.inventory"
            if len(data.required_task_ids) == 1
            else "planned.inventory." + task_id,
            workspace_ref=None,
            expected_subject=task.task.expected_subject,
            allowed_tool_ids=["source.read"],
            required=True,
            output_subject_policy="same_subject",
        )
        for task_id in data.required_task_ids
    ]
    proposal = PlanProposal(
        case_id=task.case_id,
        run_id=task.run_id,
        generation=task.generation,
        parent_request_id=task.request_id,
        tasks=nodes,
        reason_refs=list(task.task.input_refs),
    )
    return [{"schema": "PlanProposal/1", "payload": proposal.model_dump(mode="json")}]


def validate_proposal(task, data, proposal):
    parsed = PlanProposal.model_validate(proposal)
    if (parsed.case_id, parsed.run_id, parsed.generation, parsed.parent_request_id) != (
        task.case_id,
        task.run_id,
        task.generation,
        task.request_id,
    ):
        raise ValueError("DENIED plan scope")
    validate_dag(parsed.tasks, "task_id", "dependencies", maximum=data.max_tasks)
    if {t.task_id for t in parsed.tasks if t.required} != set(data.required_task_ids):
        raise ValueError("MISSING_EVIDENCE required tasks weakened")
    for node in parsed.tasks:
        if node.role not in data.allowed_roles or node.input_refs != task.task.input_refs:
            raise ValueError("DENIED unknown role or future input ref")
        if node.expected_subject != task.task.expected_subject or node.workspace_ref is not None:
            raise ValueError("DENIED guessed subject/workspace")
        if node.role != "Surveyor" or node.operation != "survey":
            raise ValueError("MISSING_EVIDENCE next stage not yet committed")
    return parsed


def review(task, data, packet, outputs, observations):
    validate_proposal(task, data, outputs[0]["payload"])


def inspect(outputs):
    plan = PlanProposal.model_validate(outputs[0]["payload"])
    return {
        "proposed_tasks": [
            {"id": t.task_id, "role": t.role, "dependencies": t.dependencies} for t in plan.tasks
        ],
        "dispatch_authority": "NONE",
        "future_stages": "Admit only after exact predecessor refs are committed.",
    }


def sample(operation):
    return {
        "accepted": True,
        "baseline_verified": True,
        "max_tasks": 32,
        "budget_micro_usd": 0,
        "required_task_ids": ["planned-survey"],
        "allowed_roles": ["Surveyor"],
    }
