"""Shared scalar constraints; no piece-specific dependencies."""

from enum import StrEnum
from typing import Annotated, ClassVar, Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
    model_serializer,
)

# Explicit recursion gives JSON Schema and TypeScript a real JSON union.
type JsonValue = (
    None | StrictBool | StrictInt | StrictFloat | StrictStr | list[JsonValue] | dict[str, JsonValue]
)


Text = Annotated[str, Field(min_length=1)]
Count = Annotated[StrictInt, Field(ge=0)]
PositiveInt = Annotated[StrictInt, Field(gt=0)]
Probability = Annotated[float, Field(ge=0, le=1, strict=True)]
NonNegative = Annotated[float, Field(ge=0, strict=True)]
Hash = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


def integer_stage(value: object) -> object:
    if type(value) is not int:
        raise ValueError("stage percentage must be an integer")
    return value


StagePct = Annotated[Literal[0, 1, 10, 50, 100], BeforeValidator(integer_stage)]
Timestamp = AwareDatetime


class Format(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_default=True, allow_inf_nan=False, serialize_by_alias=True
    )
    schema_name: ClassVar[str]

    @model_serializer(mode="wrap")
    def preserve_optional_presence(self, handler):
        result = handler(self)
        for name, field in type(self).model_fields.items():
            if name not in self.model_fields_set and field.default is None:
                result.pop(field.serialization_alias or field.alias or name, None)
        return result


class ProducerKind(StrEnum):
    AGENT = "agent"
    SERVICE = "service"


class Producer(Format):
    kind: ProducerKind
    name: Text
    version: Text
    model: Text | None = None


class Variant(StrEnum):
    OLD = "OLD"
    OLD_TWIN = "OLD_TWIN"
    NEW = "NEW"


class Side(StrEnum):
    OLD = "OLD"
    NEW = "NEW"


class Stage(StrEnum):
    CREATED = "CREATED"
    GATED = "GATED"
    SURVEYED = "SURVEYED"
    BUILT = "BUILT"
    LINKS_PROVEN = "LINKS_PROVEN"
    DELIVERED = "DELIVERED"
    RECORDED = "RECORDED"
    CONTRACTED = "CONTRACTED"
    ATTACK_PLANNED = "ATTACK_PLANNED"
    GRAFTED = "GRAFTED"
    PROVING = "PROVING"
    REPAIRING = "REPAIRING"
    CERTIFIED = "CERTIFIED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    PR_OPEN = "PR_OPEN"
    MERGED = "MERGED"
    SHADOW = "SHADOW"
    HEAL_1 = "HEAL_1"
    HEAL_10 = "HEAL_10"
    HEAL_50 = "HEAL_50"
    LIVE_100 = "LIVE_100"
    CLEANUP_PR = "CLEANUP_PR"
    DONE = "DONE"
    CUTBACK = "CUTBACK"
