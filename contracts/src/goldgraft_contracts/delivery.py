"""Recipes, rollout configuration, usage and PayPal handoff artifacts."""

from enum import StrEnum

from pydantic import StrictInt

from .common import Count, Format, NonNegative, PositiveInt, Probability, StagePct, Text, Timestamp
from .money import Currency, Money
from .survey import Family


class Fingerprint(Format):
    lang: Text
    framework: Text
    family: Family
    ast_shape_hash: Text


class RecipeStatus(StrEnum):
    QUARANTINE = "QUARANTINE"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class RecipeEnv(Format):
    dockerfile: Text
    compose: Text
    seed: Text
    driver_template: Text


class Recipe(Format):
    id: Text
    fingerprint: Fingerprint
    transform: Text
    env: RecipeEnv | None = None
    scenarios: list[Text]
    provenance: list[Text]
    confidence: Probability
    status: RecipeStatus
    signature: Text


class SwitchConfig(Format):
    graft_id: Text
    stage_pct: StagePct
    version: PositiveInt
    expires_at: Timestamp
    origin_rules: list[Text]
    signature: Text


class BudgetRecord(Format):
    graft_id: Text
    agent: Text
    model: Text
    tokens_in: Count
    tokens_cached: Count
    tokens_out: Count
    usd: NonNegative
    cap_usd: NonNegative


class HandoffType(StrEnum):
    BILLING_AGREEMENT = "BILLING_AGREEMENT"
    RECURRING_PROFILE = "RECURRING_PROFILE"


class HandoffRecord(Format):
    type: HandoffType
    id: Text
    customer_ref: Text
    amount: StrictInt
    currency: Currency
    cycle: Text
    next_billing: Timestamp | None
    status: Text
    source: Text


class HandoffSummary(Format):
    counts: dict[str, Count]
    totals_per_currency: list[Money]
    duplicates: list[Text]
    inactive: Count


class HandoffPack(Format):
    records: list[HandoffRecord]
    validation_summary: HandoffSummary
    freeze_window_advice: Text
