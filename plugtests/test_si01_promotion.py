"""Promotion accepts statistical advice only behind the current evidence gate."""

from dataclasses import replace

import pytest
from goldgraft_contracts.plan5_common import content_digest
from goldgraft_contracts.runner import HealDecision
from goldgraft_fakes._fixtures import example

from integration.promotion import gate_promotion
from plugtests.test_si01_evidence import evaluate, setup_evidence


def advice(action="STEP_UP"):
    value = example("HealDecision/1")
    value.update(
        graft_id="run",
        action=action,
        from_stage_pct=1,
        to_stage_pct=10 if action == "STEP_UP" else (0 if action == "CUTBACK" else 1),
        hard_stop=None,
    )
    return HealDecision.model_validate(value)


def promote(plan, result, context, records, **kw):
    return gate_promotion(
        advice(),
        plan,
        result,
        context,
        resolve=records.get,
        authenticate=lambda *args: True,
        verify_check=lambda payload, *args: payload.outcome == "reproduced",
        authenticate_advice=lambda *args: True,
        **kw,
    )


def test_complete_current_evidence_can_wrap_authenticated_advice():
    plan, ctx, records = setup_evidence()
    result = evaluate(plan, ctx, records)
    assert promote(plan, result, ctx, records).action == "STEP_UP"


@pytest.mark.parametrize(
    "fault", ["missing", "epoch", "policy", "result", "expiry", "result_scope"]
)
def test_high_score_cannot_override_stale_or_incomplete_evidence(fault):
    plan, ctx, records = setup_evidence()
    result = evaluate(plan, ctx, records)
    if fault == "missing":
        del records["fixture:security"]
    elif fault == "epoch":
        ctx = replace(ctx, resource_epochs={"resource": 2})
    elif fault == "policy":
        ctx = replace(ctx, policy_digest="b" * 64)
    elif fault == "result":
        result = result.model_copy(update={"result_digest": "b" * 64})
    elif fault == "result_scope":
        result = result.model_copy(update={"case_id": "foreign"})
    else:
        ctx = replace(ctx, now=plan.expires_at)
    assert promote(plan, result, ctx, records).action == "HOLD"


def test_untrusted_advice_cannot_step_up_but_cutback_is_preserved():
    plan, ctx, records = setup_evidence()
    result = evaluate(plan, ctx, records)
    assert gate_promotion(advice(), plan, result, ctx, resolve=records.get).action == "HOLD"
    assert (
        gate_promotion(advice("CUTBACK"), plan, result, ctx, resolve=records.get).action
        == "CUTBACK"
    )


def test_rehashed_result_cannot_replace_the_current_evidence_set():
    plan, ctx, records = setup_evidence()
    result = evaluate(plan, ctx, records)
    fields = result.model_dump(mode="json", exclude={"result_digest"})
    fields["results"][0]["evidence_refs"] = ["fixture:substituted"]
    result = result.__class__.model_validate({**fields, "result_digest": content_digest(fields)})
    assert promote(plan, result, ctx, records).action == "HOLD"
