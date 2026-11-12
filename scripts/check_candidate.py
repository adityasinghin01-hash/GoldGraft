"""Exercise the separate PHP candidate with scripted responses; never contact a provider."""

import importlib.util
import json
import sqlite3
import subprocess
import tempfile
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    metadata = json.loads((ROOT / ".context/portable-php.json").read_text(encoding="utf-8"))
    php = Path(metadata["php"])
    folder = ROOT / ".context/candidate-tests"
    folder.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="state-", dir=folder) as state:
        command = [
            str(php),
            "-n",
            "-d",
            "extension_dir=" + str(php.parent / "ext"),
            "-d",
            "extension=pdo_sqlite",
            "-d",
            "extension=sodium",
        ]
        p = subprocess.run(
            [
                *command,
                str(ROOT / "pieces/shops/legacy-php-shop/candidate/test_checkout.php"),
                state,
            ],
            capture_output=True,
            text=True,
            timeout=45,
        )
        if p.returncode:
            raise RuntimeError("candidate_component_failed: " + p.stdout[-1000:] + p.stderr[-2000:])
        result = json.loads(p.stdout)
        if (
            result.get("status") != "PASS"
            or result.get("provider_calls") != 0
            or result.get("payment_qualified") is not False
        ):
            raise RuntimeError("candidate_evidence_boundary_invalid")
        restart = subprocess.run(
            [
                *command,
                str(ROOT / "pieces/shops/legacy-php-shop/candidate/restart_check.php"),
                state,
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if restart.returncode:
            raise RuntimeError("candidate_process_restart_failed: " + restart.stderr[-1000:])
        result["restart"] = json.loads(restart.stdout)
        spec = importlib.util.spec_from_file_location(
            "candidate_continuity", ROOT / "pieces/shops/legacy-php-shop/candidate/continuity.py"
        )
        continuity = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(continuity)
        result["snapshots"] = {
            name: continuity.inspect(Path(state) / (name + ".sqlite"))
            for name in ("happy", "pending", "lost", "refund-lost", "cutback")
        }
        if result["snapshots"]["refund-lost"]["unresolved_dispatches"] != 1:
            raise RuntimeError("unknown_refund_was_hidden")
        # Deliberately damage a separate synthetic DB: the inspector must reject
        # an origin change rather than print private data or silently repair it.
        path = Path(state) / "pending.sqlite"
        with closing(sqlite3.connect(path)) as db, db:
            body = json.loads(db.execute("SELECT body FROM candidate_orders").fetchone()[0])
            body["origin"] = "OLD"
            db.execute("UPDATE candidate_orders SET body=?", (json.dumps(body),))
        try:
            continuity.inspect(path)
        except ValueError:
            result["tampered_origin_rejected"] = True
        else:
            raise RuntimeError("tampered_origin_accepted")
    (folder / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        json.dumps({k: v for k, v in result.items() if k not in ("names", "snapshots")}, indent=2)
    )


if __name__ == "__main__":
    main()
