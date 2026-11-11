"""Developer assembly for labelled persistent offline runtime only."""

import argparse
import json
from pathlib import Path

from goldgraft_foundation.offline_profile import load_runtime_profile

from .herald import HeraldInputs, deterministic_renderer, inspect_text
from .model_readiness import model_access_report
from .roles import herald_configuration, surveyor_configuration
from .scheduler import tick
from .surveyor import inspect_inventory

RUN = "fake:runtime-run"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["doctor", "run", "status", "cancel", "resume", "inspect"]
    )
    parser.add_argument("--mode", choices=["offline", "service"], default="offline")
    parser.add_argument("--state-file", type=Path)
    parser.add_argument(
        "--check-local-key",
        action="store_true",
        help="doctor only: presence/permissions check of the approved local file; never loads it",
    )
    parser.add_argument(
        "--fixture",
        choices=["two_task_read", "surveyor_inventory", "surveyor_herald"],
        default="two_task_read",
    )
    parser.add_argument(
        "--projection", choices=["private_status", "public_safe"], default="private_status"
    )
    args = parser.parse_args(argv)
    if args.mode != "offline":
        parser.error("UNSUPPORTED: actual service/model profile is not qualified")
    if args.check_local_key and args.command != "doctor":
        parser.error("--check-local-key is only valid for doctor")
    if args.command == "doctor":
        print(
            json.dumps(
                {
                    "mode": "offline",
                    "evidence_class": "scripted",
                    "service_profile": "NOT QUALIFIED",
                    "paid_model_checks": "NOT RUN",
                    "ceiling_micro_usd": 0,
                    "max_turns": 12,
                    "max_tools": 24,
                    "model_access": model_access_report(
                        local_key_file=Path.home() / ".config/goldgraft/anthropic.env"
                        if args.check_local_key
                        else None
                    ),
                }
            )
        )
        return 0
    if args.state_file is None:
        parser.error("--state-file is required")
    if args.command != "run" and not args.state_file.is_file():
        parser.error("MISSING_EVIDENCE: existing state file required")
    try:
        ports = load_runtime_profile(
            args.mode,
            args.state_file,
            fixture=args.fixture,
            configuration=surveyor_configuration()
            if args.fixture in {"surveyor_inventory", "surveyor_herald"}
            else None,
            herald_configuration=herald_configuration(projection=args.projection)
            if args.fixture == "surveyor_herald"
            else None,
            renderer=deterministic_renderer if args.fixture == "surveyor_herald" else None,
        )
        if args.command == "cancel":
            ports.control.cancel(RUN, "fake:cli-cancel")
        if args.command in {"run", "resume"}:
            tick(RUN, ports.clock(), ports)
        snapshot = ports.control.snapshot(RUN)
        if args.command == "inspect":
            if args.fixture == "surveyor_herald":
                task = next((t for t in snapshot.tasks if t.task.task_id == "herald"), None)
                if task is None:
                    raise ValueError("MISSING_EVIDENCE Herald dependency")
                payload, facts = ports.artifacts.inspect_herald(task, ports.context_for("herald"))
                print(
                    json.dumps(inspect_text(payload, HeraldInputs.model_validate(facts)), indent=2)
                )
                return 0
            if args.fixture != "surveyor_inventory":
                raise ValueError("UNSUPPORTED inventory inspection requires Surveyor fixture")
            task = snapshot.tasks[0]
            descriptor, payload = ports.artifacts.inspect_output(task, ports.context_for("survey"))
            result = ports.control.result("survey")
            print(
                json.dumps(
                    inspect_inventory(
                        payload,
                        input_refs=task.task.input_refs,
                        output_ref=descriptor.ref,
                        subject=descriptor.subject_digest,
                        evidence_refs=result.evidence_refs,
                        omissions=ports.artifacts.bundle["omissions"],
                    ),
                    indent=2,
                )
            )
            return 0
        print(
            json.dumps(
                {
                    "mode": "offline",
                    "evidence_class": "scripted",
                    "accepted_results": ports.control.accepted_result_count(),
                    "model_dispatches": ports.model.total_dispatches(),
                    "tool_dispatches": ports.tools.total_dispatches(),
                    "termination": "NOT APPLICABLE: no external process was dispatched",
                    "snapshot": snapshot.model_dump(mode="json"),
                }
            )
        )
        return 0
    except ValueError as exc:
        # Never echo untrusted arguments, source, provider error bodies or secret values.
        print(json.dumps({"error": str(exc).split()[0], "evidence_class": "scripted"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
