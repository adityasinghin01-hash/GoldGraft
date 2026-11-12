"""Replay rules require observed state changes and distinct payment identities."""

import json
from copy import deepcopy

import pytest
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


def test_callback_deadline_and_restart_evidence():
    from pieces.proof.lifecycle import CallbackWatch, LifecycleEvidence, RestartWatch

    old, twin, new, contract, plan, _ = judge_inputs()
    order = new[0].order_ref
    first_capture = next(event for event in new if event.kind == "CAPTURE")
    last_approval = max(event.t_ms for event in new if event.kind == "APPROVE")
    assert last_approval < first_capture.t_ms
    restart = RestartWatch(order, first_capture.t_ms - 1, "runner/restart")
    watch = CallbackWatch(order, last_approval, first_capture.t_ms, (), "runner/callback")
    evidence = LifecycleEvidence(new[0].run_id, callbacks=(watch,), restarts=(restart,))
    result = judge(old, twin, new, contract, plan, new_lifecycle=evidence)
    assert {(hit.rule, hit.side) for hit in result.rule_hits} == {("R13", "NEW")}

    short = CallbackWatch(order, last_approval, last_approval - 1, (), "runner/callback")
    evidence = LifecycleEvidence(new[0].run_id, callbacks=(short,))
    assert judge(old, twin, new, contract, plan, new_lifecycle=evidence).grade == "UNVERIFIED"


def test_restart_failure_and_legacy_refund_route():
    from pieces.proof.lifecycle import LifecycleEvidence, RefundRoute, RestartWatch, lifecycle_hits

    _, _, new, _, _, _ = judge_inputs()
    order = new[0].order_ref
    after_approval = max(event.t_ms for event in new if event.kind == "APPROVE") + 1
    restart = RestartWatch(order, after_approval, "runner/restart")
    interrupted = [event for event in new if event.kind in {"APPROVE", "INTENT"}]
    hits, incomplete = lifecycle_hits(
        interrupted, LifecycleEvidence(new[0].run_id, restarts=(restart,))
    )
    assert hits == {"R14": {"runner/restart"}}
    assert not incomplete

    raw = json.loads((CMEL / "REFUND.NEW.json").read_text())
    events = [validate("CMEL/1", item) for item in raw]
    refund = next(event for event in events if event.kind == "REFUND")
    for mapping in (None, "runner/verified-legacy-equivalence"):
        route = RefundRoute(
            refund.order_ref, refund.pp.refund_id, "LEGACY", "REST", mapping, "runner/refund"
        )
        hits, incomplete = lifecycle_hits(
            events, LifecycleEvidence(refund.run_id, refunds=(route,))
        )
        assert bool(hits.get("R15")) == (mapping is None)
        assert not incomplete


def test_trusted_catalogue_quote_rejects_browser_amount():
    from goldgraft_contracts.money import Money

    from pieces.proof.lifecycle import CatalogueQuote, LifecycleEvidence

    old, twin, new, contract, plan, raw = judge_inputs()
    order = new[0].order_ref
    quote = CatalogueQuote(order, Money(minor=2500, currency="USD"), "catalogue/tee")
    evidence = LifecycleEvidence(new[0].run_id, quotes=(quote,))
    assert judge(old, twin, new, contract, plan, new_lifecycle=evidence).grade == "PASS"

    intent = next(event for event in new if event.kind == "INTENT")
    intent.money = Money(minor=1, currency="EUR")
    result = judge(old, twin, new, contract, plan, new_lifecycle=evidence)
    assert {"R12", "R17"} <= {hit.rule for hit in result.rule_hits}
    assert result.grade == "PROBLEM"

    write = next(exchange for exchange in raw.exchanges if exchange.db_change is not None)
    write.db_change.after["total_minor"] = 2500.5
    result = judge(old, twin, new, contract, plan, new_capture=raw)
    assert "R16" in {hit.rule for hit in result.rule_hits}


