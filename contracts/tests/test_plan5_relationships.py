"""Valid JSON with wrong ownership, bytes or relationships must still be denied."""

import copy
import hashlib
import json
from datetime import UTC
from pathlib import Path

import pytest
from goldgraft_contracts.registry import validate
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]


def example(name):
    return json.loads(
        (ROOT / "contracts/examples" / (name.replace("/", ".") + ".json")).read_text()
    )


def test_authenticated_artifact_bytes_case_subject_and_owner():
    from goldgraft_contracts.plan5_validation import ArtifactBinding, validate_artifact

    payload = (ROOT / "contracts/examples/ChangeList.2.json").read_bytes()
    descriptor = example("ArtifactDescriptor/1")
    descriptor.update(
        schema="ChangeList/2",
        payload_digest=hashlib.sha256(payload).hexdigest(),
        byte_count=len(payload),
        producer_identity_ref="identity:grafter",
        trust="model_proposal",
    )
    binding = ArtifactBinding(
        tenant_id="tenant-demo",
        case_id=descriptor["case_id"],
        run_id=descriptor["run_id"],
        generation=descriptor["generation"],
        subject_digest=descriptor["subject_digest"],
        input_digest=descriptor["input_digest"],
        schema="ChangeList/2",
        producer_identity_ref="identity:grafter",
        producer_role="Grafter",
        allowed_trust=frozenset({"model_proposal"}),
    )
    d = validate("ArtifactDescriptor/1", descriptor)
    result = validate_artifact(
        d,
        payload,
        binding,
        authenticated_tenant="tenant-demo",
        authenticated_producer="identity:grafter",
    )
    assert result.provenance == "snapshot"
    for key, bad in [
        ("case_id", "another-case"),
        ("run_id", "another-run"),
        ("generation", 2),
        ("subject_digest", "f" * 64),
        ("input_digest", "e" * 64),
        ("producer_identity_ref", "identity:scribe"),
        ("trust", "collector_observed"),
    ]:
        changed = dict(descriptor, **{key: bad})
        with pytest.raises(ValueError):
            validate_artifact(
                validate("ArtifactDescriptor/1", changed),
                payload,
                binding,
                authenticated_tenant="tenant-demo",
                authenticated_producer="identity:grafter",
            )
    with pytest.raises(ValueError):
        validate_artifact(
            d,
            payload + b" ",
            binding,
            authenticated_tenant="tenant-demo",
            authenticated_producer="identity:grafter",
        )
    with pytest.raises(ValueError):
        validate_artifact(
            d,
            payload,
            binding,
            authenticated_tenant="other-tenant",
            authenticated_producer="identity:grafter",
        )


def test_closed_tool_catalog_blocks_legacy_and_wrong_role():
    from goldgraft_contracts.plan5_tools import validate_tool_arguments

    value = {"snapshot_ref": "fixture:source", "path": "checkout.php", "max_bytes": 4096}
    assert validate_tool_arguments("Surveyor", "source.read", value).path == "checkout.php"
    for role, tool, args in [
        ("Surveyor", "repo.read", value),
        ("Herald", "source.read", value),
        ("Surveyor", "source.read", dict(value, path="../secret")),
        ("Surveyor", "source.read", dict(value, max_bytes=True)),
        ("Surveyor", "source.read", dict(value, url="http://169.254.169.254")),
    ]:
        with pytest.raises(ValueError):
            validate_tool_arguments(role, tool, args)


def test_manifest_chunk_coverage_and_same_content_replay():
    from goldgraft_contracts.plan5_validation import validate_chunk_coverage

    body = b"licensed synthetic source"
    manifest = [
        {
            "relative_path": "shop.php",
            "file_type": "file",
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        }
    ]
    chunks = [
        {
            "upload_id": "u",
            "file_path": "shop.php",
            "offset": 0,
            "length": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "blob_ref": "blob:1",
        }
    ]
    assert (
        validate_chunk_coverage(manifest, chunks + chunks, {"blob:1": body}, upload_id="u")
        == hashlib.sha256(body).hexdigest()
    )
    for bad_chunks, blobs in [
        (chunks, {"blob:1": b"wrong"}),
        ([dict(chunks[0], offset=1)], {"blob:1": body}),
        ([dict(chunks[0], upload_id="other")], {"blob:1": body}),
        ([dict(chunks[0], file_path="../escape")], {"blob:1": body}),
    ]:
        with pytest.raises(ValueError):
            validate_chunk_coverage(manifest, bad_chunks, blobs, upload_id="u")


