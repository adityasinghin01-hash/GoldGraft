"""Run explicit local PHP/Playwright checks without Docker. No provider calls."""

import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import reference_lab as lab

ROOT = Path(__file__).resolve().parents[1]
SHOP = ROOT / "pieces/shops/legacy-php-shop"
STORAGE = Path("D:/DevTools/GoldGraft/portable-lab")


def source_fingerprint(source):
    files = {}
    for path in source.rglob("*"):
        if path.is_file() and "data" not in path.relative_to(source).parts:
            files[path.relative_to(source).as_posix()] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    return files


def verify_vendor(source, inventory):
    expected = {
        entry["path"][4:]: entry["git_blob_sha1"]
        for entry in inventory["files"]
        if entry["path"].startswith("src/")
    }
    observed = source_fingerprint(source)
    if set(expected) != set(observed):
        raise lab.LabHold("PINNED_VENDOR_FILE_SET_CHANGED")
    for name, digest in expected.items():
        data = (source / name).read_bytes()
        if hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() != digest:
            raise lab.LabHold("PINNED_VENDOR_BYTES_CHANGED")


def run(command, env, timeout=30):
    result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise lab.LabHold("PORTABLE_COMPONENT_COMMAND_FAILED")
    return result.stdout


def start(flags, source, env, logs, port=None):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", port or 0))
        port = sock.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    output = logs.open("ab")
    process = subprocess.Popen(
        [*flags, "-S", f"127.0.0.1:{port}", "-t", str(source), str(SHOP / "lab/router.php")],
        env=env,
        stdout=output,
        stderr=output,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    output.close()
    lab.BASE = base
    for _ in range(50):
        if process.poll() is not None:
            raise lab.LabHold("PORTABLE_SERVER_EXITED")
        try:
            if lab.request("/__lab/health")[0] == 200:
                return process, base
        except OSError:
            pass
        time.sleep(0.1)
    stop(process)
    raise lab.LabHold("PORTABLE_SERVER_NOT_READY")


def stop(process):
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--node", type=Path, help="explicit Node executable; global PATH is unchanged"
    )
    parser.add_argument(
        "--characterize-store",
        action="store_true",
        help="Phase 2 offline legacy order-store characterization",
    )
    parser.add_argument(
        "--variant",
        choices=["OLD", "OLD_TWIN"],
        default="OLD",
        help="local baseline run label only",
    )
    args = parser.parse_args()
    node = str(args.node.resolve()) if args.node else "node"
    node_version = run([node, "--version"], dict(os.environ)).strip()
    runtime = json.loads((ROOT / ".context/portable-php.json").read_text(encoding="utf-8"))
    php = [runtime["php"], *runtime["flags"]]
    verify_vendor(
        SHOP / "vendor/src",
        json.loads((SHOP / "phase1/source_inventory.json").read_text(encoding="utf-8")),
    )
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    work = STORAGE / run_id
    source = work / "src"
    process = None
    work.mkdir(parents=True)
    key_file, key = lab.prepare_key(work / "secrets")
    # This is trusted, pinned fixture code only. Windows execution is not a malicious-code sandbox.
    shutil.copytree(SHOP / "vendor/src", source)
    (source / "data").mkdir()
    original = source_fingerprint(SHOP / "vendor/src")
    if source_fingerprint(source) != original:
        raise lab.LabHold("SOURCE_COPY_MISMATCH")
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("PAYPAL_") and k != "SHOP_RECEIVER_EMAIL"
    }
    env.update(
        GOLDGRAFT_LAB_KEY_FILE=str(key_file),
        GOLDGRAFT_LAB_SOURCE_ROOT=str(source),
        GOLDGRAFT_OFFLINE_RUN_ID=run_id,
    )
    checks = []
    result = {
        "status": "HOLD",
        "evidence": "LOCAL_WINDOWS_COMPONENT_CHECKS",
        "run_id": run_id,
        "docker_used": False,
        "payment_tests_run": False,
        "runtime_qualified": False,
        "node_version": node_version,
        "node_22_component_check": node_version.startswith("v22."),
        "variant": args.variant,
        "source_sha256": original,
    }
    try:
        for path in [*source.rglob("*.php"), *(SHOP / "lab").glob("*.php")]:
            run([*php, "-l", str(path)], env)
        checks.append("all_application_and_lab_PHP_syntax")
        info = json.loads(
            run(
                [
                    *php,
                    "-r",
                    'echo json_encode(["version"=>PHP_VERSION,"curl"=>extension_loaded("curl"),'
                    '"openssl"=>extension_loaded("openssl")]);',
                ],
                env,
            )
        )
        if not info["curl"] or not info["openssl"]:
            raise lab.LabHold("PHP_EXTENSIONS_UNAVAILABLE")
        # Disable outbound PHP network/process helpers in this offline server.
        server_flags = [
            *php,
            "-d",
            "allow_url_fopen=0",
            "-d",
            "disable_functions=curl_exec,curl_multi_exec,fsockopen,pfsockopen,stream_socket_client,exec,shell_exec,system,passthru,proc_open,popen",
        ]
        process, base = start(server_flags, source, env, work / "php-server.log")
        checks.extend(lab.check_http(key))
        for path in [
            "/../config.php",
            "/%2e%2e/config.php",
            "/assets/../config.php",
            "/data/__lab_persistence.json",
        ]:
            if lab.request(path, key)[0] != 404:
                raise lab.LabHold("PORTABLE_PRIVATE_PATH_NOT_DENIED")
        run([*php, str(SHOP / "lab/state_check.php"), "seed"], env)
        order_store = None
        if args.characterize_store:
            run([*php, str(SHOP / "lab/order_store_check.php"), "seed"], env)
        stop(process)
        process, base = start(server_flags, source, env, work / "php-server.log")
        run([*php, str(SHOP / "lab/state_check.php"), "verify"], env)
        checks.append("synthetic_marker_survives_process_restart")
        if args.characterize_store:
            order_store = json.loads(
                run([*php, str(SHOP / "lab/order_store_check.php"), "verify"], env)
            )
            if order_store.get("status") != "PASS" or order_store.get("payment_operations") != 0:
                raise lab.LabHold("SYNTHETIC_ORDER_STORE_UNVERIFIED")
            checks.append("unchanged_legacy_order_store_survives_restart_with_synthetic_orders")
            # Corruption is exercised in a separate disposable copy, never in the seeded run store.
            corrupt_source = work / "corruption-source"
            shutil.copytree(SHOP / "vendor/src", corrupt_source)
            (corrupt_source / "data").mkdir()
            corrupt_env = {**env, "GOLDGRAFT_LAB_SOURCE_ROOT": str(corrupt_source)}
            corruption = json.loads(
                run([*php, str(SHOP / "lab/order_store_check.php"), "corrupt"], corrupt_env)
            )
            if source_fingerprint(corrupt_source) != original:
                raise lab.LabHold("CORRUPTION_PROBE_SOURCE_DRIFT")
            order_store["corruption_observation"] = corruption
        browser_result = work / "browser-result.json"
        env.update(
            GOLDGRAFT_LAB_BASE_URL=base,
            GOLDGRAFT_LAB_SCREENSHOT=str(work / "shop.png"),
            GOLDGRAFT_LAB_BROWSER_RESULT=str(browser_result),
        )
        run([node, str(ROOT / "scripts/check-reference-browser.mjs")], env, timeout=60)
        browser = json.loads(browser_result.read_text(encoding="utf-8"))
        if (
            source_fingerprint(source) != original
            or source_fingerprint(SHOP / "vendor/src") != original
        ):
            raise lab.LabHold("BASELINE_SOURCE_DRIFT")
        checks.append("original_and_run_source_hashes_unchanged")
        result.update(
            status="PASS",
            checks=checks,
            php=info,
            browser=browser,
            screenshot=str(work / "shop.png"),
            work_directory=str(work),
            order_store=order_store,
        )
    except (lab.LabHold, OSError, ValueError, subprocess.TimeoutExpired):
        result.update(reason="PORTABLE_COMPONENT_UNVERIFIED", completed_checks=checks)
    finally:
        stop(process)
        (work / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        (ROOT / ".context/portable-lab-result.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8"
        )
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
