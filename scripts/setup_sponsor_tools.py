"""Install reviewed local sponsor tools from the committed manifest/lock.

Installs on D: without account actions.
"""

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/sponsors"
DEST = Path("D:/DevTools/GoldGraft/sponsor-tools")


def main():
    metadata = json.loads((ROOT / ".context/portable-node.json").read_text(encoding="utf-8"))
    node = Path(metadata["node"])
    if metadata["version"] != "v22.23.4":
        raise ValueError("reviewed_node_runtime_required")
    npm = node.parent / "node_modules/npm/bin/npm-cli.js"
    DEST.mkdir(parents=True, exist_ok=True)
    for name in ("package.json", "package-lock.json"):
        source, destination = SOURCE / name, DEST / name
        if destination.exists():
            if json.loads(destination.read_text()) != json.loads(source.read_text()):
                raise ValueError("existing_tooling_differs_preserve_and_review")
        else:
            shutil.copyfile(source, destination)
    subprocess.run(
        [
            str(node),
            str(npm),
            "ci",
            "--prefix",
            str(DEST),
            "--cache",
            "D:/DevTools/GoldGraft/npm-cache",
            "--ignore-scripts",
            "--no-audit",
            "--no-fund",
        ],
        check=True,
        timeout=300,
    )
    print(
        json.dumps(
            {
                "status": "LOCAL_TOOLS_INSTALLED",
                "global_path_changed": False,
                "accounts_created": 0,
                "vendor_credits_redeemed": False,
            }
        )
    )


if __name__ == "__main__":
    main()