def test_draft_claim_needs_session_capability_continuation_and_same_owner():
    from datetime import datetime

    from goldgraft_contracts.plan5_validation import validate_draft_claim

    draft = validate("DraftCase/1", example("DraftCase/1"))
    args = dict(
        draft=draft,
        principal_id="person-demo",
        capability=b"local-cookie-only",
        expected_capability_digest=hashlib.sha256(b"local-cookie-only").hexdigest(),
        continuation_ref=draft.continuation_ref,
        now=datetime(2026, 11, 10, 12, 0, tzinfo=UTC),
        original_requester=None,
    )
    assert validate_draft_claim(**args) == draft.draft_id
    for updates in [
        {"principal_id": None},
        {"capability": None},
        {"continuation_ref": "wrong"},
        {"original_requester": "other-person"},
        {"now": draft.expires_at},
    ]:
        with pytest.raises(ValueError):
            validate_draft_claim(**dict(args, **updates))


def test_wrong_role_task_and_future_subject_drift_denied():
    value = example("PlanProposal/1")
    for updates in [
        {"role": "Herald"},
        {"operation": "deploy_exact"},
        {"allowed_tool_ids": ["repo.write"]},
        {"expected_schemas": ["ChangeList/2"]},
    ]:
        changed = copy.deepcopy(value)
        changed["tasks"][0].update(updates)
        with pytest.raises(ValidationError):
            validate("PlanProposal/1", changed)


def test_required_manifest_paths_cannot_alias_or_exceed_bytes():
    value = example("CreateUploadRequest/1")
    for changes in [
        {"expected_total_bytes": value["expected_total_bytes"] + 1},
        {"manifest": value["manifest"] + value["manifest"]},
    ]:
        with pytest.raises(ValidationError):
            validate("CreateUploadRequest/1", dict(value, **changes))


@pytest.mark.parametrize("bad", [True, 1.5, "1", -1])
def test_model_cost_is_integer_micro_usd(bad):
    value = example("ModelBudget/1")
    value["spent_micro_usd"] = bad
    with pytest.raises(ValidationError):
        validate("ModelBudget/1", value)


def test_unknown_spend_stays_inside_cumulative_cap():
    value = example("ModelBudget/1")
    value.update(spent_micro_usd=19000000, unknown_micro_usd=1000000, outstanding_micro_usd=1)
    with pytest.raises(ValidationError):
        validate("ModelBudget/1", value)


def test_required_package_scope_cannot_shrink_or_hide_missing_backend():
    from datetime import UTC, datetime

    from goldgraft_contracts.plan5_validation import validate_work_package

    package = validate("WorkPackage/1", example("WorkPackage/1"))
    graph = validate("ResourceGraph/1", example("ResourceGraph/1"))
    p = package.model_dump(mode="json")
    p["resource_graph_digest"] = graph.graph_digest
    package = validate("WorkPackage/1", p)
    snapshot = validate("SourceSnapshot/1", example("SourceSnapshot/1"))
    components = example("ComponentManifest/1")
    components["components"][0]["source_snapshot_ref"] = package.source_snapshot_refs[0]
    components = validate("ComponentManifest/1", components)
    flows = validate("RequiredFlowManifest/1", example("RequiredFlowManifest/1"))
    args = dict(
        graph=graph,
        snapshots={ref: snapshot for ref in package.source_snapshot_refs},
        components=components,
        flows=flows,
        omissions=validate("OmissionManifest/1", {"items": []}),
        unresolved=validate("UnresolvedInputs/1", {"items": []}),
        required_node_ids={graph.nodes[0].node_id},
        required_flow_ids={flows.flows[0].flow_id},
        qualified_recipe_refs=set(package.state_recipe_refs),
        now=datetime(2026, 11, 10, 12, tzinfo=UTC),
    )
    assert validate_work_package(package, **args) == package
    for changes in [
        {"required_node_ids": {"missing-backend"}},
        {"qualified_recipe_refs": set()},
        {"now": package.acquisition_expires_at},
        {"snapshots": {}},
        {"unresolved": validate("UnresolvedInputs/1", {"items": [example("Issue/1")]})},
    ]:
        with pytest.raises(ValueError):
            validate_work_package(package, **dict(args, **changes))
    changed = flows.model_copy(deep=True)
    changed.flows[0].required = False
    with pytest.raises(ValueError):
        validate_work_package(package, **dict(args, flows=changed))


