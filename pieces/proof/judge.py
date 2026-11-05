"""Compare canonical old, repeat-old and new money evidence."""

import json
from collections import defaultdict
from collections.abc import Sequence
from itertools import zip_longest

from goldgraft_contracts.money import MoneyEvent
from goldgraft_contracts.proof import MoneyContract, RuleHit, Verdict
from goldgraft_contracts.runner import RawCapture
from goldgraft_contracts.survey import TargetPlan


def identity(event):
    pp = event["pp"]
    return (
        pp.get("refund_id") if event["kind"] == "REFUND" else pp.get("capture_id", pp.get("txn_id"))
    )


def rule_hits(events, capture: RawCapture | None):
    hits = defaultdict(set)
    by_order = defaultdict(list)
    for event in events:
        by_order[event["order_ref"]].append(event)
    db_writes = defaultdict(list)
    if capture is not None:
        for index, exchange in enumerate(capture.exchanges):
            if exchange.db_change is None:
                continue
            headers = {key.lower(): value for key, value in exchange.headers.items()}
            ref = headers.get("x-goldgraft-order-ref")
            after = exchange.db_change.after or {}
            db_writes[ref].append((index, after.get("refunded_minor")))

    for order, items in by_order.items():

        def hit(rule, items=items):
            hits[rule].update(event["raw_ref"] for event in items)

        intents = [e for e in items if e["kind"] == "INTENT"]
        captures = [e for e in items if e["kind"] == "CAPTURE"]
        paid = [e for e in items if e["kind"] == "SHOP_PAID"]
        completed = [e for e in captures if e.get("status_norm") == "COMPLETED"]
        ledger_completed = {identity(e) for e in completed if e["source"] == "PAYPAL_LEDGER"}
        if paid and len(ledger_completed) != 1:
            hit("R01")
        for observation in captures:
            if intents and observation["money"]["minor"] != intents[0]["money"]["minor"]:
                hit("R02")
            if intents and observation["money"]["currency"] != intents[0]["money"]["currency"]:
                hit("R03")
        if completed and not paid:
            hit("R04")
        if len({identity(e) for e in completed}) > 1:
            hit("R05")
        for paid_event in paid:
            if not any(e["kind"] == "APPROVE" and e["seq"] < paid_event["seq"] for e in items):
                hit("R06")
        if any(e.get("status_norm") == "PENDING" for e in captures):
            if paid or not any(e["kind"] == "SHOP_PENDING" for e in items):
                hit("R07")
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
                    hit("R08")
        # Refund totals are checked per independent witness, not API+ledger copies.
        captured_total = sum({identity(e): e["money"]["minor"] for e in completed}.values())
        for source in ("PAYPAL_CALL", "PAYPAL_LEDGER"):
            refunds = {
                identity(e): e["money"]["minor"]
                for e in items
                if e["kind"] == "REFUND" and e["source"] == source
            }
            if sum(refunds.values()) > captured_total:
                hit("R11")
        for index, refunded in db_writes[order]:
            if type(refunded) is int and refunded > captured_total:
                hits["R11"].add(
                    f"raw/{capture.scenario_id}.{capture.variant}.json#/exchanges/{index}"
                )
    return hits


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


def judge(
    old: Sequence[MoneyEvent],
    old_twin: Sequence[MoneyEvent],
    new: Sequence[MoneyEvent],
    contract: MoneyContract,
    target_plan: TargetPlan,
    *,
    old_capture: RawCapture | None = None,
    new_capture: RawCapture | None = None,
) -> Verdict:
    streams = [old, old_twin, new]
    ids = {event.scenario_id for stream in streams for event in stream}
    if len(ids) != 1:
        raise ValueError("Judge needs evidence for exactly one scenario")
    scenario = ids.pop()
    baseline, twin, candidate = [
        [event.model_dump(mode="json", exclude_none=True) for event in stream] for stream in streams
    ]

    allowed_ids = {"legacy_token", "txn_id", "order_id", "capture_id", "refund_id", "debug_id"}
    noise = set()
    for left, right in zip(baseline, twin, strict=False):
        if (left["kind"], left["source"], left["order_ref"]) != (
            right["kind"],
            right["source"],
            right["order_ref"],
        ):
            continue
        for field in ("run_id", "variant", "raw_ref", "t_ms"):
            if left[field] != right[field]:
                noise.add(field)
        for field in allowed_ids:
            if left["pp"].get(field) != right["pp"].get(field):
                noise.add(f"pp.{field}")

    deltas = {delta.id for delta in target_plan.deltas}
    for delta, legacy, modern in (
        ("D_TOKEN_ORDER", "legacy_token", "order_id"),
        ("D_TXN_CAPTURE", "txn_id", "capture_id"),
    ):
        if delta in deltas and f"pp.{legacy}" in noise:
            noise.add(f"pp.{modern}")

    def verdict(grade, hits=(), diff=()):
        return Verdict(
            scenario_id=scenario,
            grade=grade,
            rule_hits=list(hits),
            parity_diff=list(diff),
            noise_masked=sorted(noise),
            deltas_applied=sorted(deltas),
        )

    def has_required_evidence(events):
        witnessed = {event["order_ref"] for event in events if event["source"] == "PAYPAL_LEDGER"}
        required = {
            event["order_ref"]
            for event in events
            if event["kind"] in {"CAPTURE", "REFUND", "SHOP_PAID", "SHOP_PENDING"}
        }
        return bool(events) and required <= witnessed

    if not all(has_required_evidence(events) for events in (baseline, twin, candidate)):
        return verdict("UNVERIFIED")

    rules = {rule.id for rule in contract.rules}
    for stream, capture in ((old, old_capture), (new, new_capture)):
        if capture is not None and any(
            (event.scenario_id, event.run_id, event.graft_id, event.variant)
            != (capture.scenario_id, capture.run_id, capture.graft_id, capture.variant)
            for event in stream
        ):
            raise ValueError("Raw evidence does not match the canonical event stream")
    old_hits = rule_hits(baseline, old_capture)
    new_hits = rule_hits(candidate, new_capture)
    hits = [
        RuleHit(rule=rule, side=side, evidence=sorted(found[rule]))
        for side, found in (("NEW", new_hits), ("OLD", old_hits))
        for rule in sorted(found.keys() & rules)
    ]
    before = projection(baseline, noise=noise, old=True, deltas=deltas)
    after = projection(candidate, noise=noise, old=False, deltas=deltas)
    diff = [
        {"index": index, "old": left, "new": right}
        for index, (left, right) in enumerate(zip_longest(before, after))
        if left != right
    ]
    if any(hit.side == "NEW" for hit in hits):
        return verdict("PROBLEM", hits, diff)
    if hits and not diff:
        return verdict("PASS_FIXED", hits)
    return verdict("PROBLEM" if diff else "PASS", hits, diff)
