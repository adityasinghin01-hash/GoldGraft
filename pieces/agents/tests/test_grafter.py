import json

import pytest
from goldgraft_contracts.plan5_common import content_digest
from goldgraft_fakes.offline_store import encoded

from pieces.agents.component_agents.grafter import sample
from pieces.agents.component_cli import create
from pieces.agents.scheduler import tick

from .test_runtime import NOW


def test_grafter_only_writer_and_cas(tmp_path):
    d = sample("candidate_patch")
    p = create("Grafter", tmp_path / "g.sqlite", clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 1
    t = p.control.snapshot(p.run_ref).tasks[0]
    output = p.artifacts.inspect_outputs(t, p.context_for(t.task.task_id))[0]["payload"]
    assert output["branch"] is None and output["changes"][0]["commit"] is None
    assert output["baseline_snapshot_ref"] == d["source_ref"]
    with p.control.store.transaction() as db:
        candidate = json.loads(
            db.execute("SELECT body FROM scripts WHERE namespace='candidate-tree'").fetchone()[0]
        )
        assert candidate["files"] == {**d["files"], **d["replacements"]}
        descriptor = json.loads(
            db.execute(
                "SELECT descriptor FROM artifacts WHERE ref=?", (t.output_refs[0],)
            ).fetchone()[0]
        )
        assert descriptor["subject_digest"] != t.task.expected_subject
        assert descriptor["derivation_ref"]
    assert d["files"] == {"checkout.php": "<?php legacy_capture();"}
    assert tick(p.run_ref, NOW, p).claimed == 0


@pytest.mark.parametrize(
    "fault", ["writer", "stale", "test", "symbol", "same_failure", "no_failure"]
)
def test_grafter_denies_unsafe_patch_before_model(tmp_path, fault):
    d = sample("candidate_patch")
    if fault == "writer":
        d["exclusive_writer"] = False
    elif fault == "stale":
        d["expected_tree"] = "e" * 64
    elif fault == "test":
        d["files"]["tests/payment.php"] = "old"
        d["expected_tree"] = content_digest(d["files"])
        d["allowed_paths"].append("tests/payment.php")
        d["replacements"] = {"tests/payment.php": "pass"}
    elif fault == "symbol":
        d["required_symbol"] = "made_up"
    elif fault == "same_failure":
        d["repair_round"] = 1
        d["failure_fingerprint"] = d["previous_failure_fingerprint"] = "e" * 64
    else:
        d["repair_round"] = 1
    p = create("Grafter", tmp_path / "g.sqlite", data=d, clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 0
    assert p.model.total_dispatches() == 0


@pytest.mark.parametrize("fault", ["other_writer", "changed_tree"])
def test_candidate_compare_and_swap_rechecks_at_tool(tmp_path, fault):
    p = create("Grafter", tmp_path / "g.sqlite", clock=lambda: NOW)
    t = p.control.snapshot(p.run_ref).tasks[0]
    d = sample("candidate_patch")
    state = {
        "owner": "unrelated-writer" if fault == "other_writer" else t.task.task_id,
        "files": d["files"] if fault == "other_writer" else {"checkout.php": "changed"},
    }
    with p.control.store.transaction() as db:
        db.execute(
            "INSERT INTO scripts VALUES('candidate-tree',?,?)", (d["workspace_ref"], encoded(state))
        )
    assert tick(p.run_ref, NOW, p).completed == 0
    with p.control.store.transaction() as db:
        assert (
            db.execute(
                "SELECT COUNT(*) FROM scripts WHERE namespace='candidate-receipt'"
            ).fetchone()[0]
            == 0
        )


@pytest.mark.parametrize("fault", ["parent", "collector", "tree"])
def test_forged_child_lineage_is_not_accepted(tmp_path, fault):
    p = create("Grafter", tmp_path / "g.sqlite", clock=lambda: NOW)
    original = p.artifacts.stage_outputs

    def forged(*args):
        refs = original(*args)
        with p.control.store.transaction() as db:
            if fault == "tree":
                row = db.execute(
                    "SELECT body FROM scripts WHERE namespace='candidate-receipt'"
                ).fetchone()
                v = json.loads(row[0])
                v["manifest"]["source_tree_digest"] = "e" * 64
                db.execute(
                    "UPDATE scripts SET body=? WHERE namespace='candidate-receipt'", (encoded(v),)
                )
            else:
                row = db.execute(
                    "SELECT descriptor FROM artifacts WHERE ref=?", (refs[0],)
                ).fetchone()
                d = json.loads(row[0])
                blob = db.execute(
                    "SELECT body FROM blobs WHERE ref=?", (d["derivation_ref"],)
                ).fetchone()
                v = json.loads(bytes(blob[0]))
                v["parent_subject" if fault == "parent" else "collector_identity_ref"] = (
                    "e" * 64 if fault == "parent" else "fake:untrusted"
                )
                db.execute(
                    "UPDATE blobs SET body=? WHERE ref=?",
                    (encoded(v).encode(), d["derivation_ref"]),
                )
        return refs

    p.artifacts.stage_outputs = forged
    assert tick(p.run_ref, NOW, p).completed == 0


def test_grafter_model_metadata_and_grounded_summary_are_accepted(tmp_path):
    p = create("Grafter", tmp_path / "g.sqlite", clock=lambda: NOW)
    original = p.model.renderer

    def explained(*args):
        v = original(*args)
        v["producer"]["model"] = "qualified-synthetic-model"
        v["changes"][0]["summary"] = "Isolated payment patch; independent build/proof required."
        return v

    p.model.renderer = explained
    assert tick(p.run_ref, NOW, p).completed == 1


def test_grafter_cannot_accept_uninstalled_plan_operation(tmp_path):
    d = sample("candidate_patch")
    d["target_plan"]["items"][0]["target_op"] = "invented_symbol"
    p = create("Grafter", tmp_path / "g.sqlite", data=d, clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 0


@pytest.mark.parametrize("fault", ["wrong_tree", "missing_snapshot"])
def test_grafter_faulty_collector_receipt_is_held(tmp_path, fault):
    d = sample("candidate_patch")
    d["collector_receipt_fault"] = fault
    p = create("Grafter", tmp_path / "g.sqlite", data=d, clock=lambda: NOW)
    assert tick(p.run_ref, NOW, p).completed == 0