def test_exact_approval_authority_expiry_and_epoch_binding():
    from datetime import UTC, datetime

    from goldgraft_contracts.plan5_common import content_digest
    from goldgraft_contracts.plan5_validation import validate_approval_set

    plan = example("ActionPlan/1")
    plan["plan_digest"] = content_digest({k: v for k, v in plan.items() if k != "plan_digest"})
    plan = validate("ActionPlan/1", plan)
    slot = plan.slots[0]
    authority = example("ApplyAuthority/1")
    authority["controller_id"] = slot.required_controller_ids[0]
    authority = validate("ApplyAuthority/1", authority)
    approval = example("ApplyApproval/1")
    approval.update(
        controller_id=authority.controller_id,
        action_plan_digest=plan.plan_digest,
        target_resources=[slot.target_key.resource_id],
        authority_refs=slot.required_authority_refs,
        authority_binding_epochs={authority.authority_id: authority.grant_epoch},
        trigger_chain_digest=slot.trigger_digest,
    )
    approval = validate("ApplyApproval/1", approval)
    aset = example("ApprovalSet/1")
    aset.update(
        plan_digest=plan.plan_digest,
        required_controller_ids=slot.required_controller_ids,
        authority_epochs={authority.authority_id: authority.grant_epoch},
    )
    aset = validate("ApprovalSet/1", aset)
    args = dict(
        approvals={aset.approval_refs[0]: approval},
        authorities={slot.required_authority_refs[0]: authority},
        now=datetime(2026, 11, 10, 12, tzinfo=UTC),
    )
    assert validate_approval_set(plan, aset, **args) == aset
    for key, bad in [
        ("controller_id", "other"),
        ("action_plan_digest", "f" * 64),
        ("artifact_digest", "sha256:" + "f" * 64),
        ("authority_binding_epochs", {authority.authority_id: 99}),
        ("expires_at", "2026-11-10T01:00:00Z"),
        ("trigger_chain_digest", "f" * 64),
    ]:
        raw = approval.model_dump(mode="json")
        raw[key] = bad
        altered = validate("ApplyApproval/1", raw)
        # Exact image comparison uses an image-bearing slot.
        checked_plan = plan
        if key == "artifact_digest":
            raw_plan = plan.model_dump(mode="json")
            raw_plan["slots"][0]["artifact_digest"] = approval.artifact_digest
            from goldgraft_contracts.plan5_common import content_digest

            raw_plan["plan_digest"] = content_digest(
                {k: v for k, v in raw_plan.items() if k != "plan_digest"}
            )
            checked_plan = validate("ActionPlan/1", raw_plan)
            raw["action_plan_digest"] = checked_plan.plan_digest
            altered = validate("ApplyApproval/1", raw)
        altered_set = aset.model_copy(update={"plan_digest": checked_plan.plan_digest})
        with pytest.raises(ValueError):
            validate_approval_set(
                checked_plan, altered_set, **dict(args, approvals={aset.approval_refs[0]: altered})
            )

    # A valid authority must not mask another unresolved required authority.
    raw_plan = plan.model_dump(mode="json")
    raw_plan["slots"][0]["required_authority_refs"].append("authority:required-second")
    raw_plan["plan_digest"] = content_digest(
        {k: v for k, v in raw_plan.items() if k != "plan_digest"}
    )
    expanded_plan = validate("ActionPlan/1", raw_plan)
    expanded_set = aset.model_copy(update={"plan_digest": expanded_plan.plan_digest})
    rebound = approval.model_copy(update={"action_plan_digest": expanded_plan.plan_digest})
    with pytest.raises(ValueError):
        validate_approval_set(
            expanded_plan, expanded_set, **dict(args, approvals={aset.approval_refs[0]: rebound})
        )

    # Two actual controllers must independently cover their respective authorities.
    host_authority = authority.model_copy(
        update={"authority_id": "host-authority", "controller_id": "host-controller"}
    )
    raw_plan["slots"][0]["required_controller_ids"].append("host-controller")
    raw_plan["plan_digest"] = content_digest(
        {k: v for k, v in raw_plan.items() if k != "plan_digest"}
    )
    split_plan = validate("ActionPlan/1", raw_plan)
    split_set = aset.model_copy(
        update={
            "plan_digest": split_plan.plan_digest,
            "required_controller_ids": [authority.controller_id, "host-controller"],
            "approval_refs": [aset.approval_refs[0], "approval:host"],
            "authority_epochs": {
                authority.authority_id: authority.grant_epoch,
                "host-authority": 1,
            },
        }
    )
    owner_approval = approval.model_copy(update={"action_plan_digest": split_plan.plan_digest})
    host_approval = owner_approval.model_copy(
        update={
            "controller_id": "host-controller",
            "authority_refs": ["authority:required-second"],
            "authority_binding_epochs": {"host-authority": 1},
        }
    )
    split_args = dict(
        args,
        approvals={aset.approval_refs[0]: owner_approval, "approval:host": host_approval},
        authorities={
            slot.required_authority_refs[0]: authority,
            "authority:required-second": host_authority,
        },
    )
    assert validate_approval_set(split_plan, split_set, **split_args) == split_set
    with pytest.raises(ValueError):
        validate_approval_set(
            split_plan,
            split_set,
            **dict(split_args, approvals={aset.approval_refs[0]: owner_approval}),
        )


