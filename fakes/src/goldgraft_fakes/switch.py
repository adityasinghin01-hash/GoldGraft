"""Reference behaviour of a Graft Switch library (design 03 origin routing, 05 H1–H3).

Every switch library (PHP, Node, Python, …) must give the same answers as this file on
``plugtests/switch_cases.json``. Rules:

1. NEW buyers' payments: go NEW only if the SwitchConfig is valid — correct ed25519
   signature, matching graft, not expired — otherwise OLD (fail safe).
2. Bucketing is deterministic per order:
   ``bucket = int(sha256(f"{graft_id}:{order_ref}").hexdigest()[:8], 16) % 100``;
   NEW when ``bucket < stage_pct``. The same order always takes the same path.
3. Origin routing: follow-up actions (REFUND, VOID, RENEWAL, CAPTURE of an existing
   payment) go by the payment's origin, never by the percentage:
   origin OLD (legacy id shape / stored tag) -> OLD; origin NEW -> NEW.
   An action on an OLD-origin payment stays OLD even when the config is invalid.
4. Signed bytes = canonical JSON (sorted keys, no spaces, UTF-8) of the config WITHOUT
   its ``signature`` field; ``signature`` = base64 of the 64-byte ed25519 signature.
"""

import base64
import hashlib
import json
from datetime import datetime

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

FOLLOW_UPS = {"REFUND", "VOID", "RENEWAL", "CAPTURE"}


def signed_bytes(config: dict) -> bytes:
    body = {k: v for k, v in config.items() if k != "signature"}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def config_valid(config: dict, public_key_b64: str, graft_id: str, now: datetime) -> bool:
    try:
        key = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key_b64))
        key.verify(base64.b64decode(config["signature"]), signed_bytes(config))
    except (InvalidSignature, KeyError, ValueError, TypeError):
        return False
    if config.get("graft_id") != graft_id:
        return False
    expires = datetime.fromisoformat(str(config["expires_at"]).replace("Z", "+00:00"))
    return now < expires


def bucket(graft_id: str, order_ref: str) -> int:
    return int(hashlib.sha256(f"{graft_id}:{order_ref}".encode()).hexdigest()[:8], 16) % 100


def decide(config: dict | None, public_key_b64: str, *, graft_id: str, order_ref: str,
           now: datetime, action: str = "PAY", origin: str | None = None) -> str:
    if action in FOLLOW_UPS:
        return "NEW" if origin == "NEW" else "OLD"
    if config is None or not config_valid(config, public_key_b64, graft_id, now):
        return "OLD"
    return "NEW" if bucket(graft_id, order_ref) < config["stage_pct"] else "OLD"
