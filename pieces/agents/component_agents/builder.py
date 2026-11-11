"""Reproducible build/driver proposals; never model-authored observed images."""

from goldgraft_contracts.plan5_common import content_digest
from pydantic import Field

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
    root_map_ref: str
    required_symbols: list[str] = Field(min_length=1, max_length=32)
    candidate_snapshot_ref: str | None = None


def admit(task, data):
    admission(data)
    if not data.root_map_ref or not set(data.required_symbols) <= set(
        data.catalog.installed_symbols
    ):
        raise ValueError("MISSING_EVIDENCE inventory or installed symbol")
    if task.task.operation == "build_candidate" and data.candidate_snapshot_ref != data.subject_ref:
        raise ValueError("DENIED exact candidate snapshot required")


def schemas(operation, data):
    return ["ExecutionProposal/1"]


def requested(operation):
    return ["Driver/1"] if operation == "validate_driver" else ["RunnableShop/1", "ArtifactBuild/1"]


def requests(task, data):
    return [
        dict(
            tool="recipe.lookup",
            arguments=dict(catalog_ref=data.catalog.ref, fingerprint=data.catalog.fingerprint),
        ),
        dict(
            tool="dependency.inspect",
            arguments=dict(
                recipe_ref=data.catalog.recipe_ref,
                package=data.catalog.package,
                version=data.catalog.version,
            ),
        ),
        *execution_calls(task, proposal(task, data, requested(task.task.operation))),
    ]


def route(data):
    """Five calls need four turns at best (Haiku's whole cap): use the 8-turn Haiku profile."""
    return "haiku8"


def facts(task, data):
    facts = execution_facts(
        task,
        requested(task.task.operation),
        ", result.source_tree_digest equals source_tree_digest and result.driver_valid is "
        "true (for builds the receipt must also carry synthetic_manifest and image_digest)",
    )
    facts["call_policy"] = (
        "1) recipe.lookup(catalog.ref, catalog.fingerprint) and dependency.inspect("
        "catalog.recipe_ref, catalog.package, catalog.version) together in one response. "
        "2) execution.request alone, with proposal = ExecutionProposal/1 {task_id, "
        "operation, subject_ref: subject_ref, recipe_ref: catalog.recipe_ref, scenario_ref: "
        "null, variant: null, requested_output_schemas (exact order above), "
        "expected_subject, evidence_refs}. 3) execution.status(request_id). 4) If the "
        "receipt passes receipt_rule, submit that same proposal; else report_hold."
    )
    return facts


def synthesize(task, data, packet, observations):
    return [
        dict(
            schema="ExecutionProposal/1",
            payload=proposal(task, data, requested(task.task.operation)),
        )
    ]


def review(task, data, packet, outputs, observations):
    if not same_proposal(
        outputs[0]["payload"], proposal(task, data, requested(task.task.operation))
    ):
        raise ValueError("DENIED build proposal changed")
    result = receipt(task, observations)
    if (
        result.get("source_tree_digest") != data.source_tree_digest
        or result.get("driver_valid") is not True
    ):
        raise ValueError("MISSING_EVIDENCE reproducibility/driver")
    if task.task.operation != "validate_driver":
        manifest = result.get("synthetic_manifest")
        if not manifest or result.get("image_digest") != "sha256:" + content_digest(manifest):
            raise ValueError("DENIED image bytes/digest")


def inspect(outputs):
    p = outputs[0]["payload"]
    return dict(
        operation=p["operation"],
        source_ref=p["subject_ref"],
        requested=p["requested_output_schemas"],
        build_evidence="Synthetic counterpart only; real runner qualification OPEN",
        host_execution="NONE",
    )


def sample(operation):
    manifest = {"fixture": "offline-build", "source": "demo"}
    return dict(
        subject_ref="fixture:candidate" if operation == "build_candidate" else "fixture:baseline",
        catalog=catalog_sample(),
        source_tree_digest=content_digest("fixture-source"),
        root_map_ref="fixture:root-map",
        required_symbols=["create_order"],
        candidate_snapshot_ref="fixture:candidate" if operation == "build_candidate" else None,
        execution_state="observed",
        execution_result=dict(
            source_tree_digest=content_digest("fixture-source"),
            driver_valid=True,
            synthetic_manifest=manifest,
            image_digest="sha256:" + content_digest(manifest),
        ),
    )
