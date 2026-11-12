"""Check actual pinned backend/contracts against Vijay's contribution; no services/push."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN = "c209bf6c1d8f5fe31c78a00bef6bd55f93668848"
HISTORICAL_PIN = "9968f9b17327f7e424e8d202c7402b1d90c6036b"


def team_revision(team):
    actual = subprocess.check_output(
        ["git", "-c", "safe.directory=" + team.as_posix(), "-C", str(team), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    # Same-repository tests exercise the checkout explicitly selected by the
    # operator. External compatibility checkouts remain pinned. Neither grants
    # live authority or host isolation; those flags stay false.
    if team != ROOT and actual not in {PIN, HISTORICAL_PIN}:
        raise ValueError("reviewed_external_team_revision_required")
    return actual


def host_environment(team):
    env = {
        k: os.environ[k] for k in ("SystemRoot", "WINDIR", "TEMP", "TMP", "PATH") if k in os.environ
    }
    env["PYTHONPATH"] = os.pathsep.join(
        str(p)
        for p in (
            team,
            team / "contracts/src",
            team / "foundation/src",
            team / "fakes/src",
        )
    )
    env["VIJAY_WORKSPACE"] = str(ROOT)
    metadata = ROOT / ".context/portable-php.json"
    php = os.environ.get("VIJAY_PHP")
    if not php and metadata.exists():
        php = json.loads(metadata.read_text(encoding="utf-8"))["php"]
    if not php:
        php = shutil.which("php")
    if not php:
        raise ValueError("native_php_required_for_boundary_profile")
    env["VIJAY_PHP"] = php
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--team-root", type=Path, default=ROOT)
    args = p.parse_args()
    team = args.team_root.resolve()
    actual = team_revision(team)
    python = sys.executable
    folder = ROOT / ".context/team-boundaries"
    folder.mkdir(parents=True, exist_ok=True)
    junit = folder / "pytest.xml"
    process = subprocess.run(
        [
            str(python),
            "-m",
            "pytest",
            "-q",
            str(ROOT / "integration_tests/test_vijay_boundaries.py"),
            "--basetemp",
            str(folder / "tmp"),
            "--junitxml",
            str(junit),
            "-p",
            "no:cacheprovider",
        ],
        check=False,
        cwd=team,
        env=host_environment(team),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    (folder / "pytest.log").write_text(process.stdout + process.stderr, encoding="utf-8")
    suite = ET.parse(junit).getroot().find("testsuite") if junit.exists() else None
    result = {
        "status": "PASS" if process.returncode == 0 else "HOLD",
        "team_commit": actual,
        "evidence": "ACTUAL_BACKEND_CONTRACTS_PHP_WITH_INJECTED_HTTP_AND_VERIFIERS",
        "tests": int(suite.get("tests", 0)) if suite is not None else 0,
        "skipped": int(suite.get("skipped", 0)) if suite is not None else 0,
        "real_provider_calls": 0,
        "payment_qualified": False,
        "isolation_qualified": False,
        "merchant_exit_qualified": False,
        "published": False,
    }
    (folder / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))
    if process.returncode:
        print(process.stdout[-6000:])
    return process.returncode


if __name__ == "__main__":
    raise SystemExit(main())
