"""Create a local, source-hashed handoff; never uploads or marks external gates passed."""

import hashlib
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = [
    "pieces/shops",
    "pieces/switch-libs",
    "tools/sponsors",
    "scripts",
    "tests",
    "integration_tests",
    "fixtures/socket-candidate",
    "docs/vijay",
]
ROOT_FILES = [
    "AGENTS.md",
    "README.md",
    ".gitattributes",
    ".gitignore",
    "package.json",
    "package-lock.json",
]
EXTENSIONS = {
    ".py",
    ".php",
    ".mjs",
    ".ts",
    ".json",
    ".yaml",
    ".yml",
    ".md",
    ".cmd",
    ".html",
    ".css",
    ".svg",
    ".txt",
}


def main():
    reports = {
        name: json.loads((ROOT / path).read_text(encoding="utf-8"))
        for name, path in {
            "local_profile": ".context/local-profile/result.json",
            "actual_counterparts": ".context/team-boundaries/result.json",
            "shop_socket_and_proof": ".context/shop-integration/result.json",
        }.items()
    }
    if any(r["status"] != "PASS" for r in reports.values()):
        raise ValueError("required_local_check_not_passed")
    paths = [ROOT / name for name in ROOT_FILES]
    for folder in FOLDERS:
        for path in (ROOT / folder).rglob("*"):
            if any(
                p in {"__pycache__", "node_modules", ".secrets", ".context", ".git"}
                for p in path.parts
            ):
                continue
            if path.is_symlink():
                raise ValueError("linked_handoff_input")
            if path.is_file() and (
                path.suffix in EXTENSIONS or path.name.startswith(("LICENSE", "Dockerfile"))
            ):
                paths.append(path)
    records = {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(set(paths))
    }
    summary = {
        "kind": "LOCAL_ROLE_IMPLEMENTATION_HANDOFF_NOT_OPERATIONAL_QUALIFICATION",
        "generated_at": datetime.now(UTC).isoformat(),
        "source_revision": "LOCAL_UNCOMMITTED",
        "team_commit": reports["actual_counterparts"]["team_commit"],
        "local_status": "READY_FOR_TEAM_REVIEW",
        "local_check_groups": len(reports["local_profile"]["steps"]),
        "actual_counterpart_tests": reports["actual_counterparts"]["tests"],
        "shop_socket_conforms": reports["shop_socket_and_proof"]["conformance"]["conforms"],
        "recordings": reports["shop_socket_and_proof"]["capture_count"],
        "scenario_grades": reports["shop_socket_and_proof"]["scenario_grades"],
        "executed_mutations": reports["shop_socket_and_proof"]["executed_mutations"],
        "unguarded_critical_rules": reports["shop_socket_and_proof"]["unguarded_critical_rules"],
        "unique_reference_shops": 1,
        "role_scenarios": 14,
        "socket_scenarios": 9,
        "full_phase_gates_complete": False,
        "payment_qualified": False,
        "isolation_qualified": False,
        "merchant_exit_qualified": False,
        "model_calls_in_this_delivery": 0,
        "provider_calls_in_this_delivery": 0,
        "published": False,
        "files": records,
        "remaining": [
            "eight critical rules without executed candidate mutation guards",
            "genuine fourteen-scenario shop sandbox evidence",
            "qualified isolation/exact runtime image",
            "real callback ingress and custody qualification",
            "approved state bootstrap/apply/final runtime and merchant exit",
            "qualified proof/signing on the exact merchant subject",
            "Kernel/account/credit qualification",
        ],
    }
    folder = ROOT / ".context/handoff"
    folder.mkdir(parents=True, exist_ok=True)
    manifest = folder / "MANIFEST.json"
    manifest.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    bundle = folder / "goldgraft-vijay-local.zip"
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in records:
            archive.write(ROOT / name, name)
        archive.write(manifest, "HANDOFF_STATUS.json")
    with zipfile.ZipFile(bundle) as archive:
        for name, expected in records.items():
            if hashlib.sha256(archive.read(name)).hexdigest() != expected:
                raise ValueError("handoff_byte_mismatch")
        if any(name.startswith((".context/", ".secrets/", ".git/")) for name in archive.namelist()):
            raise ValueError("private_state_in_handoff")
    print(
        json.dumps(
            {
                "status": "PASS",
                "files": len(records),
                "bundle": str(bundle),
                "sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
                "published": False,
            }
        )
    )


if __name__ == "__main__":
    main()
