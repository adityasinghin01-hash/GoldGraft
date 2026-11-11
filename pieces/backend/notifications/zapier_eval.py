"""Opt-in Zapier Catch Hook sender for Herald's unsent previews (local evaluation).

Sponsor acceptance (SPONSOR_UTILISATION_AND_OWNERSHIP §8): one minimal notification
per logical event, retry/dedupe evidence, opt-out, delivery-failure and quota
handling; never an approval, effect channel, secret or sensitive payload. Losing
this sender changes no task/proof/approval/exit state: it only reads previews.
The hook URL is private custody: never logged, returned, hashed or stored here.
Gupta's GU connector may adopt or replace this; it is not production qualified.
"""

import http.client
import json
import os
import re
import socket
import sqlite3
import stat
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from goldgraft_contracts.plan5_common import reject_secret

HOOK = re.compile(r"https://hooks\.zapier\.com/hooks/catch/[0-9]{1,20}/[A-Za-z0-9]{1,40}/?")
EVENT = re.compile(r"[0-9a-f]{64}")
MAX_ATTEMPTS = 3
RETRYABLE = {429, 500, 502, 503, 504}


def hook_url(path):
    """Read ZAPIER_HOOK_URL from an owner-only 0600 regular file; validate the host."""
    path = Path(path)
    try:
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ValueError
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            meta = os.fstat(fd)
            if meta.st_uid != os.getuid() or stat.S_IMODE(meta.st_mode) != 0o600:
                raise ValueError
            raw = os.read(fd, 4097)
        finally:
            os.close(fd)
        values = [
            line.partition("=")[2].strip().strip("\"'")
            for line in raw.decode().splitlines()
            if line.startswith("ZAPIER_HOOK_URL=")
        ]
    except (OSError, ValueError, UnicodeError):
        raise ValueError("ZAPIER_HOOK_UNAVAILABLE") from None
    if len(raw) > 4096 or len(values) != 1 or not HOOK.fullmatch(values[0]):
        raise ValueError("ZAPIER_HOOK_UNAVAILABLE")
    return values[0]


def https_post(url, body, timeout):
    """No redirects, no proxies from the environment, bounded response read."""
    parts = urlsplit(url)
    connection = http.client.HTTPSConnection(parts.hostname, 443, timeout=timeout)
    try:
        connection.request(
            "POST", parts.path, body=body, headers={"Content-Type": "application/json"}
        )
        response = connection.getresponse()
        return response.status, response.read(4096)
    finally:
        connection.close()


class ZapierSender:
    def __init__(self, outbox_path, hook_path, *, post=https_post, timeout=10):
        self.path, self.hook_path, self.post, self.timeout = (
            Path(outbox_path),
            hook_path,
            post,
            timeout,
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS consent(singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                    destination TEXT NOT NULL, opted_in INTEGER NOT NULL, changed_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS outbox(event_key TEXT PRIMARY KEY,
                    state TEXT NOT NULL, attempts INTEGER NOT NULL, last_status INTEGER,
                    receipt TEXT, updated_at TEXT NOT NULL);
            """)
        self.path.chmod(0o600)

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def opt_in(self, destination):
        if not isinstance(destination, str) or not re.fullmatch(
            r"[A-Za-z0-9 _.-]{1,60}", destination
        ):
            raise ValueError("INVALID destination label")
        self._consent(destination, True)

    def opt_out(self):
        self._consent("none", False)

    def _consent(self, destination, value):
        with self._db() as db:
            db.execute(
                "INSERT OR REPLACE INTO consent VALUES(1,?,?,?)", (destination, int(value), _now())
            )

    def status(self, event_key):
        with self._db() as db:
            row = db.execute("SELECT * FROM outbox WHERE event_key=?", (event_key,)).fetchone()
        return dict(row) if row else None

    def send(self, preview):
        payload = _minimal(preview)
        key = payload["event_key"]
        url = hook_url(self.hook_path)  # before any outbox state changes
        with self._db() as db:
            consent = db.execute("SELECT * FROM consent WHERE singleton=1").fetchone()
            if consent is None or not consent["opted_in"]:
                raise ValueError("DENIED no opt-in")
            payload["destination"] = consent["destination"]
            row = db.execute("SELECT * FROM outbox WHERE event_key=?", (key,)).fetchone()
            if row and row["state"] == "sent":
                return dict(row, deduplicated=True)
            if row and row["state"] == "unknown":
                raise ValueError("UNKNOWN delivery outcome; not resent automatically")
            if row and (row["state"] != "retryable" or row["attempts"] >= MAX_ATTEMPTS):
                raise ValueError("DENIED delivery closed")
            attempts = (row["attempts"] if row else 0) + 1
            db.execute(
                "INSERT OR REPLACE INTO outbox VALUES(?,?,?,?,?,?)",
                (key, "intended", attempts, None, None, _now()),
            )
        try:
            status, body = self.post(
                url, json.dumps(payload, sort_keys=True).encode(), self.timeout
            )
        except (ConnectionRefusedError, socket.gaierror):
            # Nothing could have reached Zapier: safe to retry the same event key.
            return self._record(key, "retryable", None, None)
        except OSError:
            # Timeout/reset after sending may have delivered: never resend automatically.
            return self._record(key, "unknown", None, None)
        if 200 <= status < 300:
            return self._record(key, "sent", status, _receipt(body))
        if status in RETRYABLE:
            state = "retryable" if attempts < MAX_ATTEMPTS else "failed"
            return self._record(key, state, status, None)
        return self._record(key, "failed", status, None)

    def _record(self, key, state, status, receipt):
        with self._db() as db:
            db.execute(
                "UPDATE outbox SET state=?,last_status=?,receipt=?,updated_at=? WHERE event_key=?",
                (state, status, json.dumps(receipt) if receipt else None, _now(), key),
            )
            return dict(db.execute("SELECT * FROM outbox WHERE event_key=?", (key,)).fetchone())


def _minimal(preview):
    if not isinstance(preview, dict) or set(preview) != {
        "event_key",
        "text",
        "projection",
        "delivery",
        "authority",
    }:
        raise ValueError("DENIED preview shape")
    if (preview["delivery"], preview["authority"]) != ("NOT SENT", "NONE"):
        raise ValueError("DENIED preview authority")
    text = preview["text"]
    if (
        not EVENT.fullmatch(str(preview["event_key"]))
        or not isinstance(text, str)
        or not 1 <= len(text) <= 600
    ):
        raise ValueError("DENIED preview content")
    if preview["projection"] not in {"private_status", "public_safe"}:
        raise ValueError("DENIED preview projection")
    reject_secret(text)
    return {
        "event_key": preview["event_key"],
        "text": text,
        "projection": preview["projection"],
        "source": "GoldGraft synthetic evaluation",
        "notice": "Notification only; not an approval. Act only in the authenticated case view.",
    }


def _receipt(body):
    try:
        data = json.loads(body)
    except (ValueError, TypeError):
        return {"status": "accepted_unparsed"}
    safe = {}
    for field in ["id", "request_id", "status", "attempt"]:
        value = data.get(field) if isinstance(data, dict) else None
        if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value):
            safe[field] = value
    return safe or {"status": "accepted_unparsed"}


def _now():
    return datetime.now(UTC).isoformat()
