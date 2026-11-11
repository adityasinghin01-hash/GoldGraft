"""Independent, hand-labelled RootMap artifact scorer; never a model/safety verdict."""

import json
from pathlib import Path

from goldgraft_contracts.plan5_common import RelativePath, content_digest, reject_secret
from goldgraft_contracts.survey import RootMap
from pydantic import TypeAdapter

FLOWS = ("create", "approve", "capture", "mark_paid", "refund", "notify", "recurring")


def load_cases(path=None):
    raw = (
        Path(path) if path is not None else Path(__file__).with_name("surveyor_cases.json")
    ).read_text()
    if len(raw.encode()) > 65536:
        raise ValueError("bounded inventory evaluation catalog required")
    reject_secret(raw)
    catalog = json.loads(raw)
    if (
        catalog.get("format") != "SurveyorArtifactEvaluation/1"
        or catalog.get("source_rights")
        != "Original synthetic snippets authored for GoldGraft; project MIT licence."
    ):
        raise ValueError("original synthetic evaluation catalog required")
    cases = catalog["cases"]
    if (len(cases) != 4 if path is None else not 1 <= len(cases) <= 20) or len(
        {c["id"] for c in cases}
    ) != len(cases):
        raise ValueError("invalid inventory evaluation cases")
    for case in cases:
        for name in case["files"]:
            TypeAdapter(RelativePath).validate_python(name)
        for expected in case["expected"]:
            line = case["files"][expected["file"]].splitlines()[expected["line"] - 1]
            if expected["needle"] not in line or expected["flow"] not in FLOWS:
                raise ValueError("hand-labelled expectation does not match synthetic source")
    return cases


def score_artifact(case, payload):
    """Only artifact quality; runtime scope/effects/receipts need their separate checks."""
    failures = []
    try:
        result = RootMap.model_validate(payload)
    except (ValueError, TypeError):
        return {
            "case_id": case["id"],
            "passed": False,
            "failed_checks": ["schema"],
            "scope": "artifact_quality_only",
            "case_digest": content_digest(case),
        }
    if result.shop_id != case["shop_id"]:
        failures.append("shop_identity")
    stack = case.get(
        "expected_stack",
        {"lang": "synthetic", "framework": "none", "versions": {}, "db": "none"},
    )
    if result.stack.model_dump(mode="json") != stack:
        failures.append("source_stack")
    if [lens.value for lens in result.lenses_run] != ["code"]:
        failures.append("observed_lenses")
    wanted = {
        (e["family"], e["operation"], e["file"], e["line"], e["mapping_id"])
        for e in case["expected"]
    }
    actual = set()
    for touchpoint in result.touchpoints:
        location = touchpoint.location.model_dump(mode="json")
        actual.add(
            (
                touchpoint.family.value,
                touchpoint.operation,
                location.get("file"),
                location.get("line"),
                touchpoint.target.paypal_mapping_id,
            )
        )
        if (
            touchpoint.live
            or touchpoint.money_30d is not None
            or touchpoint.confidence > 0.5
            or touchpoint.target.rest_op != "unqualified"
            or touchpoint.paypal_only
            or [lens.value for lens in touchpoint.lenses] != ["code"]
        ):
            failures.append("unsupported_touchpoint_claim")
    if actual != wanted or len(actual) != len(result.touchpoints):
        failures.append("exact_inventory")
    if len({t.id for t in result.touchpoints}) != len(result.touchpoints):
        failures.append("unique_ids")
    for flow, locations in result.money_flow.model_dump(mode="json").items():
        expected = {(e["file"], e["line"]) for e in case["expected"] if e["flow"] == flow}
        received = {(r.get("file"), r.get("line")) for r in locations}
        if expected != received or len(received) != len(locations):
            failures.append("flow_" + flow)
    if result.recall_evidence.model_dump() != {
        "runtime_calls_total": 0,
        "matched_by_static": 0,
        "misses": [],
    }:
        failures.append("unmeasured_runtime_recall")
    return {
        "case_id": case["id"],
        "passed": not failures,
        "failed_checks": sorted(set(failures)),
        "scope": "artifact_quality_only",
        "case_digest": content_digest(case),
    }
