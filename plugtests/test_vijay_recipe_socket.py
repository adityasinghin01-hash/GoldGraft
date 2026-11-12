"""Vijay's real recipe (pieces/shops/vijay-php-reference) through the shop socket.

Runs actual PHP. Uses Vijay's reviewed candidate (fixtures/socket-candidate), the
only candidate his trusted-host profile executes; an AI-written candidate must be
refused until a protected runner exists. No network, model or provider calls.
"""

import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest

from integration.connected_run import connect_run
from integration.shop_socket import RecipeProof, conformance, load_recipe

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "pieces/shops/vijay-php-reference"
CANDIDATE = ROOT / "fixtures/socket-candidate"
R9 = ROOT / "deploy/runs/r9-final-connected"
PHP = os.environ.get("GOLDGRAFT_PHP") or shutil.which("php") or ""

pytestmark = pytest.mark.skipif(not PHP, reason="real PHP required")


def reviewed_run(tmp_path):
    """Agent-run folder whose CHANGES are exactly Vijay's reviewed candidate."""
    run = tmp_path / "reviewed-run"
    run.mkdir()
    approved = json.loads((PACK / "reviewed_candidate.json").read_text())
    rows = []
    for rel, digest in approved.items():
        after = (CANDIDATE / rel).read_text(encoding="utf-8")
        assert hashlib.sha256(after.encode()).hexdigest() == digest, rel
        source = PACK / "source" / rel
        before = source.read_text(encoding="utf-8") if source.exists() else ""
        rows.append({"path": rel, "before": before, "after": after, "author": "vijay-reviewed"})
    changes = json.loads((R9 / "CHANGES.json").read_text())
    changes["files"] = rows
    (run / "CHANGES.json").write_text(json.dumps(changes))
    for name in ("RESULT.json", "OUTPUTS.json"):
        (run / name).write_bytes((R9 / name).read_bytes())
    return run


def test_vijay_recipe_conforms_and_all_nine_scenarios_are_judged(tmp_path):
    recipe = load_recipe(PACK)
    assert recipe.provenance == "vijay" and recipe.holds() == []
    report = conformance(recipe, tmp_path / "conf", agent_run_dir=reviewed_run(tmp_path), php=PHP)
    assert report["conforms"], report["failures"]
    proof = RecipeProof(tmp_path / "conf" / f"conformance-{recipe.shop_id}", recipe)
    grades = sorted(str(row["verdict"].grade) for row in proof.rows)
    assert len(grades) == 9 and set(grades) <= {"PASS", "PASS_FIXED"}, grades
    flags = json.loads(
        (tmp_path / "conf" / f"conformance-{recipe.shop_id}/local-proof/REPORT.json").read_text()
    )
    assert flags["real_payment_qualified"] is False
    assert flags["isolated_execution_qualified"] is False


def test_ai_written_candidate_is_refused_until_a_protected_runner_exists(tmp_path):
    report = conformance(load_recipe(PACK), tmp_path / "conf", agent_run_dir=R9, php=PHP)
    assert not report["conforms"]
    assert any("reviewed local host recipe held" in f for f in report["failures"])


def test_all_four_pieces_run_together_with_vijays_shop(tmp_path):
    summary = connect_run(reviewed_run(tmp_path), tmp_path / "state", recipe=load_recipe(PACK))
    assert summary["shop"] == {
        "shop_id": "vijay-php-reference",
        "recipe": "vijay",
        "later_gates": [],
    }
    assert summary["gupta_control"]["status"] == "operation_started"
    by_state = summary["proof_result"]["by_state"]
    assert len(by_state["verified"]) >= 30
    assert "isolation:runner" not in by_state["verified"]
    assert not any(h.startswith(("state_recipe", "finalisation_recipe")) for h in summary["holds"])
