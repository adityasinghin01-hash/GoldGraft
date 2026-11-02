#!/usr/bin/env python3
"""Export deterministic, standalone JSON Schemas from the versioned registry."""

import json
from pathlib import Path

from goldgraft_contracts.registry import REGISTRY

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "contracts/schemas"


def export_schemas(output: Path = OUTPUT) -> None:
    output.mkdir(parents=True, exist_ok=True)
    expected = set()
    for name, model in sorted(REGISTRY.items()):
        filename = f"{name.replace('/', '.')}.json"
        expected.add(filename)
        schema = model.model_json_schema(by_alias=True, mode="validation")
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        schema["$id"] = f"https://goldgraft.dev/schemas/{filename}"
        schema["title"] = name.replace("/", "V")
        (output / filename).write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
    for stale in output.glob("*.json"):
        if stale.name not in expected:
            stale.unlink()


if __name__ == "__main__":
    export_schemas()
    print(f"Exported {len(REGISTRY)} schemas")
