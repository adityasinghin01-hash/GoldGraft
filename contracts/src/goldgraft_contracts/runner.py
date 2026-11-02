"""New runner, recorder, shop-pack and guard boundaries (brief C1)."""

from enum import StrEnum
from typing import Annotated

from pydantic import (
    ConfigDict,
    Field,
    StrictInt,
    field_validator,
    model_serializer,
    model_validator,
)

from .common import (
    Count,
    Format,
    JsonValue,
    PositiveInt,
    Probability,
    Side,
    Stage,
    StagePct,
    Text,
    Timestamp,
    Variant,
)
from .money import Money, PayPalRefs
from .survey import MoneyFlow, Touchpoint

SecretRef = Annotated[str, Field(pattern=r"^(doppler|vault|secret)://\S+$")]
EnvName = Annotated[str, Field(pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")]


class JobKind(StrEnum):
    BUILD = "BUILD"
    RECORD = "RECORD"
    PROVE = "PROVE"
    MUTANT_RUN = "MUTANT_RUN"
    SHADOW = "SHADOW"
    GAUNTLET = "GAUNTLET"


class JobTimeouts(Format):
    build_s: PositiveInt
    run_s: PositiveInt
    total_s: PositiveInt


class JobSpec(Format):
    job_id: Text
    graft_id: Text
    stage: Stage
    kind: JobKind
    shop_pack_ref: Text
    variants: Annotated[list[Variant], Field(min_length=1)]
    scenario_ids: list[Text]
    mutant_ids: list[Text]
    timeouts: JobTimeouts
    secrets_ref: SecretRef
    signature: Text | None


class JobStatus(StrEnum):
    OK = "OK"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    BLOCKED = "BLOCKED"


class JobRunnerIdentity(Format):
    workflow: Text
    sha: Text
    run_id: Text


class JobResult(Format):
    job_id: Text
    status: JobStatus
    started: Timestamp
    finished: Timestamp
    raw_capture_refs: list[Text]
    artifacts: list[Text]
    logs_ref: Text
    runner_identity: JobRunnerIdentity
    rate_limit_pauses: Count
    error: Text | None = None

    @model_validator(mode="after")
    def chronological(self):
        if self.finished < self.started:
            raise ValueError("finished must be at or after started")
        return self


class Direction(StrEnum):
    SHOP_TO_PAYPAL = "SHOP_TO_PAYPAL"
    PAYPAL_TO_SHOP = "PAYPAL_TO_SHOP"
    BROWSER_TO_SHOP = "BROWSER_TO_SHOP"
    PAYPAL_NOTIFY_TO_SHOP = "PAYPAL_NOTIFY_TO_SHOP"
    SHOP_DB_WRITE = "SHOP_DB_WRITE"


class DbChange(Format):
    table: Text
    key: dict[str, JsonValue]
    before: dict[str, JsonValue] | None
    after: dict[str, JsonValue] | None


# Reject instead of silently redacting: capture producers must remove secrets first.
SECRET_HEADERS = frozenset(
    {
        "authorization",
        "proxy-authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "api-key",
        "paypal-auth-assertion",
        "paypal-access-token",
        "x-auth-token",
        "x-access-token",
        "client-secret",
        "x-client-secret",
    }
)


class RawExchange(Format):
    model_config = ConfigDict(
        json_schema_extra={
            "oneOf": [
                {
                    "required": ["body_text"],
                    "not": {"required": ["body_json"]},
                    "properties": {"body_text": {"type": "string"}},
                },
                {"required": ["body_json"], "not": {"required": ["body_text"]}},
                {
                    "properties": {"direction": {"const": "SHOP_DB_WRITE"}},
                    "not": {"anyOf": [{"required": ["body_text"]}, {"required": ["body_json"]}]},
                },
            ],
            "allOf": [
                {
                    "if": {"properties": {"direction": {"const": "SHOP_DB_WRITE"}}},
                    "then": {
                        "required": ["db_change"],
                        "properties": {"db_change": {"type": "object"}},
                    },
                    "else": {"properties": {"db_change": {"type": "null"}}},
                }
            ],
        }
    )
    seq: Count
    t_ms: Count
    direction: Direction
    method: Text
    url: Text
    headers: dict[str, str]
    body_text: str | None = None
    body_json: JsonValue = None
    status: Annotated[StrictInt, Field(ge=100, le=599)] | None = None
    db_change: DbChange | None = None

    @field_validator("headers")
    @classmethod
    def redacted_headers(cls, value: dict[str, str]) -> dict[str, str]:
        for name, content in value.items():
            normalized = name.lower()
            sensitive = normalized in SECRET_HEADERS or any(
                fragment in normalized for fragment in ("secret", "token", "api-key", "api_key")
            )
            if sensitive and content != "[REDACTED]":
                raise ValueError("secret headers must be replaced by [REDACTED]")
        return value

    @model_validator(mode="after")
    def body_and_db(self):
        # Explicit JSON null is a body; omitted body_json is not.
        has_json = "body_json" in self.model_fields_set
        if "body_text" in self.model_fields_set and has_json:
            raise ValueError("body_text and body_json are mutually exclusive")
        if self.direction == Direction.SHOP_DB_WRITE:
            if self.db_change is None:
                raise ValueError("SHOP_DB_WRITE requires db_change")
        elif self.db_change is not None:
            raise ValueError("db_change requires SHOP_DB_WRITE direction")
        elif self.body_text is None and not has_json:
            raise ValueError("HTTP exchanges require body_text or body_json")
        return self

    @model_serializer(mode="wrap")
    def wire_body(self, handler):
        result = handler(self)
        if self.body_text is not None:
            result.pop("body_json", None)
        elif "body_json" in self.model_fields_set:
            result.pop("body_text", None)
        else:
            result.pop("body_text", None)
            result.pop("body_json", None)
        return result


class RawCapture(Format):
    graft_id: Text
    run_id: Text
    variant: Variant
    scenario_id: Text
    exchanges: list[RawExchange]

    @model_validator(mode="after")
    def ordered(self):
        sequences = [item.seq for item in self.exchanges]
        if sequences != sorted(set(sequences)):
            raise ValueError("exchange seq values must increase strictly")
        return self


class ShopSource(Format):
    repo: Text
    commit: Text


class ComposeStart(Format):
    compose_file: Text


class CommandStart(Format):
    command: Text


class AnswerKey(Format):
    touchpoints: list[Touchpoint]
    money_flow: MoneyFlow


class ShopPack(Format):
    shop_id: Text
    name: Text
    language: Text
    framework: Text
    licence: Text
    source: ShopSource
    start: ComposeStart | CommandStart
    port: Annotated[StrictInt, Field(ge=1, le=65535)]
    health_url: Text
    buyer_script: Text
    scenarios_supported: list[Text]
    answer_key: AnswerKey
    env_needed: list[EnvName]


class GuardEventKind(StrEnum):
    ATTEMPT = "ATTEMPT"
    APPROVED = "APPROVED"
    CAPTURED = "CAPTURED"
    DECLINED = "DECLINED"
    ERROR = "ERROR"
    REFUNDED = "REFUNDED"


class GuardEvent(Format):
    graft_id: Text
    shop_id: Text
    path: Side
    event: GuardEventKind
    order_ref: Text
    money: Money | None = None
    paypal_ids: PayPalRefs | None = None
    latency_ms: Count
    ts: Timestamp
    lib_version: Text
    signature: Text | None = None


class HealAction(StrEnum):
    HOLD = "HOLD"
    STEP_UP = "STEP_UP"
    CUTBACK = "CUTBACK"


class HealStats(Format):
    n_old: Count
    n_new: Count
    success_old: Count
    success_new: Count
    prob_new_not_worse: Probability
    threshold: Probability

    @model_validator(mode="after")
    def successes(self):
        if self.success_old > self.n_old or self.success_new > self.n_new:
            raise ValueError("success count cannot exceed sample count")
        return self


class HealDecision(Format):
    graft_id: Text
    from_stage_pct: StagePct
    action: HealAction
    to_stage_pct: StagePct
    reason: Text
    stats: HealStats
    hard_stop: Text | None = None

    @model_validator(mode="after")
    def transition(self):
        stages = [0, 1, 10, 50, 100]
        if self.action == HealAction.HOLD and self.to_stage_pct != self.from_stage_pct:
            raise ValueError("HOLD must preserve stage")
        if self.action == HealAction.CUTBACK and self.to_stage_pct != 0:
            raise ValueError("CUTBACK must return to 0")
        if self.action == HealAction.STEP_UP:
            idx = stages.index(self.from_stage_pct)
            if idx == len(stages) - 1 or self.to_stage_pct != stages[idx + 1]:
                raise ValueError("STEP_UP must select the next stage")
        if self.hard_stop and self.action != HealAction.CUTBACK:
            raise ValueError("hard_stop requires CUTBACK")
        return self
