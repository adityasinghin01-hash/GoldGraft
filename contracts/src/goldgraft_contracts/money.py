"""Money and the canonical money event language (design 01 §3)."""

from enum import StrEnum
from typing import Annotated

from pydantic import AfterValidator, Field, StrictInt

from .common import Count, Format, Text, Variant
from .currencies import CURRENCY_MINOR_DIGITS


def supported_currency(value: str) -> str:
    if value not in CURRENCY_MINOR_DIGITS:
        raise ValueError("currency must be in CURRENCY_MINOR_DIGITS")
    return value


Currency = Annotated[
    str,
    Field(pattern=r"^[A-Z]{3}$", json_schema_extra={"enum": sorted(CURRENCY_MINOR_DIGITS)}),
    AfterValidator(supported_currency),
]


class Money(Format):
    minor: StrictInt
    currency: Currency


class Source(StrEnum):
    SHOP_HTTP = "SHOP_HTTP"
    SHOP_DB = "SHOP_DB"
    PAYPAL_CALL = "PAYPAL_CALL"
    PAYPAL_LEDGER = "PAYPAL_LEDGER"
    NOTIFICATION = "NOTIFICATION"


class Kind(StrEnum):
    INTENT = "INTENT"
    APPROVE = "APPROVE"
    AUTHORIZE = "AUTHORIZE"
    CAPTURE = "CAPTURE"
    VOID = "VOID"
    SHOP_PAID = "SHOP_PAID"
    SHOP_PENDING = "SHOP_PENDING"
    SHOP_UNPAID = "SHOP_UNPAID"
    NOTIFY = "NOTIFY"
    NOTIFY_VERIFIED = "NOTIFY_VERIFIED"
    NOTIFY_REJECTED = "NOTIFY_REJECTED"
    REFUND = "REFUND"
    RECUR_SETUP = "RECUR_SETUP"
    RECUR_CHARGE = "RECUR_CHARGE"
    ERROR = "ERROR"


class StatusNorm(StrEnum):
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"
    DECLINED = "DECLINED"
    REFUNDED = "REFUNDED"
    FAILED = "FAILED"


class PayPalRefs(Format):
    legacy_token: Text | None = None
    txn_id: Text | None = None
    order_id: Text | None = None
    capture_id: Text | None = None
    refund_id: Text | None = None
    profile_id: Text | None = None
    debug_id: Text | None = None


class MoneyEvent(Format):
    graft_id: Text
    run_id: Text
    variant: Variant
    scenario_id: Text
    seq: Count
    t_ms: Count
    source: Source
    kind: Kind
    order_ref: Text
    pp: PayPalRefs
    money: Money | None = None
    status_norm: StatusNorm | None = None
    items_hash: Text | None = None
    raw_ref: Text
    noise: list[Text]


CMEL = MoneyEvent


class MappingRow(Format):
    source: Text
    signal_fields: list[Text]
    cmel_kind: Kind
    notes: str
