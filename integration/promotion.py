"""Service rollout composition. A wrapped decision still grants no provider authority."""

from datetime import timedelta

from goldgraft_contracts.plan5_common import content_digest
from goldgraft_contracts.proof_evidence import PromotionDecision, ProofResult

from integration.proof_evidence import evaluate_plan, same_binding


def require_current_result(plan, result, context, **evidence_ports):
    result = ProofResult.model_validate(result.model_dump(mode="json"))
    if (
        not same_binding(result, context)
        or result.plan_ref != plan.plan_id
        or result.plan_digest != context.plan_digest
        or not plan.created_at <= result.checked_at <= context.now < plan.expires_at
    ):
        raise ValueError("STALE_RESULT")
    fresh = evaluate_plan(plan, context, **evidence_ports)
    if fresh.outcome != "ready" or result.outcome != "ready" or fresh.results != result.results:
        raise ValueError("EVIDENCE_HOLD")
    return fresh


def gate_promotion(
    advice,
    plan,
    result,
    context,
    *,
    resolve,
    authenticate=None,
    verify_check=None,
    approve_exclusion=None,
    authenticate_advice=None,
):
    action, reason = "HOLD", "ADVICE_HOLD"
    if advice.action == "CUTBACK":
        action, reason = "CUTBACK", "CUTBACK"
    elif advice.action == "STEP_UP":
        reason = "EVIDENCE_HOLD"
        try:
            if (
                authenticate_advice is None
                or authenticate_advice(advice, context) is not True
                or advice.graft_id != context.run_id
            ):
                raise ValueError("UNAUTHENTICATED_ADVICE")
            require_current_result(
                plan,
                result,
                context,
                resolve=resolve,
                authenticate=authenticate,
                verify_check=verify_check,
                approve_exclusion=approve_exclusion,
            )
            action, reason = "STEP_UP", "EVIDENCE_READY"
        except Exception:
            pass
    binding = {
        k: getattr(context, k)
        for k in (
            "case_id",
            "run_id",
            "generation",
            "resource_epochs",
            "scope_digest",
            "work_package_digest",
            "policy_digest",
        )
    }
    return PromotionDecision(
        **binding,
        advice=advice,
        advice_digest=content_digest(advice),
        proof_plan_digest=plan.plan_digest,
        proof_result_ref=result.result_id,
        proof_result_digest=result.result_digest,
        action=action,
        reason_code=reason,
        checked_at=context.now,
        expires_at=min(plan.expires_at, context.now + timedelta(minutes=5))
        if context.now < plan.expires_at
        else None,
    )
