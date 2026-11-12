"""The shop socket: a recipe folder that conforms plugs into the connected run
unchanged, and a broken one is refused with its exact reason. Recordings here
are the reference fixtures written by a contract-only recipe.py."""

import dataclasses
import hashlib
import json
import shutil

import pytest

from integration.connected_run import connect_run
from integration.local_shop import ROOT
from integration.shop_socket import conformance, discover_recipes, load_recipe, reference_recipe

REFERENCE = ROOT / "fixtures/proof/legacy-php-shop"
SHOP = ROOT / "fixtures/shops/legacy-php-shop"

RECIPE_PY = '''"""Test recipe: writes recorded reference captures. Imports contracts only."""
import hashlib, json
from pathlib import Path

RAW = Path({raw!r})
SCENARIOS = {scenarios!r}
CLAIM = {claim!r}
DROP = {drop!r}


def execute(run_dir, output, *, php="php"):
    output.mkdir(parents=True)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    report = {{
        "run_id": run_dir.name,
        "evidence_class": "recorded_reference_captures",
        "real_payment_qualified": CLAIM,
        "isolated_execution_qualified": False,
        "merchant_delivery_qualified": False,
        "normative_contract_sha256": sha(Path(__file__).parent / "contract.json"),
        "capture_sha256": {{}},
    }}
    for scenario in SCENARIOS:
        for variant in ("OLD", "OLD_TWIN", "NEW"):
            name = f"{{scenario}}.{{variant}}.json"
            if name == DROP:
                continue
            capture = json.loads((RAW / name).read_bytes())
            capture.update(graft_id=run_dir.name, run_id=run_dir.name + "-recorded")
            (output / name).write_text(json.dumps(capture))
            report["capture_sha256"][name] = sha(output / name)
    (output / "REPORT.json").write_text(json.dumps(report))
    return report
'''


@pytest.fixture
def agent_run(tmp_path):
    directory = tmp_path / "agents"
    directory.mkdir()
    (directory / "RESULT.json").write_text(
        json.dumps({"shop": "legacy-php-shop", "status": "completed", "tasks": []})
    )
    (directory / "CHANGES.json").write_text('{"files": []}')
    plan = json.loads((REFERENCE / "target_plan.json").read_bytes())
    (directory / "OUTPUTS.json").write_text(
        json.dumps({"architect": [{"schema": "TargetPlan/1", "payload": plan}]})
    )
    return directory


def make_recipe(
    tmp_path, *, shop_id="vijay-test-shop", claim=False, drop=None, licence=True, bad_rule=False
):
    """A complete pieces/shops/<id>/ folder, laid out exactly as Vijay's piece will be."""
    folder = tmp_path / "shops" / shop_id
    (folder / "scenarios").mkdir(parents=True)
    pack = json.loads((SHOP / "goldgraft-shop.yaml").read_bytes())
    pack["shop_id"] = shop_id
    (folder / "goldgraft-shop.yaml").write_text(json.dumps(pack))
    for sid in pack["scenarios_supported"]:
        scenario = json.loads((REFERENCE / "scenarios" / f"{sid}.json").read_bytes())
        if bad_rule and sid == "HAPPY":
            scenario["rules"] = [*scenario["rules"], "R99"]
        (folder / "scenarios" / f"{sid}.json").write_text(json.dumps(scenario))
    shutil.copy(REFERENCE / "contract.json", folder / "contract.json")
    shutil.copy(REFERENCE / "target_plan.json", folder / "target_plan.json")
    shutil.copytree(SHOP / "src", folder / "source")
    if licence:
        shutil.copy(SHOP / "LICENSE.cutover", folder / "LICENSE")
    (folder / "recipe.py").write_text(
        RECIPE_PY.format(
            raw=str(REFERENCE / "raw"),
            scenarios=pack["scenarios_supported"],
            claim=claim,
            drop=drop,
        )
    )
    return folder


def test_reference_stand_in_is_wired_through_the_socket(tmp_path, agent_run):
    recipe = reference_recipe()
    assert recipe.provenance == "reference_stand_in"
    assert recipe.shop_id in {r.shop_id for r in discover_recipes()}
    report = conformance(
        dataclasses.replace(recipe, execute=_recorded(recipe)), tmp_path, agent_run_dir=agent_run
    )
    assert report["conforms"], report["failures"]
    assert {h.split(":")[0] for h in report["holds"]} >= {
        "state_recipe",
        "finalisation_recipe",
        "exit_check_recipe",
    }


def test_a_conforming_recipe_folder_plugs_into_the_connected_run(tmp_path, agent_run):
    recipe = load_recipe(make_recipe(tmp_path))
    assert recipe.provenance == "vijay" and recipe.shop_id == "vijay-test-shop"
    report = conformance(recipe, tmp_path / "conf", agent_run_dir=agent_run)
    assert report["conforms"], report["failures"]
    summary = connect_run(agent_run, tmp_path / "state", recipe=recipe)
    assert summary["shop"]["shop_id"] == "vijay-test-shop"
    assert summary["shop"]["recipe"] == "vijay"
    assert summary["gupta_control"]["status"] == "operation_started"
    states = {c: s for s, ids in summary["proof_result"]["by_state"].items() for c in ids}
    assert states["baseline:HAPPY"] == states["candidate:HAPPY"] == "verified"
    assert any("exit_check_recipe" in h for h in summary["holds"])


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"claim": True}, "self-declare"),
        ({"drop": "HAPPY.NEW.json"}, "incomplete"),
        ({"licence": False}, "licence"),
        ({"bad_rule": True}, "unknown rules"),
    ],
)
def test_broken_recipes_are_refused_with_the_reason(tmp_path, agent_run, change, reason):
    recipe = load_recipe(make_recipe(tmp_path, **change))
    report = conformance(recipe, tmp_path / "conf", agent_run_dir=agent_run)
    assert not report["conforms"]
    assert any(reason in f for f in report["failures"]), report["failures"]


def test_missing_scenario_file_cannot_load(tmp_path):
    folder = make_recipe(tmp_path)
    (folder / "scenarios" / "HAPPY.json").unlink()
    with pytest.raises(FileNotFoundError):
        load_recipe(folder)


def _recorded(recipe):
    """Reference recordings under the run's own id (stand-in for PHP execution)."""

    def execute(run_dir, output, *, php="php"):
        output.mkdir(parents=True)
        sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
        report = {
            "run_id": run_dir.name,
            "real_payment_qualified": False,
            "isolated_execution_qualified": False,
            "merchant_delivery_qualified": False,
            "normative_contract_sha256": hashlib.sha256(recipe.contract_bytes).hexdigest(),
            "capture_sha256": {},
        }
        for scenario in recipe.scenarios:
            for variant in ("OLD", "OLD_TWIN", "NEW"):
                name = f"{scenario}.{variant}.json"
                capture = json.loads((REFERENCE / "raw" / name).read_bytes())
                capture.update(graft_id=run_dir.name, run_id=run_dir.name + "-local-php")
                (output / name).write_text(json.dumps(capture))
                report["capture_sha256"][name] = sha(output / name)
        (output / "REPORT.json").write_text(json.dumps(report))
        return report

    return execute
