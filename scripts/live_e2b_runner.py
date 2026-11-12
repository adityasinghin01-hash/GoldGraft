#!/usr/bin/env python3
"""Explicit live smoke only: three small public-source command VMs, no merchant proof."""

import argparse
import json
import os
import stat
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from pieces.runner.container_runner import E2BIsolationBackend, IsolationNotEstablished

DEFAULT_KEY_FILE = Path.home() / ".config/goldgraft/e2b.env"


def _read_key(path):
    """Read one private dotenv value without evaluating shell code or logging it."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "r", encoding="utf-8") as stream:
            info = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_mode & 0o077
                or info.st_uid != os.getuid()
                or info.st_size > 16 * 1024
            ):
                raise ValueError
            values = []
            for line in stream.read(16 * 1024 + 1).splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                name, separator, value = line.partition("=")
                if name.strip() == "E2B_API_KEY" and separator:
                    value = value.strip()
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                        value = value[1:-1]
                    values.append(value)
            if len(values) != 1 or not values[0] or any(c.isspace() for c in values[0]):
                raise ValueError
            return values[0]
    except (OSError, ValueError, UnicodeError):
        raise IsolationNotEstablished("E2B private key file unavailable or invalid") from None


def smoke(api_key, *, sandbox_factory=None):
    backend = E2BIsolationBackend(
        api_key=api_key, authorize_remote=True, sdk_factory=sandbox_factory
    )
    records = []
    with tempfile.TemporaryDirectory(prefix="goldgraft-e2b-smoke-") as directory:
        source = Path(directory).resolve()
        (source / "main.py").write_text("print('goldgraft-e2b-smoke')\n", encoding="utf-8")
        cases = [
            ("success", ["python3", "main.py"], 10),
            ("nonzero", ["sh", "-c", "printf deliberate-failure >&2; exit 7"], 10),
            ("timeout", ["sleep", "5"], 1),
        ]
        for name, command, timeout in cases:
            try:
                result = backend.run(command, cwd=source, env={}, timeout_s=timeout)
            except IsolationNotEstablished as exc:
                records.append(
                    {
                        "case": name,
                        "passed": False,
                        "error": str(exc),
                        "sandbox_id": exc.sandbox_id,
                        "termination_confirmed": exc.termination_confirmed,
                    }
                )
                # Stop at the first unknown boundary or cleanup; never create another VM.
                break
            expected = {
                "success": result["exit_code"] == 0
                and result["stdout"] == "goldgraft-e2b-smoke\n"
                and not result["timed_out"],
                "nonzero": result["exit_code"] == 7
                and result["stderr"] == "deliberate-failure"
                and not result["timed_out"],
                "timeout": result["timed_out"] and result["exit_code"] is None,
            }[name]
            records.append(
                {
                    "case": name,
                    "passed": bool(
                        expected
                        and result["isolation_verified"]
                        and result["termination_confirmed"]
                    ),
                    "result": result,
                }
            )
            if not records[-1]["passed"]:
                break
    return {
        "created_at": datetime.now(UTC).isoformat(),
        "qualification_scope": "bounded_command_primitive",
        "passed": len(records) == 3 and all(record["passed"] for record in records),
        "php_merchant_qualification": False,
        "cases": records,
    }


def main(argv=None, *, sandbox_factory=None, key_file=DEFAULT_KEY_FILE):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--authorize-e2b",
        action="store_true",
        help="explicitly authorise up to three remote smoke VMs",
    )
    parser.add_argument("--smoke", action="store_true", required=True)
    parser.add_argument("--report-dir", type=Path, default=Path("reports/e2b"))
    args = parser.parse_args(argv)
    if not args.authorize_e2b:
        parser.error("remote jobs require --authorize-e2b; key presence is not authority")
    # Check report destination before provisioning, and never overwrite earlier evidence.
    args.report_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix="e2b-smoke-",
        suffix=".json",
        dir=args.report_dir,
        delete=False,
    ) as report:
        try:
            key = _read_key(key_file)
            evidence = smoke(key, sandbox_factory=sandbox_factory)
        except IsolationNotEstablished as exc:
            evidence = {
                "passed": False,
                "error": str(exc),
                "sandbox_id": exc.sandbox_id,
                "termination_confirmed": exc.termination_confirmed,
            }
        json.dump(evidence, report, indent=2)
        report.write("\n")
        report_path = report.name
    print(f"E2B smoke {'passed' if evidence['passed'] else 'held'}; report: {report_path}")
    return 0 if evidence["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
