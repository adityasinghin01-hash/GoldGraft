"""Compile SDK-grounded examples and run an actual local Newman collection. No cloud operations."""

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path("D:/DevTools/GoldGraft/sponsor-tools")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", type=Path, required=True)
    args = parser.parse_args()
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("PAYPAL_", "KERNEL_")) and k != "SHOP_RECEIVER_EMAIL"
    }
    folder = ROOT / ".context/sponsor-examples"
    folder.mkdir(parents=True, exist_ok=True)
    base = [
        str(args.node),
        str(TOOLS / "node_modules/typescript/lib/tsc.js"),
        "--noEmit",
        "--strict",
        "--target",
        "ES2022",
        "--module",
        "node16",
        "--moduleResolution",
        "node16",
        "--skipLibCheck",
        "--baseUrl",
        str(TOOLS / "node_modules"),
    ]
    positive = subprocess.run(
        [*base, str(ROOT / "tools/sponsors/apimatic/payment_recipe.ts")],
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    if positive.returncode:
        raise RuntimeError("sdk_positive_compile_failed: " + positive.stdout[-1000:])
    negative = subprocess.run(
        [*base, str(ROOT / "tools/sponsors/apimatic/negative_recipe.ts")],
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    errors = negative.stdout.count("error TS")
    if negative.returncode == 0 or errors != 3:
        raise RuntimeError(
            "sdk_three_negative_assumptions_not_rejected: " + negative.stdout[-1000:]
        )
    ready = folder / (uuid.uuid4().hex + ".json")
    shop = subprocess.Popen(
        [
            sys.executable,
            str(ROOT / "pieces/shops/legacy-php-shop/local_shop.py"),
            "--duration",
            "18",
            "--ready-file",
            str(ready),
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    try:
        deadline = time.monotonic() + 10
        while not ready.exists() and time.monotonic() < deadline:
            if shop.poll() is not None:
                raise RuntimeError("offline_shop_start_failed")
            time.sleep(0.1)
        if not ready.exists():
            raise RuntimeError("offline_shop_readiness_timeout")
        run = subprocess.run(
            [str(args.node), str(ROOT / "tools/sponsors/postman/run_offline.mjs"), str(ready)],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
        if run.returncode:
            raise RuntimeError("newman_local_check_failed")
        newman = json.loads(run.stdout)
        shop.communicate(timeout=25)
        if shop.returncode or ready.exists():
            raise RuntimeError("offline_shop_shutdown_unverified")
        result = {
            "status": "PASS",
            "sdk_version": "2.5.0",
            "positive_compile": "PASS",
            "deliberate_sdk_errors_caught": errors,
            "newman": newman,
            "kernel_sessions_created": 0,
            "sponsor_accounts_created": 0,
            "payment_scenarios_completed": 0,
            "provider_calls": 0,
        }
        (folder / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
    finally:
        if shop.poll() is None:
            try:
                shop.communicate(timeout=25)
            except subprocess.TimeoutExpired:
                shop.terminate()
                shop.wait(timeout=5)


if __name__ == "__main__":
    main()
