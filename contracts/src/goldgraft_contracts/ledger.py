"""Ledger envelope validation; hashing/storage belong to foundation, not contracts."""

import json
from enum import StrEnum
from typing import Annotated

from pydantic import ConfigDict, Field, ValidationInfo, model_serializer, model_validator

from .common import Count, Format, Hash, JsonValue, Producer, Text, Timestamp

INLINE_LIMIT_BYTES = 16 * 1024


class EntryType(StrEnum):
    STAGE = "STAGE"
    ARTIFACT = "ARTIFACT"
    MESSAGE = "MESSAGE"
    VERDICT = "VERDICT"
    SWITCH = "SWITCH"
    ALERT = "ALERT"
    COST = "COST"


class LedgerEntry(Format):
    model_config = ConfigDict(
        json_schema_extra={
            "oneOf": [
                {"required": ["payload"], "not": {"required": ["payload_ref"]}},
                {
                    "required": ["payload_ref"],
                    "not": {"required": ["payload"]},
                    "properties": {"payload_ref": {"type": "string"}},
                },
            ]
        }
    )
    seq: Count
    graft_id: Text
    ts: Timestamp
    type: EntryType
    producer: Producer
    inputs: list[Hash]
    payload: JsonValue = None
    payload_ref: Text | None = None
    payload_hash: Hash
    schema_: Annotated[str, Field(alias="schema", pattern=r"^[A-Za-z][A-Za-z0-9]*/[1-9][0-9]*$")]
    prev_hash: Hash
    entry_hash: Hash

    @model_validator(mode="after")
    def checked_payload(self, info: ValidationInfo):
        from .registry import REGISTRY, validate

        inline = "payload" in self.model_fields_set
        if inline == ("payload_ref" in self.model_fields_set) or (
            not inline and self.payload_ref is None
        ):
            raise ValueError("exactly one of payload and payload_ref is required")
        if self.schema_ not in REGISTRY:
            raise ValueError(f"Unknown schema: {self.schema_}")
        if inline:
            size = len(
                json.dumps(
                    self.payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False
                ).encode("utf-8")
            )
            if size > INLINE_LIMIT_BYTES:
                raise ValueError("inline payload exceeds 16 KB (16384 UTF-8 bytes)")
            validate(self.schema_, self.payload, context=info.context)
        return self

    @model_serializer(mode="wrap")
    def wire_payload(self, handler):
        result = handler(self)
        result.pop("payload_ref" if "payload" in self.model_fields_set else "payload", None)
        return result
