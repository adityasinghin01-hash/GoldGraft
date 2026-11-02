"""Minimal agent artifacts owned by Aditya (design 06)."""

from enum import StrEnum
from typing import Annotated

from pydantic import (
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    ValidationInfo,
    model_validator,
)

from .common import Count, Format, Hash, JsonValue, Producer, Stage, StagePct, Text, Timestamp
from .proof import Mutant, Scenario, Severity


class AgentArtifact(Format):
    id: Text
    graft_id: Text
    producer: Producer
    created_at: Timestamp


class Assignment(AgentArtifact):
    """minimal v1, owner Aditya may extend"""

    stage: Stage
    assignee: Text
    input_refs: list[Text]
    attempt: Count


class Lane(StrEnum):
    FULL = "FULL"
    NO_RUNTIME = "NO-RUNTIME"
    NO_CODE = "NO-CODE"


class LaneChange(AgentArtifact):
    """minimal v1, owner Aditya may extend"""

    lane: Lane
    reason: Text


class Change(Format):
    commit: Text
    plan_item_ids: list[Text]
    summary: Text


class ChangeList(AgentArtifact):
    """minimal v1, owner Aditya may extend"""

    branch: Text
    changes: list[Change]
    open_item_ids: list[Text]


class ScenarioSet(AgentArtifact):
    """minimal v1, owner Aditya may extend"""

    scenarios: list[Scenario]
    unguarded_rule_ids: list[Text]


class MutantSet(AgentArtifact):
    """minimal v1, owner Aditya may extend"""

    mutants: list[Mutant]
    unguarded_rule_ids: list[Text]


class TriangleRequest(AgentArtifact):
    """minimal v1, owner Aditya may extend"""

    rule_id: Text
    scenario_ids: list[Text]
    mutant_ids: list[Text]
    reason: Text


class HealNote(AgentArtifact):
    """minimal v1, owner Aditya may extend"""

    stage_pct: StagePct
    text: Text
    pause_requested: StrictBool
    cutback_requested: StrictBool
    evidence_refs: list[Text]


class DetectionRule(AgentArtifact):
    """minimal v1, owner Aditya may extend"""

    language: Text
    pattern: Text
    operation: Text
    evidence_refs: list[Text]


class HeraldKind(StrEnum):
    GRAFT_CARD = "GRAFT_CARD"
    PR_BODY = "PR_BODY"
    HANDOFF = "HANDOFF"
    VERDICT_EXPLAIN = "VERDICT_EXPLAIN"


class LedgerNumber(Format):
    entry_hash: Hash
    json_pointer: Annotated[str, Field(pattern=r"^/")]
    value: StrictInt | StrictFloat


class HeraldText(AgentArtifact):
    """minimal v1, owner Aditya may extend"""

    kind: HeraldKind
    text: Text
    numbers_used: list[LedgerNumber]

    @model_validator(mode="after")
    def copied_numbers(self, info: ValidationInfo):
        entries = (info.context or {}).get("ledger_entries", {})
        for number in self.numbers_used:
            value = entries.get(number.entry_hash)
            try:
                for token in number.json_pointer[1:].split("/"):
                    token = token.replace("~1", "/").replace("~0", "~")
                    value = value[int(token)] if isinstance(value, list) else value[token]
            except (KeyError, TypeError, IndexError, ValueError) as exc:
                raise ValueError("numbers_used must resolve to supplied ledger_entries") from exc
            if type(value) not in (int, float) or value != number.value:
                raise ValueError("numbers_used value must be copied from a ledger entry")
        return self


class DashboardSpec(AgentArtifact):
    """minimal v1, owner Aditya may extend"""

    question: Text
    title: Text
    metrics: list[Text]
    group_by: list[Text]
    filters: dict[str, JsonValue]
    evidence_refs: list[Text]


class Alert(AgentArtifact):
    """minimal v1, owner Aditya may extend"""

    severity: Severity
    message: Text
    evidence_refs: list[Text]
    halted_agent: Text | None = None
