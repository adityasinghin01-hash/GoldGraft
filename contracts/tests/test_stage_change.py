import pytest
from goldgraft_contracts.registry import validate
from pydantic import ValidationError


def test_stage_change_format():
    payload = dict(graft_id="g1", from_stage="SURVEYED", to_stage="LANE_NO_CODE",
                   attempt=1, reason="No repository", actor={"kind": "service", "name": "tracker"},
                   evidence_refs=[])
    assert validate("StageChange/1", payload).to_stage == "LANE_NO_CODE"
    for changes in ({"to_stage": "unknown"}, {"attempt": 0}, {"attempt": True},
                    {"reason": ""}, {"actor": {"kind": "merchant", "name": "x"}}):
        with pytest.raises(ValidationError):
            validate("StageChange/1", {**payload, **changes})
