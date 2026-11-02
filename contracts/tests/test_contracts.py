import json
from pathlib import Path

import pytest
from goldgraft_contracts.registry import REGISTRY, validate
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "contracts/examples"


@pytest.mark.parametrize("name", sorted(REGISTRY))
def test_example_and_extra_field(name):
    payload = json.loads((EXAMPLES / f"{name.replace('/', '.')}.json").read_text())
    result = validate(name, payload)
    assert isinstance(result, REGISTRY[name])
    with pytest.raises(ValidationError):
        validate(name, {**payload, "unexpected": True})


def test_unknown_schema():
    with pytest.raises(ValueError, match="Unknown schema"):
        validate("Missing/1", {})
