"""Sole isolated candidate writer; no host writes or self-approved success."""

from goldgraft_contracts.plan5_common import Digest, P5Record, Ref, RelativePath, content_digest
from goldgraft_contracts.survey import TargetPlan
from pydantic import Field, StrictBool

from ..component import metadata
from .architect import sample as architect_sample
from .execution import Catalog


class Input(P5Record):
    workspace_ref: Ref
    source_ref: Ref
    expected_tree: Digest
    files: dict[RelativePath, str] = Field(min_length=1, max_length=4)
    allowed_paths: list[RelativePath] = Field(min_length=1, max_length=4)
    replacements: dict[RelativePath, str] = Field(min_length=1, max_length=4)
    target_plan: TargetPlan
    catalog: Catalog
    required_symbol: str
    exclusive_writer: StrictBool
    repair_round: int = Field(ge=0, le=2, strict=True)
    failure_fingerprint: Digest | None
    previous_failure_fingerprint: Digest | None


def admit(task, data):
    if (
        not data.exclusive_writer
        or task.task.workspace_ref != data.workspace_ref
        or content_digest(data.files) != data.expected_tree
    ):
        raise ValueError("DENIED exclusive writer/CAS")
    paths = set(data.replacements)
    if not paths <= set(data.allowed_paths) <= set(data.files):
        raise ValueError("DENIED allowed candidate paths")
    if any(
        p.startswith(("tests/", "contracts/", "docs/", "."))
        or "test" in p.lower()
        or "rule" in p.lower()
        for p in paths
    ):
        raise ValueError("DENIED test/normative edit")
    if (
        not data.catalog.qualified_fixture
        or data.required_symbol not in data.catalog.installed_symbols
    ):
        raise ValueError("MISSING_EVIDENCE installed symbol")
    if not data.target_plan.items or any(not i.paypal_only for i in data.target_plan.items):
        raise ValueError("DENIED plan scope")
    if data.repair_round and (
        data.failure_fingerprint is None
        or data.failure_fingerprint == data.previous_failure_fingerprint
    ):
        raise ValueError("MISSING_EVIDENCE new independent failure")


def schemas(operation, data):
    return ["ChangeList/2"]


def requests(task, data):
    return [
        *[
            dict(
                tool="source.read",
                arguments=dict(snapshot_ref=data.source_ref, path=p, max_bytes=4096),
            )
            for p in data.files
        ],
        dict(
            tool="dependency.inspect",
            arguments=dict(
                recipe_ref=data.catalog.recipe_ref,
                package=data.catalog.package,
                version=data.catalog.version,
            ),
        ),
        dict(
            tool="candidate.patch",
            arguments=dict(
                workspace_ref=data.workspace_ref,
                expected_tree=data.expected_tree,
                patch_ref="inline:patch",
            ),
            patch=data.replacements,
        ),
    ]


def synthesize(task, data, packet, observations):
    receipt = observations[-1]["value"]["payload"]
    value = metadata(task, packet)
    value.update(
        provenance="snapshot",
        branch=None,
        baseline_snapshot_ref=data.source_ref,
        candidate_snapshot_ref=receipt["snapshot_ref"],
        patch_digest=content_digest(data.replacements),
        changes=[
            dict(
                plan_item_ids=[i.touchpoint for i in data.target_plan.items],
                summary="Payment-only isolated snapshot patch; independent build/proof required.",
                commit=None,
            )
        ],
        open_item_ids=[],
    )
    return [dict(schema="ChangeList/2", payload=value)]


def review(task, data, packet, outputs, observations):
    receipt = observations[-1]["value"]["payload"]
    files = {**data.files, **data.replacements}
    if (
        receipt.get("tree") != content_digest(files)
        or receipt.get("synthetic_only") is not True
        or outputs != synthesize(task, data, packet, observations)
    ):
        raise ValueError("DENIED collector patch/snapshot lineage")


def inspect(outputs):
    v = outputs[0]["payload"]
    return dict(
        candidate_snapshot_ref=v["candidate_snapshot_ref"],
        patch_digest=v["patch_digest"],
        provenance=v["provenance"],
        git_commit=None,
        independent_build_and_proof="REQUIRED",
        merchant_writes="NONE",
    )


def sample(operation):
    a = architect_sample("architect")
    plan = dict(
        path="REWRITE",
        items=[
            dict(
                touchpoint="tp-capture",
                target_op="capture_order",
                mapping_id="fixture-map-capture",
                delta_ids=[],
                paypal_only=True,
            )
        ],
        target_experience=["ORDERS_V2"],
        origin_rules=["captured-before-paid"],
        order=["READ_BOTH", "NEW_FLOWS_BEHIND_SWITCH", "CLEANUP"],
        handoff=[],
        deltas=[],
    )
    files = {"checkout.php": "<?php legacy_capture();"}
    return dict(
        workspace_ref="fixture:candidate-workspace",
        source_ref="fixture:baseline",
        expected_tree=content_digest(files),
        files=files,
        allowed_paths=["checkout.php"],
        replacements={"checkout.php": "<?php capture_order();"},
        target_plan=plan,
        catalog=a["catalog"],
        required_symbol="capture_order",
        exclusive_writer=True,
        repair_round=0,
        failure_fingerprint=None,
        previous_failure_fingerprint=None,
    )
