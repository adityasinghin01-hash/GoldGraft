"""Local-only sandbox credential setup/status. Never print credential values."""

import argparse
import getpass
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / ".secrets/sandbox.json"
GROUPS = {
    "REST seller": ("PAYPAL_SANDBOX_CLIENT_ID", "PAYPAL_SANDBOX_CLIENT_SECRET"),
    "NVP seller": ("PAYPAL_NVP_USER", "PAYPAL_NVP_PWD", "PAYPAL_NVP_SIGNATURE"),
    "Sandbox buyer": ("PAYPAL_SANDBOX_BUYER_EMAIL", "PAYPAL_SANDBOX_BUYER_PASSWORD"),
    "Sandbox recipient": ("SHOP_RECEIVER_EMAIL",),
}
ALLOWED = {"PAYPAL_ENVIRONMENT", *(name for names in GROUPS.values() for name in names)}


def load_config(path):
    path = Path(path)
    if (
        path.is_symlink()
        or any(p.is_symlink() for p in path.parents)
        or path.stat().st_size > 16384
    ):
        raise ValueError("invalid_local_config")
    data = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(data, dict)
        or set(data) - ALLOWED
        or any(not isinstance(v, str) or "\n" in v or "\r" in v for v in data.values())
        or data.get("PAYPAL_ENVIRONMENT") != "sandbox"
    ):
        raise ValueError("invalid_local_sandbox_config")
    return data


def has_control(value):
    return any(ord(c) < 32 or ord(c) == 127 for c in value)


def status(data):
    return {
        name: {
            "configured": all(
                bool(data.get(n, "").strip()) and not has_control(data.get(n, "")) for n in names
            ),
            "missing_names": [n for n in names if not data.get(n, "").strip()],
            "invalid_names": [n for n in names if has_control(data.get(n, ""))],
        }
        for name, names in GROUPS.items()
    }


def prompt_value(name, current):
    while True:
        value = getpass.getpass(name + ": ")
        if has_control(value) or (not value.strip() and has_control(current)):
            print(
                "Invalid hidden input/control character. Copy the value again and paste "
                "with right-click; do not use Ctrl+V here. This field must be re-entered."
            )
            continue
        return value.strip() or current


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configure", action="store_true", help="interactive local terminal only")
    args = parser.parse_args()
    data = load_config(DEFAULT) if DEFAULT.exists() else {"PAYPAL_ENVIRONMENT": "sandbox"}
    if args.configure:
        if not sys.stdin.isatty():
            raise ValueError("configuration_requires_your_interactive_terminal")
        print("PayPal SANDBOX only. Input is hidden. Enter leaves a field unchanged/pending.")
        print("Use existing app/account credentials from PayPal Developer. Never use live keys.")
        for group, names in GROUPS.items():
            print(group)
            for name in names:
                value = prompt_value(name, data.get(name, ""))
                if value:
                    data[name] = value
        DEFAULT.parent.mkdir(parents=True, exist_ok=True)
        temporary = DEFAULT.with_suffix(".tmp")
        if temporary.exists() or DEFAULT.is_symlink():
            raise ValueError("unexpected_existing_config_path")
        with temporary.open("x", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2)
        temporary.chmod(0o600)
        os.replace(temporary, DEFAULT)
        load_config(DEFAULT)
    print(
        json.dumps(
            {
                "environment": "sandbox",
                "groups": status(data),
                "configuration_file_present": DEFAULT.exists(),
                "credential_values_printed": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError):
        print(json.dumps({"status": "BLOCKED", "reason": "local_config_invalid_or_unavailable"}))
        raise SystemExit(2) from None
