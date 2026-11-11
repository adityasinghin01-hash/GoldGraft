"""Scorer tests are tests of the evaluator, never real-model evaluation results."""

import copy
import json

import pytest

from pieces.agents.evals.surveyor import FLOWS, load_cases, score_artifact


def reference(case):
    return {
        "shop_id": case["shop_id"],
        "stack": {"lang": "synthetic", "framework": "none", "versions": {}, "db": "none"},
        "lenses_run": ["code"],
        "touchpoints": [
            {
                "id": f"tp-{index}",
                "family": e["family"],
                "operation": e["operation"],
                "location": {"file": e["file"], "line": e["line"]},
                "lenses": ["code"],
                "confidence": 0.5,
                "live": False,
                "paypal_only": False,
                "target": {"paypal_mapping_id": e["mapping_id"], "rest_op": "unqualified"},
            }
            for index, e in enumerate(case["expected"])
        ],
        "money_flow": {
            flow: [
                {"file": e["file"], "line": e["line"]}
                for e in case["expected"]
                if e["flow"] == flow
            ]
            for flow in FLOWS
        },
        "recall_evidence": {"runtime_calls_total": 0, "matched_by_static": 0, "misses": []},
    }


@pytest.mark.parametrize("case", load_cases(), ids=lambda c: c["id"])
def test_checker_accepts_hand_labelled_reference_artifacts(case):
    score = score_artifact(case, reference(case))
    assert score["passed"] is True
    assert score["scope"] == "artifact_quality_only"


@pytest.mark.parametrize(
    "change", ["wrong_location", "missing", "live", "recall", "flow", "schema"]
)
def test_checker_rejects_wrong_artifacts_without_a_model_judge(change):
    case = load_cases()[0]
    payload = copy.deepcopy(reference(case))
    if change == "wrong_location":
        payload["touchpoints"][0]["location"]["line"] = 99
    elif change == "missing":
        payload["touchpoints"].pop()
    elif change == "live":
        payload["touchpoints"][0]["live"] = True
    elif change == "recall":
        payload["recall_evidence"]["runtime_calls_total"] = 1
    elif change == "flow":
        payload["money_flow"]["refund"] = []
    else:
        payload["unrecognised"] = True
    score = score_artifact(case, payload)
    assert score["passed"] is False
    assert score["failed_checks"]


def test_checker_rejects_an_invented_source_stack():
    case = load_cases()[0]
    payload = reference(case)
    payload["stack"]["lang"] = "invented-runtime"
    score = score_artifact(case, payload)
    assert score["passed"] is False
    assert "source_stack" in score["failed_checks"]


def novel_catalog(tmp_path):
    case = {
        "id": "novel-refund",
        "shop_id": "eval-refund-novel",
        "files": {"refunds/退款.php": "<?php\n$operation = 'RefundTransaction';\n"},
        "expected": [
            {
                "family": "EC_NVP",
                "operation": "RefundTransaction",
                "file": "refunds/退款.php",
                "line": 2,
                "flow": "refund",
                "mapping_id": "nvp-refund",
                "needle": "RefundTransaction",
            }
        ],
    }
    catalog = {
        "format": "SurveyorArtifactEvaluation/1",
        "source_rights": "Original synthetic snippets authored for GoldGraft; project MIT licence.",
        "cases": [case],
    }
    path = tmp_path / "novel.json"
    path.write_text(json.dumps(catalog))
    return path, catalog


def test_separate_novel_cases_preserve_four_original_cases_and_independent_checker(tmp_path):
    path, _ = novel_catalog(tmp_path)
    case = load_cases(path)[0]
    assert score_artifact(case, reference(case))["passed"]
    assert len(load_cases()) == 4


@pytest.mark.parametrize("fault", ["rights", "empty", "format"])
def test_novel_case_catalog_denies_missing_rights_or_invalid_scope(tmp_path, fault):
    path, catalog = novel_catalog(tmp_path)
    if fault == "rights":
        catalog["source_rights"] = "unverified private merchant source"
    elif fault == "empty":
        catalog["cases"] = []
    else:
        catalog["format"] = "other"
    path.write_text(json.dumps(catalog))
    with pytest.raises(ValueError):
        load_cases(path)
