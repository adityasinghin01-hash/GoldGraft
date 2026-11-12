"""Offline local Phase 1 report. Never runs shops, calls providers or verifies service authority."""

import argparse
import importlib.util
import json
from pathlib import Path

from sandbox_config import load_config
from sandbox_config import status as credential_status

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / "pieces/shops/legacy-php-shop/phase1"
spec = importlib.util.spec_from_file_location("phase1_readiness", PHASE / "readiness.py")
readiness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(readiness)


def summarize(scenarios, dependencies, probes, source, credentials, component):
    """Local report. Supplied artifacts do not establish service/payment qualification."""
    known_probes = {p["probe"]: p for p in probes.get("checks", [])}
    credential_checks = []
    for name in ("oauth", "nvp-balance"):
        item = known_probes.get(name, {})
        valid = (
            probes.get("environment") == "sandbox"
            and item.get("status") == "PASS"
            and item.get("http_status") == 200
            and item.get("payment_operations") == 0
            and item.get("checkout_qualified") is False
            and item.get("reason") == "credential_probe_only"
        )
        credential_checks.append(
            {
                "probe": name,
                "status": "REPORTED_PASS" if valid else "UNVERIFIED",
                "evidence": "OPERATOR_REPORTED_NOT_INDEPENDENT_CAPTURE",
            }
        )
    portable_ok = (
        component.get("status") == "PASS"
        and component.get("evidence") == "LOCAL_WINDOWS_COMPONENT_CHECKS"
        and component.get("node_22_component_check") is True
        and component.get("node_version", "").startswith("v22.")
        and component.get("browser", {}).get("status") == "PASS"
        and component.get("payment_tests_run") is False
        and component.get("runtime_qualified") is False
    )
    ready = (
        source.get("status") == "SOURCE_MATCH"
        and portable_ok
        and credentials
        and all(c["configured"] for c in credentials.values())
        and all(p["status"] == "REPORTED_PASS" for p in credential_checks)
    )
    return {
        "document_kind": "local_phase1_progress_not_shared_evidence_or_proof",
        "team_revision": dependencies["team_revision"],
        "source": source,
        "credential_presence": credentials,
        "credential_checks": credential_checks,
        "portable_node22_component": "PASS" if portable_ok else "UNVERIFIED",
        "preparation_gate": "READY_FOR_COUNTERPART" if ready else "INCOMPLETE",
        "phase1_gate": "HOLD",
        "runtime_qualified": False,
        "checkout_qualified": False,
        "payment_operations_run_by_report": 0,
        "required_flows": [
            {
                "id": s["id"],
                "title": s["title"],
                "status": "BLOCKED",
                "attempted": False,
                "reason": "qualified_broker_runner_recorder_and_capture_evidence_missing",
                "dependencies": ["GU02", "GU03", "SH01"],
                "evidence_refs": [],
            }
            for s in scenarios["scenarios"]
        ],
        "dependencies": dependencies["required"],
        "limitation": (
            "Offline readiness only. Even supplied PASS flags cannot close "
            "payment or service qualification."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, help="explicit ignored credential JSON; values never printed"
    )
    parser.add_argument(
        "--source-root", type=Path, default=ROOT / ".context/review-2026-11-07/reference"
    )
    args = parser.parse_args()
    try:
        scenarios = json.loads((PHASE / "scenarios.json").read_text(encoding="utf-8"))
        dependencies = json.loads((PHASE / "dependencies.json").read_text(encoding="utf-8"))
        probes = json.loads((PHASE / "credential_checks.json").read_text(encoding="utf-8"))
        inventory = json.loads((PHASE / "source_inventory.json").read_text(encoding="utf-8"))
        component_path = ROOT / ".context/portable-lab-result.json"
        component = (
            json.loads(component_path.read_text(encoding="utf-8"))
            if component_path.exists()
            else {}
        )
        credentials = credential_status(load_config(args.config)) if args.config else {}
        result = summarize(
            scenarios,
            dependencies,
            probes,
            readiness.review_source(args.source_root, inventory),
            credentials,
            component,
        )
    except (OSError, ValueError, TypeError, KeyError):
        print(
            json.dumps({"phase1_gate": "HOLD", "reason": "local_report_input_invalid_or_missing"})
        )
        return 2
    print(json.dumps(result, indent=2))
    return 2  # A preparation report cannot pass the full phase gate.


if __name__ == "__main__":
    raise SystemExit(main())
