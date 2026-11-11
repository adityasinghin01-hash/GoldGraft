"""Offline Surveyor diagnostic over named synthetic bytes, never paid inference.

Hand-labelled cases feed only the independent checker. The deterministic proposal
comes from the actual source analyzer; the scripted ModelPort stages that proposal.
No CLI switch activates service mode, arbitrary source access or an inference SDK.
"""

import argparse
import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path

from goldgraft_contracts.plan5_common import RelativePath, content_digest
from goldgraft_foundation.offline_profile import load_runtime_profile
from pydantic import TypeAdapter

from ..roles import surveyor_configuration
from ..scheduler import tick
from ..source_inventory import build_static_inventory, package_from_sources
from ..surveyor import inspect_inventory
from .surveyor import FLOWS, load_cases, score_artifact


def load_readiness_cases():
    document = json.loads(Path(__file__).with_name("surveyor_readiness_cases.json").read_text())
    baseline = {case["id"]: case for case in load_cases()}
    cases = [
        dict(baseline[key], expected_outcome="completed") for key in document["baseline_case_ids"]
    ]
    cases += document["cases"]
    if len(cases) != 20 or len({case["id"] for case in cases}) != 20:
        raise ValueError("INVALID diagnostic case identities")
    for case in cases:
        if not re.fullmatch(r"[a-z0-9-]{1,64}", case["id"]):
            raise ValueError("INVALID diagnostic case identity")
        for name in case["files"]:
            TypeAdapter(RelativePath).validate_python(name)
        if case["expected_outcome"] not in {"completed", "blocked"}:
            raise ValueError("INVALID diagnostic outcome")
        for expected in case.get("expected", []):
            lines = case["files"][expected["file"]].splitlines()
            if not 1 <= expected["line"] <= len(lines) or expected["flow"] not in FLOWS:
                raise ValueError("INVALID independent source label")
    return cases


def _run_case(case, state, repeat):
    started = time.monotonic()
    # Expected labels are deliberately never passed to the analyzer or ports.
    package = package_from_sources(shop_id=case["shop_id"], files=case["files"])
    package["required_lenses"] = case.get("required_lenses", ["code"])
    configuration = dict(
        surveyor_configuration(), offline_final_payload=build_static_inventory(package)
    )

    def open_ports():
        return load_runtime_profile(
            "offline",
            state,
            fixture="surveyor_inventory",
            configuration=configuration,
            inputs=package,
            clock=lambda: datetime.now(UTC),
        )

    ports = open_ports()
    tick("fake:runtime-run", ports.clock(), ports)
    task = ports.control.snapshot("fake:runtime-run").tasks[0]
    result = ports.control.result("survey")
    failures, inspection, artifact_check = [], None, None
    if result.outcome != case["expected_outcome"]:
        failures.append("outcome")
    if result.outcome == "completed":
        descriptor, payload = ports.artifacts.inspect_output(task, ports.context_for("survey"))
        if case["expected_outcome"] == "completed":
            artifact_check = score_artifact(case, payload)
            if not artifact_check["passed"]:
                failures += artifact_check["failed_checks"]
        inspection = inspect_inventory(
            payload,
            input_refs=task.task.input_refs,
            output_ref=descriptor.ref,
            subject=descriptor.subject_digest,
            evidence_refs=result.evidence_refs,
            omissions=package["omissions"],
        )
        if descriptor.ref != result.output_refs[0]:
            failures.append("accepted_output_use")
    elif (
        result.output_refs
        or result.issue is None
        or result.issue.code != "MISSING_EVIDENCE"
        or task.state != "held"
        or ports.model.total_dispatches()
        or ports.tools.total_dispatches()
    ):
        failures.append("required_hold_before_dispatch")
    if reason := case.get("expected_omission_reason"):
        if reason not in {item["reason_code"] for item in package["omissions"]["items"]}:
            failures.append("missing_omission_reason")
    before = ports.model.total_dispatches() + ports.tools.total_dispatches()
    # Reopen persisted boundary state; never clear a hold or invent a retry ID.
    reopened = open_ports()
    tick("fake:runtime-run", reopened.clock(), reopened)
    after = reopened.model.total_dispatches() + reopened.tools.total_dispatches()
    if after != before or reopened.control.result("survey") != result:
        failures.append("resume_identity")
    return {
        "case_id": case["id"],
        "repeat": repeat,
        "case_digest": content_digest(case),
        "prompt_digest": configuration["prompt_digest"],
        "policy_digest": configuration["policy_digest"],
        "state_file": str(state),
        "outcome": result.outcome,
        "issue": result.issue.model_dump(mode="json") if result.issue else None,
        "result_digest": content_digest(result),
        "output_refs": result.output_refs,
        "artifact_check": artifact_check,
        "inspection": inspection,
        "omissions": package["omissions"],
        "scripted_dispatches": ports.model.total_dispatches(),
        "tool_dispatches": ports.tools.total_dispatches(),
        "resume_added_dispatches": after - before,
        "model_api_calls": 0,
        "provider_tokens": None,
        "source_utf8_bytes": sum(len(text.encode()) for text in case["files"].values()),
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "passed": not failures,
        "failed_checks": failures,
    }


def evaluate(state_dir, *, repeats=3, case_id=None):
    cases = load_readiness_cases()
    if type(repeats) is not int or repeats not in {1, 3}:
        raise ValueError("INVALID repeat bound")
    if case_id is not None:
        cases = [case for case in cases if case["id"] == case_id]
        if not cases:
            raise ValueError("INVALID unlisted diagnostic case")
    state_dir = Path(state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    runs = [
        _run_case(case, state_dir / f"{case['id']}-repeat-{repeat}.sqlite", repeat)
        for case in cases
        for repeat in range(1, repeats + 1)
    ]
    return {
        "format": "SurveyorSourceReadinessDiagnosticResult/1",
        "evidence_class": "component_offline",
        "inference": "deterministic analyzer through explicitly scripted ModelPort",
        "real_model_evaluation": "NOT RUN",
        "model_api_calls": 0,
        "model_spend_micro_usd": 0,
        "provider_tokens": None,
        "runs_total": len(runs),
        "runs_passed": sum(run["passed"] for run in runs),
        "passed": all(run["passed"] for run in runs),
        "runs": runs,
        "limitations": [
            "Offline source-readiness diagnostics, not real-model quality or safety scores.",
            "Repeat IDs do not simulate provider sampling or seeded model inference.",
            "Literal indicators include comments/strings; aliases/unknown families may be missed.",
            "PHP reference recognition is not parsing/execution/include_path/reachability proof.",
            "GU services, VJ coverage, SH proof and runtime/site/account lenses are unqualified.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--case", choices=[case["id"] for case in load_readiness_cases()])
    parser.add_argument("--repeats", type=int, choices=[1, 3], default=3)
    args = parser.parse_args(argv)
    report = evaluate(args.state_dir, repeats=args.repeats, case_id=args.case)
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
