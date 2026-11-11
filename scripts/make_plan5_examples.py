"""Generate labelled, synthetic contract examples, not working service/agent results."""

import copy
import hashlib
import json
import sys
import types
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated, Literal, Union, get_args, get_origin

from goldgraft_contracts.plan5_common import content_digest
from goldgraft_contracts.registry import PLAN5_REGISTRY, validate
from pydantic import AwareDatetime, BaseModel

ROOT = Path(__file__).resolve().parents[1]
BODY = b'<?php /* MIT synthetic fixture only */ echo "sample";'
FILE_DIGEST = hashlib.sha256(BODY).hexdigest()
UTC = "2026-11-10T00:00:00Z"
LATER = "2026-11-11T00:00:00Z"


def d(label):
    return content_digest({"synthetic": label})


COMMON = {
    "case_id": "case-demo",
    "run_id": "run-demo",
    "task_id": "survey-demo",
    "tenant_id": "tenant-demo",
    "requester_id": "person-demo",
    "actor_id": "person-demo",
    "controller_id": "controller-demo",
    "node_id": "source-demo",
    "from_node": "source-demo",
    "to_node": "source-demo",
    "provider_id": "local_folder",
    "account_id": "synthetic-account",
    "environment_id": "synthetic",
    "resource_id": "synthetic-resource",
    "input_digest": content_digest(["fixture:input"]),
    "bundle_digest": d("review-bundle"),
    "review_bundle_digest": d("review-bundle"),
    "reviewed_bundle_digest": d("review-bundle"),
    "plan_digest": d("action-plan"),
    "action_plan_digest": d("action-plan"),
    "sha256": FILE_DIGEST,
    "file_path": "shop.php",
    "relative_path": "shop.php",
    "path": "shop.php",
    "bytes": len(BODY),
    "length": len(BODY),
    "expected_total_bytes": len(BODY),
    "offset": 0,
    "shop_url": "https://shop.example.test/",
    "redirect_url": "https://provider.example.test/authorize",
    "copy_url": "https://goldgraft.example.test/invitation/synthetic",
    "expires_at": LATER,
    "acquisition_expires_at": LATER,
    "deadline": LATER,
    "lease_until": LATER,
    "due_at": "2026-11-10T12:00:00Z",
    "revoked_at": None,
}
EMPTY = {
    "dependencies",
    "depends_on",
    "open_item_ids",
    "unresolved_effect_refs",
    "unknown_effects",
    "compensatable_effects",
    "irreversible_effects",
    "reversible_effects",
    "missing_evidence_refs",
    "pending_external_effect_refs",
    "pending_effect_refs",
    "unsupported_paths",
    "skipped_required",
    "required_actions",
    "limitation_codes",
}


def scalar(annotation, name, metadata):
    metadata = [item for m in metadata for item in getattr(m, "metadata", [m])]
    origin, args = get_origin(annotation), get_args(annotation)
    if origin is Annotated:
        return scalar(args[0], name, list(metadata) + list(args[1:]))
    if origin in (Union, types.UnionType):
        if type(None) in args:
            return None
        return scalar(args[0], name, metadata)
    if origin is Literal:
        return args[0]
    if name in COMMON:
        return COMMON[name]
    if origin is list:
        if name in EMPTY:
            return []
        if name == "expected_schemas":
            return ["RootMap/1"]
        if name == "allowed_tool_ids":
            return ["source.read"]
        if name in {"input_refs", "parent_refs"}:
            return ["fixture:input"]
        return [scalar(args[0], name.removesuffix("s"), [])]
    if origin is dict:
        return {"binding-demo": scalar(args[1], "mapping_value", [])}
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return model_sample(annotation)
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return next(iter(annotation)).value
    if annotation in (datetime, AwareDatetime):
        return UTC
    if annotation is bool:
        return True
    if annotation is int:
        minimum = max(
            [1 if getattr(m, "gt", None) == 0 else getattr(m, "ge", 0) or 0 for m in metadata]
            or [0]
        )
        return minimum
    if annotation is str:
        patterns = [getattr(m, "pattern", "") for m in metadata]
        if any("sha256:" in p for p in patterns):
            return "sha256:" + d(name)
        if any("a-f0-9" in p for p in patterns):
            return d(name)
        if any("public:" in p for p in patterns):
            return "public:synthetic-metric"
        return "fixture:" + name
    raise TypeError((annotation, name))


