"""Replay the offline proof smoke test for the PayPal sandbox integration."""

import argparse
import json
from pathlib import Path

from integration.offline import run_offline


def run_sandbox_payment(
    *, dry_run: bool = False, state_dir: Path = Path(".goldgraft/sandbox-dry-run")
) -> dict:
    if not dry_run:
        raise ValueError(
            "Live sandbox execution requires a qualified payment transport, "
            "isolated recorder and authenticated callback. Use --dry-run for fixture replay."
        )
    report = run_offline(state_dir)
    return {
        "live": False,
        "evidence_class": report["evidence_class"],
        "provider_calls": report["provider_calls"],
        "fixture_verdicts": {
            verdict["scenario_id"]: verdict["grade"]
            for verdict in report["fixtures"]["verdicts"]
        },
        "simulated_payment_proof": report["payment_recorder"]["proof_status"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Replay without provider calls")
    parser.add_argument("--state-dir", type=Path, default=Path(".goldgraft/sandbox-dry-run"))
    args = parser.parse_args()
    try:
        result = run_sandbox_payment(dry_run=args.dry_run, state_dir=args.state_dir)
    except ValueError as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
