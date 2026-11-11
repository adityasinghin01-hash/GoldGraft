"""Offline integrated construction evidence; no provider/model connection or apply."""

import argparse
import json
from pathlib import Path

from .scheduler import tick
from .workflow import create, inspect


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "resume", "inspect"])
    parser.add_argument("--state-file", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command != "run" and not args.state_file.is_file():
        parser.error("existing state required")
    p = create(args.state_file)
    if args.command != "inspect":
        tick(p.run_ref, p.clock(), p)
    result = inspect(p)
    result.update(
        model_dispatches=p.model.total_dispatches(), tool_dispatches=p.tools.total_dispatches()
    )
    if args.command == "inspect":
        result["artifacts"] = {
            t.task.task_id: p.artifacts.committed(t.task.task_id)[1]
            for t in p.control.snapshot(p.run_ref).tasks
            if t.state == "succeeded"
        }
    print(json.dumps(result, indent=2))
    return 0 if all(t.state == "succeeded" for t in p.control.snapshot(p.run_ref).tasks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
