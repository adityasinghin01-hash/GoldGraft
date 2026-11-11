"""Local fixture access shared by stand-ins; never imports a real piece."""

import json
from pathlib import Path

from goldgraft_contracts.registry import REGISTRY, validate

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "fixtures"
PROOF = FIXTURES / "proof/legacy-php-shop"
EXAMPLES = ROOT / "contracts/examples"
SHOP = FIXTURES / "shops/legacy-php-shop"


def read(path: Path):
    return json.loads(path.read_text())


def example(name: str) -> dict:
    schema = name if "/" in name else f"{name}/1"
    if schema not in REGISTRY:
        raise ValueError("unknown versioned fixture schema")
    return read(EXAMPLES / f"{schema.replace('/', '.')}.json")


def boundary(schema: str, path: Path):
    return validate(schema, read(path))


def events(path: Path, schema: str) -> list:
    return [validate(schema, item) for item in read(path)]


def ledger_entries() -> list[dict]:
    return [
        json.loads(line)
        for line in (FIXTURES / "events/demo_graft_events.jsonl").read_text().splitlines()
    ]
