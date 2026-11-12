"""Local proof checks for evidence already authenticated by the caller."""

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from goldgraft_contracts.lifecycle import ReviewBundle
from goldgraft_contracts.plan5_common import content_digest

_SHA256 = frozenset("0123456789abcdef")


def _digest(value: str) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= _SHA256


@dataclass(frozen=True)
class ProofSubject:
    case_id: str
    run_id: str
    generation: int
    fence: str
    scope_digest: str
    package_digest: str
    image_digest: str
    config_digest: str
    runtime_identity: str
    origin: str

    def complete(self) -> bool:
        return (
            type(self.generation) is int
            and self.generation > 0
            and all(
                isinstance(value, str) and value.strip()
                for value in (
                    self.case_id,
                    self.run_id,
                    self.fence,
                    self.runtime_identity,
                    self.origin,
                )
            )
            and all(
                _digest(value)
                for value in (
                    self.scope_digest,
                    self.package_digest,
                    self.image_digest,
                    self.config_digest,
                )
            )
        )


class EvidenceState(StrEnum):
    VERIFIED = "VERIFIED"
    UNKNOWN = "UNKNOWN"
    FAILED = "FAILED"
    UNSUPPORTED = "UNSUPPORTED"


class Disposition(StrEnum):
    READY = "READY"
    PARTIAL = "PARTIAL"
    HOLD = "HOLD"


class GapReason(StrEnum):
    MISSING = "MISSING"
    DUPLICATE = "DUPLICATE"
    SUBJECT = "SUBJECT_MISMATCH"
    UNKNOWN = "UNKNOWN"
    FAILED = "FAILED"
    UNSUPPORTED = "UNSUPPORTED"
    FIXTURE_ONLY = "FIXTURE_ONLY"


@dataclass(frozen=True)
class Requirement:
    subject: ProofSubject
    critical: bool = True


@dataclass(frozen=True)
class Observation:
    check: str
    subject: ProofSubject
    state: EvidenceState
    evidence_digest: str
    fixture: bool


@dataclass(frozen=True)
class EvidenceGap:
    check: str
    reason: GapReason
    critical: bool


@dataclass(frozen=True)
class LifecycleReview:
    disposition: Disposition
    verified_count: int
    gaps: tuple[EvidenceGap, ...]


def review_lifecycle(
    required: Mapping[str, Requirement], observations: Iterable[Observation]
) -> LifecycleReview:
    """Compare authenticated observations to a trusted, current plan.

    The caller owns artifact digest authentication, authority, and the current
    fence. This check does not grant authority or perform provider operations.
    """
    for check in ("baseline", "candidate"):
        if check not in required or required[check].critical is not True:
            raise ValueError("Lifecycle review requires critical baseline and candidate checks")

    counts: Counter[str] = Counter()
    observed = {}
    for item in observations:
        if item.check in required:
            counts[item.check] += 1
            observed[item.check] = item

    gaps = []
    for check, requirement in sorted(required.items()):
        item = observed.get(check)
        reason = None
        if item is None:
            reason = GapReason.MISSING
        elif counts[check] != 1:
            reason = GapReason.DUPLICATE
        elif (
            not requirement.subject.complete()
            or not item.subject.complete()
            or item.subject != requirement.subject
        ):
            reason = GapReason.SUBJECT
        elif not isinstance(item.state, EvidenceState):
            reason = GapReason.UNKNOWN
        elif item.state != EvidenceState.VERIFIED:
            reason = GapReason(item.state.value)
        elif not _digest(item.evidence_digest):
            reason = GapReason.MISSING
        elif item.fixture is not False:
            reason = GapReason.FIXTURE_ONLY
        if reason is not None:
            gaps.append(EvidenceGap(check, reason, requirement.critical))

    disposition = Disposition.READY
    if any(gap.critical for gap in gaps):
        disposition = Disposition.HOLD
    elif gaps:
        disposition = Disposition.PARTIAL
    return LifecycleReview(disposition, len(required) - len(gaps), tuple(gaps))


def review_bundle(
    bundle: ReviewBundle,
    required: Mapping[str, Requirement],
    observations: Iterable[Observation],
    *,
    expected_bundle_digest: str,
) -> LifecycleReview:
    """Review the existing shared bundle against a current authenticated plan.

    Result/snapshot refs must be critical check keys in that plan. The caller
    authenticates their bytes, semantics, subject lineage and current fence,
    and supplies the independently retained bundle digest. READY is scoped
    review sufficiency, never apply authority, live qualification or exit.
    """
    review = review_lifecycle(required, observations)
    gaps = list(review.gaps)
    candidate = required["candidate"].subject
    if (
        not _digest(expected_bundle_digest)
        or bundle.bundle_digest != expected_bundle_digest
        or content_digest(bundle.model_dump(mode="json", exclude={"bundle_digest"}))
        != expected_bundle_digest
        or any(
            (r.subject.case_id, r.subject.run_id) != (bundle.case_id, bundle.run_id)
            for r in required.values()
        )
        or bundle.work_package_digest != candidate.package_digest
        or bundle.artifact_digest != f"sha256:{candidate.image_digest}"
        or bundle.effective_config_digest != candidate.config_digest
    ):
        gaps.append(EvidenceGap("bundle", GapReason.SUBJECT, True))
    for name in (
        "baseline_snapshot_refs", "candidate_snapshot_refs", "scenario_result_refs",
        "domain_rule_result_refs", "security_result_refs",
    ):
        refs = getattr(bundle, name)
        if not refs:
            gaps.append(EvidenceGap(name, GapReason.MISSING, True))
        subject = required["baseline"].subject if name == "baseline_snapshot_refs" else candidate
        for ref in refs:
            requirement = required.get(ref)
            if requirement is None or requirement.critical is not True:
                gaps.append(EvidenceGap(ref, GapReason.MISSING, True))
            elif requirement.subject != subject:
                gaps.append(EvidenceGap(ref, GapReason.SUBJECT, True))
    gaps.extend(EvidenceGap(ref, GapReason.MISSING, True) for ref in bundle.missing_evidence_refs)
    gaps.extend(EvidenceGap(path, GapReason.UNSUPPORTED, True) for path in bundle.unsupported_paths)
    disposition = Disposition.HOLD if any(gap.critical for gap in gaps) else review.disposition
    return LifecycleReview(disposition, review.verified_count, tuple(gaps))
