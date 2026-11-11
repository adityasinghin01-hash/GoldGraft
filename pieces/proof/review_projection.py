"""Project private lifecycle findings to an identifier-free public summary."""

from dataclasses import dataclass

from .lifecycle_evidence import Disposition, GapReason, LifecycleReview


@dataclass(frozen=True)
class PublicReview:
    disposition: Disposition
    verified_count: int
    gap_count: int
    gap_reasons: tuple[GapReason, ...]


def public_review(review: LifecycleReview) -> PublicReview:
    """Return fixed statuses and aggregate counts from an internal review."""
    return PublicReview(
        disposition=review.disposition,
        verified_count=review.verified_count,
        gap_count=len(review.gaps),
        gap_reasons=tuple(sorted({gap.reason for gap in review.gaps})),
    )
