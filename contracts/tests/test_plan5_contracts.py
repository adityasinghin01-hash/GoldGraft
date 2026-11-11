"""B1 tests shared executable boundaries, never agent implementation or live services."""

import copy
import json
from pathlib import Path

import pytest
from goldgraft_contracts.registry import REGISTRY, validate
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = {
    "ResourceGraph/1",
    "ResourceBinding/1",
    "AdapterCapabilities/1",
    "AdapterObservation/1",
    "SourceSnapshot/1",
    "UploadSession/1",
    "WorkPackage/1",
    "ComponentManifest/1",
    "DependencyManifest/1",
    "ConfigurationManifest/1",
    "RequiredFlowManifest/1",
    "OmissionManifest/1",
    "UnresolvedInputs/1",
    "ConnectionCase/1",
    "ConnectionReadiness/1",
    "ActionIntent/1",
    "WorkAcceptance/1",
    "WorkStatus/1",
    "WorkCancellation/1",
    "WorkerOperation/1",
    "LifecycleRun/1",
    "LifecycleWorkRequest/1",
    "LifecycleWorkResult/1",
    "ReviewBundle/1",
    "ApplyApproval/1",
    "EffectIntent/1",
    "BaselineEvidence/1",
    "DeploymentObservation/1",
    "RecoveryPlan/1",
    "ExitManifest/1",
    "TargetReservation/1",
    "ActionPlan/1",
    "ApplyAuthority/1",
    "ApprovalSet/1",
    "StateCutover/1",
    "ArtifactBuild/1",
    "AssetManifest/1",
    "FinalisationPlan/1",
    "ExitCheckPlan/1",
    "ChangeList/2",
    "ArtifactDescriptor/1",
    "SubjectManifest/1",
    "SubjectDerivation/1",
    "TaskContext/1",
    "PlanProposal/1",
    "AgentTask/1",
    "TaskLease/1",
    "TaskCheckpoint/1",
    "AgentResult/1",
    "ExecutionProposal/1",
    "ModelTurnRequest/1",
    "ModelTurnResult/1",
    "ModelTurnStatus/1",
    "ToolInvocation/1",
    "TaskEvent/1",
    "RunTaskSnapshot/1",
    "WakeCondition/1",
    "DeliverySnapshot/1",
    "DeliveryDecision/1",
    "ResolvedDeliveryView/1",
    "LifecycleWorkRequestReceipt/1",
    "PendingResult/1",
    "ActionStatusView/1",
    "ProcessingDisclosure/1",
    "CaseView/1",
    "CaseList/1",
    "DraftCase/1",
    "ProviderIntent/1",
    "ControllerInvitation/1",
    "CaseEvent/1",
    "PrivateReviewView/1",
    "PublicProofView/1",
    "ChunkReceipt/1",
    "P5Problem/1",
}


def example(schema):
    return json.loads(
        (ROOT / "contracts/examples" / (schema.replace("/", ".") + ".json")).read_text()
    )


def test_required_bootstrap_inventory():
    assert REQUIRED <= REGISTRY.keys()


@pytest.mark.parametrize("schema", sorted(REQUIRED))
def test_record_roundtrip_and_unknown_field(schema):
    value = example(schema)
    result = validate(schema, value)
    validate(schema, json.loads(result.model_dump_json()))
    with pytest.raises(ValidationError):
        validate(schema, {**value, "authority_override": True})


@pytest.mark.parametrize(
    "field,bad",
    [
        ("generation", True),
        ("generation", 1.0),
        ("generation", "1"),
        ("expected_subject", "x" * 64),
        ("deadline", "2026-11-10T00:00:00"),
        ("deadline", "2026-11-10T05:30:00+05:30"),
        ("deadline", 1),
    ],
)
def test_strict_types_and_utc(field, bad):
    value = example("TaskContext/1")
    value[field] = bad
    with pytest.raises(ValidationError):
        validate("TaskContext/1", value)


@pytest.mark.parametrize(
    "schema,updates",
    [
        (
            "ModelTurnResult/1",
            {
                "kind": "final",
                "calls": [
                    {
                        "call_id": "a",
                        "tool": "status.read",
                        "arguments_ref": "args:a",
                        "arguments_digest": "a" * 64,
                    }
                ],
            },
        ),
        ("AgentResult/1", {"outcome": "completed", "output_refs": []}),
        ("AgentResult/1", {"outcome": "unknown", "issue": None}),
        ("WorkStatus/1", {"state": "operation_started", "work_id": None, "generation": None}),
        ("ChangeList/2", {"provenance": "snapshot", "branch": "fake-git"}),
        ("ChangeList/2", {"provenance": "git", "branch": None}),
        ("FinalisationPlan/1", {"candidate_change_required": True, "final_candidate_ref": None}),
        ("ExitCheckPlan/1", {"allowed_restart_count": 2}),
        (
            "TargetReservation/1",
            {"state": "released", "unresolved_effect_refs": ["effect:unknown"]},
        ),
        ("DeliveryDecision/1", {"kind": "complete", "operation": "deploy_exact"}),
        ("ArtifactBuild/1", {"oci_manifest_digest": "a" * 64}),
        ("ManifestEntry/1", {"relative_path": "../outside"}),
        ("ManifestEntry/1", {"relative_path": "C:/outside"}),
        (
            "ConfigurationManifest/1",
            {
                "entries": [
                    {
                        "name": "paypal_client_secret",
                        "kind": "public_value",
                        "value": "do-not-store",
                        "secret_ref": None,
                        "required": True,
                        "evidence_refs": [],
                    }
                ]
            },
        ),
    ],
)
def test_conditional_safety_fields(schema, updates):
    value = example(schema)
    value.update(copy.deepcopy(updates))
    with pytest.raises(ValidationError):
        validate(schema, value)


def test_task_and_effect_dags_reject_cycles_and_duplicates():
    for schema, key, id_field, dependency_field in [
        ("PlanProposal/1", "tasks", "task_id", "dependencies"),
        ("ActionPlan/1", "slots", "slot_id", "depends_on"),
    ]:
        value = example(schema)
        item = value[key][0]
        item[dependency_field] = [item[id_field]]
        with pytest.raises(ValidationError):
            validate(schema, value)
        value = example(schema)
        value[key].append(copy.deepcopy(value[key][0]))
        with pytest.raises(ValidationError):
            validate(schema, value)


@pytest.mark.parametrize(
    "schema,updates",
    [
        ("ModelTurnResult/1", {"kind": "final", "final_artifact_ref": "fixture:final"}),
        ("AgentResult/1", {"output_refs": []}),
        ("ChangeList/2", {"branch": "fake-git"}),
        ("WorkStatus/1", {"state": "operation_started", "work_id": None, "generation": None}),
        ("DeliveryDecision/1", {"kind": "complete", "operation": "deploy_exact"}),
        ("ManifestEntry/1", {"sha256": None}),
    ],
)
def test_exported_schema_denies_conditional_forms(schema, updates):
    from jsonschema import Draft202012Validator

    value = example(schema)
    value.update(updates)
    assert not Draft202012Validator(REGISTRY[schema].model_json_schema(by_alias=True)).is_valid(
        value
    )
