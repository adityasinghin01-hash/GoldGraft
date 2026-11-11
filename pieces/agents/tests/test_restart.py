import json
import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    "boundary",
    ["before_model", "after_model", "before_tool", "after_tool", "before_finish", "after_finish"],
)
def test_process_crash_reconciles_original_identity(tmp_path, boundary):
    """os._exit bypasses finally/cleanup; a new process recovers persisted boundary state."""
    state = tmp_path / "crash.sqlite"
    code = """
import os, sys
from datetime import UTC, datetime
from pathlib import Path
from goldgraft_fakes.plan5_profile import create_profile
from pieces.agents.runtime import run_task
now = datetime(2026, 11, 10, 12, tzinfo=UTC)
p = create_profile(Path(sys.argv[1]), clock=lambda: now)
lease = p.control.claim('crashing-worker', now)
def crash(point):
    if point == sys.argv[2]:
        os._exit(73)
run_task(lease, p.control, p.artifacts, p.model, p.tools, now=now, fault=crash)
"""
    crashed = subprocess.run(
        [sys.executable, "-c", code, str(state), boundary], capture_output=True, text=True
    )
    assert crashed.returncode == 73, crashed.stdout + crashed.stderr
    recover = """
import json, sys
from datetime import UTC, datetime
from pathlib import Path
from goldgraft_fakes.plan5_profile import create_profile
from pieces.agents.scheduler import tick
now = datetime(2026, 11, 10, 12, 1, 1, tzinfo=UTC)
p = create_profile(Path(sys.argv[1]), clock=lambda: now)
tick('fake:runtime-run', now, p)
with p.control.store.transaction() as db:
    model_max = db.execute('SELECT COALESCE(MAX(dispatch_count),0) FROM model_turns').fetchone()[0]
    tool_max = db.execute('SELECT COALESCE(MAX(dispatch_count),0) FROM tools').fetchone()[0]
print(json.dumps({'states': [t.state for t in p.control.snapshot('fake:runtime-run').tasks],
    'accepted': p.control.accepted_result_count(), 'model_max': model_max, 'tool_max': tool_max,
    'models': p.model.total_dispatches(), 'tools': p.tools.total_dispatches()}))
"""
    resumed = subprocess.run(
        [sys.executable, "-c", recover, str(state)], capture_output=True, text=True
    )
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    value = json.loads(resumed.stdout)
    assert value["model_max"] <= 1 and value["tool_max"] <= 1
    if boundary == "before_tool":
        # Original intent has no qualified fence-rebinding receipt. Conservatively hold it.
        assert value["states"] == ["held", "pending"]
        assert value["tools"] == 0
    else:
        assert value["states"] == ["succeeded", "succeeded"]
        assert value["accepted"] == 2
        assert value["models"] == 4 and value["tools"] == 2


def test_cli_new_process_status_same_run(tmp_path):
    state = tmp_path / "cli.sqlite"
    command = [sys.executable, "-m", "pieces.agents.cli"]
    first = subprocess.run(
        command + ["run", "--mode", "offline", "--state-file", str(state)],
        capture_output=True,
        text=True,
    )
    assert first.returncode == 0, first.stdout + first.stderr
    status = subprocess.run(
        command + ["status", "--mode", "offline", "--state-file", str(state)],
        capture_output=True,
        text=True,
    )
    assert status.returncode == 0, status.stdout + status.stderr
    value = json.loads(status.stdout)
    assert value["evidence_class"] == "scripted"
    assert value["accepted_results"] == 2
    second = subprocess.run(
        command + ["run", "--mode", "offline", "--state-file", str(state)],
        capture_output=True,
        text=True,
    )
    assert second.returncode == 0 and json.loads(second.stdout)["accepted_results"] == 2


def test_service_cli_refuses_unqualified_profile(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pieces.agents.cli",
            "run",
            "--mode",
            "service",
            "--state-file",
            str(tmp_path / "state.sqlite"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert not (tmp_path / "state.sqlite").exists()
