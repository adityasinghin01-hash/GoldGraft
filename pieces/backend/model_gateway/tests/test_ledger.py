"""Actual transactional accounting and restart/concurrency behavior; no network."""

from concurrent.futures import ProcessPoolExecutor

import pytest


def reserve_worker(path, identity):
    from pieces.backend.model_gateway.ledger import Ledger

    try:
        Ledger(path).reserve(identity, identity, 30000)
        return True
    except ValueError:
        return False


def test_concurrent_batches_cannot_each_spend_the_same_project_allowance(tmp_path):
    from pieces.backend.model_gateway.ledger import Ledger

    path = tmp_path / "money.sqlite"
    Ledger(path)
    with ProcessPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reserve_worker, [path, path], ["one", "two"]))
    assert sum(results) == 1
    assert Ledger(path).snapshot()["reserved_micro_usd"] == 30000


def test_observed_usage_releases_only_unused_known_reservation(tmp_path):
    from pieces.backend.model_gateway.ledger import Ledger

    ledger = Ledger(tmp_path / "money.sqlite")
    ledger.reserve("batch", "same", 12000)
    ledger.begin("batch", "turn", "request", 3000)
    ledger.submit("batch", "turn")
    ledger.observe("batch", "turn", 250, {"result": "checked"}, {"input_tokens": 10})
    ledger.close("batch")
    state = Ledger(ledger.path).snapshot()
    assert state["spent_micro_usd"] == 250
    assert state["reserved_micro_usd"] == 0
    assert ledger.turn("batch", "turn")["result"] == {"result": "checked"}


@pytest.mark.parametrize("state", ["intended", "submitted", "unknown"])
def test_uncertain_turn_survives_restart_and_cannot_be_renamed_or_closed(tmp_path, state):
    from pieces.backend.model_gateway.ledger import Ledger

    ledger = Ledger(tmp_path / "money.sqlite")
    ledger.reserve("batch", "same", 12000)
    ledger.begin("batch", "old-id", "request", 3000)
    if state != "intended":
        ledger.submit("batch", "old-id")
    if state == "unknown":
        ledger.mark_unknown("batch", "old-id")
    ledger = Ledger(ledger.path)
    assert ledger.snapshot()["reserved_micro_usd"] == 12000
    with pytest.raises(ValueError, match="UNKNOWN"):
        ledger.reserve("new-batch", "other", 12000)
    with pytest.raises(ValueError, match="UNKNOWN"):
        ledger.begin("batch", "replacement", "other", 3000)
    with pytest.raises(ValueError, match="UNKNOWN"):
        ledger.close("batch")


def test_stop_orders_before_submission_and_late_usage_is_still_counted(tmp_path):
    from pieces.backend.model_gateway.ledger import Ledger

    ledger = Ledger(tmp_path / "money.sqlite")
    ledger.reserve("batch", "same", 12000)
    ledger.begin("batch", "turn", "request", 3000)
    ledger.stop("batch")
    with pytest.raises(ValueError, match="STOPPED"):
        ledger.submit("batch", "turn")
    # Independent already-submitted batch: late response still costs money.
    ledger.abort_intended("batch", "turn")
    ledger.close("batch")
    ledger.reserve("other", "other", 12000)
    ledger.begin("other", "turn", "request", 3000)
    ledger.submit("other", "turn")
    ledger.stop("other")
    ledger.observe("other", "turn", 300, {"blocked": "stopped"}, {})
    assert ledger.snapshot()["spent_micro_usd"] == 300


def test_changed_identity_and_cap_reset_are_rejected(tmp_path):
    from pieces.backend.model_gateway.ledger import Ledger

    ledger = Ledger(tmp_path / "money.sqlite")
    ledger.reserve("batch", "same", 50000)
    ledger.reserve("batch", "same", 50000)
    with pytest.raises(ValueError, match="CONFLICT"):
        ledger.reserve("batch", "changed", 50000)
    with pytest.raises(ValueError, match="BUDGET"):
        ledger.reserve("extra", "extra", 1)
    for value in [True, 1.5, -1, 20000001]:
        with pytest.raises(ValueError):
            ledger.reserve("invalid", "invalid", value)


