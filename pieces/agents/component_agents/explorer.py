"""Exact-variant scenario requests; missing capture cannot become proof."""

from typing import Literal

from goldgraft_contracts.plan5_common import Ref, content_digest
from pydantic import StrictBool

from .execution import (
    INLINE,  # noqa: F401  (role-declared inline staging, read by the gateway)
    ExecutionInput,
    admission,
    catalog_sample,
    execution_calls,
    execution_facts,
    proposal,
    receipt,
    same_proposal,
)


class Input(ExecutionInput):
    scenario_ref: Ref
    variant: Literal["OLD", "OLD_TWIN", "NEW"]
    driver_ref: Ref
    final_contract_ref: Ref | None = None
    required_flow: str
    driver_valid: StrictBool


def admit(task, data):
    admission(data)
    if not data.driver_valid or not data.required_flow:
        raise ValueError("MISSING_EVIDENCE approved driver/required flow")
    if data.variant == "NEW" and data.final_contract_ref is None:
        raise ValueError("MISSING_EVIDENCE candidate final Contract")


def schemas(operation, data):
    return ["ExecutionProposal/1"]


def draft(task, data):
    return proposal(task, data, ["RawCapture/1"], scenario=data.scenario_ref, variant=data.variant)


def route(data):
    return "haiku8"  # 3 calls + submit; one turn of slack on the 4-turn profile is too thin


def facts(task, data):
    facts = execution_facts(
        task,
        ["RawCapture/1"],
        ", result.variant equals variant, result.flow equals required_flow, "
        "result.capture_ref names that same variant, result.source_tree_digest equals "
        "source_tree_digest, result.recorder is 'fixture:recorder' and result.complete is "
        "true",
    )
    facts["call_policy"] = (
        "1) execution.request alone, with proposal = ExecutionProposal/1 {task_id, "
        "operation, subject_ref: subject_ref, recipe_ref: catalog.recipe_ref, scenario_ref: "
        "scenario_ref, variant: variant, requested_output_schemas: ['RawCapture/1'], "
        "expected_subject, evidence_refs}. 2) execution.status(request_id). 3) If the "
        "receipt passes receipt_rule, submit that same proposal; else report_hold. A "
        "missing or partial capture is never proof."
    )
    return facts


def requests(task, data):
    return execution_calls(task, draft(task, data))


def synthesize(task, data, packet, observations):
    return [dict(schema="ExecutionProposal/1", payload=draft(task, data))]


def review(task, data, packet, outputs, observations):
    if not same_proposal(outputs[0]["payload"], draft(task, data)):
        raise ValueError("DENIED scenario proposal mutation")
    result = receipt(task, observations)
    if (
        result.get("capture_ref"),
        result.get("variant"),
        result.get("flow"),
        result.get("source_tree_digest"),
    ) != (
        "fixture:capture:" + data.variant,
        data.variant,
        data.required_flow,
        data.source_tree_digest,
    ):
        raise ValueError("MISSING_EVIDENCE exact capture/flow/subject")
    if result.get("recorder") != "fixture:recorder" or result.get("complete") is not True:
        raise ValueError("MISSING_EVIDENCE recorder capture completeness")


def inspect(outputs):
    p = outputs[0]["payload"]
    return dict(
        scenario=p["scenario_ref"],
        variant=p["variant"],
        capture_owner="recorder",
        money_mapping_owner="SH",
        proof="NOT EVALUATED; synthetic capture only",
    )


def sample(operation):
    return dict(
        subject_ref="fixture:baseline",
        catalog=catalog_sample(),
        source_tree_digest=content_digest("fixture-source"),
        execution_state="observed",
        execution_result=dict(
            capture_ref="fixture:capture:OLD",
            variant="OLD",
            flow="capture",
            source_tree_digest=content_digest("fixture-source"),
            recorder="fixture:recorder",
            complete=True,
        ),
        scenario_ref="fixture:scenario-capture",
        variant="OLD",
        driver_ref="fixture:driver",
        final_contract_ref=None,
        required_flow="capture",
        driver_valid=True,
    )
