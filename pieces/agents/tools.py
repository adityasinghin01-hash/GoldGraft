"""Mandatory invocation checks, independent of optional Sentinel reasoning."""

from goldgraft_contracts.agent_runtime import ControlError


def validate_invocation(task, invocation):
    if (
        invocation.task_id,
        invocation.case_id,
        invocation.run_id,
        invocation.generation,
        invocation.lease_epoch,
        invocation.input_digest,
    ) != (
        task.task.task_id,
        task.case_id,
        task.run_id,
        task.generation,
        task.lease_epoch,
        task.input_digest,
    ) or invocation.tool_id not in task.task.allowed_tool_ids:
        return ControlError(code="DENIED", retry_class="none", evidence_refs=[])
    return None
