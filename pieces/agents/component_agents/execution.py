"""Own bounded execution-proposal helpers; runner receipts remain external evidence."""

from goldgraft_contracts.agent_runtime import ExecutionProposal
from goldgraft_contracts.plan5_common import Digest, Id, P5Record, Ref
from pydantic import Field, StrictBool


class Catalog(P5Record):
    ref: Ref
    fingerprint: Id
    recipe_ref: Ref
    package: Id
    version: Id
    topic: Id
    qualified_fixture: StrictBool
    installed_symbols: list[Id] = Field(max_length=32)


class ExecutionInput(P5Record):
    subject_ref: Ref
    catalog: Catalog
    source_tree_digest: Digest
    execution_state: str = Field(pattern=r"^(observed|unknown|failed)$")
    execution_result: dict


def admission(data):
    if not data.catalog.qualified_fixture:
        raise ValueError("MISSING_EVIDENCE qualified recipe fixture")


def proposal(task, data, outputs, *, scenario=None, variant=None):
    return ExecutionProposal(
        task_id=task.task.task_id,
        operation=task.task.operation,
        subject_ref=data.subject_ref,
        recipe_ref=data.catalog.recipe_ref,
        scenario_ref=scenario,
        variant=variant,
        requested_output_schemas=outputs,
        expected_subject=task.task.expected_subject,
        evidence_refs=task.task.input_refs,
    ).model_dump(mode="json")


# The model sends the proposal inline; the gateway validates and stages it task-scoped.
INLINE = {"execution.request": {"proposal_ref": ("proposal", "ExecutionProposal/1")}}


def same_proposal(payload, expected):
    """Semantic equality after contract normalization (omitted nulls, key order)."""
    try:
        return ExecutionProposal.model_validate(payload).model_dump(mode="json") == expected
    except (ValueError, TypeError):
        return False


def execution_facts(task, outputs, extra_policy=""):
    return {
        "request_id": task.request_id,
        "task_id": task.task.task_id,
        "operation": task.task.operation,
        "expected_subject": task.task.expected_subject,
        "evidence_refs": list(task.task.input_refs),
        "requested_output_schemas": outputs,
        "receipt_rule": "Accept the execution.status receipt only if state is 'observed', "
        "synthetic_only is true, subject equals expected_subject and request_id equals "
        "request_id" + extra_policy + "; otherwise call report_hold (MISSING_EVIDENCE). "
        "Never write or alter observed results yourself.",
    }


def execution_calls(task, value):
    return [
        dict(
            tool="execution.request", arguments={"proposal_ref": "inline:proposal"}, proposal=value
        ),
        dict(tool="execution.status", arguments={"request_id": task.request_id}),
    ]


def receipt(task, observations):
    result = observations[-1]["value"]["payload"]
    if (
        result.get("state"),
        result.get("subject"),
        result.get("request_id"),
        result.get("synthetic_only"),
    ) != ("observed", task.task.expected_subject, task.request_id, True):
        raise ValueError("MISSING_EVIDENCE observed exact execution; reconcile original request")
    return result["result"]


def catalog_sample():
    return dict(
        ref="fixture:catalog",
        fingerprint="fixture-php",
        recipe_ref="fixture:recipe",
        package="fixture-sdk",
        version="1",
        topic="orders",
        qualified_fixture=True,
        installed_symbols=["create_order", "capture_order"],
    )
