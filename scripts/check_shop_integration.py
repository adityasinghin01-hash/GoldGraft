"""Execute the accepted shop socket and actual connected proof pipeline, offline."""

import argparse
import json
import os
import subprocess
import sys
import uuid
from collections import Counter
from pathlib import Path

from check_team_boundaries import ROOT, host_environment, team_revision


def worker(team):
    from integration.connected_run import connect_run
    from integration.shop_socket import RecipeProof, conformance, load_recipe

    folder = ROOT / ".context/shop-integration" / uuid.uuid4().hex
    directory = folder / "operator-fixture"
    directory.mkdir(parents=True)
    pack = ROOT / "pieces/shops/vijay-php-reference"
    fixture = ROOT / "fixtures/socket-candidate"
    rows = []
    for path in sorted(fixture.rglob("*.php")):
        rel = path.relative_to(fixture).as_posix()
        old = pack / "source" / rel
        rows.append(
            {
                "path": rel,
                "before": old.read_text(encoding="utf-8") if old.exists() else "",
                "after": path.read_text(encoding="utf-8"),
                "author": "reviewed_operator_fixture",
            }
        )
    (directory / "RESULT.json").write_text(
        json.dumps(
            {
                "shop": "legacy-php-shop",
                "status": "completed",
                "producer": "reviewed_operator_fixture",
                "tasks": [],
                "model_calls": 0,
            }
        ),
        encoding="utf-8",
    )
    (directory / "CHANGES.json").write_text(
        json.dumps({"files": rows, "open_items": ["offline compatibility fixture only"]}),
        encoding="utf-8",
    )
    outputs = {
        "architect": [
            {
                "schema": "TargetPlan/1",
                "payload": json.loads((pack / "target_plan.json").read_bytes()),
            }
        ]
    }
    (directory / "OUTPUTS.json").write_text(json.dumps(outputs), encoding="utf-8")
    recipe = load_recipe(pack)
    result = conformance(
        recipe,
        folder / "conformance",
        agent_run_dir=directory,
        php=os.environ["VIJAY_PHP"],
    )
    if not result["conforms"]:
        raise ValueError("actual_shop_socket_refused:" + json.dumps(result))
    run_dir = folder / "conformance" / ("conformance-" + recipe.shop_id)
    proof = RecipeProof(run_dir, recipe)
    summary = connect_run(run_dir, folder / "connected", recipe=recipe, php=os.environ["VIJAY_PHP"])
    counts = dict(Counter(str(row["verdict"].grade) for row in proof.rows))
    report = {
        "status": "PASS",
        "evidence": "ACTUAL_SHOP_SOCKET_PHP_AND_CONNECTED_PROOF_SIMULATED_PAYPAL",
        "team_commit": team_revision(team),
        "shop_id": recipe.shop_id,
        "unique_reference_shops": 1,
        "conformance": result,
        "capture_count": len(proof.report["capture_sha256"]),
        "scenario_count": len(proof.rows),
        "scenario_grades": counts,
        "executed_mutations": len(proof.report.get("candidate_mutations", [])),
        "unguarded_critical_rules": proof.report.get("unguarded_critical_rule_ids", []),
        "connected": summary,
        "candidate_producer": "reviewed_operator_fixture_not_an_agent_run",
        "real_provider_calls": 0,
        "model_calls": 0,
        "real_payment_qualified": False,
        "isolated_execution_qualified": False,
        "merchant_delivery_qualified": False,
    }
    # A modified byte must be refused by the real counterpart, even though the
    # original local run is valid. Preserve the original capture immediately.
    target = run_dir / "local-proof/HAPPY.NEW.json"
    original = target.read_bytes()
    try:
        target.write_bytes(original + b" ")
        try:
            RecipeProof(run_dir, recipe)
        except ValueError:
            report["recording_drift_rejected"] = True
        else:
            raise ValueError("modified_recording_not_rejected")
    finally:
        target.write_bytes(original)
    destination = ROOT / ".context/shop-integration/result.json"
    destination.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("connected",)}, default=str))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--team-root", type=Path, default=ROOT)
    p.add_argument("--worker", action="store_true")
    args = p.parse_args()
    team = args.team_root.resolve()
    if args.worker:
        return worker(team)
    team_revision(team)
    env = host_environment(team)
    env["GOLDGRAFT_TEAM_ROOT"] = str(team)
    # All host temporary copies go to D:, not the nearly full system drive.
    state = ROOT / ".context/host-temp"
    state.mkdir(parents=True, exist_ok=True)
    env["TEMP"] = env["TMP"] = str(state)
    python = sys.executable
    process = subprocess.run(
        [str(python), str(Path(__file__)), "--worker", "--team-root", str(team)],
        check=False,
        cwd=team,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=200,
    )
    folder = ROOT / ".context/shop-integration"
    folder.mkdir(exist_ok=True)
    (folder / "execution.log").write_text(process.stdout + process.stderr, encoding="utf-8")
    if process.returncode:
        print(process.stderr[-4500:])
    else:
        print(process.stdout)
    return process.returncode


if __name__ == "__main__":
    raise SystemExit(main())
