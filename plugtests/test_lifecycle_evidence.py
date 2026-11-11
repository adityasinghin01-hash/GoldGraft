"""Regression tests for exact subject binding and private/public proof views."""

import json
from dataclasses import asdict, replace

import pytest

from pieces.proof.lifecycle_evidence import (
    Disposition,
    EvidenceState,
    GapReason,
    Observation,
    ProofSubject,
    Requirement,
    review_lifecycle,
)
from pieces.proof.review_projection import public_review

BASELINE = ProofSubject(
    case_id="private-case",
    run_id="private-run",
    generation=2,
    fence="private-fence",
    scope_digest="1" * 64,
    package_digest="2" * 64,
    image_digest="3" * 64,
    config_digest="4" * 64,
    runtime_identity="private-runtime",
    origin="https://private.example",
)
CANDIDATE = replace(BASELINE, image_digest="5" * 64)
PLAN = {"baseline": Requirement(BASELINE), "candidate": Requirement(CANDIDATE)}
OLD = Observation("baseline", BASELINE, EvidenceState.VERIFIED, "6" * 64, False)
NEW = Observation("candidate", CANDIDATE, EvidenceState.VERIFIED, "7" * 64, False)


def test_current_verified_baseline_and_candidate_are_ready():
    review = review_lifecycle(PLAN, [NEW, OLD])
    assert (review.disposition, review.verified_count, review.gaps) == (Disposition.READY, 2, ())


@pytest.mark.parametrize(
    "changes",
    [
        {"case_id": "different-case"},
        {"run_id": "different-run"},
        {"generation": 1},
        {"generation": True},
        {"fence": "old-fence"},
        {"scope_digest": "8" * 64},
        {"package_digest": "8" * 64},
        {"image_digest": BASELINE.image_digest},
        {"image_digest": ""},
        {"config_digest": "8" * 64},
        {"runtime_identity": "wrong-runtime"},
        {"origin": "https://another.example"},
    ],
)
def test_subject_drift_is_a_hold(changes):
    candidate = replace(NEW, subject=replace(CANDIDATE, **changes))
    review = review_lifecycle(PLAN, [OLD, candidate])
    assert review.disposition == Disposition.HOLD
    assert review.gaps[0].reason == GapReason.SUBJECT


@pytest.mark.parametrize(
    ("observations", "reason"),
    [
        ([], GapReason.MISSING),
        ([NEW, NEW], GapReason.DUPLICATE),
        ([replace(NEW, evidence_digest="")], GapReason.MISSING),
        ([replace(NEW, fixture=True)], GapReason.FIXTURE_ONLY),
        ([replace(NEW, state=EvidenceState.UNKNOWN)], GapReason.UNKNOWN),
        ([replace(NEW, state=EvidenceState.FAILED)], GapReason.FAILED),
        ([replace(NEW, state=EvidenceState.UNSUPPORTED)], GapReason.UNSUPPORTED),
    ],
)
def test_missing_or_unqualified_critical_evidence_holds(observations, reason):
    review = review_lifecycle(PLAN, [OLD, *observations])
    assert review.disposition == Disposition.HOLD
    assert review.verified_count == 1
    assert review.gaps[0].reason == reason


def test_public_projection_excludes_private_check_names_and_evidence():
    check = "customer alice@example.com capture PAY-123 transaction TX-456"
    plan = {**PLAN, check: Requirement(CANDIDATE, critical=False)}
    review = review_lifecycle(plan, [NEW, OLD])
    assert review.gaps[0].check == check
    assert json.loads(json.dumps(asdict(public_review(review)))) == {
        "disposition": "PARTIAL",
        "verified_count": 2,
        "gap_count": 1,
        "gap_reasons": ["MISSING"],
    }


@pytest.mark.parametrize(
    "plan",
    [
        {},
        {"candidate": Requirement(CANDIDATE)},
        {"baseline": Requirement(BASELINE)},
        {**PLAN, "candidate": Requirement(CANDIDATE, critical=False)},
    ],
)
def test_incomplete_policy_cannot_be_ready(plan):
    with pytest.raises(ValueError, match="critical baseline and candidate"):
        review_lifecycle(plan, [NEW, OLD])
