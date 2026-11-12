"""Current proof/review gate composed with Gupta's existing exact approval checker."""

from goldgraft_contracts.plan5_common import content_digest

from integration.promotion import require_current_result
from integration.proof_evidence import review_authenticated_bundle
from pieces.backend.lifecycle.approvals import verify_plan_approvals


def require_current_apply_review(
    action_plan,
    approval_set,
    proof_plan,
    proof_result,
    context,
    *,
    approval_inputs,
    resolve,
    authenticate=None,
    verify_check=None,
    subject_for=None,
    approve_exclusion=None,
):
    """Pure accepting composition; dispatch still needs an atomic authority-at-use transaction."""
    if (
        (
            action_plan.case_id,
            action_plan.run_id,
            action_plan.generation,
            action_plan.scope_digest,
            action_plan.policy_digest,
            action_plan.review_bundle_digest,
        )
        != (
            context.case_id,
            context.run_id,
            context.generation,
            context.scope_digest,
            context.policy_digest,
            context.review_bundle_digest,
        )
        or context.review_bundle_ref is None
        or context.review_bundle_digest is None
        or approval_inputs["current_resource_epochs"] != context.resource_epochs
        or content_digest(action_plan.model_dump(mode="json", exclude={"plan_digest"}))
        != action_plan.plan_digest
    ):
        raise ValueError("APPLY_REVIEW_STALE")
    require_current_result(
        proof_plan,
        proof_result,
        context,
        resolve=resolve,
        authenticate=authenticate,
        verify_check=verify_check,
        approve_exclusion=approve_exclusion,
    )
    bundle = review_authenticated_bundle(
        proof_plan,
        proof_result,
        context,
        bundle_ref=context.review_bundle_ref,
        bundle_digest=context.review_bundle_digest,
        resolve=resolve,
        authenticate=authenticate,
        subject_for=subject_for,
    )
    if (
        bundle.proposed_apply_plan_ref != action_plan.plan_id
        or bundle.recovery_plan_ref != action_plan.recovery_plan_ref
    ):
        raise ValueError("APPLY_REVIEW_STALE")
    verify_plan_approvals(action_plan, approval_set, **{**approval_inputs, "now": context.now})
    return approval_set
