"""Recreate the ignored contract cache from exact Git blobs; no network or schema edits."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from check_shop_pack import PINNED, ROOT
from check_team_boundaries import team_revision


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team-root", type=Path, default=ROOT)
    args = parser.parse_args()
    team = args.team_root.resolve()
    git = ["git", "-c", "safe.directory=" + team.as_posix(), "-C", str(team)]
    actual_team_revision = team_revision(team)
    files = {}
    for name, expected in PINNED.items():
        # Read Git objects, not Windows CRLF-converted working tree bytes.
        raw = subprocess.check_output(
            [*git, "cat-file", "blob", "HEAD:contracts/src/goldgraft_contracts/" + name]
        )
        actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if actual != expected:
            raise ValueError("pinned_contract_changed")
        files[name] = raw
    target = ROOT / ".context/team-contracts/goldgraft_contracts"
    if any(p.is_symlink() for p in [target, *target.parents]):
        raise ValueError("linked_cache")
    for name, raw in files.items():
        path = target / name
        if path.exists() and path.read_bytes() != raw:
            raise ValueError("existing_contract_cache_drift")
    target.mkdir(parents=True, exist_ok=True)
    for name, raw in files.items():
        (target / name).write_bytes(raw)
    if not (target / "__init__.py").exists():
        (target / "__init__.py").write_text("", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "PASS",
                "files": len(files),
                "team_revision": actual_team_revision,
                "provider_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
