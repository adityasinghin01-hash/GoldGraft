"""Read-only first-reference state inspection.

No export, drain, fence, replay or payment effects.
"""

import argparse
import json
import re
import stat
from collections import Counter
from pathlib import Path

MAX_BYTES = 2_000_000
AMOUNT = re.compile(r"^(0|[1-9][0-9]{0,6})\.[0-9]{2}$")
WRITERS = [
    {"path": "src/api/create-payment.php", "state": "data/orders.json", "effect": "CREATED"},
    {"path": "src/api/execute-payment.php", "state": "data/orders.json", "effect": "PAID"},
    {"path": "src/api/refund.php", "state": "data/orders.json", "effect": "REFUNDED"},
    {"path": "src/ipn.php", "state": "data/ipn.log", "effect": "append_only_notification_log"},
]


def linked(path):
    return path.is_symlink() or getattr(path, "is_junction", lambda: False)()


def unique_object(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def read_orders(path):
    path = Path(path)
    if any(linked(p) for p in [path, *path.parents]):
        raise ValueError("linked_input_denied")
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_BYTES or before.st_nlink != 1:
        raise ValueError("bounded_regular_file_required")
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("bounded_regular_file_required")
    after = path.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise ValueError("input_changed_during_read")
    data = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    if data == []:  # Empty legacy array is accepted; a nonempty indexed list is not an order map.
        return {}
    if not isinstance(data, dict) or len(data) > 10000:
        raise ValueError("bounded_order_map_required")
    return data


def inspect_orders(data):
    findings, statuses = Counter(), Counter()
    for token, row in data.items():
        if not isinstance(row, dict):
            findings["invalid_record"] += 1
            continue
        status = row.get("status")
        if status in ("CREATED", "PAID", "REFUNDED"):
            statuses[status] += 1
        else:
            statuses["UNKNOWN"] += 1
            findings["unsupported_or_missing_status"] += 1
        if not isinstance(token, str) or not token or row.get("token") != token:
            findings["token_correspondence_missing"] += 1
        if not isinstance(row.get("amount"), str) or not AMOUNT.fullmatch(row["amount"]):
            findings["invalid_usd_amount"] += 1
        if status in ("PAID", "REFUNDED") and (
            not isinstance(row.get("transaction_id"), str) or not row["transaction_id"]
        ):
            findings["original_transaction_id_missing"] += 1
        if status == "REFUNDED" and (
            not isinstance(row.get("refund_id"), str) or not row["refund_id"]
        ):
            findings["refund_id_missing"] += 1
        if status in ("PAID", "REFUNDED"):
            # The original sample never supplies complete historical custody/origin evidence.
            findings["origin_and_account_binding_require_qualified_evidence"] += 1
    return {
        "records": len(data),
        "status_counts": dict(statuses),
        "finding_counts": dict(findings),
        "private_record_values_emitted": False,
    }


def report(path=None):
    result = {
        "document_kind": "local_read_only_shop_state_inventory_not_shared_statecutover",
        "source_scope": "pinned_plain_php_reference_only",
        "writers": WRITERS,
        "current_helpers": {
            "order_read": "src/api/orders.php (unauthenticated in original; never expose)",
            "browser_return": "src/success.php (not payment acceptance)",
            "cancel": "src/cancel.php",
            "notification": "src/ipn.php",
        },
        "qualified_primitive_status": {
            name: "NOT_ESTABLISHED"
            for name in [
                "authenticated_consistent_export",
                "admission_control",
                "browser_handler_drain",
                "all_writer_fence",
                "durable_callback_receipt",
                "event_high_water_mark",
                "restore_and_effect_replay",
                "merchant_independent_exit_executor",
            ]
        },
        "migration_gate": "HOLD",
        "actions_executed": [],
        "provider_calls": 0,
        "source_inspection_is_not_live_writer_discovery": True,
    }
    if path is None:
        result["local_state"] = {"status": "NOT_SUPPLIED"}
    else:
        try:
            result["local_state"] = {
                "status": "READ_ONLY_INSPECTED",
                **inspect_orders(read_orders(path)),
            }
        except (OSError, ValueError, TypeError, RecursionError):
            result["local_state"] = {
                "status": "HOLD",
                "reason": "order_state_invalid_unreadable_linked_or_changed",
                "private_record_values_emitted": False,
            }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--orders", type=Path, help="explicit authorized local JSON input; never changed"
    )
    args = parser.parse_args()
    result = report(args.orders)
    print(json.dumps(result, indent=2))
    return 2 if result["local_state"]["status"] == "HOLD" else 0


if __name__ == "__main__":
    raise SystemExit(main())