def model_sample(model):
    name = model.__name__
    value = {}
    for key, field in model.model_fields.items():
        value[field.alias or key] = scalar(field.annotation, key, field.metadata)
    if name in {"TaskSpec", "TaskContext"}:
        value.update(
            role="Surveyor",
            operation="survey",
            expected_schemas=["RootMap/1"],
            allowed_tool_ids=["source.read"],
        )
    if name == "AgentTask":
        value.update(lease_epoch=0, lease_owner=None, lease_until=None, output_refs=[])
    if name == "SourceRevision":
        value.update(kind="capture", value="synthetic-capture")
    if name == "SourceSnapshot":
        value.update(source_kind="local_folder")
    if name == "ManifestEntry":
        value["sha256"] = FILE_DIGEST
    if name == "ResourceBinding":
        value["recipients"] = [
            {"principal_id": "person-demo", "role": "requester"},
            {"principal_id": "controller-demo", "role": "controller"},
        ]
    if name == "ResourceGraph":
        value["graph_digest"] = content_digest(
            {k: v for k, v in value.items() if k != "graph_digest"}
        )
    if name == "ConfigurationEntry":
        value.update(
            name="SYNTHETIC_PUBLIC_MODE", kind="public_value", value="fixture", secret_ref=None
        )
    if name == "ChangeListV2":
        value.update(
            provenance="snapshot",
            branch=None,
            producer={"kind": "agent", "name": "Grafter", "version": "synthetic-contract-example"},
        )
    if name == "ApplyApproval":
        value.update(delivery_route="direct_artifact", source_head=None, source_base=None)
    if name == "TargetReservation":
        value["resource_epochs"] = {content_digest(t): 1 for t in value["target_keys"]}
    if name == "FinalisationPlan":
        value["candidate_change_required"] = False
    if name == "DeliveryDecision":
        value.update(operation="review_evaluate", slot_id=None)
    if name == "WorkerOperation":
        value["observed_digest"] = value["source_manifest_digest"]
    if name == "WakeCondition":
        value["due_at"] = COMMON["due_at"]
    if name == "PublicMetric":
        value["evidence_ref"] = "public:synthetic-metric"
    if name == "P5Problem":
        value.update(type="about:blank", title="Synthetic held example", status=422)
    if name == "ModelBudget":
        value.update(
            target_micro_usd=15000000,
            ceiling_micro_usd=20000000,
            spent_micro_usd=0,
            outstanding_micro_usd=0,
            unknown_micro_usd=0,
        )
    if name == "ArtifactDescriptor":
        payload = (ROOT / "contracts/examples/RootMap.1.json").read_bytes()
        value.update(
            schema="RootMap/1",
            payload_digest=hashlib.sha256(payload).hexdigest(),
            byte_count=len(payload),
            evidence_class="scripted",
        )
    if name == "CreateUploadRequest":
        value["expected_manifest_digest"] = content_digest(value["manifest"])
    return value


NEGATIVES = [
    ("bool_generation", "TaskContext/1", {"generation": True}),
    ("float_generation", "TaskContext/1", {"generation": 1.0}),
    ("naive_time", "TaskContext/1", {"deadline": "2026-11-10T12:00:00"}),
    ("non_utc_time", "TaskContext/1", {"deadline": "2026-11-10T12:00:00+05:30"}),
    ("extra_authority", "TaskContext/1", {"admin": True}),
    ("unknown_role", "TaskContext/1", {"role": "Unregistered"}),
    (
        "mixed_model_form",
        "ModelTurnResult/1",
        {"kind": "final", "final_artifact_ref": "fixture:untrusted-final"},
    ),
    ("empty_completed_output", "AgentResult/1", {"output_refs": []}),
    ("unknown_without_issue", "AgentResult/1", {"outcome": "unknown", "issue": None}),
    ("fake_snapshot_git", "ChangeList/2", {"branch": "fabricated"}),
    ("oci_is_not_tar", "ArtifactBuild/1", {"oci_manifest_digest": d("not-an-oci-string")}),
    ("path_escape", "ManifestEntry/1", {"relative_path": "../outside"}),
    ("absolute_path", "ManifestEntry/1", {"relative_path": "/outside"}),
    (
        "unresolved_reservation_release",
        "TargetReservation/1",
        {"state": "released", "unresolved_effect_refs": ["fixture:unknown-effect"]},
    ),
    ("multiple_exit_restarts", "ExitCheckPlan/1", {"allowed_restart_count": 2}),
    (
        "missing_changed_final_candidate",
        "FinalisationPlan/1",
        {"candidate_change_required": True, "final_candidate_ref": None},
    ),
    (
        "complete_with_deploy",
        "DeliveryDecision/1",
        {"kind": "complete", "operation": "deploy_exact"},
    ),
    (
        "unreserved_micro_cost",
        "ModelBudget/1",
        {"spent_micro_usd": 20000000, "unknown_micro_usd": 1},
    ),
    ("float_micro_cost", "ModelBudget/1", {"spent_micro_usd": 0.5}),
]


