"""Offline-compatible SwitchConfig/1 routing. No HTTP, secrets, events or persistence."""

import base64
import hashlib
import json
import re
from datetime import datetime

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

FOLLOW_UPS = {"REFUND", "VOID", "RENEWAL", "CAPTURE"}
FIELDS = {"graft_id", "stage_pct", "version", "expires_at", "origin_rules", "signature"}
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})$")


def timestamp(value):
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("timezone_required")
        return value
    if not isinstance(value, str) or not ISO.fullmatch(value):
        raise ValueError("invalid_timestamp")
    if value[-1] != "Z" and (int(value[-5:-3]) > 23 or int(value[-2:]) > 59):
        raise ValueError("invalid_timestamp")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def signed_bytes(config):
    return json.dumps(
        {k: v for k, v in config.items() if k != "signature"},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def decoded(value, size):
    if not isinstance(value, str):
        raise ValueError("invalid_base64")
    raw = base64.b64decode(value, validate=True)
    if len(raw) != size or base64.b64encode(raw).decode("ascii") != value:
        raise ValueError("invalid_key_or_signature")
    return raw


def config_valid(config, public_key_b64, graft_id, now):
    try:
        if (
            not isinstance(config, dict)
            or set(config) != FIELDS
            or not isinstance(config["graft_id"], str)
            or not config["graft_id"]
            or config["graft_id"] != graft_id
            or type(config["stage_pct"]) is not int
            or config["stage_pct"] not in (0, 1, 10, 50, 100)
            or type(config["version"]) is not int
            or not 0 < config["version"] <= 2**53 - 1
            or not isinstance(config["origin_rules"], list)
            or any(not isinstance(s, str) or not s for s in config["origin_rules"])
        ):
            return False
        expires = timestamp(config["expires_at"])
        clock = timestamp(now)
        Ed25519PublicKey.from_public_bytes(decoded(public_key_b64, 32)).verify(
            decoded(config["signature"], 64), signed_bytes(config)
        )
        return clock < expires
    except (ValueError, TypeError, KeyError, InvalidSignature, UnicodeError, OverflowError):
        return False


def bucket(graft_id, order_ref):
    return int(hashlib.sha256(f"{graft_id}:{order_ref}".encode()).hexdigest()[:8], 16) % 100


def decide(config, public_key_b64, *, graft_id, order_ref, now, action="PAY", origin=None):
    # Exact existing reference behaviour; callers must use route_existing for unknown origins.
    if action in FOLLOW_UPS:
        return "NEW" if origin == "NEW" else "OLD"
    if not config_valid(config, public_key_b64, graft_id, now):
        return "OLD"
    return "NEW" if bucket(graft_id, order_ref) < config["stage_pct"] else "OLD"


def route_existing(action, origin):
    if action not in FOLLOW_UPS or origin not in ("OLD", "NEW"):
        raise ValueError("stored_origin_required")
    return origin


class VerifiedConfigCache:
    """Caller-owned verified snapshot; no invented TTL, fetch auth or durable storage."""

    def __init__(self, graft_id, public_key_b64):
        self.graft_id, self.key, self._config = graft_id, public_key_b64, None

    def accept(self, config, now):
        if not config_valid(config, self.key, self.graft_id, now):
            return False
        if self._config is not None:
            if config["version"] < self._config["version"]:
                return False
            if config["version"] == self._config["version"] and signed_bytes(
                config
            ) != signed_bytes(self._config):
                return False
        self._config = json.loads(json.dumps(config))
        return True

    def current(self, now):
        return (
            json.loads(json.dumps(self._config))
            if config_valid(self._config, self.key, self.graft_id, now)
            else None
        )
