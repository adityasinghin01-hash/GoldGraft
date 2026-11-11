"""Exercise actual own runtime/diagnostic, with explicit scripted counterparts."""

import json
import subprocess
import sys


def test_readiness_diagnostic_consumes_outputs_and_preserves_held_states(tmp_path):
    from pieces.agents.evals.surveyor_readiness import evaluate, load_readiness_cases

    cases = load_readiness_cases()
    assert len(cases) == 20
    report = evaluate(tmp_path / "state", repeats=1)
    assert report["evidence_class"] == "component_offline"
    assert report["model_api_calls"] == 0
    assert report["real_model_evaluation"] == "NOT RUN"
    assert report["passed"] and report["runs_passed"] == report["runs_total"] == 20
    completed = [run for run in report["runs"] if run["outcome"] == "completed"]
    held = [run for run in report["runs"] if run["outcome"] == "blocked"]
    assert len(completed) == 10 and len(held) == 10
    assert all(run["artifact_check"]["passed"] and run["inspection"] for run in completed)
    assert all(not run["output_refs"] and run["scripted_dispatches"] == 0 for run in held)
    assert all(run["resume_added_dispatches"] == 0 for run in report["runs"])


def test_readiness_cli_reopens_original_identities_without_another_dispatch(tmp_path):
    command = [
        sys.executable,
        "-B",
        "-m",
        "pieces.agents.evals.surveyor_readiness",
        "--state-dir",
        str(tmp_path / "state"),
        "--case",
        "readiness-dynamic-variable",
        "--repeats",
        "1",
    ]
    reports = []
    for _ in range(2):
        result = subprocess.run(command, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr
        reports.append(json.loads(result.stdout))
    assert reports[0]["runs"][0]["result_digest"] == reports[1]["runs"][0]["result_digest"]
    assert reports[1]["runs"][0]["outcome"] == "blocked"
    assert reports[1]["runs"][0]["scripted_dispatches"] == 0


def test_readiness_cli_cannot_select_service_or_unlisted_source(tmp_path):
    state = tmp_path / "absent"
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pieces.agents.evals.surveyor_readiness",
            "--state-dir",
            str(state),
            "--case",
            "../../merchant-code",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert not state.exists()
