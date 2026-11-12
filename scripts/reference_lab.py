"""Build/check the local offline PHP reference. No PayPal calls or production deployment."""

import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
SHOP = ROOT / "pieces/shops/legacy-php-shop"
LOCAL = ROOT / ".context/reference-lab"
BASE = "http://127.0.0.1:8081"


class LabHold(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def prepare_key(directory=LOCAL):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "lab.key"
    if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
        raise LabHold("LINKED_LAB_KEY")
    if not path.exists():
        with path.open("x", encoding="ascii") as stream:
            stream.write(secrets.token_hex(32))
        path.chmod(0o600)
    key = path.read_text(encoding="ascii").strip()
    if not re.fullmatch(r"[a-f0-9]{64}", key):
        raise LabHold("INVALID_LAB_KEY_PRESERVED")
    return path, key


def docker_path():
    found = shutil.which("docker")
    if found:
        return Path(found)
    for path in [
        Path(os.environ.get("LOCALAPPDATA", ""))
        / "Programs/DockerDesktop/resources/bin/docker.exe",
        Path("C:/Program Files/Docker/Docker/resources/bin/docker.exe"),
    ]:
        if path.is_file():
            return path
    raise LabHold("DOCKER_CLI_MISSING")


def run_docker(cli, arguments, env, *, timeout=30):
    try:
        result = subprocess.run(
            [str(cli), *arguments], env=env, capture_output=True, text=True, timeout=timeout
        )
    except (OSError, subprocess.TimeoutExpired):
        raise LabHold("DOCKER_COMMAND_UNAVAILABLE_OR_TIMEOUT") from None
    # Keep diagnostic output local. Never echo configuration/secrets or raw command output.
    LOCAL.mkdir(parents=True, exist_ok=True)
    (LOCAL / "last-command.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise LabHold("DOCKER_COMMAND_FAILED")
    return result.stdout


def request(path, key=None, method="GET"):
    headers = {"X-GoldGraft-Lab-Key": key} if key else {}
    opener = build_opener(ProxyHandler({}), NoRedirect())
    try:
        with opener.open(
            Request(BASE + path, headers=headers, method=method), timeout=5
        ) as response:
            return response.status, response.read(200_000)
    except HTTPError as error:
        try:
            return error.code, error.read(200_000)
        finally:
            error.close()


def check_http(key):
    status, body = request("/__lab/health")
    if status != 200 or json.loads(body).get("payments") != "disabled":
        raise LabHold("OFFLINE_HEALTH_NOT_VERIFIED")
    for path in ["/", "/api/orders.php", "/config.php", "/data/orders.json"]:
        if request(path)[0] != 401:
            raise LabHold("UNAUTHENTICATED_ROUTE_NOT_DENIED")
    if request("/", "wrong-key")[0] != 401:
        raise LabHold("INVALID_LAB_KEY_NOT_DENIED")
    status, page = request("/", key)
    if status != 200 or b"paypal-button" not in page:
        raise LabHold("REFERENCE_PAGE_NOT_VERIFIED")
    for path in ["/config.php", "/lib/orders_store.php", "/data/orders.json", "/ipn.php"]:
        if request(path, key)[0] != 404:
            raise LabHold("PRIVATE_ROUTE_NOT_DENIED")
    for path in [
        "/api/create-payment.php",
        "/api/execute-payment.php",
        "/api/refund.php",
        "/ipn.php",
    ]:
        if request(path, key, "POST")[0] != 503:
            raise LabHold("PAYMENT_EXECUTION_NOT_DISABLED")
    return [
        "offline_health",
        "lab_authentication",
        "private_route_denial",
        "payment_execution_disabled",
        "reference_page",
    ]


def execute(action, cli, env, key):
    compose = ["compose", "-f", str(SHOP / "compose.yaml")]
    if action == "config":
        run_docker(cli, [*compose, "config", "--quiet"], env)
        return {
            "status": "PASS",
            "evidence": "compose_configuration_only",
            "runtime_qualified": False,
        }
    try:
        server = run_docker(cli, ["info", "--format", "{{json .ServerVersion}}"], env)
        if not isinstance(json.loads(server), str) or not json.loads(server):
            raise LabHold("DOCKER_ENGINE_UNAVAILABLE")
    except (LabHold, ValueError):
        raise LabHold("DOCKER_ENGINE_UNAVAILABLE") from None
    if action == "up":
        run_docker(
            cli,
            [*compose, "up", "--build", "-d", "--wait", "--wait-timeout", "90"],
            env,
            timeout=600,
        )
        return {
            "status": "PASS",
            "evidence": "local_container_start_only",
            "runtime_qualified": False,
        }
    if action == "down":
        run_docker(cli, [*compose, "down"], env)
        return {"status": "PASS", "evidence": "stopped_state_volume_preserved"}
    checks = check_http(key)
    # Check PHP capability and every application/wrapper file's syntax in the real image.
    run_docker(
        cli,
        [*compose, "exec", "-T", "shop", "php", "-r", 'exit(extension_loaded("curl") ? 0 : 1);'],
        env,
    )
    run_docker(
        cli, [*compose, "exec", "-T", "shop", "php", "/opt/shop/lab/state_check.php", "seed"], env
    )
    run_docker(cli, [*compose, "restart", "--no-deps", "shop"], env)
    run_docker(cli, [*compose, "up", "-d", "--wait", "--wait-timeout", "90"], env, timeout=120)
    run_docker(
        cli, [*compose, "exec", "-T", "shop", "php", "/opt/shop/lab/state_check.php", "verify"], env
    )
    checks.extend(["php_curl_extension", "synthetic_marker_survives_restart"])
    identity = json.loads(run_docker(cli, [*compose, "images", "--format", "json"], env))
    return {
        "status": "PASS",
        "evidence": "LOCAL_OFFLINE_LAB_CHECKS",
        "checks": checks,
        "images": identity,
        "payment_tests_run": False,
        "runtime_qualified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["config", "up", "check", "down"])
    args = parser.parse_args()
    try:
        key_path, key = prepare_key()
        cli = docker_path()
        env = {
            **os.environ,
            "PATH": str(cli.parent) + os.pathsep + os.environ.get("PATH", ""),
            "GOLDGRAFT_LAB_KEY_FILE": str(key_path),
        }
        result = execute(args.action, cli, env, key)
    except (LabHold, OSError, ValueError):
        import sys

        error = sys.exception()
        reason = str(error) if isinstance(error, LabHold) else "LOCAL_LAB_CHECK_UNVERIFIED"
        result = {
            "status": "HOLD",
            "reason": reason,
            "payment_tests_run": False,
            "runtime_qualified": False,
        }
    LOCAL.mkdir(parents=True, exist_ok=True)
    (LOCAL / "last-result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
