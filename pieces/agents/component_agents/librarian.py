"""Consented, de-identified learning proposals; promotion is separate authority."""

from types import SimpleNamespace

from goldgraft_contracts.plan5_common import Ref, content_digest
from pydantic import StrictBool

from ..component import metadata
from .execution import ExecutionInput, admission, catalog_sample, execution_calls, proposal, receipt


class Input(ExecutionInput):
    learning_consent: StrictBool
    source_rights: StrictBool
    synthetic_certified_fixture: StrictBool
    completed: StrictBool
    tenant_id: str
    origin_fixture_ref: Ref
    independent_fixture_ref: Ref
    template_id: str
    deidentified: StrictBool


def admit(task, data):
    admission(data)
    if not all(
        [
            data.learning_consent,
            data.source_rights,
            data.synthetic_certified_fixture,
            data.completed,
            data.deidentified,
        ]
    ):
        raise ValueError("DENIED learning consent/rights/completion")
    if data.tenant_id != "offline" or data.template_id != "template:pending-capture-guard:1":
        raise ValueError("DENIED tenant/raw-source template")
    if task.task.operation == "selfcheck_recipe" and (
        data.independent_fixture_ref == data.origin_fixture_ref
        or data.subject_ref != data.independent_fixture_ref
    ):
        raise ValueError("DENIED selfcheck requires non-origin fixture")


def schemas(operation, data):
    return (
        ["ExecutionProposal/1"]
        if operation == "selfcheck_recipe"
        else ["Recipe/1", "DetectionRule/1"]
    )


def drafts(task, data):
    r = dict(
        id="quarantine-" + content_digest(data.template_id)[:16],
        fingerprint=dict(
            lang="php",
            framework="fixture",
            family="EC_NVP",
            ast_shape_hash=content_digest("pending-capture"),
        ),
        transform=data.template_id,
        env=None,
        scenarios=["guard-captured-before-paid"],
        provenance=task.task.input_refs,
        confidence=0,
        status="QUARANTINE",
        signature="UNSIGNED_SYNTHETIC_QUARANTINE",
    )
    d = {
        **metadata(task, SimpleNamespace(observed_at=task.created_at)),
        "language": "php",
        "pattern": "literal:legacy_capture",
        "operation": "capture",
        "evidence_refs": task.task.input_refs,
    }
    return [dict(schema="Recipe/1", payload=r), dict(schema="DetectionRule/1", payload=d)]


def draft_execution(task, data):
    return proposal(task, data, ["ProbeResult/1"])


def requests(task, data):
    if task.task.operation == "selfcheck_recipe":
        return execution_calls(task, draft_execution(task, data))
    values = drafts(task, data)
    return [
        dict(
            tool="recipe.stage",
            arguments={"recipe_ref": "inline:recipe", "detection_rule_ref": "inline:detection"},
            drafts={"recipe_ref": values[0]["payload"], "detection_rule_ref": values[1]["payload"]},
        )
    ]


def synthesize(task, data, packet, observations):
    return (
        [dict(schema="ExecutionProposal/1", payload=draft_execution(task, data))]
        if task.task.operation == "selfcheck_recipe"
        else drafts(task, data)
    )


def review(task, data, packet, outputs, observations):
    if outputs != synthesize(task, data, packet, observations):
        raise ValueError("DENIED raw reuse or self promotion")
    if task.task.operation == "selfcheck_recipe":
        result = receipt(task, observations)
        if (
            result.get("fixture_ref") != data.independent_fixture_ref
            or result.get("passed") is not True
        ):
            raise ValueError("MISSING_EVIDENCE independent selfcheck")
    else:
        result = observations[-1]["value"]["payload"]
        if (
            result.get("drafts") != {x["schema"]: x["payload"] for x in outputs}
            or result.get("active_promotion") is not False
        ):
            raise ValueError("DENIED quarantine stage")


def inspect(outputs):
    if outputs[0]["schema"] == "ExecutionProposal/1":
        return dict(
            independent_fixture=outputs[0]["payload"]["subject_ref"], promotion="NOT AUTHORISED"
        )
    return dict(
        recipe_id=outputs[0]["payload"]["id"],
        status="QUARANTINE",
        signature="UNSIGNED_SYNTHETIC_QUARANTINE",
        active_promotion=False,
        merchant_delivery_dependency=False,
    )


def sample(operation):
    return dict(
        subject_ref="fixture:independent"
        if operation == "selfcheck_recipe"
        else "fixture:deidentified-metadata",
        catalog=catalog_sample(),
        source_tree_digest=content_digest("deidentified"),
        execution_state="observed",
        execution_result=dict(fixture_ref="fixture:independent", passed=True),
        learning_consent=True,
        source_rights=True,
        synthetic_certified_fixture=True,
        completed=True,
        tenant_id="offline",
        origin_fixture_ref="fixture:origin",
        independent_fixture_ref="fixture:independent",
        template_id="template:pending-capture-guard:1",
        deidentified=True,
    )
