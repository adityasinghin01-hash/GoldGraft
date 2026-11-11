"""Version-bound local component evidence gate, never a production release certificate."""

import hashlib
import json
from pathlib import Path


def verify_qualification(path, profile):
    try:
        document = json.loads(Path(path).read_text())
        if (
            document["purpose"] != "synthetic_component_only"
            or document["profile"] != profile.ref
            or not document["files"]
            or not document["checks"]
        ):
            raise ValueError("QUALIFICATION_MISSING")
        for record in document["files"] + document["checks"]:
            payload = Path(record["path"]).read_bytes()
            if hashlib.sha256(payload).hexdigest() != record["sha256"]:
                raise ValueError("QUALIFICATION_STALE")
        for check in document["checks"]:
            record = json.loads(Path(check["path"]).read_text())
            if (
                record["exit_code"] != 0
                or hashlib.sha256(Path(record["log"]).read_bytes()).hexdigest()
                != record["log_sha256"]
            ):
                raise ValueError("QUALIFICATION_CHECK_FAILED")
        return document
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        raise ValueError("QUALIFICATION_UNAVAILABLE") from None