def main(check=False):
    output = ROOT / "contracts/examples"
    entries = []
    values = {}

    def emit(path, data):
        if check:
            if not path.is_file() or path.read_bytes() != data:
                raise ValueError(f"generated fixture mismatch: {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    for schema, model in sorted(PLAN5_REGISTRY.items()):
        value = model_sample(model)
        values[schema] = value
        try:
            validate(schema, value)
        except Exception as exc:
            raise ValueError(f"{schema}: {exc}") from exc
        data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
        path = output / (schema.replace("/", ".") + ".json")
        emit(path, data)
        entries.append(
            {
                "schema": schema,
                "path": str(path.relative_to(ROOT)),
                "sha256": hashlib.sha256(data).hexdigest(),
                "evidence_class": "scripted",
                "owner": "SI01",
                "scenario": "strict_schema_example",
                "generator": "make_plan5_examples",
                "expected": "valid",
                "input_refs": [],
                "limitation": (
                    "Synthetic data and provenance; no real authority or behavior qualified"
                ),
            }
        )
    for name, schema, updates in NEGATIVES:
        value = copy.deepcopy(values[schema])
        value.update(updates)
        try:
            validate(schema, value)
        except ValueError:
            pass
        else:
            raise AssertionError(f"negative fixture accepted: {name}")
        data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
        path = ROOT / "fixtures/plan5/negative" / (name + ".json")
        emit(path, data)
        entries.append(
            {
                "schema": schema,
                "path": str(path.relative_to(ROOT)),
                "sha256": hashlib.sha256(data).hexdigest(),
                "evidence_class": "scripted",
                "owner": "SI01",
                "scenario": name,
                "expected": "validation_error",
                "generator": "make_plan5_examples",
                "input_refs": ["fixture:" + schema],
                "limitation": "Deliberately invalid synthetic boundary input",
            }
        )
    index = ROOT / "fixtures/plan5/index.json"
    existing = json.loads(index.read_text()) if index.exists() else {}
    retained = [
        e
        for e in existing.get("entries", [])
        if e.get("generator") != "make_plan5_examples"
        and e.get("scenario") != "strict_schema_example"
    ]
    content = {
        "format": "GoldGraftPlan5FixtureIndex/1",
        "evidence_class": "scripted",
        "entries": entries + retained,
        "frontend_modes": existing.get("frontend_modes", []),
        "limitations": existing.get(
            "limitations",
            ["B1 schema examples only; B2 persistent counterparts and frontend modes not built"],
        ),
    }
    emit(index, (json.dumps(content, indent=2) + "\n").encode())
    legacy_index = ROOT / "fixtures/INDEX.md"
    marker = "\n<!-- PLAN5 GENERATED INDEX START -->"
    prior_index = legacy_index.read_text().split(marker)[0].rstrip() + "\n"
    section = [
        marker,
        "\n\n## Plan5 B1 synthetic boundary fixtures\n\n",
        "These are contract examples and deliberate invalid inputs, not recordings.\n\n",
        "| Path | Schema / expectation | Purpose | Owner | Evidence | Source |\n",
        "|---|---|---|---|---|---|\n",
    ]
    fixture_rows = list(
        {e["path"]: e for e in content["entries"] if e["path"].startswith("fixtures/")}.values()
    )
    fixture_rows.append(
        {"path": "fixtures/plan5/index.json", "schema": "fixture index", "expected": "catalog"}
    )
    for row in sorted(fixture_rows, key=lambda e: e["path"]):
        relative = row["path"].removeprefix("fixtures/")
        section.append(
            f"| [{relative}]({relative}) | {row['schema']} {row['expected']} "
            "| Plan5 boundary validation only | SI01 | S — SYNTHETIC "
            "| https://json-schema.org/draft/2020-12/schema |\n"
        )
    section.append("<!-- PLAN5 GENERATED INDEX END -->\n")
    emit(legacy_index, (prior_index + "".join(section)).encode())
    print(
        f"{'Checked' if check else 'Generated'} {len(PLAN5_REGISTRY)} positive "
        f"and {len(NEGATIVES)} negative synthetic examples"
    )


if __name__ == "__main__":
    main(check="--check" in sys.argv)