def test_lineage_requires_collector_and_exact_parent_inputs():
    from goldgraft_contracts.plan5_common import content_digest
    from goldgraft_contracts.plan5_validation import validate_subject_lineage

    task = example("AgentTask/1")
    task["task"].update(
        role="Grafter",
        operation="candidate_patch",
        expected_schemas=["ChangeList/2"],
        allowed_tool_ids=["candidate.patch"],
        output_subject_policy="candidate_child",
    )
    task = validate("AgentTask/1", task)
    manifest = validate("SubjectManifest/1", example("SubjectManifest/1"))
    descriptor = example("ArtifactDescriptor/1")
    descriptor.update(
        input_digest=task.input_digest,
        subject_digest=content_digest(manifest),
        derivation_ref="fixture:derivation",
    )
    descriptor = validate("ArtifactDescriptor/1", descriptor)
    derivation = example("SubjectDerivation/1")
    derivation.update(
        task_id=task.task.task_id,
        parent_refs=task.task.input_refs,
        parent_subject=task.task.expected_subject,
        output_refs=[descriptor.ref],
        output_subject=descriptor.subject_digest,
    )
    derivation = validate("SubjectDerivation/1", derivation)
    args = dict(
        derivation=derivation,
        derivation_ref="fixture:derivation",
        authenticated_collector=derivation.collector_identity_ref,
    )
    validate_subject_lineage(task, descriptor, manifest, **args)
    for update in [
        {"derivation": None},
        {"authenticated_collector": "forged"},
        {"derivation": derivation.model_copy(update={"parent_refs": ["wrong"]})},
        {"derivation": derivation.model_copy(update={"task_id": "other"})},
    ]:
        with pytest.raises(ValueError):
            validate_subject_lineage(task, descriptor, manifest, **dict(args, **update))


def test_incremental_plan_admission_resolves_existing_dependencies():
    from goldgraft_contracts.plan5_validation import validate_plan_admission

    snapshot = validate("RunTaskSnapshot/1", example("RunTaskSnapshot/1"))
    proposal = example("PlanProposal/1")
    proposal["tasks"][0].update(
        task_id="herald-next",
        output_slot="herald-text",
        role="Herald",
        operation="explain_status",
        allowed_tool_ids=["status.read"],
        expected_schemas=["HeraldText/1"],
        dependencies=[snapshot.tasks[0].task.task_id],
    )
    extension = validate("PlanProposal/1", proposal)
    assert (
        validate_plan_admission(extension, existing=snapshot, required_task_ids=set()) == extension
    )
    with pytest.raises(ValueError):
        validate_plan_admission(extension, existing=None, required_task_ids=set())
    with pytest.raises(ValueError):
        validate_plan_admission(
            extension, existing=snapshot, required_task_ids={"absent-required-task"}
        )
    proposal["tasks"][0]["dependencies"] = ["missing-task"]
    with pytest.raises(ValueError):
        validate_plan_admission(
            validate("PlanProposal/1", proposal), existing=snapshot, required_task_ids=set()
        )
