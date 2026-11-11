"""Developer-only, source-owned role construction and inspection; no API/provider jobs."""

import argparse
import json
from pathlib import Path

from goldgraft_foundation.offline_profile import load_component_profile

from . import component
from .component_agents import IMPLEMENTED_ROLES
from .roles import COMPONENT_POLICIES, component_configuration
from .scheduler import tick


def create(role, path, *, operation=None, data=None, clock=None):
    policy = COMPONENT_POLICIES[role]
    operation = operation or policy.operation
    if operation not in (policy.operation,) + policy.additional_operations:
        raise ValueError("DENIED role operation")
    module = component.implementation(role)
    data = module.sample(operation) if data is None else data
    typed = module.Input.model_validate(data)
    return load_component_profile(
        "offline",
        path,
        configuration=component_configuration(role),
        operation=operation,
        data=typed.model_dump(mode="json"),
        schemas=module.schemas(operation, typed),
        planner=component.requests,
        renderer=component.synthesize,
        clock=clock,
        output_policy="candidate_child" if role == "Grafter" else "same_subject",
        workspace_ref=typed.workspace_ref if role == "Grafter" else None,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "status", "inspect", "resume"])
    parser.add_argument("--role", choices=IMPLEMENTED_ROLES, required=True)
    parser.add_argument("--operation")
    parser.add_argument("--state-file", type=Path, required=True)
    parser.add_argument("--mode", choices=["offline", "service"], default="offline")
    args = parser.parse_args(argv)
    if args.mode != "offline":
        parser.error("UNSUPPORTED real service qualification missing")
    if args.command != "run" and not args.state_file.is_file():
        parser.error("existing state required")
    try:
        p = create(args.role, args.state_file, operation=args.operation)
        if args.command in {"run", "resume"}:
            tick(p.run_ref, p.clock(), p)
        snapshot = p.control.snapshot(p.run_ref)
        task = snapshot.tasks[0]
        if args.command == "inspect":
            outputs = p.artifacts.inspect_outputs(task, p.context_for(task.task.task_id))
            result = component.inspect_outputs(args.role, outputs)
            result.update(input_refs=task.task.input_refs, output_refs=task.output_refs)
        else:
            result = {
                "evidence_class": "scripted",
                "model_api_calls": 0,
                "snapshot": snapshot.model_dump(mode="json"),
                "model_dispatches": p.model.total_dispatches(),
                "tool_dispatches": p.tools.total_dispatches(),
            }
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, TypeError):
        print(json.dumps({"error": "DENIED_OR_MISSING_EVIDENCE", "evidence_class": "scripted"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
