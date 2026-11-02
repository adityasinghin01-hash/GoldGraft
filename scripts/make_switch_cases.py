"""Generate plugtests/switch_cases.json: shared cases every switch library must pass.

Uses a TEST-ONLY ed25519 key derived from a fixed seed. It signs nothing real.
Run: uv run python scripts/make_switch_cases.py
"""

import base64
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from goldgraft_fakes.switch import decide, signed_bytes

OUT = Path(__file__).resolve().parents[1] / "plugtests" / "switch_cases.json"
SEED = hashlib.sha256(b"goldgraft TEST-ONLY switch key - not secret").digest()
KEY = Ed25519PrivateKey.from_private_bytes(SEED)
PUB = base64.b64encode(KEY.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode()
NOW = "2026-11-05T12:00:00+00:00"
GRAFT = "demo-1"


def config(pct, *, expires="2026-11-06T00:00:00+00:00", graft=GRAFT, tamper=False):
    cfg = {"graft_id": graft, "stage_pct": pct, "version": 3, "expires_at": expires,
           "origin_rules": ["legacy refunds stay OLD"], "signature": ""}
    cfg["signature"] = base64.b64encode(KEY.sign(signed_bytes(cfg))).decode()
    if tamper:
        cfg["stage_pct"] = 100
    return cfg


def main():
    raw = []
    for pct in (0, 1, 10, 50, 100):
        for n in range(40):
            raw.append({"name": f"pct{pct}-order{n}", "config": config(pct),
                        "order_ref": f"order-{n}", "action": "PAY", "origin": None})
    raw += [
        {"name": "no-config", "config": None, "order_ref": "order-1", "action": "PAY",
         "origin": None},
        {"name": "expired", "config": config(100, expires="2026-11-05T11:59:59+00:00"),
         "order_ref": "order-1", "action": "PAY", "origin": None},
        {"name": "tampered-pct", "config": config(0, tamper=True), "order_ref": "order-1",
         "action": "PAY", "origin": None},
        {"name": "other-graft", "config": config(100, graft="other"), "order_ref": "order-1",
         "action": "PAY", "origin": None},
        {"name": "legacy-refund-at-100", "config": config(100), "order_ref": "order-9",
         "action": "REFUND", "origin": "OLD"},
        {"name": "new-refund-at-0", "config": config(0), "order_ref": "order-9",
         "action": "REFUND", "origin": "NEW"},
        {"name": "legacy-refund-invalid-config", "config": None, "order_ref": "order-9",
         "action": "REFUND", "origin": "OLD"},
    ]
    now = datetime.fromisoformat(NOW).astimezone(UTC)
    for case in raw:
        case["expect"] = decide(case["config"], PUB, graft_id=GRAFT, order_ref=case["order_ref"],
                                now=now, action=case["action"], origin=case["origin"])
    doc = {"_label": "SYNTHETIC — shared conformance cases for every Graft Switch library",
           "_rules": "see fakes/src/goldgraft_fakes/switch.py",
           "public_key_b64": PUB, "graft_id": GRAFT, "now": NOW, "cases": raw}
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    print(f"{len(raw)} cases, NEW={sum(c['expect'] == 'NEW' for c in raw)}")


if __name__ == "__main__":
    main()
