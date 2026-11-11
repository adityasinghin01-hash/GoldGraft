"""Herald consumer qualification; actual own code, synthetic committed projections."""

from datetime import timedelta

import pytest
from goldgraft_contracts.plan5_common import content_digest

from pieces.agents.herald import inspect_text, notification_preview, render_text

from .test_herald import facts_for, profile, source_ready


def invalid_facts(facts, change):
    if change == "contradictory_reason":
        return facts.model_copy(update={"status": "unknown", "reason_code": "SOURCE_MISSING"})
    if change == "missing_review_proof":
        return facts.model_copy(update={"status": "review_ready", "proof_complete": False})
    if change == "wrong_review_subject":
        return facts.model_copy(
            update={"status": "review_ready", "proof_complete": True, "proof_subject": "f" * 64}
        )
    if change == "conflicting_assets":
        return facts.model_copy(
            update={"retained": ["application_state"], "removed": ["application_state"]}
        )
    if change == "missing_input":
        return facts.model_copy(update={"input_refs": []})
    if change == "missing_evidence":
        return facts.model_copy(update={"evidence_refs": []})
    digest, row = next(iter(facts.ledger_entries.items()))
    if change == "forged_journal_hash":
        return facts.model_copy(update={"ledger_entries": {"f" * 64: row}})
    if change == "cross_generation_journal":
        row = row.model_copy(update={"generation": facts.generation + 1})
        return facts.model_copy(update={"ledger_entries": {content_digest(row): row}})
    if change in {"float_count", "bool_count", "negative_count"}:
        count = {"float_count": 5.0, "bool_count": True, "negative_count": -1}[change]
        row = row.model_copy(update={"payload": {"source_indicators": count}})
        return facts.model_copy(update={"ledger_entries": {content_digest(row): row}})
    raise AssertionError(change)


@pytest.mark.parametrize(
    "change",
    [
        "contradictory_reason",
        "missing_review_proof",
        "wrong_review_subject",
        "conflicting_assets",
        "missing_input",
        "missing_evidence",
        "forged_journal_hash",
        "cross_generation_journal",
        "float_count",
        "bool_count",
        "negative_count",
    ],
)
def test_direct_preview_cannot_bypass_renderer_fact_validation(tmp_path, change):
    ports = profile(tmp_path)
    source_ready(ports)
    task, facts = facts_for(ports)
    invalid = invalid_facts(facts, change)
    with pytest.raises(ValueError):
        render_text(task, invalid)
    with pytest.raises(ValueError):
        notification_preview(invalid, opted_in=True)
    assert notification_preview(invalid) is None
    assert ports.model.total_dispatches() == 3


def test_inspection_rejects_changed_observation_timestamp(tmp_path):
    ports = profile(tmp_path)
    source_ready(ports)
    task, facts = facts_for(ports)
    payload = render_text(task, facts)
    payload["created_at"] = (facts.observed_at + timedelta(seconds=1)).isoformat()
    with pytest.raises(ValueError):
        inspect_text(payload, facts)


@pytest.mark.parametrize("change", ["cross_generation_journal", "missing_evidence"])
def test_inspection_rejects_invalid_facts_even_when_displayed_text_is_unchanged(tmp_path, change):
    ports = profile(tmp_path)
    source_ready(ports)
    task, facts = facts_for(ports)
    payload = render_text(task, facts)
    invalid = invalid_facts(facts, change)
    if change == "cross_generation_journal":
        payload["numbers_used"][0]["entry_hash"] = next(iter(invalid.ledger_entries))
    with pytest.raises(ValueError):
        inspect_text(payload, invalid)


# Independent applicability expectations from the approved closed claim profile.
STATUSES = (
    "queued",
    "working",
    "inventory_ready",
    "waiting_input",
    "held",
    "unknown",
    "cancellation_pending",
    "cancelled",
    "review_ready",
    "delivery_pending",
    "synthetic_complete",
)
REASON_APPLICABILITY = {
    "NONE": set(STATUSES),
    "SOURCE_MISSING": {"held", "waiting_input"},
    "PROOF_MISSING": {"held", "waiting_input", "delivery_pending"},
    "AUTHORITY_REVOKED": {"held"},
    "OUTCOME_UNKNOWN": {"held", "unknown"},
    "BUDGET_EXHAUSTED": {"held", "waiting_input"},
    "TERMINATION_PENDING": {"held", "cancellation_pending"},
    "EXIT_PENDING": {"held", "delivery_pending"},
}
KINDS = ("GRAFT_CARD", "PR_BODY", "HANDOFF", "VERDICT_EXPLAIN")


