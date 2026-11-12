"""Bounded private PHP child-process adapter. No network transport or ambient secrets."""

import json
import os
import subprocess
import threading
from pathlib import Path


class PhpPort:
    def __init__(self, php, database, *, merchant_id, rest):
        self.php, self.database, self.merchant = Path(php), Path(database), merchant_id
        self.rest = rest

    def call(self, action, order_id, cart=None):
        environment = {
            k: os.environ[k] for k in ("SystemRoot", "WINDIR", "TEMP", "TMP") if k in os.environ
        }
        runtime = (
            [
                "-n",
                "-d",
                "extension_dir=" + str(self.php.parent / "ext"),
                "-d",
                "extension=pdo_sqlite",
            ]
            if os.name == "nt"
            else []
        )
        command = [
            str(self.php),
            *runtime,
            "-d",
            "display_errors=0",
            str(Path(__file__).with_name("port_worker.php")),
            str(self.database),
        ]
        child = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            env=environment,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        deadline = threading.Timer(25, child.kill)
        deadline.start()
        try:
            child.stdin.write(
                json.dumps(
                    {
                        "action": action,
                        "id": order_id,
                        "cart": cart,
                        "merchant_id": self.merchant,
                    }
                )
                + "\n"
            )
            child.stdin.flush()
            for _ in range(8):
                line = child.stdout.readline(262145)
                if not line or len(line) > 262144:
                    raise ValueError("bounded_php_response_required")
                frame = json.loads(line)
                if frame.get("kind") == "result":
                    child.wait(timeout=3)
                    if frame.get("status") != "OK":
                        raise ValueError("shop_order_held")
                    return frame["order"]
                if frame.get("kind") != "rest":
                    raise ValueError("unsupported_php_frame")
                try:
                    status, data = self.rest(
                        frame["method"], frame["path"], frame["body"], frame["headers"]
                    )
                    reply = {"kind": "reply", "status": status, "data": data}
                except Exception:  # noqa: BLE001 -- Redact all backend errors at this private transport boundary.
                    reply = {"kind": "held"}
                child.stdin.write(json.dumps(reply, allow_nan=False) + "\n")
                child.stdin.flush()
            raise ValueError("php_exchange_budget_exhausted")
        finally:
            deadline.cancel()
            if child.poll() is None:
                child.kill()
                child.wait(timeout=5)
            child.stdin.close()
            child.stdout.close()
