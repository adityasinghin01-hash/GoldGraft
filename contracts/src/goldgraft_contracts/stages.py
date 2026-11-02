"""StageChange/1: durable cycle entries, including the explicit fallback lanes.

Existing Stage consumers retain C1's enum. Only this new format accepts lane names.
The initial entry has from_stage=null; attempt counts visits to the destination.
"""

from typing import Literal

from .common import Format, PositiveInt, ProducerKind, Stage, Text

type StageName = Stage | Literal["LANE_NO_CODE", "LANE_NO_RUNTIME", "LANE_MAP_ONLY"]


class StageActor(Format):
    kind: ProducerKind
    name: Text


class StageChange(Format):
    graft_id: Text
    from_stage: StageName | None
    to_stage: StageName
    attempt: PositiveInt
    reason: Text
    actor: StageActor
    evidence_refs: list[Text]
