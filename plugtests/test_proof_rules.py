"""Replay rules require observed state changes and distinct payment identities."""

import json
from copy import deepcopy

from goldgraft_contracts.registry import validate

from pieces.proof.judge import judge, rule_hits

from .conftest import ROOT

CMEL = ROOT / "fixtures/proof/legacy-php-shop/cmel"


def test_duplicate_notification_flags_changed_shop_state():
    events = json.loads((CMEL / "NOTIFY_DUP.OLD.json").read_text())
    assert "R09" not in rule_hits(events, None)

    paid = next(event for event in events if event["kind"] == "SHOP_PAID")
    events.append({**paid, "kind": "SHOP_UNPAID", "seq": events[-1]["seq"] + 1})
    assert "R09" in rule_hits(events, None)


def test_confirmation_replay_flags_a_different_capture():
    events = json.loads((CMEL / "DOUBLE.NEW.json").read_text())
    assert "R10" not in rule_hits(events, None)

    capture = deepcopy(
        next(
            event
            for event in events
            if event["kind"] == "CAPTURE" and event["source"] == "PAYPAL_CALL"
        )
    )
    capture["seq"] = events[-1]["seq"] + 1
    capture["pp"]["capture_id"] = "second-capture"
    events.append(capture)
    assert "R10" in rule_hits(events, None)


def judge_inputs():
    fixture = CMEL.parent
    streams = [
        [
            validate("CMEL/1", item)
            for item in json.loads((CMEL / f"DOUBLE.{variant}.json").read_text())
        ]
        for variant in ("OLD", "OLD_TWIN", "NEW")
    ]
    contract = validate("Contract/1", json.loads((fixture / "contract.json").read_text()))
    plan = validate("TargetPlan/1", json.loads((fixture / "target_plan.json").read_text()))
    raw = validate("RawCapture/1", json.loads((fixture / "raw/DOUBLE.NEW.json").read_text()))
    return *streams, contract, plan, raw


def test_raw_confirmation_results_expose_a_replay_error_and_changed_receipt():
    old, twin, new, contract, plan, raw = judge_inputs()
    replies = [exchange for exchange in raw.exchanges if "/confirmation-result" in exchange.url]
    replies[-1].status = 503
    verdict = judge(old, twin, new, contract, plan, new_capture=raw)
    assert verdict.grade == "PROBLEM"
    assert {(hit.side, hit.rule) for hit in verdict.rule_hits} == {("NEW", "R05")}

    replies[-1].status = 200
    replies[-1].body_json["capture_id"] = "wrong-receipt"
    verdict = judge(old, twin, new, contract, plan, new_capture=raw)
    assert verdict.grade == "PROBLEM"
    assert {(hit.side, hit.rule) for hit in verdict.rule_hits} == {("NEW", "R10")}


def test_failed_ledger_read_cannot_be_hidden_by_another_witness():
    old, twin, new, contract, plan, raw = judge_inputs()
    last = raw.exchanges[-1]
    assert last.headers["X-GoldGraft-Ledger"] == "capture"
    last.status = 503
    assert judge(old, twin, new, contract, plan, new_capture=raw).grade == "UNVERIFIED"


def test_ledger_witness_must_match_capture_identity_and_repeat_old_money():
    old, twin, new, contract, plan, _ = judge_inputs()
    altered = deepcopy(new)
    for event in altered:
        if event.source == "PAYPAL_LEDGER":
            event.pp.capture_id = "unrelated-capture"
    assert judge(old, twin, altered, contract, plan).grade == "UNVERIFIED"
    next(event for event in twin if event.kind == "INTENT").money.minor += 1
    assert judge(old, twin, new, contract, plan).grade == "UNVERIFIED"


def test_pending_capture_can_resolve_to_paid():
    events = json.loads((CMEL / "DOUBLE.NEW.json").read_text())
    capture = deepcopy(next(event for event in events if event["kind"] == "CAPTURE"))
    capture["status_norm"] = "PENDING"
    events.insert(capture["seq"], capture)
    for index, event in enumerate(events):
        event["seq"] = index
    assert "R07" not in rule_hits(events, None)
