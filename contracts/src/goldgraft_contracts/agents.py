"""Minimal agent artifacts owned by Aditya (design 06)."""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import (
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    ValidationInfo,
    model_validator,
)

from .common import Count, Format, Hash, JsonValue, Producer, Stage, StagePct, Text, Timestamp
from .plan5_common import Digest, GitCommit, Ids, P5Record, Ref, Utc
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


# Additive v2; the Git-only v1 payload and its examples are untouched.


class SnapshotChange(P5Record):
    plan_item_ids: Ids
    summary: Text
    commit: GitCommit | None


class ChangeListV2(P5Record):
    id: Text
    graft_id: Text
    producer: Producer
    created_at: Utc
    provenance: Literal["git", "snapshot"]
    branch: Text | None
    baseline_snapshot_ref: Ref
    candidate_snapshot_ref: Ref
    patch_digest: Digest
    changes: list[SnapshotChange]
    open_item_ids: Ids

    @model_validator(mode="after")
    def route_provenance(self):
        if self.provenance == "git":
            if (
                self.branch is None
                or not self.changes
                or any(c.commit is None for c in self.changes)
            ):
                raise ValueError("Git provenance requires branch and provider-validated commit IDs")
        elif self.branch is not None or any(c.commit is not None for c in self.changes):
            raise ValueError("snapshot provenance cannot invent Git branch or commits")
        if self.producer.kind.value != "agent" or self.producer.name != "Grafter":
            raise ValueError("ChangeList/2 belongs exclusively to Grafter")
        return self


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
