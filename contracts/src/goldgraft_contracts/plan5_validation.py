"""Pure accepting-boundary checks over authenticated inputs; no custody/backend engine.

GU must supply current authenticated tenancy/identity/authority and resolved bytes.
These checks never authenticate a provider, issue a grant, persist a claim, or run effects.
"""

import hashlib
import hmac
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime

from .agent_runtime import (
    AgentTask,
    ArtifactDescriptor,
    ControlError,
    ControlFailure,
    SubjectDerivation,
    SubjectManifest,
)
from .connection_control import CreateUploadRequest, DraftCase
from .plan5_common import content_digest
from .plan5_tools import ROLE_OUTPUTS
from .registry import validate
from .work_package import Chunk, ManifestEntry


def validate_plan_admission(proposal, *, existing, required_task_ids: set[str]):
    """Validate the whole accumulated immutable DAG before GU's seed/extend CAS."""
    from .plan5_common import unique, validate_dag

    prior = []
    if existing is not None:
        if (existing.case_id, existing.run_id, existing.generation) != (
            proposal.case_id,
            proposal.run_id,
            proposal.generation,
        ) or existing.cancellation_ref is not None:
            raise ValueError("stale/cancelled plan extension")
        prior = [t.task for t in existing.tasks]
    tasks = prior + list(proposal.tasks)
    validate_dag(tasks, "task_id", "dependencies")
    unique([t.output_slot for t in tasks], "accumulated output slots")
    required = {t.task_id for t in tasks if t.required}
    if not required_task_ids <= required:
        raise ValueError("required tasks cannot be omitted or made optional")
    return proposal


def validate_service_payload(schema: str, payload: object):
    """Service adapters use this instead of serializing raw Pydantic input errors."""
    try:
        return validate(schema, payload)
    except (ValueError, TypeError):
        raise ControlFailure(
            ControlError(code="INVALID", retry_class="none", evidence_refs=[])
        ) from None


@dataclass(frozen=True)
class ArtifactBinding:
    tenant_id: str
    case_id: str
    run_id: str
    generation: int
    subject_digest: str
    input_digest: str
    schema: str
    producer_identity_ref: str
    producer_role: str
    allowed_trust: frozenset[str]


def _strict_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON object key")
        value[key] = item
    return value


def validate_artifact(
    descriptor: ArtifactDescriptor,
    payload: bytes,
    binding: ArtifactBinding,
    *,
    authenticated_tenant: str,
    authenticated_producer: str,
    now: datetime | None = None,
    validation_context: dict | None = None,
):
    if (
        authenticated_tenant != binding.tenant_id
        or authenticated_producer != binding.producer_identity_ref
    ):
        raise ValueError("authenticated tenant/producer mismatch")
    for attr in [
        "case_id",
        "run_id",
        "generation",
        "subject_digest",
        "input_digest",
        "producer_identity_ref",
    ]:
        if getattr(descriptor, attr) != getattr(binding, attr):
            raise ValueError("artifact identity/subject/input mismatch")
    if descriptor.schema_id != binding.schema or descriptor.trust not in binding.allowed_trust:
        raise ValueError("artifact schema/trust mismatch")
    now = datetime.now(UTC) if now is None else now
    if descriptor.expires_at is not None and now >= descriptor.expires_at:
        raise ValueError("artifact custody expired")
    if (
        len(payload) != descriptor.byte_count
        or hashlib.sha256(payload).hexdigest() != descriptor.payload_digest
    ):
        raise ValueError("artifact byte count/hash mismatch")
    observed_only = {
        "ArtifactBuild/1",
        "RawCapture/1",
        "RunnableShop/1",
        "Driver/1",
        "SubjectDerivation/1",
        "WorkerOperation/1",
        "BaselineEvidence/1",
        "DeploymentObservation/1",
        "ExitManifest/1",
    }
    if descriptor.schema_id in observed_only and descriptor.trust != "collector_observed":
        raise ValueError("model cannot issue observed records")
    if descriptor.trust == "model_proposal" and binding.schema not in ROLE_OUTPUTS.get(
        binding.producer_role, frozenset()
    ):
        raise ValueError("output schema not owned by authenticated role")

    def reject_constant(value):
        raise ValueError("nonfinite JSON constant forbidden")

    decoded = json.loads(payload, object_pairs_hook=_strict_object, parse_constant=reject_constant)
    # Context is resolved by the trusted accepting boundary, never taken from payload JSON.
    result = validate(binding.schema, decoded, context=validation_context)
    producer = getattr(result, "producer", None)
    if producer is not None and (
        producer.name != binding.producer_role or producer.kind.value != "agent"
    ):
        raise ValueError("payload cannot choose output producer")
    return result


