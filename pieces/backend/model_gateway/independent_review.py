"""Opt-in, signed one-case authority; earlier unknown money and identity stay intact."""

import hashlib
import hmac
import json

from goldgraft_contracts.plan5_common import canonical_bytes, reject_secret

from .ledger import Ledger, money
from .secrets import private_bytes

# Project phase ceiling ($10 for all13 agents, Aditya 11 Nov2026). A signed body
# must also equal the ledger's actual active cap, which every admission re-checks.
PROJECT_PHASE_CEILING_MICRO_USD = 10000000


class IndependentTestLedger(Ledger):
    def __init__(self, path, *, review_path, signing_path, profile, case_id, case_digest, batch):
        try:
            document = json.loads(private_bytes(review_path, maximum=8192))
            body = document["body"]
            key = private_bytes(signing_path, maximum=32)
            signature = hmac.new(key, canonical_bytes(body), hashlib.sha256).hexdigest()
            reject_secret(canonical_bytes(body).decode())
            strings = {
                "kind",
                "authorization_ref",
                "original_batch",
                "original_batch_fingerprint",
                "original_turn",
                "original_fingerprint",
                "new_batch",
                "case_id",
                "case_digest",
                "profile",
            }
            amounts = {
                "original_turn_reservation",
                "original_batch_ceiling",
                "max_batch_reservation",
                "active_cap",
            }
            if (
                set(document) != {"body", "signature"}
                or set(body) != strings | amounts
                or len(key) != 32
                or not hmac.compare_digest(signature, document["signature"])
                or any(type(body[k]) is not str or not 1 <= len(body[k]) <= 256 for k in strings)
                or any(money(body[k]) == 0 for k in amounts)
                or body["kind"] != "one_independent_synthetic_test_retaining_unknown"
                or (body["profile"], body["case_id"], body["case_digest"], body["new_batch"])
                != (profile.ref, case_id, case_digest, batch)
                or body["new_batch"] == body["original_batch"]
                or body["max_batch_reservation"] != profile.batch_reservation
                or body["active_cap"] > PROJECT_PHASE_CEILING_MICRO_USD
            ):
                raise ValueError("REVIEW_DENIED")
        except (OSError, ValueError, TypeError, KeyError):
            raise ValueError("REVIEW_DENIED") from None
        self._review = body
        super().__init__(path)

    def reserve(self, batch, fingerprint, ceiling):
        if (
            batch == self._review["new_batch"]
            and money(ceiling) > self._review["max_batch_reservation"]
        ):
            raise ValueError("REVIEW_BATCH_BOUND")
        return super().reserve(batch, fingerprint, ceiling)

    def _uncertain(self, db, batch=None):
        rows = db.execute(
            "SELECT * FROM turns WHERE state IN ('intended','submitted','unknown')"
        ).fetchall()
        if not rows:
            return False
        review = self._review
        if batch != review["new_batch"] or len(rows) != 1:
            return True
        row = rows[0]
        original = self._batch(db, review["original_batch"])
        # A new unknown, changed original identity/accounting, or changed active
        # authority always blocks. No row is reconciled, released or rewritten.
        return not (
            (
                row["batch"],
                row["id"],
                row["fingerprint"],
                row["reserved"],
                row["actual"],
                row["state"],
            )
            == (
                review["original_batch"],
                review["original_turn"],
                review["original_fingerprint"],
                review["original_turn_reservation"],
                0,
                "unknown",
            )
            and (
                original["fingerprint"],
                original["ceiling"],
                original["actual"],
                original["state"],
            )
            == (
                review["original_batch_fingerprint"],
                review["original_batch_ceiling"],
                0,
                "reserved",
            )
            and db.execute("SELECT active_cap FROM budget WHERE singleton=1").fetchone()[0]
            == review["active_cap"]
        )
