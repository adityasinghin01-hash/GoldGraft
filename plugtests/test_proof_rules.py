"""Replay rules require observed state changes and distinct payment identities."""

import json
from copy import deepcopy

from pieces.proof.judge import rule_hits

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
