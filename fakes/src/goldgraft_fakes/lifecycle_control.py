"""Scripted persistent GU/VJ/SH delivery counterpart, never Singh's reducer/engine."""

import hashlib
import json

from goldgraft_contracts.agent_runtime import ArtifactDescriptor
from goldgraft_contracts.lifecycle import (
    DeliveryDecision,
    DeliverySnapshot,
    LifecycleWorkRequestReceipt,
    PendingResult,
)
from goldgraft_contracts.plan5_common import content_digest
from goldgraft_contracts.registry import validate

from .offline_store import OfflineStore, encoded, fail


class OfflineLifecycleControl:
    def __init__(self, path, *, clock=None):
        self.store = OfflineStore(path, clock=clock)

    def fixture_snapshot(self, run_ref, snapshot):
        """Explicit synthetic observation injection; no automatic transition logic."""
        with self.store.transaction() as db:
            prior = db.execute("SELECT body FROM deliveries WHERE run_ref=?", (run_ref,)).fetchone()
            if prior:
                old = DeliverySnapshot.model_validate_json(prior["body"])
                if (old.case_id, old.run_id, old.generation) != (
                    snapshot.case_id,
                    snapshot.run_id,
                    snapshot.generation,
                ):
                    fail("CONFLICT snapshot identity")
            db.execute(
                "INSERT OR REPLACE INTO deliveries VALUES(?,?)", (run_ref, encoded(snapshot))
            )

    def snapshot(self, run_ref):
        with self.store.transaction() as db:
            return self._snapshot(db, run_ref)

    @staticmethod
    def _snapshot(db, ref):
        row = db.execute("SELECT body FROM deliveries WHERE run_ref=?", (ref,)).fetchone()
        if row is None:
            fail("NOT_FOUND")
        return DeliverySnapshot.model_validate_json(row["body"])

    def fixture_slot(self, run_ref, decision, *, authority_current, approvals_current):
        snapshot = self.snapshot(run_ref)
        body = {
            "decision_digest": content_digest(decision),
            "authority_current": authority_current,
            "approvals_current": approvals_current,
            "case_id": snapshot.case_id,
            "evidence_class": "scripted",
        }
        with self.store.transaction() as db:
            db.execute(
                "INSERT OR REPLACE INTO scripts VALUES(?,?,?)",
                ("delivery-slot:" + run_ref, decision.slot_id, encoded(body)),
            )

    def submit(self, decision, request_id):
        decision = DeliveryDecision.model_validate(decision.model_dump(mode="json"))
        with self.store.transaction() as db:
            fingerprint = content_digest(decision)
            prior = db.execute("SELECT * FROM effects WHERE id=?", (request_id,)).fetchone()
            if prior:
                if prior["fingerprint"] != fingerprint:
                    fail("CONFLICT")
                return LifecycleWorkRequestReceipt.model_validate(
                    json.loads(prior["body"])["receipt"]
                )
            snapshots = [
                (r["run_ref"], DeliverySnapshot.model_validate_json(r["body"]))
                for r in db.execute("SELECT * FROM deliveries")
            ]
            matches = [
                (ref, s)
                for ref, s in snapshots
                if (s.case_id, s.run_id, s.generation)
                == (decision.case_id, decision.run_id, decision.generation)
            ]
            if len(matches) != 1:
                fail("DENIED")
            ref, snapshot = matches[0]
            if snapshot.cancellation_ref and decision.operation != "reconcile_effect":
                fail("CANCELLED")
            if snapshot.state_version != decision.expected_state_version:
                fail("STALE")
            if decision.kind != "request":
                fail("DENIED nonrequest")
            if decision.operation == "reconcile_effect":
                row = db.execute(
                    "SELECT body FROM effects WHERE id=?", (decision.existing_effect_ref,)
                ).fetchone()
                if row is None:
                    fail("MISSING_EVIDENCE original effect")
                original = json.loads(row["body"])
                if original["run_ref"] != ref:
                    fail("DENIED")
                return LifecycleWorkRequestReceipt.model_validate(original["receipt"])
            if decision.slot_id is not None:
                slot = db.execute(
                    "SELECT body FROM scripts WHERE namespace=? AND id=?",
                    ("delivery-slot:" + ref, decision.slot_id),
                ).fetchone()
                if slot is None:
                    fail("MISSING_EVIDENCE exact approval/authority")
                slot = json.loads(slot["body"])
                if (
                    not slot["authority_current"]
                    or not slot["approvals_current"]
                    or slot["decision_digest"] != fingerprint
                ):
                    fail("DENIED stale approval")
            logical = content_digest(
                {
                    "run": ref,
                    "generation": decision.generation,
                    "slot": decision.slot_id,
                    "operation": decision.operation if decision.slot_id is None else None,
                    "version": decision.expected_state_version
                    if decision.slot_id is None
                    else None,
                }
            )
            if db.execute("SELECT 1 FROM effects WHERE logical_key=?", (logical,)).fetchone():
                fail("CONFLICT original effect must reconcile")
            receipt = LifecycleWorkRequestReceipt(
                request_id=request_id,
                run_id=snapshot.run_id,
                generation=snapshot.generation,
                accepted_at=self.store.clock(),
                request_digest=fingerprint,
            )
            status = PendingResult(
                request_id=request_id,
                state="unknown",
                evidence_refs=[],
                checked_at=self.store.clock(),
            )
            body = {
                "receipt": receipt.model_dump(mode="json"),
                "status": status.model_dump(mode="json"),
                "run_ref": ref,
                "evidence_class": "scripted",
                "decision": decision.model_dump(mode="json"),
            }
            db.execute(
                "INSERT INTO effects VALUES(?,?,?,?,1)",
                (request_id, logical, fingerprint, encoded(body)),
            )
            return receipt

    def status(self, request_id):
        with self.store.transaction() as db:
            row = db.execute("SELECT body FROM effects WHERE id=?", (request_id,)).fetchone()
            if row is None:
                fail("NOT_FOUND")
            body = json.loads(row["body"])
            status = body["status"]
            return validate(
                "PendingResult/1" if "state" in status else "LifecycleWorkResult/1", status
            )

    def fixture_result(self, request_id, result):
        with self.store.transaction() as db:
            row = db.execute("SELECT body FROM effects WHERE id=?", (request_id,)).fetchone()
            if row is None:
                fail("NOT_FOUND")
            body = json.loads(row["body"])
            if (result.request_id, result.run_id, result.generation) != (
                request_id,
                body["receipt"]["run_id"],
                body["receipt"]["generation"],
            ):
                fail("DENIED")
            if not result.authenticity_ref.startswith("fake:"):
                fail("DENIED nonfake authenticity")
            body["status"] = result.model_dump(mode="json")
            db.execute("UPDATE effects SET body=? WHERE id=?", (encoded(body), request_id))

    def dispatch_count(self, request_id):
        with self.store.transaction() as db:
            row = db.execute(
                "SELECT dispatch_count FROM effects WHERE id=?", (request_id,)
            ).fetchone()
            return row[0] if row else 0

    def fixture_record(self, run_ref, schema, payload):
        payload = dict(payload)
        if "authenticity_ref" in payload:
            if not payload["authenticity_ref"].startswith(("fake:", "fixture:")):
                fail("DENIED nonfake authenticity")
            payload["authenticity_ref"] = "fake:scripted-authenticity-not-verifiable"
        payload = validate(schema, payload).model_dump(mode="json", by_alias=True)
        with self.store.transaction() as db:
            s = self._snapshot(db, run_ref)
            if (
                payload.get("case_id", s.case_id) != s.case_id
                or payload.get("run_id", s.run_id) != s.run_id
            ):
                fail("DENIED")
            data = encoded(payload).encode()
            ref = "fake:lifecycle-artifact:" + content_digest(
                {"run": run_ref, "schema": schema, "body": payload}
            )
            descriptor = ArtifactDescriptor(
                ref=ref,
                case_id=s.case_id,
                run_id=s.run_id,
                generation=s.generation,
                schema=schema,
                payload_digest=hashlib.sha256(data).hexdigest(),
                byte_count=len(data),
                subject_digest=content_digest("synthetic-lifecycle-subject"),
                input_digest=content_digest([]),
                derivation_ref=None,
                producer_identity_ref="fake:lifecycle-counterpart",
                trust="collector_observed",
                evidence_class="scripted",
                created_at=self.store.clock(),
                expires_at=None,
            )
            db.execute(
                "INSERT OR IGNORE INTO artifacts VALUES(?,?,?)", (ref, encoded(descriptor), data)
            )
            return ref

    def resolve_fixture(self, ref, *, run_ref):
        with self.store.transaction() as db:
            snapshot = self._snapshot(db, run_ref)
            row = db.execute("SELECT * FROM artifacts WHERE ref=?", (ref,)).fetchone()
            if row is None:
                fail("NOT_FOUND")
            d = ArtifactDescriptor.model_validate_json(row["descriptor"])
            if (d.case_id, d.run_id, d.generation) != (
                snapshot.case_id,
                snapshot.run_id,
                snapshot.generation,
            ):
                fail("DENIED")
            if (
                d.evidence_class != "scripted"
                or hashlib.sha256(row["payload"]).hexdigest() != d.payload_digest
            ):
                fail("INVALID")
            return d, validate(d.schema_id, json.loads(row["payload"]))
