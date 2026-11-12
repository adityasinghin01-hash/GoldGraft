"""Bounded loopback-only scripted candidate harness. No sandbox credentials or transport."""

import argparse
import json
import os
import secrets
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "pieces/shops/legacy-php-shop/candidate"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--duration", type=int, default=3600)
    p.add_argument("--ready-file", type=Path, default=ROOT / ".context/candidate-ready.json")
    args = p.parse_args()
    if not 5 <= args.duration <= 3600:
        raise ValueError("duration_out_of_bounds")
    ready = args.ready_file.resolve()
    if not ready.is_relative_to((ROOT / ".context").resolve()) or ready.exists():
        raise ValueError("fresh_private_readiness_path_required")
    ready.parent.mkdir(parents=True, exist_ok=True)
    php = Path(json.loads((ROOT / ".context/portable-php.json").read_text(encoding="utf-8"))["php"])
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    folder = ROOT / ".context/candidate-lab"
    folder.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=folder, prefix="run-") as state:
        # Explicit allowlist; do not inherit API/buyer keys, proxies or PHP config.
        env = {k: os.environ[k] for k in ("SystemRoot", "WINDIR", "TEMP", "TMP") if k in os.environ}
        env["CANDIDATE_LAB_KEY"] = secrets.token_urlsafe(32)
        env["CANDIDATE_LAB_STATE"] = state
        flags = [
            "-n",
            "-d",
            "extension_dir=" + str(php.parent / "ext"),
            "-d",
            "extension=pdo_sqlite",
            "-d",
            "allow_url_fopen=0",
            "-d",
            "display_errors=0",
            "-d",
            "log_errors=1",
            "-d",
            "disable_functions=exec,shell_exec,system,passthru,popen,proc_open,fsockopen,stream_socket_client",
            "-d",
            'open_basedir="'
            + os.pathsep.join([str(CANDIDATE), str(CANDIDATE.parent / "domain"), state])
            + '"',
        ]
        with open(Path(state) / "server.log", "w", encoding="utf-8") as log:
            server = subprocess.Popen(
                [
                    str(php),
                    *flags,
                    "-S",
                    "127.0.0.1:" + str(port),
                    str(CANDIDATE / "offline_router.php"),
                ],
                cwd=CANDIDATE,
                env=env,
                stdout=log,
                stderr=log,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            try:
                base = "http://127.0.0.1:" + str(port)
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    if server.poll() is not None:
                        raise RuntimeError("candidate_server_exited")
                    try:
                        with urlopen(base + "/__candidate/health", timeout=1) as response:
                            if json.load(response).get("mode") == "OFFLINE_SCRIPTED":
                                break
                    except OSError:
                        time.sleep(0.1)
                else:
                    log.flush()
                    raise RuntimeError(
                        "candidate_readiness_timeout: "
                        + (Path(state) / "server.log").read_text(encoding="utf-8")[-1600:]
                    )
                ready.write_text(
                    json.dumps(
                        {
                            "base_url": base,
                            "lab_key": env["CANDIDATE_LAB_KEY"],
                            "mode": "OFFLINE_SCRIPTED",
                            "state_directory": state,
                        }
                    ),
                    encoding="utf-8",
                )
                print(
                    json.dumps(
                        {
                            "status": "READY",
                            "mode": "OFFLINE_SCRIPTED",
                            "ready_file": str(ready),
                            "provider_calls": 0,
                        }
                    ),
                    flush=True,
                )
                server.wait(timeout=args.duration)
                raise RuntimeError("candidate_server_exited_early")
            except subprocess.TimeoutExpired:
                pass
            except KeyboardInterrupt:
                pass
            finally:
                if server.poll() is None:
                    server.terminate()
                    server.wait(timeout=5)
                if ready.exists():
                    ready.unlink()


if __name__ == "__main__":
    main()
