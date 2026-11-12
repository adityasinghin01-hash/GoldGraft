"""Actual PHP/browser component check; scripted provider only, no credentials."""

import importlib.util
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    node = json.loads((ROOT / ".context/portable-node.json").read_text(encoding="utf-8"))["node"]
    folder = ROOT / ".context/candidate-browser"
    folder.mkdir(parents=True, exist_ok=True)
    ready = folder / (uuid.uuid4().hex + ".json")
    supervisor = subprocess.Popen(
        [
            sys.executable,
            str(ROOT / "scripts/candidate_lab.py"),
            "--duration",
            "18",
            "--ready-file",
            str(ready),
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    try:
        deadline = time.monotonic() + 10
        while not ready.exists() and time.monotonic() < deadline:
            if supervisor.poll() is not None:
                raise RuntimeError(
                    "candidate_lab_start_failed: " + supervisor.communicate()[1].decode()[-1200:]
                )
            time.sleep(0.1)
        if not ready.exists():
            raise RuntimeError("candidate_lab_readiness_missing")
        config = json.loads(ready.read_text(encoding="utf-8"))
        env = {
            k: os.environ[k]
            for k in ("SystemRoot", "WINDIR", "TEMP", "TMP", "USERPROFILE")
            if k in os.environ
        }
        env["PLAYWRIGHT_BROWSERS_PATH"] = str(ROOT / ".context/playwright-browsers")
        buyer = subprocess.run(
            [node, str(ROOT / "scripts/candidate_buyer.mjs"), str(ready)],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=15,
        )
        if buyer.returncode:
            raise RuntimeError("candidate_browser_failed: " + buyer.stderr[-1600:])
        result = json.loads(buyer.stdout)
        spec = importlib.util.spec_from_file_location(
            "candidate_continuity", ROOT / "pieces/shops/legacy-php-shop/candidate/continuity.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result["state"] = module.inspect(Path(config["state_directory"]) / "candidate.sqlite")
        if result["state"]["records"] != 2 or result["state"]["operations"] != 4:
            raise RuntimeError("browser_duplicates_created_extra_operations")
        stdout, stderr = supervisor.communicate(timeout=25)
        if supervisor.returncode or ready.exists() or Path(config["state_directory"]).exists():
            raise RuntimeError("candidate_clean_shutdown_unverified: " + stderr.decode()[-1200:])
        result["clean_stop"] = True
        (folder / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result))
    finally:
        if supervisor.poll() is None:
            # The bounded owner process closes its own child and temporary state.
            supervisor.communicate(timeout=25)


if __name__ == "__main__":
    main()
