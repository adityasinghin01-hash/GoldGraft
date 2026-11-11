"""B1 version/fixture compatibility without substituting stand-ins for new services."""

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from goldgraft_contracts.registry import PLAN5_REGISTRY, REGISTRY, validate
from goldgraft_fakes._fixtures import example
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]


def test_versioned_fixture_lookup_keeps_v1_and_selects_v2():
    assert example("ChangeList") == example("ChangeList/1")
    assert "provenance" not in example("ChangeList/1")
    assert example("ChangeList/2")["provenance"] == "snapshot"
    with pytest.raises(ValueError):
        example("../private/2")


def test_existing_v1_examples_are_byte_identical_to_base():
    for name in set(REGISTRY) - set(PLAN5_REGISTRY):
        path = "contracts/examples/" + name.replace("/", ".") + ".json"
        base = subprocess.check_output(["git", "show", "HEAD:" + path], cwd=ROOT)
        assert (ROOT / path).read_bytes() == base


def test_index_hashes_and_negative_expectations():
    index = json.loads((ROOT / "fixtures/plan5/index.json").read_text())
    schemas, negatives = set(), 0
    for row in index["entries"]:
        path = ROOT / row["path"]
        assert path.resolve().is_relative_to(ROOT)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
        assert row["evidence_class"] == "scripted"
        payload = json.loads(path.read_text())
        if row["expected"] == "validation_error":
            with pytest.raises(ValidationError):
                validate(row["schema"], payload)
            negatives += 1
        else:
            validate(row["schema"], payload)
            schemas.add(row["schema"])
    assert schemas == set(PLAN5_REGISTRY)
    assert negatives >= 19


def test_legacy_tool_and_lane_do_not_fit_new_task():
    value = example("TaskSpec/1")
    value["allowed_tool_ids"] = ["lane.set", "cage.shell"]
    with pytest.raises(ValidationError):
        validate("TaskSpec/1", value)
    value = example("AgentTask/1")
    value["lane"] = "NO-CODE"
    with pytest.raises(ValidationError):
        validate("AgentTask/1", value)
