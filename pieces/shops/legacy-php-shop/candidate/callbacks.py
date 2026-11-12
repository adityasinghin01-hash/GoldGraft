"""Merchant-domain callback consumer using Gupta's actual gateway port.

Ingress, raw receipt encryption, signature verification and authority are backend
duties. This consumer takes receipts only by calling that port itself; incoming
JSON can never supply a trusted verification flag. Financial state changes only
through the injected original-rail reconciliation handler, never callback amounts.
"""

import hashlib
import json
import sqlite3


class CallbackConsumer:
    def __init__(self, gateway, database, *, graft_id, lookup_intent, reconcile):
        self.gateway = gateway
        self.graft_id = graft_id
        self.lookup = lookup_intent
        self.reconcile = reconcile
        self.db = sqlite3.connect(database)
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS merchant_callback_effects "
            "(event_id TEXT PRIMARY KEY, digest TEXT NOT NULL, state TEXT NOT NULL)"
        )

    def close(self):
        self.db.close()

    def _apply(self, local_id, event_id, payload, receipt):
        if (
            not getattr(self.gateway.inbox, "durable", False)
            or receipt.verification != "verified"
            or receipt.binding_ok is not True
            or not receipt.binding_checked
            or receipt.holds
        ):
            return {
                "status": "HOLD",
                "reason": "durable_verified_binding_required",
                "reconciled": False,
            }
        # Bind duplicate identity to local order and original message. Retrying a
        # failed GET is safe; no mutating payment operation exists in this port.
        digest = hashlib.sha256(
            json.dumps(
                [local_id, payload],
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode()
        ).hexdigest()
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            prior = self.db.execute(
                "SELECT digest,state FROM merchant_callback_effects WHERE event_id=?",
                (event_id,),
            ).fetchone()
            if prior and prior[0] != digest:
                return {
                    "status": "HOLD",
                    "reason": "callback_identity_conflict",
                    "reconciled": False,
                }
            if prior and prior[1] == "APPLIED":
                return {"status": "DUPLICATE", "reconciled": False}
            self.db.execute(
                "INSERT OR IGNORE INTO merchant_callback_effects VALUES (?,?,'RECHECK')",
                (event_id, digest),
            )
        try:
            # The callable must be the existing original-rail GET reconciler,
            # not a generic tool dispatcher. Its failure leaves RECHECK durable.
            self.reconcile(local_id)
        except Exception:  # noqa: BLE001 -- The backend may report an unknown effect via its own exception type.
            return {
                "status": "HOLD",
                "reason": "original_rail_reconciliation_pending",
                "reconciled": False,
            }
        with self.db:
            self.db.execute(
                "UPDATE merchant_callback_effects SET state='APPLIED' WHERE event_id=?",
                (event_id,),
            )
        return {"status": "RECONCILED", "reconciled": True}

    def webhook(self, local_id, payload, headers):
        try:
            intent = self.lookup(local_id)
            if intent["origin"] != "NEW" or not isinstance(payload, dict):
                raise ValueError("wrong_rail")
            event_id = payload.get("id")
            event = payload.get("event_type")
            if (
                not isinstance(event_id, str)
                or not 1 <= len(event_id) <= 128
                or event
                not in (
                    "PAYMENT.CAPTURE.COMPLETED",
                    "PAYMENT.CAPTURE.PENDING",
                    "PAYMENT.CAPTURE.DENIED",
                    "PAYMENT.CAPTURE.REFUNDED",
                )
            ):
                raise ValueError("unsupported_event")
            # Values are from recorded merchant intent; never from the message.
            expected = {
                "order_id": intent["provider_order_id"],
                "merchant_id": intent["merchant_id"],
                "amount_minor": intent["amount_minor"],
                "currency": "USD",
                "event_type": event,
            }
            receipt = self.gateway.handle_webhook(
                payload, headers, graft_id=self.graft_id, expected=expected
            )
            return self._apply(local_id, "WEBHOOK:" + event_id, payload, receipt)
        except (KeyError, TypeError, ValueError):
            return {
                "status": "HOLD",
                "reason": "callback_or_intent_not_supported",
                "reconciled": False,
            }

    def ipn(self, local_id, raw_body, headers):
        try:
            from urllib.parse import parse_qsl

            intent = self.lookup(local_id)
            if intent["origin"] != "OLD" or not isinstance(raw_body, str):
                raise ValueError("wrong_rail")
            fields = dict(parse_qsl(raw_body, keep_blank_values=True))
            status = fields.get("payment_status")
            if status not in ("Pending", "Completed"):
                raise ValueError("unsupported_ipn_status")
            expected = {
                "txn_id": intent["transaction_id"],
                "receiver_email": intent["receiver_email"],
                "payment_status": status,
                "amount_minor": intent["amount_minor"],
                "currency": "USD",
            }
            receipt = self.gateway.handle_ipn(
                raw_body, headers, graft_id=self.graft_id, expected=expected
            )
            # Pending and Completed for one transaction are different effects;
            # delivery/transmission IDs are not business event identities.
            event_id = "IPN:" + intent["transaction_id"] + ":" + status
            return self._apply(local_id, event_id, fields, receipt)
        except (KeyError, TypeError, ValueError):
            return {
                "status": "HOLD",
                "reason": "callback_or_intent_not_supported",
                "reconciled": False,
            }
