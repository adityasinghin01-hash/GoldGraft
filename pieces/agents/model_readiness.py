"""Read-only local prerequisites. This report grants no model/provider authority."""

import os
import re
import stat
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def _local_key_configuration(path: Path | None):
    """Presence only, opt-in, no secret value or authority leaves this function."""
    if path is None:
        return {"state": "NOT_CHECKED"}
    try:
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode):
            return {"state": "UNSAFE_FILE_TYPE"}
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            current = os.fstat(descriptor)
            if not stat.S_ISREG(current.st_mode):
                return {"state": "UNSAFE_FILE_TYPE"}
            if current.st_uid != os.getuid() or stat.S_IMODE(current.st_mode) != 0o600:
                return {"state": "UNSAFE_PERMISSIONS"}
            if current.st_size > 16384:
                return {"state": "OVERSIZED"}
            raw = os.read(descriptor, 16385)
            if len(raw) > 16384:
                return {"state": "OVERSIZED"}
        finally:
            os.close(descriptor)
        entries = []
        for line in raw.decode("utf-8").lstrip("\ufeff").splitlines():
            match = re.fullmatch(r"(?:export\s+)?ANTHROPIC_API_KEY\s*=\s*(.*)", line.strip())
            if match:
                value = match[1].strip()
                if len(value) >= 2 and value[0] in {"'", '"'} and value[-1] == value[0]:
                    value = value[1:-1]
                entries.append(value)
        if len(entries) > 1:
            return {"state": "DUPLICATE_ENTRIES"}
        if not entries or not entries[0]:
            return {"state": "ABSENT"}
        if entries[0] in {"[YOUR_KEY]", "YOUR_KEY"}:
            return {"state": "PLACEHOLDER"}
        return {"state": "PRESENT_UNVALIDATED"}
    except FileNotFoundError:
        return {"state": "ABSENT"}
    except (OSError, UnicodeError, ValueError):
        # Never return an exception containing file contents or credential data.
        return {"state": "UNVERIFIED"}


def model_access_report(*, local_key_file: Path | None = None):
    try:
        sdk_version = version("anthropic")
    except PackageNotFoundError:
        sdk_version = None
    return {
        "api_key_presence": "PRESENT"
        if os.environ.get("ANTHROPIC_API_KEY", "").strip()
        else "ABSENT",
        "api_key_presence_scope": "current_process_environment_only",
        "local_key_configuration": _local_key_configuration(local_key_file),
        "anthropic_sdk_version": sdk_version,
        "budget_scope": "all_13_agents_and_all_project_api_checks",
        "initial_paid_checkpoint_micro_usd": 50000,
        "outer_review_checkpoint_micro_usd": 5000000,
        "project_target_micro_usd": 15000000,
        "project_hard_ceiling_micro_usd": 20000000,
        "checkpoint_ladder_micro_usd": [
            50000,
            100000,
            250000,
            500000,
            1000000,
            2000000,
            5000000,
            10000000,
            15000000,
            20000000,
        ],
        "checkpoint_changes": "require_reviewed_approval",
        "paid_calls_enabled": False,
        "broker_profile": "NOT QUALIFIED IN THIS RUNTIME",
        "reservation_ledger": "NOT QUALIFIED",
        "real_model_evaluation": "NOT RUN",
        "note": "Budget declarations and key presence are not spend authorisation.",
        "required_before_paid_dispatch": [
            "GU broker/processing/custody qualification and compatible ModelPort adapter",
            "Pinned Anthropic Python client behind GU with hidden retries disabled",
            "Approved exact model, entitlement, processing terms, pricing and tokenizer",
            "One cumulative ledger: spent + outstanding + unknown reservations",
            "Calculated synthetic-source trial and independent expected outputs",
            "Local key configuration; never paste a key into chat",
        ],
    }