def validate_subject_lineage(
    task: AgentTask,
    descriptor: ArtifactDescriptor,
    manifest: SubjectManifest,
    *,
    derivation: SubjectDerivation | None,
    derivation_ref: str | None,
    authenticated_collector: str | None,
):
    if descriptor.subject_digest != content_digest(manifest):
        raise ValueError("subject manifest bytes/hash mismatch")
    if (descriptor.case_id, descriptor.run_id, descriptor.generation, descriptor.input_digest) != (
        task.case_id,
        task.run_id,
        task.generation,
        task.input_digest,
    ):
        raise ValueError("output binding mismatch")
    if task.task.output_subject_policy == "same_subject":
        if (
            descriptor.subject_digest != task.task.expected_subject
            or descriptor.derivation_ref is not None
            or derivation is not None
        ):
            raise ValueError("same-subject task cannot change subject")
        return
    if derivation is None or not derivation_ref or descriptor.derivation_ref != derivation_ref:
        raise ValueError("transform requires resolved derivation")
    expected_operation = {
        "candidate_child": "candidate_patch",
        "build_from_source": "artifact_build",
        "derived_evidence": "evidence_derivation",
    }[task.task.output_subject_policy]
    if (
        derivation.operation != expected_operation
        or derivation.collector_identity_ref != authenticated_collector
        or derivation.parent_refs != task.task.input_refs
        or derivation.parent_subject != task.task.expected_subject
        or derivation.output_subject != descriptor.subject_digest
        or descriptor.ref not in derivation.output_refs
        or derivation.task_id != task.task.task_id
        or (derivation.case_id, derivation.run_id, derivation.generation)
        != (task.case_id, task.run_id, task.generation)
    ):
        raise ValueError("collector lineage does not bind exact accepted inputs/output")


def validate_chunk_coverage(
    manifest: list, chunks: list, blobs: Mapping[str, bytes], *, upload_id: str
) -> str:
    entries = [ManifestEntry.model_validate(x) for x in manifest]
    request = CreateUploadRequest(
        manifest=entries,
        expected_manifest_digest=content_digest([e.model_dump(mode="json") for e in entries]),
        expected_total_bytes=sum(e.bytes for e in entries),
        binding_epochs={"validated-caller": 1},
    )
    if len(chunks) > 100000:
        raise ValueError("chunk count exceeds bounded validation profile")
    files = {e.relative_path: e for e in request.manifest if e.file_type == "file"}
    ranges = {name: {} for name in files}
    for raw in chunks:
        chunk = Chunk.model_validate(raw)
        if chunk.upload_id != upload_id or chunk.file_path not in files:
            raise ValueError("chunk outside current upload/manifest")
        body = blobs.get(chunk.blob_ref)
        if (
            not isinstance(body, bytes)
            or len(body) != chunk.length
            or hashlib.sha256(body).hexdigest() != chunk.sha256
        ):
            raise ValueError("chunk byte/digest mismatch")
        identity = (chunk.length, chunk.sha256)
        previous = ranges[chunk.file_path].get(chunk.offset)
        if previous is not None and previous[0] != identity:
            raise ValueError("conflicting duplicate chunk")
        ranges[chunk.file_path][chunk.offset] = (identity, body)
    combined = hashlib.sha256()
    for name, entry in sorted(files.items()):
        offset = 0
        file_hash = hashlib.sha256()
        for start, ((length, _digest), body) in sorted(ranges[name].items()):
            if start != offset:
                raise ValueError("chunk coverage gap/overlap")
            file_hash.update(body)
            combined.update(body)
            offset += length
        if offset != entry.bytes or file_hash.hexdigest() != entry.sha256:
            raise ValueError("incomplete file coverage/content mismatch")
    return combined.hexdigest()


def validate_draft_claim(
    *,
    draft: DraftCase,
    principal_id: str | None,
    capability: bytes | None,
    expected_capability_digest: str,
    continuation_ref: str,
    now: datetime,
    original_requester: str | None,
) -> str:
    if not principal_id or not capability or draft.state == "expired" or now >= draft.expires_at:
        raise ValueError("current session, draft capability and unexpired draft required")
    if len(capability) > 1024 or not hmac.compare_digest(
        hashlib.sha256(capability).hexdigest(), expected_capability_digest
    ):
        raise ValueError("invalid draft capability")
    if continuation_ref != draft.continuation_ref:
        raise ValueError("continuation mismatch")
    if (original_requester is not None and original_requester != principal_id) or (
        draft.state == "claimed" and original_requester is None
    ):
        raise ValueError("draft already belongs to another/missing authenticated owner")
    return draft.draft_id


