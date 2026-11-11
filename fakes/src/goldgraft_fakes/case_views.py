"""Persistent, actor-scoped synthetic case projections for frontend construction."""

import hashlib
import json
from pathlib import Path

from goldgraft_contracts.registry import validate

from .offline_store import OfflineStore, fail


class OfflineCaseViews:
    label = "Mock mode: showing saved sample data, not a live system."

    def __init__(self, path, *, fixture_root=None):
        self.store = OfflineStore(path)
        self.root = fixture_root or Path(__file__).resolve().parents[3]

    def load_mode(self, mode, *, actor):
        if actor != "synthetic-reviewer":
            fail("DENIED")
        index = json.loads((self.root / "fixtures/plan5/index.json").read_text())
        matches = [m for m in index["frontend_modes"] if m["mode"] == mode]
        if len(matches) != 1:
            fail("UNSUPPORTED fixture mode")
        values = {}
        for record in matches[0]["records"]:
            path = (self.root / record["path"]).resolve()
            if not path.is_relative_to(self.root.resolve()):
                fail("DENIED")
            data = path.read_bytes()
            if (
                hashlib.sha256(data).hexdigest() != record["sha256"]
                or record["evidence_class"] != "scripted"
            ):
                fail("INVALID fixture hash/provenance")
            value = validate(record["schema"], json.loads(data))
            values[record["schema"]] = value
        if values["CaseView/1"].evidence_class != "scripted":
            fail("DENIED fake cannot become real")
        with self.store.transaction() as db:
            body = {schema: v.model_dump(mode="json") for schema, v in values.items()}
            self.store.key(db, "case-projection:" + actor, mode, body, body)
        return values
