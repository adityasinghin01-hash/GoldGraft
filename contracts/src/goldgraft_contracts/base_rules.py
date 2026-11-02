"""The sixteen base rules as data, not executable predicate implementations."""

from .common import Format, Text
from .proof import Severity


class BaseRule(Format):
    id: Text
    title: Text
    plain_text: Text
    predicate_idea: Text
    severity: Severity


BASE_RULES: list[BaseRule] = [
    BaseRule(
        id="R01",
        title="paid only if PayPal shows one COMPLETED capture for this order",
        plain_text="paid only if PayPal shows one COMPLETED capture for this order",
        predicate_idea="SHOP_PAID(o) ⇒ ∃! LEDGER CAPTURE(o, COMPLETED)",
        severity=Severity.CRITICAL,
    ),
    BaseRule(
        id="R02",
        title="captured amount = order total",
        plain_text="captured amount = order total",
        predicate_idea="CAPTURE.money.minor = INTENT(o).money.minor",
        severity=Severity.CRITICAL,
    ),
    BaseRule(
        id="R03",
        title="captured currency = order currency",
        plain_text="captured currency = order currency",
        predicate_idea="CAPTURE.money.currency = INTENT(o).money.currency",
        severity=Severity.CRITICAL,
    ),
    BaseRule(
        id="R04",
        title="not paid ⇒ no completed capture",
        plain_text="not paid ⇒ no completed capture",
        predicate_idea="¬SHOP_PAID(o) ⇒ ¬∃ CAPTURE(o, COMPLETED)",
        severity=Severity.CRITICAL,
    ),
    BaseRule(
        id="R05",
        title="retries/double clicks ⇒ ≤1 capture, no 5xx",
        plain_text="retries/double clicks ⇒ ≤1 capture, no 5xx",
        predicate_idea="count(CAPTURE COMPLETED, o) ≤ 1",
        severity=Severity.CRITICAL,
    ),
    BaseRule(
        id="R06",
        title="unapproved order never confirmed",
        plain_text="unapproved order never confirmed",
        predicate_idea="SHOP_PAID(o) ⇒ ∃ APPROVE(o)",
        severity=Severity.CRITICAL,
    ),
    BaseRule(
        id="R07",
        title="pending capture ≠ paid",
        plain_text="pending capture ≠ paid",
        predicate_idea="CAPTURE(PENDING) ⇒ SHOP_PENDING, not SHOP_PAID",
        severity=Severity.MAJOR,
    ),
    BaseRule(
        id="R08",
        title="notification acted on only if verified",
        plain_text="notification acted on only if verified",
        predicate_idea="NOTIFY ⇒ NOTIFY_VERIFIED before any SHOP_PAID it causes",
        severity=Severity.CRITICAL,
    ),
    BaseRule(
        id="R09",
        title="duplicate notifications are harmless",
        plain_text="duplicate notifications are harmless",
        predicate_idea="same txn/event id twice ⇒ no second state change",
        severity=Severity.MAJOR,
    ),
    BaseRule(
        id="R10",
        title="replayed confirmation returns the same result, no second charge",
        plain_text="replayed confirmation returns the same result, no second charge",
        predicate_idea="replay(confirm) ⇒ same capture id",
        severity=Severity.MAJOR,
    ),
    BaseRule(
        id="R11",
        title="refunds ≤ captured; second full refund refused",
        plain_text="refunds ≤ captured; second full refund refused",
        predicate_idea="Σ REFUND ≤ CAPTURE",
        severity=Severity.CRITICAL,
    ),
    BaseRule(
        id="R12",
        title="amounts never from the browser",
        plain_text="amounts never from the browser",
        predicate_idea="INTENT.money derived server-side (static + mutant M7)",
        severity=Severity.CRITICAL,
    ),
    BaseRule(
        id="R13",
        title="no callback ⇒ backend asks PayPal",
        plain_text="no callback ⇒ backend asks PayPal",
        predicate_idea="missing NOTIFY within T ⇒ ledger lookup by shop",
        severity=Severity.MAJOR,
    ),
    BaseRule(
        id="R14",
        title="restart mid-payment loses nothing",
        plain_text="restart mid-payment loses nothing",
        predicate_idea="restart between APPROVE and CAPTURE ⇒ eventual single CAPTURE + SHOP_PAID",
        severity=Severity.MAJOR,
    ),
    BaseRule(
        id="R15",
        title="old objects stay on old rails",
        plain_text="old objects stay on old rails",
        predicate_idea="REFUND of a legacy txn uses the legacy path (or a proven REST equivalent)",
        severity=Severity.MAJOR,
    ),
    BaseRule(
        id="R16",
        title="money as integers",
        plain_text="money as integers",
        predicate_idea="static check + mutant M6",
        severity=Severity.MINOR,
    ),
]
