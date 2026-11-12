"""Run the implemented local profile only. No external service, upload or qualification claim."""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.version_info[:2] != (3, 12):
        print(json.dumps({"status": "BLOCKED", "reason": "use_isolated_python_3_12_environment"}))
        return 2
    try:
        node = json.loads((ROOT / ".context/portable-node.json").read_text(encoding="utf-8"))[
            "node"
        ]
        php = json.loads((ROOT / ".context/portable-php.json").read_text(encoding="utf-8"))["php"]
    except (OSError, ValueError, KeyError):
        print(
            json.dumps(
                {"status": "BLOCKED", "reason": "verified_portable_runtime_metadata_missing"}
            )
        )
        return 2
    steps = []

    def step(name, command, *, timeout=120, json_output=True):
        process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        if process.returncode:
            steps.append(
                {
                    "name": name,
                    "status": "HOLD",
                    "reason": "local_check_failed_or_dependency_missing",
                }
            )
            return False
        if json_output:
            value = json.loads(process.stdout)
        else:
            count = re.search(r"Ran (\d+) tests", process.stderr)
            if not count or "skipped=" in process.stderr:
                steps.append(
                    {"name": name, "status": "HOLD", "reason": "test_count_or_skip_unverified"}
                )
                return False
            value = {"cases": int(count[1]), "skipped": 0}
        steps.append({"name": name, "status": "PASS", "result": value})
        print(json.dumps({"step": name, "status": "PASS"}), flush=True)
        return True

    commands = [
        (
            "python_unit_tests",
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
            False,
        ),
        (
            "switch_libraries",
            [sys.executable, str(ROOT / "scripts/check_switches.py"), "--node", node, "--php", php],
            True,
        ),
        (
            "rollout_decision_consumer",
            [sys.executable, str(ROOT / "scripts/check_rollout.py")],
            True,
        ),
        (
            "sponsor_asset_scope",
            [sys.executable, str(ROOT / "scripts/check_sponsor_assets.py")],
            True,
        ),
        (
            "usd_cart_domain",
            [php, "-n", str(ROOT / "pieces/shops/legacy-php-shop/domain/test_usd_cart.php")],
            True,
        ),
        ("new_php_candidate", [sys.executable, str(ROOT / "scripts/check_candidate.py")], True),
        (
            "candidate_browser_lifecycle",
            [sys.executable, str(ROOT / "scripts/check_candidate_browser.py")],
            True,
        ),
        ("shop_pack_contract", [sys.executable, str(ROOT / "scripts/check_shop_pack.py")], True),
        (
            "shop_start_buyer_stop",
            [sys.executable, str(ROOT / "scripts/check_local_shop.py"), "--node", node],
            True,
        ),
    ]
    try:
        for name, command, is_json in commands:
            if not step(name, command, json_output=is_json):
                break
        if len(steps) == len(commands) and all(s["status"] == "PASS" for s in steps):
            previous = ROOT / ".context/phase2/baseline-result.json"
            orders = []
            if previous.exists():
                baseline = json.loads(previous.read_text(encoding="utf-8"))
                if baseline.get("runs"):
                    path = Path(baseline["runs"][-1]["work_directory"]) / "src/data/orders.json"
                    orders = ["--orders", str(path)]
            if orders:
                step(
                    "read_only_state_inventory",
                    [
                        sys.executable,
                        str(ROOT / "pieces/shops/legacy-php-shop/state_recipe/inspect.py"),
                        *orders,
                    ],
                )
            else:
                steps.append(
                    {
                        "name": "read_only_state_inventory",
                        "status": "HOLD",
                        "reason": "synthetic_state_fixture_not_supplied",
                    }
                )
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
        steps.append(
            {"name": "local_execution", "status": "HOLD", "reason": "input_or_process_unverified"}
        )
    passed = len(steps) == len(commands) + 1 and all(s["status"] == "PASS" for s in steps)
    report = {
        "status": "PASS" if passed else "HOLD",
        "evidence": "LOCAL_COMPONENT_PROFILE_ONLY",
        "steps": steps,
        "runtime_qualified": False,
        "payment_qualified": False,
        "external_service_calls": 0,
        "pushes": 0,
        "open_gates": [
            "SI01_new_interfaces",
            "GU02_broker",
            "GU03_runtime_recorder_gateway",
            "SH01_SH02_actual_proof_integration",
            "genuine_payment_captures",
            "GU04_GU05_apply_state_and_exit_qualification",
        ],
    }
    folder = ROOT / ".context/local-profile"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "completed_steps": len(steps),
                "payment_qualified": False,
                "report": str(folder / "result.json"),
            }
        )
    )
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
