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


def bundle_inputs():
    from goldgraft_contracts.lifecycle import ReviewBundle
    from goldgraft_contracts.plan5_common import content_digest

    from .conftest import ROOT

    raw = json.loads((ROOT / "contracts/examples/ReviewBundle.1.json").read_text())
    raw.update(case_id=BASELINE.case_id, run_id=BASELINE.run_id,
               work_package_digest=CANDIDATE.package_digest,
               artifact_digest=f"sha256:{CANDIDATE.image_digest}",
               effective_config_digest=CANDIDATE.config_digest)
    bundle = ReviewBundle.model_validate(raw)
    bundle.bundle_digest = content_digest(bundle.model_dump(mode="json", exclude={"bundle_digest"}))
    plan, observations = dict(PLAN), [OLD, NEW]
    for name in ("baseline_snapshot_refs", "candidate_snapshot_refs", "scenario_result_refs",
                 "domain_rule_result_refs", "security_result_refs"):
        subject = BASELINE if name == "baseline_snapshot_refs" else CANDIDATE
        for ref in getattr(bundle, name):
            plan[ref] = Requirement(subject)
            observations.append(Observation(ref, subject, EvidenceState.VERIFIED, "a" * 64, False))
    return bundle, plan, observations


def test_shared_review_bundle_accepts_complete_exact_authenticated_plan():
    from pieces.proof.lifecycle_evidence import review_bundle

    bundle, plan, observations = bundle_inputs()
    result = review_bundle(bundle, plan, observations, expected_bundle_digest=bundle.bundle_digest)
    assert result.disposition == Disposition.READY
    assert result.verified_count == 7


@pytest.mark.parametrize("field,value", [
    ("case_id", "wrong-case"), ("run_id", "wrong-run"),
    ("work_package_digest", "a" * 64), ("artifact_digest", f"sha256:{'a' * 64}"),
    ("effective_config_digest", "a" * 64), ("bundle_digest", "a" * 64),
    ("unsupported_paths", ["legacy-refund"]), ("missing_evidence_refs", ["private:missing"]),
    ("scenario_result_refs", []), ("security_result_refs", []),
])
def test_shared_review_bundle_drift_or_incompleteness_holds(field, value):
    from goldgraft_contracts.plan5_common import content_digest

    from pieces.proof.lifecycle_evidence import review_bundle

    bundle, plan, observations = bundle_inputs()
    setattr(bundle, field, value)
    if field != "bundle_digest":
        bundle.bundle_digest = content_digest(
            bundle.model_dump(mode="json", exclude={"bundle_digest"}))
    result = review_bundle(bundle, plan, observations,
                           expected_bundle_digest=bundle.bundle_digest)
    assert result.disposition == Disposition.HOLD


def test_rehashed_bundle_cannot_replace_current_reviewed_digest():
    from goldgraft_contracts.plan5_common import content_digest

    from pieces.proof.lifecycle_evidence import review_bundle

    bundle, plan, observations = bundle_inputs()
    expected = bundle.bundle_digest
    bundle.patch_digest = "b" * 64
    bundle.bundle_digest = content_digest(bundle.model_dump(mode="json", exclude={"bundle_digest"}))
    assert review_bundle(bundle, plan, observations,
                         expected_bundle_digest=expected).disposition == Disposition.HOLD


def test_bundle_result_ref_cannot_be_omitted_or_downgraded_in_required_plan():
    from pieces.proof.lifecycle_evidence import review_bundle

    bundle, plan, observations = bundle_inputs()
    ref = bundle.domain_rule_result_refs[0]
    for requirement in (None, Requirement(CANDIDATE, critical=False)):
        if requirement is None:
            plan.pop(ref)
        else:
            plan[ref] = requirement
        result = review_bundle(bundle, plan, observations,
                               expected_bundle_digest=bundle.bundle_digest)
        assert result.disposition == Disposition.HOLD


def test_shared_public_view_has_no_private_values_or_claimed_external_integrity():
    from datetime import UTC, datetime

    from goldgraft_contracts.registry import validate

    from pieces.proof.lifecycle_evidence import review_bundle
    from pieces.proof.review_projection import public_proof_view

    bundle, plan, observations = bundle_inputs()
    bundle.unsupported_paths = ["customer:alice@example.com:PAY-123"]
    review = review_bundle(bundle, plan, observations, expected_bundle_digest=bundle.bundle_digest)
    public = public_proof_view(review, checked_at=datetime(2026, 11, 12, tzinfo=UTC),
                               public_evidence_ref="public:stored-redacted-summary")
    wire = public.model_dump(mode="json")
    assert validate("PublicProofView/1", wire) == public
    assert wire["evidence_class"] == "component_offline"
    assert wire["integrity"] == "unknown"
    assert {metric.name: metric.value for metric in public.summary_metrics} == {
        "disposition": "HOLD", "verified_checks": "7", "gaps": "2",
    }
    assert {metric.evidence_ref for metric in public.summary_metrics} == {
        "public:stored-redacted-summary"}
    serialized = json.dumps(wire)
    for private in (BASELINE.case_id, BASELINE.run_id, BASELINE.origin,
                    CANDIDATE.image_digest, "alice@example.com", "PAY-123", "fixture:"):
        assert private not in serialized
    ready = public_proof_view(review_lifecycle(PLAN, [OLD, NEW]),
                              checked_at=datetime(2026, 11, 12, tzinfo=UTC),
                              public_evidence_ref="public:stored-redacted-summary")
    assert ready.integrity == "unknown"
