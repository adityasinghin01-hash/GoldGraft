"""Bounded start/buyer/stop check for the offline shop package, not a payment test."""

import argparse
import json
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOP = ROOT / "pieces/shops/legacy-php-shop"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", type=Path, required=True)
    args = parser.parse_args()
    folder = ROOT / ".context/local-shop-tests"
    folder.mkdir(parents=True, exist_ok=True)
    ready = folder / (uuid.uuid4().hex + ".json")
    process = subprocess.Popen(
        [
            sys.executable,
            str(SHOP / "local_shop.py"),
            "--duration",
            "14",
            "--ready-file",
            str(ready),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    try:
        deadline = time.monotonic() + 10
        while not ready.exists() and time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("local_shop_failed_to_start")
            time.sleep(0.1)
        if not ready.exists():
            raise RuntimeError("local_shop_readiness_timeout")
        buyer = subprocess.run(
            [str(args.node), str(SHOP / "buyer.mjs"), str(ready)],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if buyer.returncode:
            raise RuntimeError("offline_buyer_failed: " + buyer.stderr[-600:])
        stdout, stderr = process.communicate(timeout=20)
        if process.returncode or ready.exists():
            raise RuntimeError("local_shop_shutdown_unverified")
        result = {
            "status": "PASS",
            "evidence": "LOCAL_OFFLINE_SHOP_PACKAGE",
            "buyer": json.loads(buyer.stdout),
            "clean_stop": True,
            "provider_calls": 0,
            "payment_qualified": False,
            "runtime_qualified": False,
        }
        (folder / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
    finally:
        if process.poll() is None:
            # Stop only our supervisor; it normally exits after its bounded duration.
            try:
                process.communicate(timeout=18)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=5)


if __name__ == "__main__":
    main()
