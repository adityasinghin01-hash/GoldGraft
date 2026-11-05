"""Compare canonical old, repeat-old and new money evidence."""

import json
from collections import defaultdict
from collections.abc import Sequence
from itertools import zip_longest
from urllib.parse import parse_qsl, urlsplit

from goldgraft_contracts.money import MoneyEvent
from goldgraft_contracts.proof import MoneyContract, RuleHit, Verdict
from goldgraft_contracts.runner import RawCapture
from goldgraft_contracts.survey import TargetPlan


def identity(event):
    pp = event["pp"]
    return (
        pp.get("refund_id") if event["kind"] == "REFUND" else pp.get("capture_id", pp.get("txn_id"))
    )


def raw_ref(capture: RawCapture, index: int) -> str:
    return f"raw/{capture.scenario_id}.{capture.variant}.json#/exchanges/{index}"


def confirmation_results(capture: RawCapture):
    for index, exchange in enumerate(capture.exchanges):
        if (
            exchange.direction != "BROWSER_TO_SHOP"
            or urlsplit(exchange.url).path != "/api/confirmation-result"
        ):
            continue
        headers = {name.lower(): value for name, value in exchange.headers.items()}
        order = headers.get("x-goldgraft-order-ref")
        if order and exchange.status is not None:
            yield order, raw_ref(capture, index), exchange


def ledger_failed(capture: RawCapture | None) -> bool:
    if capture is None:
        return False
    for exchange in capture.exchanges:
        if exchange.direction != "PAYPAL_TO_SHOP" or not any(
            name.lower() == "x-goldgraft-ledger" and value
            for name, value in exchange.headers.items()
        ):
            continue
        if exchange.status is None or not 200 <= exchange.status < 300:
            return True
        ack = dict(parse_qsl(exchange.body_text or "")).get("ACK")
        if ack is not None and ack not in {"Success", "SuccessWithWarning"}:
            return True
    return False


def sufficient_evidence(events) -> bool:
    if not events:
        return False
    required = set()
    witnessed = set()
    for event in events:
        kind = event["kind"]
        if kind not in {"CAPTURE", "REFUND"}:
            if kind == "INTENT" and "money" not in event:
                return False
            continue
        transaction = identity(event)
        if transaction is None or "money" not in event or "status_norm" not in event:
            return False
        key = (event["order_ref"], kind, transaction)
        if event["source"] == "PAYPAL_LEDGER":
            witnessed.add(key)
        else:
            required.add(key)
    paid_orders = {
        event["order_ref"] for event in events if event["kind"] in {"SHOP_PAID", "SHOP_PENDING"}
    }
    return required <= witnessed and paid_orders <= {order for order, _, _ in witnessed}


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

        replies = defaultdict(list)
        for order, reference, exchange in confirmation_results(capture):
            replies[order].append((reference, exchange))
        for observations in replies.values():
            if len(observations) < 2:
                continue
            results = defaultdict(list)
            for reference, exchange in observations:
                if exchange.status >= 500:
                    hits["R05"].add(reference)
                if not 200 <= exchange.status < 300 or not isinstance(exchange.body_json, dict):
                    continue
                body = exchange.body_json
                transaction = body.get("capture_id") or body.get("transaction_id")
                if isinstance(transaction, str) and transaction:
                    results[transaction].append(reference)
            if len(results) > 1:
                hits["R10"].update(reference for refs in results.values() for reference in refs)

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
        pending = [e for e in captures if e.get("status_norm") == "PENDING"]
        if pending:
            if not completed and not any(e["kind"] == "SHOP_PENDING" for e in items):
                hit("R07")
            verified_completion = False
            completed_notification = False
            for event in items:
                kind = event["kind"]
                if kind == "NOTIFY":
                    completed_notification = event.get("status_norm") == "COMPLETED"
                elif kind == "NOTIFY_VERIFIED" and completed_notification:
                    verified_completion = True
                elif kind == "NOTIFY_REJECTED":
                    completed_notification = False
                elif (
                    kind == "SHOP_PAID"
                    and not verified_completion
                    and not any(observed["seq"] < event["seq"] for observed in completed)
                ):
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
        seen_notifications = set()
        duplicate_notification = False
        shop_state = None
        confirmation = None
        capture_by_confirmation = {}
        for event in items:
            kind = event["kind"]
            if kind == "NOTIFY":
                notification = (identity(event), event.get("status_norm"))
                duplicate_notification = notification[0] is not None and (
                    notification in seen_notifications
                )
                seen_notifications.add(notification)
            elif kind == "APPROVE":
                confirmation = event["pp"].get("order_id") or event["pp"].get("legacy_token")
                duplicate_notification = False
            elif event["source"] == "SHOP_DB":
                state = kind, event.get("money")
                if duplicate_notification and shop_state is not None and state != shop_state:
                    hit("R09")
                shop_state = state
                duplicate_notification = False
            elif kind == "CAPTURE" and event["source"] == "PAYPAL_CALL":
                transaction = identity(event)
                if confirmation is not None and transaction is not None:
                    previous = capture_by_confirmation.setdefault(confirmation, transaction)
                    if previous != transaction:
                        hit("R10")
        # Keep currencies, capture IDs and independent refund witnesses separate.
        captured = {(identity(e), e["money"]["currency"]): e["money"]["minor"] for e in completed}
        order_totals = defaultdict(int)
        for (_, currency), minor in captured.items():
            order_totals[currency] += minor
        for source in ("PAYPAL_CALL", "PAYPAL_LEDGER"):
            refunds = {
                identity(e): e
                for e in items
                if e["kind"] == "REFUND"
                and e["source"] == source
                and e.get("status_norm") == "REFUNDED"
            }
            per_capture = defaultdict(int)
            per_currency = defaultdict(int)
            for refund in refunds.values():
                refs = refund["pp"]
                parent = refs.get("capture_id") or refs.get("txn_id")
                amount = refund["money"]
                currency = amount["currency"]
                per_currency[currency] += amount["minor"]
                if parent is not None:
                    per_capture[parent, currency] += amount["minor"]
            if any(total > order_totals[currency] for currency, total in per_currency.items()):
                hit("R11")
            if any(total > captured.get(key, 0) for key, total in per_capture.items()):
                hit("R11")
        for index, refunded in db_writes[order]:
            if (
                type(refunded) is int
                and len(order_totals) == 1
                and refunded > next(iter(order_totals.values()))
            ):
                hits["R11"].add(raw_ref(capture, index))
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
            state = event["kind"], event.get("money")
            if shop_state.get(key) == state:
                continue
            shop_state[key] = state
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

    for stream, capture in ((old, old_capture), (new, new_capture)):
        if capture is not None and any(
            (event.scenario_id, event.run_id, event.graft_id, event.variant)
            != (capture.scenario_id, capture.run_id, capture.graft_id, capture.variant)
            for event in stream
        ):
            raise ValueError("Raw evidence does not match the canonical event stream")
    if not all(sufficient_evidence(events) for events in (baseline, twin, candidate)) or any(
        ledger_failed(capture) for capture in (old_capture, new_capture)
    ):
        return verdict("UNVERIFIED")
    if projection(baseline, noise=noise, old=False, deltas=deltas) != projection(
        twin, noise=noise, old=False, deltas=deltas
    ):
        return verdict("UNVERIFIED")

    rules = {rule.id for rule in contract.rules}
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
