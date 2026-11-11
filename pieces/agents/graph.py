"""Incremental own policy for the B4 Surveyor→Herald slice, not a new scheduler."""

from goldgraft_contracts.agent_runtime import PlanProposal, TaskSpec
from goldgraft_contracts.plan5_common import content_digest


def advance_surveyor_herald(run_ref, ports):
    snapshot = ports.control.snapshot(run_ref)
    if snapshot.cancellation_ref is not None or any(
        t.task.task_id == "herald" for t in snapshot.tasks
    ):
        return
    source = next((t for t in snapshot.tasks if t.task.task_id == "survey"), None)
    if source is None or source.state != "succeeded" or len(source.output_refs) != 1:
        return
    descriptor = ports.artifacts.resolve(source.output_refs[0], ports.context_for("survey"))
    if (
        descriptor.schema_id,
        descriptor.producer_identity_ref,
        descriptor.subject_digest,
        descriptor.input_digest,
    ) != (
        "RootMap/1",
        "fake:role:Surveyor",
        source.task.expected_subject,
        source.input_digest,
    ):
        raise ValueError("DENIED predecessor binding")
    ports.artifacts.prepare_herald_projection(source)
    projection = ports.herald_configuration["projection"]
    task = TaskSpec(
        task_id="herald",
        role="Herald",
        operation="explain_status",
        dependencies=["survey"],
        input_refs=list(source.output_refs),
        expected_schemas=["HeraldText/1"],
        output_slot="text." + projection,
        workspace_ref=None,
        expected_subject=descriptor.subject_digest,
        allowed_tool_ids=["status.read", "evidence.summary"],
        required=False,
        output_subject_policy="same_subject",
    )
    proposal = PlanProposal(
        case_id=snapshot.case_id,
        run_id=snapshot.run_id,
        generation=snapshot.generation,
        parent_request_id=source.request_id,
        tasks=[task],
        reason_refs=list(source.output_refs),
    )
    ports.control.extend(
        run_ref,
        snapshot.state_version,
        proposal,
        "fake:herald-extension:" + content_digest(proposal),
    )
