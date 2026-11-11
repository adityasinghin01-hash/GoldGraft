import pytest
from goldgraft_contracts.plan5_common import validate_dag

from pieces.agents.scheduler import tick
from pieces.agents.workflow import STAGES, create, inspect

from .test_runtime import NOW


def test_draft_followup_final_graph_is_acyclic(tmp_path):
    p = create(tmp_path / "w.sqlite", clock=lambda: NOW)
    report = tick(p.run_ref, NOW, p)
    snap = p.control.snapshot(p.run_ref)
    assert report.completed == len(STAGES) + 1, inspect(p)
    validate_dag([t.task for t in snap.tasks], "task_id", "dependencies", maximum=32)
    assert [t.task.task_id for t in snap.tasks].index("scribe-final") > [
        t.task.task_id for t in snap.tasks
    ].index("followup-0")
    assert len([t for t in snap.tasks if t.task.task_id.startswith("followup-")]) <= 4
    assert all(t.output_refs for t in snap.tasks)
    p2 = create(tmp_path / "w.sqlite", clock=lambda: NOW)
    before = (p2.model.total_dispatches(), p2.tools.total_dispatches())
    assert tick(p2.run_ref, NOW, p2).claimed == 0
    assert (p2.model.total_dispatches(), p2.tools.total_dispatches()) == before
    assert inspect(p2) == inspect(p)


def test_composite_input_subject_cannot_be_rebound(tmp_path):
    import json

    from goldgraft_fakes.offline_store import encoded

    from pieces.agents.runtime import run_task
    from pieces.agents.workflow import advance

    p = create(tmp_path / "w.sqlite", clock=lambda: NOW)
    lease = p.control.claim("runtime-worker", NOW)
    assert run_task(lease, p.control, p.artifacts, p.model, p.tools, now=NOW).outcome == "completed"
    advance(p.run_ref, p)
    before = p.model.total_dispatches()
    with p.control.store.transaction() as db:
        t = p.control._snapshot(db, p.run_ref).tasks[0]
        row = db.execute(
            "SELECT descriptor FROM artifacts WHERE ref=?", (t.output_refs[0],)
        ).fetchone()
        d = json.loads(row[0])
        d["subject_digest"] = "e" * 64
        db.execute("UPDATE artifacts SET descriptor=? WHERE ref=?", (encoded(d), t.output_refs[0]))
    # Only the ready dependent can be claimed; the altered predecessor never enters its context.
    lease = p.control.claim("runtime-worker", NOW)
    assert run_task(lease, p.control, p.artifacts, p.model, p.tools, now=NOW).outcome == "blocked"
    assert p.model.total_dispatches() == before


def test_append_crash_before_input_materialisation_recovers(tmp_path):
    from pieces.agents.runtime import run_task
    from pieces.agents.workflow import advance

    p = create(tmp_path / "w.sqlite", clock=lambda: NOW)
    lease = p.control.claim("runtime-worker", NOW)
    assert run_task(lease, p.control, p.artifacts, p.model, p.tools, now=NOW).outcome == "completed"
    advance(p.run_ref, p)
    with p.control.store.transaction() as db:
        task = p.control._snapshot(db, p.run_ref).tasks[-1]
        db.execute("DELETE FROM artifacts WHERE ref=?", (task.task.input_refs[0],))
    restarted = create(tmp_path / "w.sqlite", clock=lambda: NOW)
    assert tick(restarted.run_ref, NOW, restarted).completed == len(STAGES)


def test_separate_process_workflow_resume_has_no_new_dispatch(tmp_path):
    import json
    import subprocess
    import sys

    state = tmp_path / "process.sqlite"
    cmd = [sys.executable, "-m", "pieces.agents.workflow_cli"]
    run = subprocess.run(cmd + ["run", "--state-file", str(state)], capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    before = json.loads(run.stdout)
    after = subprocess.run(
        cmd + ["resume", "--state-file", str(state)], capture_output=True, text=True
    )
    assert after.returncode == 0, after.stderr
    assert json.loads(after.stdout) == before
    view = subprocess.run(
        cmd + ["inspect", "--state-file", str(state)], capture_output=True, text=True
    )
    assert view.returncode == 0, view.stderr
    assert len(json.loads(view.stdout)["artifacts"]) == 12


@pytest.mark.parametrize("boundary", ["after_tool", "before_finish", "after_finish"])
def test_candidate_process_crash_reconciles_one_patch(tmp_path, boundary):
    import json
    import subprocess
    import sys

    state = tmp_path / "crash.sqlite"
    code = """
import os,sys
from datetime import UTC,datetime
from pieces.agents.workflow import create,advance
from pieces.agents.runtime import run_task
now=datetime(2026,11,10,12,tzinfo=UTC)
p=create(sys.argv[1],clock=lambda:now)
while True:
    advance(p.run_ref,p)
    lease=p.control.claim('runtime-worker',now)
    if p.control.load(lease).task.role=='Grafter':break
    run_task(lease,p.control,p.artifacts,p.model,p.tools,now=now)
def fault(point):
    if point!=sys.argv[2]:return
    if point=='after_tool':
        with p.control.store.transaction() as db:
            sql="SELECT COUNT(*) FROM scripts WHERE namespace='candidate-receipt'"
            if db.execute(sql).fetchone()[0]!=1:return
    os._exit(73)
run_task(lease,p.control,p.artifacts,p.model,p.tools,now=now,fault=fault)
"""
    process = subprocess.run(
        [sys.executable, "-c", code, str(state), boundary], capture_output=True, text=True
    )
    assert process.returncode == 73, process.stdout + process.stderr
    recovery = """
import json,sys
from datetime import UTC,datetime
from pieces.agents.workflow import create
from pieces.agents.scheduler import tick
now=datetime(2026,11,10,12,1,1,tzinfo=UTC)
p=create(sys.argv[1],clock=lambda:now)
tick(p.run_ref,now,p)
with p.control.store.transaction() as db:
    sql="SELECT COUNT(*) FROM scripts WHERE namespace='candidate-receipt'"
    count=db.execute(sql).fetchone()[0]
    max_dispatch=db.execute('SELECT MAX(dispatch_count) FROM tools').fetchone()[0]
states=[t.state for t in p.control.snapshot(p.run_ref).tasks]
print(json.dumps(dict(states=states,patches=count,max_dispatch=max_dispatch)))
"""
    process = subprocess.run(
        [sys.executable, "-c", recovery, str(state)], capture_output=True, text=True
    )
    assert process.returncode == 0, process.stdout + process.stderr
    data = json.loads(process.stdout)
    assert data["states"] == ["succeeded"] * 12, data
    assert data["patches"] == 1 and data["max_dispatch"] == 1
