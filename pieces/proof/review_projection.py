"""Project private lifecycle findings to an identifier-free public summary."""

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from goldgraft_contracts.connection_control import PublicMetric, PublicProofView

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


def public_proof_view(
    review: LifecycleReview, *, checked_at: datetime, public_evidence_ref: str
) -> PublicProofView:
    """Project into the current shared shape without publishing private metadata.

    The public alias is fresh, not a private case, run, subject or artifact ID.
    Local sufficiency does not establish external signature integrity or qualify
    payment/deployment/exit. The host supplies an existing redacted public artifact
    reference; this function does not fabricate an evidence receipt or store one.
    Host access checks and public alias persistence/reuse are separate.
    """
    summary = public_review(review)
    alias = uuid4().hex
    return PublicProofView(
        public_id=alias,
        scope_text="Scoped lifecycle evidence review",
        evidence_class="component_offline",
        summary_metrics=[
            PublicMetric(name=name, value=value, evidence_ref=public_evidence_ref)
            for name, value in (
                ("disposition", summary.disposition.value),
                ("verified_checks", str(summary.verified_count)),
                ("gaps", str(summary.gap_count)),
            )
        ],
        integrity="unknown",
        limitations=[
            "Scoped review requires authenticated current inputs.",
            "Payment, deployment and independent exit qualification are separate.",
        ],
        checked_at=checked_at,
    )
