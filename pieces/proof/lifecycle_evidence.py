"""Local proof checks for evidence already authenticated by the caller."""

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

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
