"""Read-only, private candidate state inspection for VJ03/VJ04/VJ05 handoff.

This inspects an actual SQLite snapshot, not asserted booleans. It does not
fence, export/import merchant state, acknowledge callbacks, apply or qualify exit.
"""

import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path


def inspect(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("private_regular_bounded_database_required")
    # URI mode=ro cannot create a missing database or modify the input.
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        if connection.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
            raise ValueError("state_integrity_failed")
        meta = connection.execute("SELECT merchant FROM candidate_meta WHERE id=1").fetchall()
        if len(meta) != 1:
            raise ValueError("merchant_binding_missing")
        rows = connection.execute("SELECT id,body FROM candidate_orders ORDER BY id").fetchall()
        operations = connection.execute(
            "SELECT order_id,kind,request_id,status FROM candidate_operations "
            "ORDER BY order_id,kind"
        ).fetchall()
        resources = connection.execute(
            "SELECT kind,resource_id,order_id FROM candidate_resources ORDER BY kind,resource_id"
        ).fetchall()
        schema = connection.execute(
            "SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        canonical = json.dumps(
            [meta, rows, operations, resources], separators=(",", ":"), ensure_ascii=False
        ).encode()
        pending, holdings, refunds, paid = 0, 0, 0, 0
        known = {}
        for order_id, raw in rows:
            item = json.loads(raw)
            if (
                item["id"] != order_id
                or item["merchant_id"] != meta[0][0]
                or item["origin"] != "NEW"
                or item["api_family"] != "orders-v2"
                or item["environment"] != "sandbox"
                or item["currency"] != "USD"
            ):
                raise ValueError("origin_or_scope_mismatch")
            if (
                item["state"]
                not in (
                    "OPEN",
                    "CREATE_UNKNOWN",
                    "CREATE_RECHECK",
                    "CREATED",
                    "ACTION_REQUIRED",
                    "CAPTURE_UNKNOWN",
                    "PENDING",
                    "PAID",
                    "DECLINED",
                    "FAILED",
                    "REFUNDED",
                    "PARTIALLY_REFUNDED",
                )
                or not isinstance(item["amount"], str)
                or re.fullmatch(r"(0|[1-9][0-9]{0,6})\.[0-9]{2}", item["amount"]) is None
                or item["amount"] == "0.00"
                or type(item["buyer_cancelled"]) is not bool
            ):
                raise ValueError("invalid_financial_state")
            if (
                item["state"]
                in ("PAID", "PENDING", "DECLINED", "FAILED", "REFUNDED", "PARTIALLY_REFUNDED")
                and item["capture_id"] is None
            ):
                raise ValueError("capture_correspondence_missing")
            known[order_id] = item
            holdings += (
                item["hold"] is not None
                or item["state"].endswith(("_UNKNOWN", "_RECHECK"))
                or item["refund_state"] in ("UNKNOWN", "RECHECK")
            )
            pending += item["state"] == "PENDING"
            paid += item["state"] == "PAID"
            refunds += item["refund_state"] is not None
        bindings = {(kind, resource): order_id for kind, resource, order_id in resources}
        for kind, resource, order_id in resources:
            field = {
                "order": "provider_order_id",
                "capture": "capture_id",
                "refund": "refund_id",
            }.get(kind)
            if field is None or order_id not in known or known[order_id][field] != resource:
                raise ValueError("resource_binding_mismatch")
        for order_id, item in known.items():
            for kind, field in [
                ("order", "provider_order_id"),
                ("capture", "capture_id"),
                ("refund", "refund_id"),
            ]:
                if item[field] is not None and bindings.get((kind, item[field])) != order_id:
                    raise ValueError("resource_binding_missing")
        unresolved_dispatches = 0
        seen_requests = set()
        recorded = set()
        for order_id, kind, request, status in operations:
            if (
                order_id not in known
                or kind not in ("create", "capture", "refund")
                or status not in ("DISPATCHED", "DONE")
            ):
                raise ValueError("operation_binding_mismatch")
            if not isinstance(request, str) or len(request) != 32 or request in seen_requests:
                raise ValueError("request_identity_invalid")
            seen_requests.add(request)
            recorded.add((order_id, kind))
            unresolved_dispatches += status == "DISPATCHED"
        for kind, _, order_id in resources:
            operation = {"order": "create", "capture": "capture", "refund": "refund"}[kind]
            if (order_id, operation) not in recorded:
                raise ValueError("resource_operation_missing")
        return {
            "status": "PASS",
            "evidence": "LOCAL_READ_ONLY_CANDIDATE_SNAPSHOT",
            "records": len(rows),
            "operations": len(operations),
            "resource_bindings": len(resources),
            "snapshot_sha256": hashlib.sha256(canonical).hexdigest(),
            "schema_sha256": hashlib.sha256(
                json.dumps(schema, separators=(",", ":")).encode()
            ).hexdigest(),
            "paid_records": paid,
            "pending_records": pending,
            "refund_records": refunds,
            "held_records": holdings,
            "unresolved_dispatches": unresolved_dispatches,
            "private_values_printed": False,
            "input_modified": False,
            "migration_gate": "HOLD",
            "finalisation_gate": "HOLD",
            "exit_gate": "HOLD",
            "payment_qualified": False,
            "external_service_calls": 0,
        }
    finally:
        connection.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--database", type=Path, required=True)
    args = p.parse_args()
    try:
        result = inspect(args.database)
    except (OSError, sqlite3.Error, ValueError, KeyError, TypeError):
        result = {
            "status": "HOLD",
            "reason": "candidate_state_not_verified",
            "private_values_printed": False,
        }
    print(json.dumps(result))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
