"""Repeat offline OLD/OLD_TWIN component checks. Never qualifies payment or team runtime."""

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = [(variant, repeat) for variant in ("OLD", "OLD_TWIN") for repeat in range(1, 4)]


def summarize(runs):
    reasons = []
    if [(r.get("variant"), r.get("repeat")) for r in runs] != EXPECTED:
        reasons.append("six_expected_variant_repetitions_missing")
    identities = [r.get("run_id") for r in runs]
    stores = [r.get("work_directory") for r in runs]
    if not all(identities) or len(set(identities)) != len(identities):
        reasons.append("run_identity_not_independent")
    if not all(stores) or len(set(stores)) != len(stores):
        reasons.append("run_state_not_independent")
    source = runs[0].get("source_sha256") if runs else None
    if not source or any(r.get("source_sha256") != source for r in runs):
        reasons.append("source_identity_missing_or_drifted")
    for row in runs:
        store = row.get("order_store") or {}
        if (
            row.get("status") != "PASS"
            or row.get("evidence") != "LOCAL_WINDOWS_COMPONENT_CHECKS"
            or row.get("node_22_component_check") is not True
            or not row.get("node_version", "").startswith("v22.")
            or row.get("payment_tests_run") is not False
            or row.get("runtime_qualified") is not False
            or row.get("browser", {}).get("status") != "PASS"
            or store.get("status") != "PASS"
            or store.get("payment_operations") != 0
        ):
            reasons.append("component_run_unverified")
            break
    return {
        "document_kind": "local_phase2_baseline_component_characterization_not_job_or_proof",
        "component_status": "PASS" if not reasons else "HOLD",
        "reasons": sorted(set(reasons)),
        "phase2_gate": "HOLD",
        "phase1_gate": "HOLD",
        "runtime_qualified": False,
        "payment_operations": 0,
        "qualified_purchases": 0,
        "new_candidate_implemented": False,
        "runs": runs,
        "baseline_defects": [
            {
                "run_id": r.get("run_id"),
                **((r.get("order_store") or {}).get("corruption_observation") or {}),
            }
            for r in runs
            if (r.get("order_store") or {}).get("corruption_observation", {}).get("observed")
        ],
        "limitations": [
            "Synthetic local orders are not payment/order correspondence proof",
            "Six cart runs are not six purchases or qualified OLD/OLD_TWIN captures",
            "Protected runtime, broker, recorder, gateway and proof integration remain required",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", type=Path, required=True)
    args = parser.parse_args()
    runs = []
    for variant, repeat in EXPECTED:
        command = [
            sys.executable,
            str(ROOT / "scripts/portable_lab.py"),
            "--node",
            str(args.node),
            "--characterize-store",
            "--variant",
            variant,
        ]
        try:
            process = subprocess.run(command, capture_output=True, text=True, timeout=120)
            row = json.loads(process.stdout)
            row["repeat"] = repeat
            if process.returncode != 0:
                row["status"] = "HOLD"
        except (OSError, ValueError, subprocess.TimeoutExpired):
            row = {
                "status": "HOLD",
                "variant": variant,
                "repeat": repeat,
                "reason": "local_component_command_unverified",
            }
        runs.append(row)
        print(
            json.dumps(
                {
                    "variant": variant,
                    "repeat": repeat,
                    "status": row["status"],
                    "run_id": row.get("run_id"),
                    "payment_operations": 0,
                }
            ),
            flush=True,
        )
        if row["status"] != "PASS":
            break
    result = summarize(runs)
    result["checked_at"] = datetime.now(UTC).isoformat()
    folder = ROOT / ".context/phase2"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "baseline-result.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "component_status": result["component_status"],
                "phase2_gate": "HOLD",
                "run_count": len(runs),
                "baseline_defect_observations": len(result["baseline_defects"]),
                "report": str(path),
                "payment_operations": 0,
            }
        )
    )
    return 0 if result["component_status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
