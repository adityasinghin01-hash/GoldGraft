"""Runner observations used by the lifecycle rules without changing the wire contracts."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal

from goldgraft_contracts.money import Money, MoneyEvent


@dataclass(frozen=True)
class CallbackWatch:
    order_ref: str
    deadline_ms: int
    observed_until_ms: int
    lookup_ms: tuple[int, ...]  # Shop lookups, excluding independent proof reads.
    reference: str


@dataclass(frozen=True)
class RestartWatch:
    order_ref: str
    restart_ms: int
    reference: str


@dataclass(frozen=True)
class RefundRoute:
    order_ref: str
    refund_id: str
    origin: Literal["LEGACY", "REST"]
    route: Literal["LEGACY", "REST"]
    equivalence_ref: str | None
    reference: str


@dataclass(frozen=True)
class CatalogueQuote:
    order_ref: str
    money: Money
    reference: str


@dataclass(frozen=True)
class LifecycleEvidence:
    run_id: str
    callbacks: tuple[CallbackWatch, ...] = field(default_factory=tuple)
    restarts: tuple[RestartWatch, ...] = field(default_factory=tuple)
    refunds: tuple[RefundRoute, ...] = field(default_factory=tuple)
    quotes: tuple[CatalogueQuote, ...] = field(default_factory=tuple)


def lifecycle_hits(
    events: Sequence[MoneyEvent],
    evidence: LifecycleEvidence,
) -> tuple[dict[str, set[str]], set[str]]:
    """Return witnessed rule breaches and rules with incomplete observations."""
    if not events or any(event.run_id != evidence.run_id for event in events):
        raise ValueError("Lifecycle evidence does not match the event run")

    hits: dict[str, set[str]] = {}
    incomplete = set()

    def hit(rule: str, reference: str) -> None:
        hits.setdefault(rule, set()).add(reference)

    for watch in evidence.callbacks:
        if any(
            event.order_ref == watch.order_ref
            and event.kind == "NOTIFY"
            and event.t_ms <= watch.deadline_ms
            for event in events
        ):
            continue
        if any(watch.deadline_ms <= time <= watch.observed_until_ms for time in watch.lookup_ms):
            continue
        if watch.observed_until_ms < watch.deadline_ms:
            incomplete.add("R13")
        else:
            hit("R13", watch.reference)

    for watch in evidence.restarts:
        order = [event for event in events if event.order_ref == watch.order_ref]
        if not any(event.kind == "APPROVE" and event.t_ms < watch.restart_ms for event in order):
            incomplete.add("R14")
            continue
        captures = [
            event for event in order if event.kind == "CAPTURE" and event.status_norm == "COMPLETED"
        ]
        if any(
            event.source == "PAYPAL_CALL" and event.t_ms < watch.restart_ms for event in captures
        ):
            incomplete.add("R14")
            continue
        witnessed = {
            event.pp.capture_id or event.pp.txn_id
            for event in captures
            if event.t_ms >= watch.restart_ms and event.source == "PAYPAL_LEDGER"
        }
        if len(witnessed - {None}) != 1 or not any(
            event.kind == "SHOP_PAID" and event.t_ms >= watch.restart_ms for event in order
        ):
            hit("R14", watch.reference)

    for route in evidence.refunds:
        if route.origin not in {"LEGACY", "REST"} or route.route not in {"LEGACY", "REST"}:
            incomplete.add("R15")
        elif not any(
            event.order_ref == route.order_ref
            and event.kind == "REFUND"
            and event.pp.refund_id == route.refund_id
            for event in events
        ):
            incomplete.add("R15")
        elif route.origin == "LEGACY" and route.route == "REST" and not (
            isinstance(route.equivalence_ref, str) and route.equivalence_ref.strip()
        ):
            hit("R15", route.reference)

    for quote in evidence.quotes:
        intents = [
            event
            for event in events
            if event.order_ref == quote.order_ref and event.kind == "INTENT"
        ]
        if not intents or any(event.money is None for event in intents):
            incomplete.update(("R12", "R17"))
            continue
        for intent in intents:
            if intent.money != quote.money:
                for rule in ("R12", "R17"):
                    hit(rule, quote.reference)
                    hit(rule, intent.raw_ref)

    return hits, incomplete
