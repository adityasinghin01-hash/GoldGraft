import pytest

from pieces.agents.component_agents.builder import sample
from pieces.agents.component_cli import create
from pieces.agents.scheduler import tick

from .test_runtime import NOW


@pytest.mark.parametrize("operation", ["build_baseline", "build_candidate", "validate_driver"])
def test_builder_operations_retain_one_execution_identity(tmp_path, operation):
    p = create("Builder", tmp_path / "b.sqlite", operation=operation, clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 1
    assert tick(p.run_ref, NOW, p).claimed == 0
    with p.control.store.transaction() as db:
        assert (
            db.execute("SELECT COUNT(*) FROM scripts WHERE namespace='component-job'").fetchone()[0]
            == 1
        )
    task = p.control.snapshot(p.run_ref).tasks[0]
    out = p.artifacts.inspect_outputs(task, p.context_for(task.task.task_id))
    assert out[0]["payload"]["operation"] == operation
    assert out[0]["schema"] == "ExecutionProposal/1"


@pytest.mark.parametrize("fault", ["recipe", "symbol", "candidate", "image", "driver", "unknown"])
def test_builder_cannot_publish_or_select_unqualified_recipe(tmp_path, fault):
    d = sample("build_candidate")
    if fault == "recipe":
        d["catalog"]["qualified_fixture"] = False
    elif fault == "symbol":
        d["required_symbols"] = ["invented_symbol"]
    elif fault == "candidate":
        d["candidate_snapshot_ref"] = "other:snapshot"
    elif fault == "image":
        d["execution_result"]["image_digest"] = "sha256:" + "e" * 64
    elif fault == "driver":
        d["execution_result"]["driver_valid"] = False
    else:
        d["execution_state"] = "unknown"
    p = create(
        "Builder", tmp_path / "b.sqlite", operation="build_candidate", data=d, clock=lambda: NOW
    )
    assert tick(p.run_ref, NOW, p).completed == 0
    assert not p.control.snapshot(p.run_ref).tasks[0].output_refs
    if fault in {"recipe", "symbol", "candidate"}:
        assert p.model.total_dispatches() == 0