def test_provider_usage_overrun_is_recorded_and_freezes_further_dispatch(tmp_path):
    from pieces.backend.model_gateway.ledger import Ledger

    ledger = Ledger(tmp_path / "money.sqlite")
    ledger.reserve("batch", "same", 1000)
    ledger.begin("batch", "turn", "request", 1000)
    ledger.submit("batch", "turn")
    with pytest.raises(ValueError, match="USAGE_OVER_BOUND"):
        ledger.observe("batch", "turn", 1001, {"failed": "overrun"}, {})
    assert Ledger(ledger.path).snapshot()["spent_micro_usd"] == 1001
    with pytest.raises(ValueError, match="FROZEN"):
        ledger.reserve("next", "next", 1000)


def test_atomic_turn_limit_is_independent_of_remaining_money(tmp_path):
    from pieces.backend.model_gateway.ledger import Ledger

    ledger = Ledger(tmp_path / "money.sqlite")
    ledger.reserve("batch", "same", 20000)
    for name in ["one", "two"]:
        ledger.begin("batch", name, name, 3000, max_turns=2)
        ledger.submit("batch", name)
        ledger.observe("batch", name, 1, {}, {})
    with pytest.raises(ValueError, match="TURN_LIMIT"):
        ledger.begin("batch", "three", "three", 3000, max_turns=2)


def test_process_death_after_submission_preserves_unknown_accounting(tmp_path):
    import subprocess
    import sys

    from pieces.backend.model_gateway.ledger import Ledger

    path = tmp_path / "money.sqlite"
    script = (
        "import os,sys; from pieces.backend.model_gateway.ledger import Ledger; "
        "l=Ledger(sys.argv[1]); l.reserve('batch','same',12000); "
        "l.begin('batch','turn','request',3000); l.submit('batch','turn'); os._exit(73)"
    )
    result = subprocess.run([sys.executable, "-B", "-c", script, str(path)])
    assert result.returncode == 73
    ledger = Ledger(path)
    assert ledger.snapshot()["unknown_micro_usd"] == 3000
    assert ledger.snapshot()["reserved_micro_usd"] == 12000
    with pytest.raises(ValueError, match="UNKNOWN"):
        ledger.reserve("replacement", "replacement", 12000)


def test_cap_change_is_raise_only_bounded_recorded_and_never_touches_money(tmp_path):
    from pieces.backend.model_gateway.ledger import Ledger

    path = tmp_path / "money.sqlite"
    ledger = Ledger(path)
    ledger.reserve("old", "old", 12000)
    ledger.begin("old", "turn", "turn", 3000)
    ledger.submit("old", "turn")
    ledger.mark_unknown("old", "turn")
    before = {
        k: v for k, v in ledger.snapshot().items() if "cap" not in k and k != "available_micro_usd"
    }
    authority = "a" * 64
    for bad in [50000, 40000, 500001]:
        with pytest.raises(ValueError, match="INVALID"):
            ledger.raise_active_cap(bad, authority, limit=500000)
    with pytest.raises(ValueError, match="INVALID cap authority"):
        ledger.raise_active_cap(500000, "not-a-digest", limit=500000)
    record = ledger.raise_active_cap(500000, authority, limit=500000)
    assert (record["old_cap"], record["new_cap"]) == (50000, 500000)
    # Idempotent for the same authority after restart; a different amount conflicts.
    assert Ledger(path).raise_active_cap(500000, authority, limit=500000) == record
    with pytest.raises(ValueError, match="CONFLICT"):
        Ledger(path).raise_active_cap(600000, authority, limit=600000)
    after = Ledger(path).snapshot()
    assert {
        k: v for k, v in after.items() if "cap" not in k and k != "available_micro_usd"
    } == before
    assert after["active_cap_micro_usd"] == 500000
    assert Ledger(path).turn("old", "turn")["state"] == "unknown"
    with pytest.raises(ValueError, match="UNKNOWN"):
        Ledger(path).reserve("new", "new", 12000)
    Ledger(path).freeze()
    with pytest.raises(ValueError, match="FROZEN"):
        Ledger(path).raise_active_cap(600000, "b" * 64, limit=600000)
