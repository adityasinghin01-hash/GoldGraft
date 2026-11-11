"""One explicit independent-test review never reconciles the earlier unknown."""

import hashlib
import hmac
import json

import pytest
from goldgraft_contracts.plan5_common import canonical_bytes

from pieces.backend.model_gateway.ledger import Ledger
from pieces.backend.model_gateway.profile import Profile


def setup(tmp_path, *, old_ceiling=12672):
    path = tmp_path / "money.sqlite"
    ledger = Ledger(path)
    ledger.reserve("original", "old-batch-fingerprint", old_ceiling)
    ledger.begin("original", "old-turn", "old-turn-fingerprint", 3168)
    ledger.submit("original", "old-turn")
    ledger.mark_unknown("original", "old-turn")
    key = tmp_path / "signing"
    key.write_bytes(b"s" * 32)
    key.chmod(0o600)
    body = {
        "kind": "one_independent_synthetic_test_retaining_unknown",
        "authorization_ref": "a" * 64,
        "original_batch": "original",
        "original_batch_fingerprint": "old-batch-fingerprint",
        "original_turn": "old-turn",
        "original_fingerprint": "old-turn-fingerprint",
        "original_turn_reservation": 3168,
        "original_batch_ceiling": old_ceiling,
        "new_batch": "new-browser",
        "case_id": "inventory-browser-ipn",
        "case_digest": "b" * 64,
        "profile": Profile().ref,
        "max_batch_reservation": 12672,
        "active_cap": 50000,
    }
    review = tmp_path / "review.json"
    sign(review, body)
    return path, key, review, body


def sign(path, body):
    signature = hmac.new(b"s" * 32, canonical_bytes(body), hashlib.sha256).hexdigest()
    path.write_text(json.dumps({"body": body, "signature": signature}))
    path.chmod(0o600)


def open_review(path, key, review, **changes):
    from pieces.backend.model_gateway.independent_review import IndependentTestLedger

    args = dict(
        review_path=review,
        signing_path=key,
        profile=Profile(),
        case_id="inventory-browser-ipn",
        case_digest="b" * 64,
        batch="new-browser",
    )
    return IndependentTestLedger(path, **dict(args, **changes))


def test_review_allows_only_one_batch_and_retains_original_across_restart(tmp_path):
    path, key, review, _ = setup(tmp_path)
    before = Ledger(path).turn("original", "old-turn")
    ledger = open_review(path, key, review)
    ledger.reserve("new-browser", "new-request", 12672)
    ledger.begin("new-browser", "new-turn", "new-turn-fingerprint", 3168)
    ledger.submit("new-browser", "new-turn")
    ledger.observe("new-browser", "new-turn", 20, {}, {})
    ledger = open_review(path, key, review)
    ledger.begin("new-browser", "second-turn", "second-fingerprint", 3168)
    ledger.abort_intended("new-browser", "second-turn")
    ledger.close("new-browser")
    assert ledger.turn("original", "old-turn") == before
    assert ledger.snapshot()["reserved_micro_usd"] == 12672
    assert ledger.snapshot()["spent_micro_usd"] == 20
    with pytest.raises(ValueError, match="UNKNOWN"):
        ledger.reserve("not-approved", "other", 1)
    with pytest.raises(ValueError, match="UNKNOWN"):
        Ledger(path).reserve("default-still-closed", "other", 1)


@pytest.mark.parametrize("change", ["signature", "batch", "case_digest", "case_id", "profile"])
def test_review_rejects_tampered_or_different_scope_before_admission(tmp_path, change):
    path, key, review, body = setup(tmp_path)
    if change == "signature":
        data = json.loads(review.read_text())
        data["signature"] = "0" * 64
        review.write_text(json.dumps(data))
        args = {}
    elif change == "profile":
        body["profile"] = "unqualified"
        sign(review, body)
        args = {}
    else:
        args = {change: "other"}
    with pytest.raises(ValueError, match="REVIEW"):
        open_review(path, key, review, **args)
    assert Ledger(path).snapshot()["reserved_micro_usd"] == 12672


def test_new_unknown_blocks_even_when_original_review_is_present(tmp_path):
    path, key, review, _ = setup(tmp_path)
    ledger = open_review(path, key, review)
    ledger.reserve("new-browser", "new-request", 12672)
    ledger.begin("new-browser", "new-turn", "new-turn-fingerprint", 3168)
    ledger.submit("new-browser", "new-turn")
    ledger.mark_unknown("new-browser", "new-turn")
    with pytest.raises(ValueError, match="UNKNOWN"):
        open_review(path, key, review).begin("new-browser", "replacement", "other", 3168)
    assert ledger.snapshot()["unknown_micro_usd"] == 6336
    assert ledger.snapshot()["reserved_micro_usd"] == 25344


def test_review_cannot_change_original_fingerprint_or_reservation(tmp_path):
    path, key, review, body = setup(tmp_path)
    body["original_fingerprint"] = "incorrect"
    sign(review, body)
    ledger = open_review(path, key, review)
    with pytest.raises(ValueError, match="UNKNOWN"):
        ledger.reserve("new-browser", "new-request", 12672)


def test_review_preserves_active_cap_and_requested_batch_bound(tmp_path):
    path, key, review, _ = setup(tmp_path, old_ceiling=40000)
    ledger = open_review(path, key, review)
    with pytest.raises(ValueError, match="BUDGET"):
        ledger.reserve("new-browser", "new-request", 12672)
    with pytest.raises(ValueError, match="REVIEW"):
        ledger.reserve("new-browser", "new-request", 12673)
    assert ledger.snapshot()["active_cap_micro_usd"] == 50000


def test_review_binds_actual_raised_cap_and_rejects_above_outer_ceiling(tmp_path):
    path, key, review, body = setup(tmp_path)
    Ledger(path).raise_active_cap(500000, "c" * 64, limit=500000)
    # The old $0.05 review no longer matches the ledger's actual cap: still blocked.
    with pytest.raises(ValueError, match="UNKNOWN"):
        open_review(path, key, review).reserve("new-browser", "new-request", 12672)
    sign(review, dict(body, active_cap=500000))
    ledger = open_review(path, key, review)
    ledger.reserve("new-browser", "new-request", 12672)
    assert ledger.turn("original", "old-turn")["state"] == "unknown"
    assert ledger.snapshot()["reserved_micro_usd"] == 12672 * 2
    sign(review, dict(body, active_cap=10000001))
    with pytest.raises(ValueError, match="REVIEW_DENIED"):
        open_review(path, key, review)
