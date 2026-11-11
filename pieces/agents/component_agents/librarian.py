"""Consented, de-identified learning proposals; promotion is separate authority."""

from types import SimpleNamespace

from goldgraft_contracts.plan5_common import Ref, content_digest
from goldgraft_contracts.registry import validate
from pydantic import StrictBool

from ..component import metadata
from .execution import (
    INLINE as EXECUTION_INLINE,
)
from .execution import (
    ExecutionInput,
    admission,
    catalog_sample,
    execution_calls,
    execution_facts,
    proposal,
    receipt,
    same_proposal,
    valid_metadata,
)


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
    if task.task.operation == "selfcheck_recipe":
        if not same_proposal(outputs[0]["payload"], draft_execution(task, data)):
            raise ValueError("DENIED independent selfcheck proposal")
        result = receipt(task, observations)
        if (
            result.get("fixture_ref") != data.independent_fixture_ref
            or result.get("passed") is not True
        ):
            raise ValueError("MISSING_EVIDENCE independent selfcheck")
    else:
        want = {x["schema"]: x["payload"] for x in drafts(task, data)}
        if len(outputs) != 2 or {x["schema"] for x in outputs} != set(want):
            raise ValueError("DENIED quarantine bundle")
        for item in outputs:
            got = validate(item["schema"], item["payload"]).model_dump(mode="json")
            expected = validate(item["schema"], want[item["schema"]]).model_dump(mode="json")
            if item["schema"] == "DetectionRule/1":
                if not valid_metadata(got, expected):
                    raise ValueError("DENIED detection metadata")
                for key in ("producer", "created_at"):
                    got.pop(key)
                    expected.pop(key)
            if got != expected:
                raise ValueError("DENIED raw reuse or self promotion")
        result = observations[-1]["value"]["payload"]
        if (
            result.get("drafts") != {x["schema"]: x["payload"] for x in outputs}
            or result.get("active_promotion") is not False
        ):
            raise ValueError("DENIED quarantine stage")


INLINE = {
    **EXECUTION_INLINE,
    "recipe.stage": {
        "recipe_ref": ("recipe", "Recipe/1"),
        "detection_rule_ref": ("detection", "DetectionRule/1"),
    },
}


def route(data):
    return "haiku8"


def facts(task, data):
    if task.task.operation == "selfcheck_recipe":
        facts = execution_facts(
            task,
            ["ProbeResult/1"],
            "; result.fixture_ref equals independent_fixture_ref and result.passed true",
        )
        facts["call_policy"] = (
            "1) execution.request alone with inline proposal: task_id, operation, subject_ref, "
            "recipe_ref=catalog.recipe_ref, scenario_ref:null, variant:null, "
            "requested_output_schemas:['ProbeResult/1'], expected_subject, evidence_refs. "
            "2) execution.status(request_id). 3) submit the same proposal only if receipt_rule "
            "holds, else report_hold. The independent fixture must differ from origin. "
            "A selfcheck never promotes a recipe."
        )
        return facts
    return {
        "quarantine_id": "quarantine-" + content_digest(data.template_id)[:16],
        "shape_digest": content_digest("pending-capture"),
        "provenance_refs": list(task.task.input_refs),
        "guard_id": "guard-captured-before-paid",
        "call_policy": "Submit only consented deidentified template metadata. Call recipe.stage "
        "alone with inline recipe (Recipe/1) and detection (DetectionRule/1). Closed template "
        "catalog: lang php, framework fixture, family EC_NVP, ast_shape_hash=shape_digest; "
        "recipe id=quarantine_id, transform=template_id, env:null, scenarios:[guard_id], "
        "provenance=provenance_refs, confidence:0, status:QUARANTINE, "
        "signature:'UNSIGNED_SYNTHETIC_QUARANTINE' (a label, not a signature claim). "
        "Detection uses reference_metadata, language:php, pattern:'literal:legacy_capture', "
        "operation:capture, evidence_refs:provenance_refs. Stage receipt must say "
        "active_promotion:false, else hold. Finally submit outputs bundle containing those "
        "same two payloads from the returned drafts. Never add raw source, new tenants, "
        "ACTIVE status, a signature claim or independent proof.",
    }


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
