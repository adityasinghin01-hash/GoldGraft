"""Pure exit-result reconciliation; no restart, cleanup, provider call or grant mutation."""

from goldgraft_contracts.exit_evidence import ExitCheckResult, ExitEvidenceReconciliation
from goldgraft_contracts.lifecycle import ExitCheckPlan, ExitManifest
from goldgraft_contracts.plan5_common import canonical_bytes, content_digest

from integration.proof_evidence import same_binding


def exit_result_payload(result):
    return canonical_bytes(result.model_dump(mode="json", exclude={"signature"}))


def reconcile_exit(
    plan,
    result,
    manifest,
    reconciliation,
    context,
    *,
    authorize_plan=None,
    verify_signature=None,
    verify_observation=None,
    authenticate_reconciliation=None,
):
    """All callbacks are trusted host ports and default to denial.

    Plan authorization resolves the CURRENT reservation/fences, executor trust,
    exact final assets and separately approved bounded action. Observation and
    reconciliation authentication resolve actual receipt bytes/identities, not
    caller-selected booleans. No production trust roots are supplied by SI01.
    """
    plan = ExitCheckPlan.model_validate(plan.model_dump(mode="json"))
    result = ExitCheckResult.model_validate(result.model_dump(mode="json"))
    manifest = ExitManifest.model_validate(manifest.model_dump(mode="json"))
    reconciliation = ExitEvidenceReconciliation.model_validate(
        reconciliation.model_dump(mode="json")
    )
    digest = content_digest(plan.model_dump(mode="json", exclude={"plan_digest"}))
    if (
        digest != plan.plan_digest
        or not same_binding(result, context)
        or not same_binding(reconciliation, context)
    ):
        raise ValueError("EXIT_BINDING")
    if (plan.case_id, plan.run_id, plan.generation) != (
        context.case_id,
        context.run_id,
        context.generation,
    ):
        raise ValueError("EXIT_BINDING")
    if (
        authorize_plan is None
        or authorize_plan(plan, context) is not True
        or plan.allowed_restart_count != 1
        or result.restart_count != 1
    ):
        raise ValueError("EXIT_AUTHORITY")
    for key in (
        "reservation_ref",
        "executor_identity_ref",
        "trusted_code_digest",
        "final_artifact_digest",
        "final_config_digest",
        "state_digest",
        "evidence_read_authority_ref",
    ):
        if getattr(plan, key) != getattr(result, key):
            raise ValueError("EXIT_SUBJECT")
    if (
        (result.exit_plan_ref, result.exit_plan_digest) != (plan.exit_plan_id, plan.plan_digest)
        or (reconciliation.exit_plan_ref, reconciliation.exit_plan_digest)
        != (plan.exit_plan_id, plan.plan_digest)
        or (reconciliation.exit_result_ref, reconciliation.exit_result_digest)
        != (result.result_id, content_digest(result))
        or reconciliation.exit_manifest_digest != content_digest(manifest)
        or (manifest.case_id, manifest.run_id) != (context.case_id, context.run_id)
        or result.outcome != "verified"
        or manifest.outcome != "complete"
    ):
        raise ValueError("EXIT_RESULT")
    if not result.finished_at <= plan.deadline or not result.finished_at <= context.now:
        raise ValueError("EXIT_DEADLINE")
    if set(plan.criteria_refs) != {x.criterion_ref for x in result.observations} or len(
        plan.criteria_refs
    ) != len(result.observations):
        raise ValueError("EXIT_CRITERIA")
    receipt = reconciliation.evidence_read_receipt
    if (
        receipt.authority_ref != plan.evidence_read_authority_ref
        or not result.finished_at
        <= receipt.read_at
        <= receipt.revoked_at
        <= reconciliation.checked_at
        <= context.now
    ):
        raise ValueError("EXIT_READ_CLOSURE")
    if (
        verify_signature is None
        or verify_signature(result, exit_result_payload(result), context) is not True
    ):
        raise ValueError("EXIT_AUTHENTICITY")
    if verify_observation is None or any(
        verify_observation(observation, plan, context) is not True
        for observation in [*result.ordinary_denials, *result.observations]
    ):
        raise ValueError("EXIT_OBSERVATION")
    if (
        authenticate_reconciliation is None
        or authenticate_reconciliation(reconciliation, manifest, context) is not True
    ):
        raise ValueError("EXIT_RECONCILIATION")
    return manifest
