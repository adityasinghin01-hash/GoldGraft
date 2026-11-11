"""Source-driven deterministic Surveyor demo over guarded synthetic ports; no API.

This is executable static analysis, not a local language model or live merchant job.
Only named synthetic evaluation packages are exposed by this developer CLI.
"""

import argparse
import hashlib
import json
from base64 import urlsafe_b64encode
from datetime import UTC, datetime
from pathlib import Path

from goldgraft_contracts.plan5_common import (
    RelativePath,
    canonical_bytes,
    content_digest,
    reject_secret,
)
from goldgraft_contracts.survey import RootMap
from goldgraft_foundation.offline_profile import load_runtime_profile
from pydantic import StrictStr, TypeAdapter

from .evals.surveyor import FLOWS, load_cases
from .roles import surveyor_configuration
from .scheduler import tick
from .source_references import discover_component_gaps
from .surveyor import SurveyInputs, indicators, inspect_inventory


def package_from_sources(*, shop_id, files, stack=None):
    """Construct synthetic custody input from bytes, without reading an answer key."""
    files = TypeAdapter(dict[RelativePath, StrictStr]).validate_python(files)
    if not 1 <= len(files) <= 16 or sum(len(text.encode()) for text in files.values()) > 16384:
        raise ValueError("MISSING_EVIDENCE bounded source package")
    for text in files.values():
        reject_secret(text)
    catalog = json.loads((Path(__file__).parent / "catalogs/surveyor_static.json").read_text())
    manifest = [
        {
            "relative_path": name,
            "file_type": "file",
            "bytes": len(text.encode()),
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
        }
        for name, text in sorted(files.items())
    ]
    gaps = discover_component_gaps(files)
    bundle = {
        "snapshot_ref": "fake:survey-source",
        "omission_ref": "fake:survey-omissions",
        "rule_ref": catalog["catalog_ref"],
        "snapshot": {
            "snapshot_id": "fake:survey-source",
            "case_id": "case-demo",
            "source_kind": "local_folder",
            "source_resource_id": None,
            "provider": {
                "provider_id": "local_folder",
                "account_id": None,
                "adapter_version": "synthetic:source-inventory:1",
            },
            "revision": {"kind": "capture", "value": "synthetic:" + content_digest(manifest)},
            "manifest_digest": content_digest(manifest),
            "file_count": len(manifest),
            "total_bytes": sum(row["bytes"] for row in manifest),
            "captured_at": "2026-11-10T00:00:00Z",
            "omission_manifest_ref": "fake:survey-omissions",
            "authority_binding_refs": ["fake:synthetic-source-scope"],
            "provenance_class": "provider_reported",
            "completeness": "incomplete" if gaps else "complete_for_declared_scope",
        },
        "omissions": {"items": gaps},
        "manifest": manifest,
        "files": dict(files),
        "rules": catalog["rules"],
        "shop_id": shop_id,
        "stack": stack or {"lang": "synthetic", "framework": "none", "versions": {}, "db": "none"},
        "required_lenses": ["code"],
    }
    return SurveyInputs.model_validate(bundle).model_dump(mode="json")


def build_static_inventory(value):
    """Derive code-indicator proposals for any package within the bounded catalog."""
    inputs = SurveyInputs.model_validate(value)
    matches = indicators(inputs)
    seen, points = set(), []
    flows = {flow: [] for flow in FLOWS}
    for match in matches:
        identity = (match["rule_id"], match["file"], match["line"])
        if identity in seen:
            continue
        seen.add(identity)
        location = {"file": match["file"], "line": match["line"]}
        points.append(
            {
                # Same64 digest bits as the previous16 hex digits, encoded
                # compactly. Identity still binds rule/file/line, not ordering.
                "id": "t"
                + urlsafe_b64encode(
                    bytes.fromhex(content_digest(list(identity))[:16])
                ).decode("ascii").rstrip("="),
                "family": match["family"],
                "operation": match["operation"],
                "location": location,
                "lenses": ["code"],
                "confidence": 0.5,
                "live": False,
                "paypal_only": False,
                "target": {"paypal_mapping_id": match["rule_id"], "rest_op": "unqualified"},
            }
        )
        if location not in flows[match["flow"]]:
            flows[match["flow"]].append(location)
    if len({point["id"] for point in points}) != len(points):
        raise ValueError("DENIED ambiguous location identity")
    result = RootMap.model_validate(
        {
            "shop_id": inputs.shop_id,
            "stack": inputs.stack.model_dump(mode="json"),
            "lenses_run": ["code"],
            "touchpoints": points,
            "money_flow": flows,
            "recall_evidence": {"runtime_calls_total": 0, "matched_by_static": 0, "misses": []},
        }
    )
    payload = result.model_dump(mode="json")
    if len(canonical_bytes(payload)) > 4000:
        raise ValueError("MISSING_EVIDENCE inventory exceeds output capacity")
    return payload


def main(argv=None):
    cases = {case["id"]: case for case in load_cases()}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=sorted(cases), required=True)
    parser.add_argument("--state-file", type=Path, required=True)
    args = parser.parse_args(argv)
    case = cases[args.case]
    try:
        # Only files and declared shop identity enter analysis, never expected answers.
        package = package_from_sources(shop_id=case["shop_id"], files=case["files"])
        draft = build_static_inventory(package)
        configuration = dict(surveyor_configuration(), offline_final_payload=draft)
        ports = load_runtime_profile(
            "offline",
            args.state_file,
            fixture="surveyor_inventory",
            configuration=configuration,
            inputs=package,
            clock=lambda: datetime.now(UTC),
        )
        tick("fake:runtime-run", ports.clock(), ports)
        task = ports.control.snapshot("fake:runtime-run").tasks[0]
        result = ports.control.result("survey")
        if task.state != "succeeded":
            print(
                json.dumps(
                    {
                        "mode": "deterministic_offline",
                        "model_api_calls": 0,
                        "omissions": package["omissions"],
                        "result": result.model_dump(mode="json"),
                    }
                )
            )
            return 1
        descriptor, payload = ports.artifacts.inspect_output(task, ports.context_for("survey"))
        print(
            json.dumps(
                {
                    "mode": "deterministic_offline",
                    "model_api_calls": 0,
                    "real_model_evaluation": "NOT RUN",
                    "inventory": payload,
                    "result": result.model_dump(mode="json"),
                    "inspection": inspect_inventory(
                        payload,
                        input_refs=task.task.input_refs,
                        output_ref=descriptor.ref,
                        subject=descriptor.subject_digest,
                        evidence_refs=result.evidence_refs,
                        omissions=package["omissions"],
                    ),
                },
                indent=2,
            )
        )
        return 0
    except (ValueError, TypeError):
        print(json.dumps({"error": "DENIED_OR_MISSING_EVIDENCE", "model_api_calls": 0}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
