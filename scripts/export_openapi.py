"""Write the API contract to contracts/api/openapi.json (deterministic)."""

import json
from pathlib import Path

from goldgraft_fakes.api import create_app

OUT = Path(__file__).resolve().parents[1] / "contracts" / "api" / "openapi.json"


def main():
    spec = create_app().openapi()
    spec["info"]["title"] = "GoldGraft control-plane API"
    spec["info"]["description"] = (
        "Contract for the real backend and the stand-in. Source of truth: "
        "contracts/src/goldgraft_contracts/api_routes.py. Errors are RFC 7807 problem+json; "
        "writes need an Idempotency-Key header.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(spec, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Exported OpenAPI with {len(spec['paths'])} paths")


if __name__ == "__main__":
    main()
