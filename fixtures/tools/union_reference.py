"""Offline C4 U2 cross-check, with raw provenance for completeness and DB refunds.

This is a fixture verifier, not the production Union Judge or a CMEL-DSL engine.
It checks the rule implications exercised by this corpus. Untested branches of
R09/R10/R14 and mutation outcomes are not production implementation claims.
"""

import json
from collections import Counter, defaultdict


def identity(event):
    pp = event["pp"]
    return (
        pp.get("refund_id") if event["kind"] == "REFUND" else pp.get("capture_id", pp.get("txn_id"))
    )


def rule_hits(raw, events):
    hits = set()
    by_order = defaultdict(list)
    for event in events:
        by_order[event["order_ref"]].append(event)
    for order, items in by_order.items():
        intents = [e for e in items if e["kind"] == "INTENT"]
        captures = [e for e in items if e["kind"] == "CAPTURE"]
        paid = [e for e in items if e["kind"] == "SHOP_PAID"]
        completed = [e for e in captures if e.get("status_norm") == "COMPLETED"]
        ledger_completed = {identity(e) for e in completed if e["source"] == "PAYPAL_LEDGER"}
        if paid and len(ledger_completed) != 1:
            hits.add("R01")
        for capture in captures:
            if intents and capture["money"]["minor"] != intents[0]["money"]["minor"]:
                hits.add("R02")
            if intents and capture["money"]["currency"] != intents[0]["money"]["currency"]:
                hits.add("R03")
        if completed and not paid:
            hits.add("R04")
        if len({identity(e) for e in completed}) > 1:
            hits.add("R05")
        for paid_event in paid:
            if not any(e["kind"] == "APPROVE" and e["seq"] < paid_event["seq"] for e in items):
                hits.add("R06")
        if any(e.get("status_norm") == "PENDING" for e in captures):
            if paid or not any(e["kind"] == "SHOP_PENDING" for e in items):
                hits.add("R07")
        for paid_event in paid:
            previous = [e for e in items if e["seq"] < paid_event["seq"]]
            notify_indices = [i for i, e in enumerate(previous) if e["kind"] == "NOTIFY"]
            if notify_indices:
                # A notification-caused transition requires its verification result.
                after_notify = previous[notify_indices[-1] + 1 :]
                results = [
                    e["kind"]
                    for e in after_notify
                    if e["kind"] in {"NOTIFY_VERIFIED", "NOTIFY_REJECTED"}
                ]
                if not results or results[-1] != "NOTIFY_VERIFIED":
                    hits.add("R08")
        # Refund totals are checked per independent witness, not API+ledger copies.
        captured_total = sum({identity(e): e["money"]["minor"] for e in completed}.values())
        for source in ("PAYPAL_CALL", "PAYPAL_LEDGER"):
            refunds = {
                identity(e): e["money"]["minor"]
                for e in items
                if e["kind"] == "REFUND" and e["source"] == source
            }
            if sum(refunds.values()) > captured_total:
                hits.add("R11")
        for exchange in raw["exchanges"]:
            if (
                exchange["direction"] == "SHOP_DB_WRITE"
                and exchange["headers"]["X-GoldGraft-Order-Ref"] == order
            ):
                after = exchange["db_change"]["after"]
                if after["refunded_minor"] > captured_total:
                    hits.add("R11")
        for event in items:
            if "money" in event and type(event["money"]["minor"]) is not int:
                hits.add("R16")
        # The synthetic catalogue has the same tee/mug prices as the real code.
        carts = [
            x["body_json"]["cart"]
            for x in raw["exchanges"]
            if x["direction"] == "BROWSER_TO_SHOP"
            and x["url"].endswith("/api/create")
            and x["headers"]["X-GoldGraft-Order-Ref"] == order
        ]
        if carts:
            catalogue = {"tee": 2500, "mug": 1250, "poster": 1800}
            expected = sum(catalogue.get(sku, 0) * qty for sku, qty in carts[0].items())
            if any(e["money"] != {"minor": expected, "currency": "USD"} for e in intents):
                hits.update({"R12", "R17"})
    return hits


def complete(raw):
    reads = [
        x
        for x in raw["exchanges"]
        if x["direction"] == "PAYPAL_TO_SHOP" and x["headers"].get("X-GoldGraft-Ledger")
    ]
    return bool(reads) and all(x["status"] < 400 for x in reads)


def projection(events, *, noise, old, deltas):
    """Apply only declared vocabulary deltas, then compare money-relevant facts."""
    projected, ledger_seen, shop_state = [], set(), {}
    for event in events:
        # Repeat reads of the SAME economic ID/status are observations, not charges.
        if event["source"] == "PAYPAL_LEDGER" and "D_LEDGER_READ" in deltas:
            key = (
                event["order_ref"],
                event["kind"],
                identity(event),
                event.get("status_norm"),
                json.dumps(event.get("money"), sort_keys=True),
            )
            if key in ledger_seen:
                continue
            ledger_seen.add(key)
        # CMEL DB rows observe status even when only refund bookkeeping changed.
        if event["source"] == "SHOP_DB":
            key = event["order_ref"]
            if shop_state.get(key) == event["kind"]:
                continue
            shop_state[key] = event["kind"]
        data = {k: event[k] for k in ("kind", "source", "order_ref", "pp")}
        data["pp"] = event["pp"].copy()
        for key in ("money", "status_norm", "items_hash"):
            if key in event:
                data[key] = event[key]
        if old:
            for delta, src, dst in (
                ("D_TOKEN_ORDER", "legacy_token", "order_id"),
                ("D_TXN_CAPTURE", "txn_id", "capture_id"),
            ):
                if delta in deltas and src in data["pp"]:
                    data["pp"][dst] = data["pp"].pop(src)
        for field in noise:
            if field.startswith("pp."):
                data["pp"].pop(field[3:], None)
        projected.append(data)
    return projected


def grade(old_raw, old, new_raw, new, verdict):
    """Return U2 grade, NEW rule IDs, OLD rule IDs, and unwaived parity difference."""
    if not complete(old_raw) or not complete(new_raw):
        return "UNVERIFIED", set(), set(), False
    new_hits, old_hits = rule_hits(new_raw, new), rule_hits(old_raw, old)
    expected = projection(
        old, noise=verdict["noise_masked"], old=True, deltas=verdict["deltas_applied"]
    )
    actual = projection(
        new, noise=verdict["noise_masked"], old=False, deltas=verdict["deltas_applied"]
    )
    parity = expected != actual
    if new_hits:
        return "PROBLEM", new_hits, old_hits, parity
    if old_hits:
        return "PASS_FIXED", new_hits, old_hits, False
    return "PROBLEM" if parity else "PASS", new_hits, old_hits, parity


def grade_counts(verdicts):
    return Counter(v["grade"] for v in verdicts)
