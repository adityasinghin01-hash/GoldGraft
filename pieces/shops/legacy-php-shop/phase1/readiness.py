"""Offline reference review. Local worksheet only; not a shared WorkPackage model."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
ENV_GROUPS = {
    "rest_auth": ("PAYPAL_SANDBOX_CLIENT_ID", "PAYPAL_SANDBOX_CLIENT_SECRET"),
    "nvp_auth": ("PAYPAL_NVP_USER", "PAYPAL_NVP_PWD", "PAYPAL_NVP_SIGNATURE"),
    "buyer": ("PAYPAL_SANDBOX_BUYER_EMAIL", "PAYPAL_SANDBOX_BUYER_PASSWORD"),
    "recipient": ("SHOP_RECEIVER_EMAIL",),
}


def credential_presence(environ):
    """Names/presence only. Do not serialize credential values or their hashes."""
    return {
        group: {
            "configured": all(bool(environ.get(n, "").strip()) for n in names),
            "missing_names": [n for n in names if not environ.get(n, "").strip()],
        }
        for group, names in ENV_GROUPS.items()
    }


def linked(path):
    return path.is_symlink() or getattr(path, "is_junction", lambda: False)()


def review_source(root, inventory):
    """Compare all reference files without executing code, loading .env or following links."""
    issues = []
    expected = {}
    for entry in inventory["files"]:
        name = entry["path"]
        pure = PurePosixPath(name)
        if (
            not name
            or "\\" in name
            or pure.is_absolute()
            or ".." in pure.parts
            or str(pure) != name
            or ":" in name
            or name in expected
        ):
            raise ValueError("invalid inventory path")
        expected[name] = entry["git_blob_sha1"]
    root = Path(root)
    if linked(root) or any(linked(p) for p in root.parents):
        return {"status": "HOLD", "matched_files": 0, "issues": ["linked_source_root"]}
    if not root.is_dir():
        return {"status": "HOLD", "matched_files": 0, "issues": ["missing_source_root"]}
    actual = set()
    for count, path in enumerate(root.rglob("*"), 1):
        if count > 500:
            return {"status": "HOLD", "matched_files": 0, "issues": ["source_limit"]}
        name = path.relative_to(root).as_posix()
        if linked(path):
            issues.append("linked_path:" + name)
        elif path.is_file():
            actual.add(name)
    matched = 0
    for name, digest in expected.items():
        path = root / name
        if any(linked(p) for p in [path, *path.parents]):
            issues.append("linked_expected_path:" + name)
        elif name not in actual:
            issues.append("missing:" + name)
        elif path.stat().st_size > 2_000_000:
            issues.append("oversized:" + name)
        else:
            data = path.read_bytes()
            blob = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
            if hashlib.sha1(blob).hexdigest() != digest:
                issues.append("changed:" + name)
            else:
                matched += 1
    issues.extend("unexpected:" + name for name in sorted(actual - expected.keys()))
    return {
        "status": "SOURCE_MATCH" if not issues else "HOLD",
        "matched_files": matched,
        "issues": sorted(issues),
    }


def report(source_root=None, environ=None):
    inventory = json.loads((HERE / "source_inventory.json").read_text(encoding="utf-8"))
    scenarios = json.loads((HERE / "scenarios.json").read_text(encoding="utf-8"))
    source = (
        review_source(source_root, inventory)
        if source_root
        else {"status": "UNVERIFIED", "matched_files": 0, "issues": ["source_root_not_supplied"]}
    )
    return {
        "document_kind": "local_phase1_readiness_not_shared_contract",
        "team_revision": inventory["team_revision"],
        "evidence_level": "LOCAL_STATIC_INSPECTION",
        "source": source,
        "credential_presence": credential_presence(os.environ if environ is None else environ),
        "required_flows": [{"id": s["id"], "status": "UNVERIFIED"} for s in scenarios["scenarios"]],
        "dependencies": {
            "docker_runtime": "DEFERRED_PORTABLE_WINDOWS_COMPONENT_CHECKS_PASS_LINUX_PENDING",
            "SI01_new_shared_contracts": "PENDING",
            "GU02_sandbox_broker": "PENDING",
            "GU03_isolated_runner_recorder": "PENDING",
            "protected_lab_gateway": "PENDING",
            "qualified_image_digest_and_runtime_identity": "PENDING",
        },
        "runtime_qualified": False,
        "payment_evidence": "NOT_RUN",
        "phase_gate": "HOLD",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, help="pinned reference root; never executed")
    args = parser.parse_args()
    try:
        result = report(args.source_root)
    except (OSError, ValueError, KeyError, TypeError):
        print(json.dumps({"phase_gate": "HOLD", "error": "local_input_invalid_or_unreadable"}))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["source"]["status"] == "SOURCE_MATCH" else 2


if __name__ == "__main__":
    raise SystemExit(main())