def validate_work_package(
    package,
    *,
    graph,
    snapshots,
    components,
    flows,
    omissions,
    unresolved,
    required_node_ids: set[str],
    required_flow_ids: set[str],
    qualified_recipe_refs: set[str],
    now: datetime,
):
    """Resolve/validate required inputs without allowing model optionality to shrink scope."""
    if (
        package.acquisition_expires_at <= now
        or graph.case_id != package.case_id
        or graph.graph_digest != package.resource_graph_digest
    ):
        raise ValueError("stale/wrong-case graph/package")
    nodes = {n.node_id: n for n in graph.nodes}
    if not required_node_ids <= nodes.keys() or any(
        not nodes[n].required_for_scope for n in required_node_ids
    ):
        raise ValueError("required resource cannot be omitted or made optional")
    if not required_node_ids <= {c.node_id for c in components.components}:
        raise ValueError("required component missing")
    if set(snapshots) != set(package.source_snapshot_refs) or any(
        s.case_id != package.case_id for s in snapshots.values()
    ):
        raise ValueError("source refs not resolved to current case")
    actual_flows = {f.flow_id: f for f in flows.flows}
    if not required_flow_ids <= actual_flows.keys() or any(
        not actual_flows[f].required for f in required_flow_ids
    ):
        raise ValueError("required flow cannot be omitted or made optional")
    if not set(package.state_recipe_refs) <= qualified_recipe_refs:
        raise ValueError("unqualified state recipe")
    if package.completeness == "sufficient_for_declared_static_scope" and (
        unresolved.items
        or any(x.required_for_scope for x in omissions.items)
        or any(s.completeness != "complete_for_declared_scope" for s in snapshots.values())
    ):
        raise ValueError("required missing evidence cannot become complete")
    return package


def validate_approval_set(
    plan, approval_set, *, approvals: Mapping, authorities: Mapping, now: datetime
):
    """Check exact split-controller coverage from current authenticated resolved records."""
    if (
        (plan.case_id, plan.run_id, plan.generation, plan.plan_digest)
        != (
            approval_set.case_id,
            approval_set.run_id,
            approval_set.generation,
            approval_set.plan_digest,
        )
        or plan.expires_at <= now
        or approval_set.state != "complete"
    ):
        raise ValueError("stale/mismatched/incomplete approval set")
    if content_digest(plan.model_dump(mode="json", exclude={"plan_digest"})) != plan.plan_digest:
        raise ValueError("action plan canonical digest mismatch")
    if set(approvals) != set(approval_set.approval_refs):
        raise ValueError("approval refs not resolved exactly")
    controllers = {c for slot in plan.slots for c in slot.required_controller_ids}
    if set(approval_set.required_controller_ids) != controllers:
        raise ValueError("required controller coverage mismatch")
    for slot in plan.slots:
        required_authorities = {}
        for ref in slot.required_authority_refs:
            authority = authorities.get(ref)
            if authority is None:
                raise ValueError("required authority not resolved")
            if (
                authority.controller_id not in slot.required_controller_ids
                or authority.target_key != slot.target_key
                or slot.operation not in authority.actions
                or authority.revoked_at is not None
                or not authority.issued_at <= now < authority.expires_at
                or not authority.role_evidence_refs
                or approval_set.authority_epochs.get(authority.authority_id)
                != authority.grant_epoch
            ):
                raise ValueError("required authority stale or outside exact effect scope")
            required_authorities[ref] = authority
        for controller in slot.required_controller_ids:
            covered = False
            for approval in approvals.values():
                if (
                    approval.controller_id != controller
                    or approval.case_id != plan.case_id
                    or approval.generation != plan.generation
                    or approval.action_plan_digest != plan.plan_digest
                    or approval.reviewed_bundle_digest != plan.review_bundle_digest
                    or approval.graph_digest != plan.graph_digest
                    or approval.scope_digest != plan.scope_digest
                    or approval.policy_digest != plan.policy_digest
                    or approval.trigger_chain_digest != slot.trigger_digest
                    or approval.revoked_at is not None
                    or not approval.issued_at <= now < approval.expires_at
                    or slot.operation not in approval.allowed_actions
                    or slot.target_key.resource_id not in approval.target_resources
                    or (
                        slot.artifact_digest is not None
                        and approval.artifact_digest != slot.artifact_digest
                    )
                    or (
                        slot.config_digest is not None
                        and approval.config_digest != slot.config_digest
                    )
                    or (
                        slot.state_plan_digest is not None
                        and approval.state_plan_digest != slot.state_plan_digest
                    )
                ):
                    continue
                owned = {
                    ref: authority
                    for ref, authority in required_authorities.items()
                    if authority.controller_id == controller
                }
                if owned and all(
                    ref in approval.authority_refs
                    and approval.authority_binding_epochs.get(authority.authority_id)
                    == authority.grant_epoch
                    for ref, authority in owned.items()
                ):
                    covered = True
            if not covered:
                raise ValueError("missing current exact controller/authority for effect slot")
    return approval_set
