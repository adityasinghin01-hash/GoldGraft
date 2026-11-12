"""Proof freshness and current exact apply approvals must both hold; no effects dispatch."""

import json
from dataclasses import replace

import pytest
from goldgraft_contracts.plan5_common import canonical_bytes, content_digest
from goldgraft_contracts.proof_evidence import ProofPlan

from integration.apply_review import require_current_apply_review
from integration.proof_evidence import StoredArtifact
from plugtests.test_gupta_offline_safety import approval_records
from plugtests.test_si01_certificate import certificate_setup
from plugtests.test_si01_evidence import evaluate, seal


@pytest.mark.parametrize("fault", [None, "missing_evidence", "epoch", "policy", "review"])
def test_apply_composition_rejects_stale_evidence_even_with_complete_approvals(fault):
    _, plan, _, ctx, records, ports, _ = certificate_setup()
    action, approvals, inputs = approval_records()
    fields = plan.model_dump(mode="json", exclude={"plan_digest"})
    fields["resource_epochs"] = inputs["current_resource_epochs"]
    plan = seal(ProofPlan, **fields)
    ctx = replace(ctx, resource_epochs=plan.resource_epochs, plan_digest=plan.plan_digest)
    record = records["fixture:bundle"]
    body = json.loads(record.payload)
    body.update(proposed_apply_plan_ref=action.plan_id, recovery_plan_ref=action.recovery_plan_ref)
    body["bundle_digest"] = content_digest({k: v for k, v in body.items() if k != "bundle_digest"})
    raw = canonical_bytes(body)
    records["fixture:bundle"] = StoredArtifact(
        record.descriptor.model_copy(
            update={
                "payload_digest": content_digest(body),
                "byte_count": len(raw),
                "input_digest": plan.plan_digest,
            }
        ),
        raw,
    )
    ctx = replace(ctx, review_bundle_digest=body["bundle_digest"])
    result = evaluate(plan, ctx, records)
    action = action.model_copy(update={"review_bundle_digest": body["bundle_digest"]})
    action = action.model_copy(
        update={
            "plan_digest": content_digest(action.model_dump(mode="json", exclude={"plan_digest"}))
        }
    )
    approvals = approvals.model_copy(update={"plan_digest": action.plan_digest})
    inputs["approvals"] = {
        ref: item.model_copy(
            update={
                "action_plan_digest": action.plan_digest,
                "reviewed_bundle_digest": body["bundle_digest"],
            }
        )
        for ref, item in inputs["approvals"].items()
    }
    inputs["reservation_plan_digest"] = action.plan_digest
    if fault == "missing_evidence":
        del records["fixture:security"]
    elif fault == "epoch":
        ctx = replace(ctx, resource_epochs={k: 2 for k in ctx.resource_epochs})
    elif fault == "policy":
        ctx = replace(ctx, policy_digest="b" * 64)
    elif fault == "review":
        ctx = replace(ctx, review_bundle_digest="b" * 64)
    kwargs = {key: ports[key] for key in ("resolve", "authenticate", "verify_check", "subject_for")}
    if fault is None:
        assert (
            require_current_apply_review(
                action, approvals, plan, result, ctx, approval_inputs=inputs, **kwargs
            )
            == approvals
        )
    else:
        with pytest.raises(ValueError):
            require_current_apply_review(
                action, approvals, plan, result, ctx, approval_inputs=inputs, **kwargs
            )
