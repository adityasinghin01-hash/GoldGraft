"""Real local crypto/cross-language conformance; synthetic configs, never provider evidence."""

import argparse
import base64
import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIBS = ROOT / "pieces/switch-libs"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", type=Path, required=True)
    parser.add_argument("--php", type=Path, required=True)
    args = parser.parse_args()
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    key = Ed25519PrivateKey.generate()  # Test-only; not written to disk or printed.
    public = base64.b64encode(
        key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).decode()
    now = "2026-11-09T12:00:00.123456+00:00"
    base = {
        "graft_id": "local-test",
        "stage_pct": 100,
        "version": 3,
        "origin_rules": ["é/漢字\u2028"],
        "expires_at": "2026-11-09T13:00:00+00:00",
    }

    def signed(changes=None):
        value = {**copy.deepcopy(base), **(changes or {})}
        raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        return {**value, "signature": base64.b64encode(key.sign(raw)).decode()}

    cases = []

    def case(name, config, expect="OLD", action="PAY", origin=None):
        cases.append(
            {
                "name": name,
                "config": config,
                "expect": expect,
                "action": action,
                "origin": origin,
                "order_ref": "test-order",
            }
        )

    case("valid-real-signature-unicode", signed(), "NEW")
    for bad in [None, False, "bad", [], 1]:
        case("bad-config-" + type(bad).__name__, bad)
    for field, value in [
        ("stage_pct", True),
        ("stage_pct", 99),
        ("stage_pct", "100"),
        ("version", 0),
        ("version", 2**53),
        ("origin_rules", [1]),
        ("origin_rules", {"a": "b"}),
        ("graft_id", "wrong"),
        ("expires_at", "bad"),
        ("expires_at", "2026-02-30T12:00:00+00:00"),
        ("expires_at", "0000-12-30T12:00:00+00:00"),
        ("expires_at", "2026-11-09T24:00:00+00:00"),
        ("expires_at", "2026-11-09T13:00:00+24:00"),
        ("expires_at", "2026-11-09T13:00:00+00:60"),
        ("expires_at", now),
        ("expires_at", "2026-11-09T12:00:00.123455+00:00"),
    ]:
        case(f"validly-signed-invalid-{field}-{len(cases)}", signed({field: value}))
    case(
        "microsecond-before-expiry",
        signed({"expires_at": "2026-11-09T12:00:00.123457+00:00"}),
        "NEW",
    )
    case("offset-same-expiry", signed({"expires_at": "2026-11-09T17:30:00.123456+05:30"}))
    case("unknown-field", signed({"unexpected": "x"}))
    for signature in ["", "not-base64", "A" * 88]:
        case("invalid-signature-" + str(len(cases)), {**signed(), "signature": signature})
    case("tamper-signed-stage", {**signed({"stage_pct": 0}), "stage_pct": 100})
    for action in ["REFUND", "VOID", "RENEWAL", "CAPTURE"]:
        case(action + "-new-on-no-config", None, "NEW", action, "NEW")
        case(action + "-old-on-100", signed(), "OLD", action, "OLD")
    extra = {
        "_label": "SYNTHETIC local negatives, not shared wire formats or payment proof",
        "public_key_b64": public,
        "now": now,
        "graft_id": "local-test",
        "cases": cases,
    }
    cache = {
        "initial": signed({"stage_pct": 1}),
        "older": signed({"version": 2}),
        "same_version_changed": signed({"stage_pct": 50}),
        "newer": signed({"version": 4}),
        "expired": signed({"version": 5, "expires_at": now}),
        "now": now,
        "key": public,
        "graft_id": "local-test",
        "expires": base["expires_at"],
    }
    output = ROOT / ".context/switch-tests"
    output.mkdir(parents=True, exist_ok=True)
    negatives = output / "negative-cases.json"
    cache_path = output / "cache-cases.json"
    negatives.write_text(json.dumps(extra, ensure_ascii=False), encoding="utf-8")
    cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    commands = {
        "php": [
            str(args.php),
            "-n",
            "-d",
            "extension_dir=" + str(args.php.parent / "ext"),
            "-d",
            "extension=sodium",
        ],
        "node": [str(args.node)],
        "python": [sys.executable],
    }
    extensions = {"php": "php", "node": "mjs", "python": "py"}
    results = []
    for language, command in commands.items():
        for label, path in [("shared", LIBS / "cases/shared.json"), ("negative", negatives)]:
            process = subprocess.run(
                [*command, str(LIBS / language / ("run_cases." + extensions[language])), str(path)],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if process.returncode:
                raise RuntimeError(f"{language}_{label}_failed: {process.stdout[-1500:]}")
            value = json.loads(process.stdout)
            results.append({"language": language, "suite": label, **value})
        process = subprocess.run(
            [
                *command,
                str(LIBS / language / ("test_cache." + extensions[language])),
                str(cache_path),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if process.returncode:
            raise RuntimeError(
                f"{language}_cache_failed: {process.stdout[-500:]} {process.stderr[-500:]}"
            )
        results.append({"language": language, "suite": "cache", **json.loads(process.stdout)})
    report = {
        "status": "PASS",
        "evidence": "LOCAL_SYNTHETIC_SWITCH_CONFORMANCE",
        "libraries": 3,
        "skipped": 0,
        "checks": sum(r.get("cases", 0) for r in results),
        "results": results,
        "provider_calls": 0,
        "rollout_qualified": False,
    }
    (output / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
