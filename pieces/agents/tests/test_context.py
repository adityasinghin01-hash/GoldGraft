import importlib
import json
from datetime import UTC, datetime
from importlib.util import find_spec
from pathlib import Path

import pytest
from goldgraft_contracts.agent_runtime import (
    AgentTask,
    ControlFailure,
    TaskLease,
)

ROOT = Path(__file__).resolve().parents[3]
NOW = datetime(2026, 11, 10, 12, tzinfo=UTC)


@pytest.mark.parametrize(
    "field,bad",
    [
        ("task_id", "another-task"),
        ("run_id", "another-run"),
        ("generation", 2),
        ("lease_epoch", 2),
        ("worker_id", "another-worker"),
        ("task_version", 2),
    ],
)
def test_mismatched_lease_is_rejected(field, bad):
    assert find_spec("pieces.agents.context") is not None, "context.py is not implemented yet"
    build_context = importlib.import_module("pieces.agents.context").build_context

    examples = ROOT / "contracts/examples"

    task_data = json.loads((examples / "AgentTask.1.json").read_text())
    task_data.update(
        state="leased",
        lease_owner="worker-demo",
        lease_epoch=1,
        lease_until="2026-11-10T12:01:00Z",
    )
    task = AgentTask.model_validate(task_data)

    lease_data = json.loads((examples / "TaskLease.1.json").read_text())
    lease_data.update(
        worker_id="worker-demo",
        lease_until="2026-11-10T12:01:00Z",
    )
    lease_data[field] = bad
    lease = TaskLease.model_validate(lease_data)

    with pytest.raises(ControlFailure) as caught:
        build_context(task, lease, None, now=NOW)

    assert caught.value.error.code == "STALE"


@pytest.mark.parametrize(
    "field,bad",
    [
        ("case_id", "another-case"),
        ("run_id", "another-run"),
        ("generation", 2),
    ],
)
def test_wrong_scope_artifact_is_rejected(field, bad):
    from goldgraft_contracts.agent_runtime import ArtifactDescriptor

    from pieces.agents.context import build_context

    examples = ROOT / "contracts/examples"

    task_data = json.loads((examples / "AgentTask.1.json").read_text())
    task_data.update(
        state="leased",
        lease_owner="worker-demo",
        lease_epoch=1,
        lease_until="2026-11-10T12:01:00Z",
    )
    task = AgentTask.model_validate(task_data)

    lease_data = json.loads((examples / "TaskLease.1.json").read_text())
    lease_data.update(
        worker_id="worker-demo",
        lease_until="2026-11-10T12:01:00Z",
    )
    lease = TaskLease.model_validate(lease_data)

    artifact_data = json.loads((examples / "ArtifactDescriptor.1.json").read_text())
    artifact_data.update(
        case_id=task.case_id,
        run_id=task.run_id,
        generation=task.generation,
    )
    artifact_data[field] = bad
    artifact = ArtifactDescriptor.model_validate(artifact_data)

    class WrongScopeArtifacts:
        def resolve(self, ref, task_context):
            return artifact

    with pytest.raises(ControlFailure) as caught:
        build_context(task, lease, WrongScopeArtifacts(), now=NOW)

    assert caught.value.error.code == "DENIED"
