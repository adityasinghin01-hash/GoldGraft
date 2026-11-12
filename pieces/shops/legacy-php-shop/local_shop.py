"""Foreground, loopback-only offline reference shop. Not a Cage/payment runner."""

import argparse
import json
import os
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import portable_lab as local  # noqa: E402 -- Resolve the reviewed local helper from this repository.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--duration", type=int, default=3600, help="bounded seconds; Ctrl+C stops earlier"
    )
    parser.add_argument("--port", type=int, default=8081, help="loopback-only offline shop port")
    parser.add_argument("--ready-file", type=Path, default=ROOT / ".context/local-shop.json")
    args = parser.parse_args()
    if not 1 <= args.duration <= 86400 or not 1 <= args.port <= 65535:
        raise ValueError("invalid_duration")
    ready = args.ready_file.resolve()
    if not ready.is_relative_to((ROOT / ".context").resolve()) or ready.exists():
        raise ValueError("fresh_local_ready_path_required")
    if any(
        p.is_symlink() or getattr(p, "is_junction", lambda: False)()
        for p in [ready, *ready.parents]
    ):
        raise ValueError("linked_ready_path_denied")
    runtime = json.loads((ROOT / ".context/portable-php.json").read_text(encoding="utf-8"))
    php = [runtime["php"], *runtime["flags"]]
    local.verify_vendor(
        local.SHOP / "vendor/src",
        json.loads((local.SHOP / "phase1/source_inventory.json").read_text(encoding="utf-8")),
    )
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    work = Path("D:/DevTools/GoldGraft/local-shop") / run_id
    source = work / "src"
    work.mkdir(parents=True)
    shutil.copytree(local.SHOP / "vendor/src", source)
    (source / "data").mkdir()
    key_file, _ = local.lab.prepare_key(work / "secrets")
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("PAYPAL_") and k != "SHOP_RECEIVER_EMAIL"
    }
    env.update(GOLDGRAFT_LAB_SOURCE_ROOT=str(source), GOLDGRAFT_LAB_KEY_FILE=str(key_file))
    flags = [
        *php,
        "-d",
        "allow_url_fopen=0",
        "-d",
        "disable_functions=curl_exec,curl_multi_exec,fsockopen,pfsockopen,stream_socket_client,exec,shell_exec,system,passthru,proc_open,popen",
    ]
    process = None
    receipt = None
    try:
        process, base = local.start(flags, source, env, work / "server.log", port=args.port)
        receipt = json.dumps(
            {
                "kind": "LOCAL_OFFLINE_SHOP",
                "run_id": run_id,
                "base_url": base,
                "key_file": str(key_file),
                "source_root": str(source),
                "payments": "disabled",
                "owner_pid": os.getpid(),
                "runtime_qualified": False,
            }
        )
        ready.parent.mkdir(parents=True, exist_ok=True)
        with ready.open("x", encoding="utf-8") as stream:
            stream.write(receipt)
        print(
            json.dumps(
                {
                    "status": "LOCAL_READY",
                    "base_url": base,
                    "ready_file": str(ready),
                    "payments": "disabled",
                    "runtime_qualified": False,
                }
            ),
            flush=True,
        )
        deadline = time.monotonic() + args.duration
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise ValueError("local_shop_exited")
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        local.stop(process)
        if (
            receipt
            and ready.is_file()
            and not ready.is_symlink()
            and ready.read_text(encoding="utf-8") == receipt
        ):
            ready.unlink()  # Only our exact own, non-secret readiness receipt.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