def test_not_applicable_is_explicit_and_preserves_unverified_precedence():
    old, twin, new, contract, plan, raw = judge_inputs()
    reason = "Refunds are unsupported by this shop"
    assert judge(old, twin, new, contract, plan, not_applicable_reason=reason).grade == "N/A"
    raw.exchanges[-1].status = 503
    assert (
        judge(old, twin, new, contract, plan, new_capture=raw, not_applicable_reason=reason).grade
        == "UNVERIFIED"
    )


@pytest.mark.parametrize("field,value", [("graft_id", "foreign"), ("run_id", "mixed"),
                                         ("variant", "OLD"), ("seq", 99)])
def test_judge_rejects_mixed_or_misordered_subject_stream(field, value):
    old, twin, new, contract, plan, _ = judge_inputs()
    raw = new[-1].model_dump(mode="json")
    raw[field] = value
    new[-1] = validate("CMEL/1", raw)
    with pytest.raises(ValueError, match="subject|sequence"):
        judge(old, twin, new, contract, plan)


def test_judge_rejects_candidate_from_another_graft():
    old, twin, new, contract, plan, _ = judge_inputs()
    for event in new:
        event.graft_id = "foreign"
    with pytest.raises(ValueError, match="subject"):
        judge(old, twin, new, contract, plan)


def test_not_applicable_cannot_hide_a_normative_breach():
    old, twin, new, contract, plan, _ = judge_inputs()
    # All three streams share the defect: parity is not normative correctness.
    for stream in (old, twin, new):
        for event in stream:
            if event.kind == "CAPTURE":
                event.money.minor = 1
    result = judge(old, twin, new, contract, plan, not_applicable_reason="Skipped checkout")
    assert result.grade == "PROBLEM"
    assert {(hit.side, hit.rule) for hit in result.rule_hits} >= {("OLD", "R02"), ("NEW", "R02")}


def test_json_webhook_retained_at_ipn_path_uses_resource_content():
    from pieces.proof.cmel import to_cmel

    raw = json.loads((CMEL.parent / "raw/NOTIFY_DUP.NEW.json").read_text())
    for exchange in raw["exchanges"]:
        if exchange["direction"] == "PAYPAL_NOTIFY_TO_SHOP":
            exchange["url"] = "https://shop.example/ipn.php"
    events = to_cmel(validate("RawCapture/1", raw))
    notifications = [event for event in events if event.kind == "NOTIFY"]
    assert len(notifications) == 2
    assert all(event.status_norm == "COMPLETED" for event in notifications)
    assert all(event.pp.capture_id and event.pp.order_id for event in notifications)
    assert all(event.money.minor == 2500 and event.money.currency == "USD"
               for event in notifications)


def test_late_pending_notification_cannot_regress_a_completed_order():
    events = json.loads((CMEL / "HAPPY.NEW.json").read_text())
    assert not rule_hits(events, None)
    paid = deepcopy(next(event for event in events if event["kind"] == "SHOP_PAID"))
    capture = next(event for event in events if event["kind"] == "CAPTURE")
    notify = {**deepcopy(capture), "kind": "NOTIFY", "source": "NOTIFICATION",
              "status_norm": "PENDING"}
    for event in (notify, {**paid, "kind": "SHOP_PENDING"}):
        event["seq"] = len(events)
        events.append(event)
    assert "R04" in rule_hits(events, None)


@pytest.mark.parametrize("origin,route,equivalence", [
    ("UNKNOWN", "REST", None), ("LEGACY", "UNKNOWN", None), ("LEGACY", "REST", " "),
])
def test_unknown_or_unsubstantiated_refund_origin_does_not_pass(origin, route, equivalence):
    from pieces.proof.lifecycle import LifecycleEvidence, RefundRoute, lifecycle_hits

    events = [validate("CMEL/1", event)
              for event in json.loads((CMEL / "REFUND.NEW.json").read_text())]
    refund = next(event for event in events if event.kind == "REFUND")
    evidence = LifecycleEvidence(refund.run_id, refunds=(RefundRoute(
        refund.order_ref, refund.pp.refund_id, origin, route, equivalence, "runner/refund"),))
    hits, incomplete = lifecycle_hits(events, evidence)
    assert "R15" in hits or "R15" in incomplete