def exercise_status_matrix(task, facts):
    """Measure pure consumers on synthetic facts; this is not a model/runtime score."""
    records = []
    for projection in ("private_status", "public_safe"):
        scoped = task.model_copy(
            update={"task": task.task.model_copy(update={"output_slot": "text." + projection})}
        )
        for kind in KINDS:
            for status in STATUSES:
                for reason, permitted in REASON_APPLICABILITY.items():
                    case = facts.model_copy(
                        update={
                            "projection": projection,
                            "kind": kind,
                            "status": status,
                            "reason_code": reason,
                            "proof_complete": status == "review_ready",
                            "proof_subject": facts.subject_digest
                            if status == "review_ready"
                            else None,
                        }
                    )
                    allowed = status in permitted
                    if not allowed:
                        with pytest.raises(ValueError):
                            render_text(scoped, case)
                        with pytest.raises(ValueError):
                            notification_preview(case, opted_in=True)
                    else:
                        for detailed in (False, True):
                            payload = render_text(scoped, case, detailed=detailed)
                            view = inspect_text(payload, case)
                            assert view["text"] == payload["text"]
                            assert view["notifications_sent"] == 0
                            assert view["authoritative_status_changed"] is False
                            assert (
                                "runtime, payment and live-site outcomes remain unverified"
                                in view["text"]
                            )
                            assert (len(payload["numbers_used"]) == 1) == (
                                status == "inventory_ready"
                            )
                            if status == "inventory_ready":
                                assert "5 source indicators" in view["text"]
                                assert payload["numbers_used"][0] == {
                                    "entry_hash": next(iter(case.ledger_entries)),
                                    "json_pointer": "/payload/source_indicators",
                                    "value": 5,
                                }
                            if status == "unknown":
                                assert "outcome is unknown" in view["text"]
                            if status == "cancellation_pending":
                                assert "termination is not yet confirmed" in view["text"]
                            if status == "review_ready":
                                assert "separate approval is still required" in view["text"]
                            if status == "synthetic_complete":
                                assert "no live merchant completion is established" in view["text"]
                            if projection == "public_safe":
                                assert not {"numbers_used", "evidence_refs"} & view.keys()
                                assert all(
                                    word not in str(view)
                                    for word in ["case-demo", "run-demo", "fake:", "checkout.php"]
                                )
                        preview = notification_preview(case, opted_in=True)
                        assert preview["delivery"] == "NOT SENT" and preview["authority"] == "NONE"
                        assert preview == notification_preview(
                            case.model_copy(update={"kind": "HANDOFF"}), opted_in=True
                        )
                    records.append(
                        {
                            "projection": projection,
                            "kind": kind,
                            "status": status,
                            "reason": reason,
                            "expected": "render" if allowed else "deny",
                            "passed": True,
                        }
                    )
    assert len(records) == 704 and sum(r["expected"] == "render" for r in records) == 200
    return records


def test_all_status_reason_format_projection_consumer_combinations(tmp_path):
    ports = profile(tmp_path)
    source_ready(ports)
    task, facts = facts_for(ports)
    before = ports.control.snapshot("fake:runtime-run").model_dump(mode="json")
    exercise_status_matrix(task, facts)
    assert ports.control.snapshot("fake:runtime-run").model_dump(mode="json") == before
    assert ports.model.total_dispatches() == 3


@pytest.mark.parametrize("count", [0, 2**53 + 1])
def test_exact_integer_count_in_all_consumer_paths(tmp_path, count):
    ports = profile(tmp_path)
    source_ready(ports)
    task, facts = facts_for(ports)
    row = next(iter(facts.ledger_entries.values())).model_copy(
        update={"payload": {"source_indicators": count}}
    )
    # Synthetic journal boundary probe, not a source-derived runtime measurement.
    facts = facts.model_copy(update={"ledger_entries": {content_digest(row): row}})
    payload = render_text(task, facts)
    assert type(payload["numbers_used"][0]["value"]) is int
    assert payload["numbers_used"][0]["value"] == count
    assert str(count) + " source indicators" in inspect_text(payload, facts)["text"]
    assert str(count) + " source indicators" in notification_preview(facts, opted_in=True)["text"]
