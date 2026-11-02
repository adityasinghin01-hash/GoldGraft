"""API view models for the control-plane API (docs/design/07_FRONTEND_API.md).

These are request/response shapes only. Boundary formats (RootMap, Verdict,
Certificate, ...) are reused unchanged from the other modules.
"""

from enum import StrEnum
from typing import Annotated

from pydantic import Field, StrictBool, StrictInt

from .agents import Alert, DashboardSpec
from .common import Count, Format, NonNegative, Stage, StagePct, Text, Timestamp
from .delivery import Recipe, SwitchConfig
from .money import MoneyEvent
from .proof import Certificate, Mutant, ProofStrength, Scenario, Verdict
from .runner import GuardEvent, HealDecision
from .survey import Connection, Family

Url = Annotated[str, Field(min_length=1, pattern=r"^https?://\S+$")]


class Problem(Format):
    """RFC 7807 application/problem+json."""

    type: Text = "about:blank"
    title: Text
    status: Annotated[StrictInt, Field(ge=400, le=599)]
    detail: Text | None = None
    instance: Text | None = None


class ProbeRequest(Format):
    url: Url


class ShopCreate(Format):
    name: Text | None = None
    repo: Url | None = None
    site: Url | None = None


class Shop(Format):
    shop_id: Text
    name: Text | None = None
    repo: Text | None = None
    site: Text | None = None
    created_at: Timestamp
    connection: Connection | None = None


class ConnectRequest(Format):
    """Secrets travel once, straight to the vault. Never echoed, logged or stored here."""

    paypal_client_id: Text
    paypal_client_secret: Text
    webhook_id: Text | None = None
    nvp_user: Text | None = None
    nvp_password: Text | None = None
    nvp_signature: Text | None = None


class StartGraftRequest(Format):
    note: Text | None = None


class StageTiming(Format):
    stage: Text
    minutes: NonNegative
    usd: NonNegative


class GraftCard(Format):
    """Every number is copied from the ledger; each has a plain 'what this means' note."""

    old_pieces_found: Count
    pieces_upgraded: Count
    scenarios_total: Count
    scenarios_pass: Count
    problems: Count
    proof_strength_score: Annotated[float, Field(ge=0, le=1, strict=True)] | None = None
    cost_usd: NonNegative
    minutes: NonNegative
    notes: dict[str, Text]


class Graft(Format):
    graft_id: Text
    shop_id: Text
    stage: Text
    lane: Text | None = None
    started_at: Timestamp
    stages: list[StageTiming]
    card: GraftCard
    ledger_root: Text


class ScenarioRow(Format):
    scenario: Scenario
    verdict: Verdict | None = None


class ScenarioList(Format):
    graft_id: Text
    scenarios: list[ScenarioRow]


class CmelView(Format):
    graft_id: Text
    scenario_id: Text
    old: list[MoneyEvent]
    old_twin: list[MoneyEvent]
    new: list[MoneyEvent]


class TriangleRow(Format):
    rule_id: Text
    scenario_ids: list[Text]
    mutant_ids: list[Text]
    killed: StrictBool


class ProofView(Format):
    graft_id: Text
    proof_strength: ProofStrength
    mutants: list[Mutant]
    triangle: list[TriangleRow]


class VerifyCheckName(StrEnum):
    SIGNATURE = "SIGNATURE"
    REKOR = "REKOR"
    LEDGER_CHAIN = "LEDGER_CHAIN"
    PAYPAL_REFETCH = "PAYPAL_REFETCH"


class VerifyCheck(Format):
    name: VerifyCheckName
    ok: StrictBool
    detail: Text


class CertificateVerifyResult(Format):
    cert_id: Text
    ok: StrictBool
    checks: list[VerifyCheck]


class HealState(Format):
    graft_id: Text
    stage: Stage
    stage_pct: StagePct
    guard: Text
    switch_config: SwitchConfig
    last_decision: HealDecision | None = None
    recent: list[GuardEvent]
    label: Text = "PayPal sandbox · simulated buyers"


class InjectFaultRequest(Format):
    mutant_op: Annotated[str, Field(pattern=r"^M(0?[1-9]|1[0-2])$")]


class InjectFaultResult(Format):
    accepted: StrictBool
    label: Text = "DEMO ONLY · PayPal sandbox · simulated buyers"


class Ack(Format):
    accepted: StrictBool
    deduplicated: StrictBool = False
    ledger_seq: Count | None = None


class RecipeList(Format):
    recipes: list[Recipe]


class LearningPoint(Format):
    shop_id: Text
    recipe_used: StrictBool
    minutes: NonNegative
    usd: NonNegative


class LearningCurve(Format):
    points: list[LearningPoint]
    label: Text


class FleetRow(Format):
    shop_id: Text
    stage: Text
    old_families: list[Family]
    deadline_risk: Text
    paypal_only_items: Count


class OrchardView(Format):
    shops: list[FleetRow]
    dashboards: list[DashboardSpec]
    label: Text


class OrchardAsk(Format):
    question: Text


class OrchardAnswer(Format):
    question: Text
    answer: Text
    dashboard: DashboardSpec | None = None


class GauntletAttempt(Format):
    attempt_id: Text
    source: Text
    summary: Text
    blocked_by: Text
    blocked: StrictBool


class GauntletRun(Format):
    run_id: Text
    attempts: list[GauntletAttempt]
    alerts: list[Alert]


class ArmName(StrEnum):
    HAND = "HAND"
    PAYPAL_AI_TOOLKIT = "PAYPAL_AI_TOOLKIT"
    PLAIN_CLAUDE_CODE = "PLAIN_CLAUDE_CODE"
    GOLDGRAFT = "GOLDGRAFT"


class ComparisonArm(Format):
    arm: ArmName
    minutes: NonNegative
    usd: NonNegative
    pieces_missed: Count
    money_bugs_left: Count


class Comparison(Format):
    shop_id: Text
    arms: list[ComparisonArm]
    label: Text


API_MODELS: tuple[type[Format], ...] = (
    Problem, ProbeRequest, ShopCreate, Shop, ConnectRequest, StartGraftRequest, StageTiming,
    GraftCard, Graft, ScenarioRow, ScenarioList, CmelView, TriangleRow, ProofView, VerifyCheck,
    CertificateVerifyResult, HealState, InjectFaultRequest, InjectFaultResult, Ack, RecipeList,
    LearningPoint, LearningCurve, FleetRow, OrchardView, OrchardAsk, OrchardAnswer,
    GauntletAttempt, GauntletRun, ComparisonArm, Comparison,
)
# Re-exported so route definitions only import from this module.
__all__ = [m.__name__ for m in API_MODELS] + ["Certificate", "Url"]
