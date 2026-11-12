"""Bounded exit reconciliation uses signed-result/verifier substitutes, never real exit."""

from dataclasses import replace
from datetime import timedelta

import pytest
from goldgraft_contracts.exit_evidence import ExitCheckResult, ExitEvidenceReconciliation
from goldgraft_contracts.lifecycle import ExitCheckPlan, ExitManifest
from goldgraft_contracts.plan5_common import content_digest
from goldgraft_fakes._fixtures import example
from pydantic_core import to_jsonable_python

from integration.exit_evidence import reconcile_exit
from plugtests.test_si01_evidence import NOW, D, setup_evidence


def exit_setup():
    _, context, _ = setup_evidence()
    context = replace(context, now=NOW + timedelta(seconds=20))
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
    fields = example("ExitCheckPlan/1")
    fields.update(
        case_id="case",
        run_id="run",
        generation=1,
        deadline=NOW + timedelta(hours=1),
        criteria_refs=["fixture:criterion"],
    )
    fields = to_jsonable_python(fields)
    fields["plan_digest"] = content_digest({k: v for k, v in fields.items() if k != "plan_digest"})
    plan = ExitCheckPlan.model_validate(fields)
    fields = {
        **binding,
        "result_id": "fixture:exit-result",
        "exit_plan_ref": plan.exit_plan_id,
        "exit_plan_digest": plan.plan_digest,
        **{
            k: getattr(plan, k)
            for k in (
                "reservation_ref",
                "executor_identity_ref",
                "trusted_code_digest",
                "final_artifact_digest",
                "final_config_digest",
                "state_digest",
                "evidence_read_authority_ref",
            )
        },
        "restart_count": 1,
        "ordinary_denials": [
            dict(capability=c, evidence_ref="fixture:denial-" + c, payload_digest=D, denied_at=NOW)
            for c in ("source_read", "model_execution", "host_mutation", "worker_dispatch")
        ],
        "observations": [
            dict(
                criterion_ref="fixture:criterion",
                state="verified",
                evidence_ref="fixture:observed",
                payload_digest=D,
                observed_at=NOW + timedelta(seconds=3),
            )
        ],
        "outcome": "verified",
        "started_at": NOW + timedelta(seconds=1),
        "finished_at": NOW + timedelta(seconds=10),
    }
    fields = to_jsonable_python(fields)
    result = ExitCheckResult.model_validate(
        {
            **fields,
            "result_digest": content_digest(fields),
            "signature": dict(
                signature_ref="fixture:signature",
                signature_digest=D,
                transparency_ref="fixture:transparency",
                transparency_digest=D,
                authenticity_ref="fixture:executor-auth",
            ),
        }
    )
    fields = example("ExitManifest/1")
    fields.update(case_id="case", run_id="run")
    manifest = ExitManifest.model_validate(fields)
    closure = ExitEvidenceReconciliation(
        **binding,
        exit_plan_ref=plan.exit_plan_id,
        exit_plan_digest=plan.plan_digest,
        exit_result_ref=result.result_id,
        exit_result_digest=content_digest(result),
        exit_manifest_ref="fixture:manifest",
        exit_manifest_digest=content_digest(manifest),
        evidence_read_receipt=dict(
            authority_ref=plan.evidence_read_authority_ref,
            disclosure_ref="fixture:disclosure",
            read_evidence_ref="fixture:read",
            read_digest=D,
            read_at=NOW + timedelta(seconds=11),
            revocation_ref="fixture:read-revoked",
            revocation_digest=D,
            revoked_at=NOW + timedelta(seconds=12),
        ),
        authenticity_ref="fixture:reconciliation-auth",
        checked_at=NOW + timedelta(seconds=13),
    )
    ports = {
        name: (lambda *args: True)
        for name in (
            "authorize_plan",
            "verify_signature",
            "verify_observation",
            "authenticate_reconciliation",
        )
    }
    return plan, result, manifest, closure, context, ports


def test_exact_bounded_result_and_later_read_closure_reconcile_existing_manifest():
    plan, result, manifest, closure, ctx, ports = exit_setup()
    assert reconcile_exit(plan, result, manifest, closure, ctx, **ports) == manifest
    assert closure.evidence_read_receipt.revoked_at > result.finished_at


@pytest.mark.parametrize(
    "port",
    ["authorize_plan", "verify_signature", "verify_observation", "authenticate_reconciliation"],
)
def test_missing_trust_or_observation_cannot_complete_exit(port):
    plan, result, manifest, closure, ctx, ports = exit_setup()
    ports[port] = None
    with pytest.raises(ValueError):
        reconcile_exit(plan, result, manifest, closure, ctx, **ports)


@pytest.mark.parametrize(
    "fault",
    [
        "epoch",
        "executor",
        "image",
        "criteria",
        "plan",
        "closure",
        "manifest",
        "read_grant",
        "restart",
        "late_denial",
        "tamper",
    ],
)
def test_forged_stale_unbounded_or_incomplete_exit_is_held(fault):
    plan, result, manifest, closure, ctx, ports = exit_setup()
    if fault == "epoch":
        ctx = replace(ctx, resource_epochs={"resource": 2})
    elif fault in {"executor", "image", "restart", "late_denial", "tamper"}:
        fields = result.model_dump(mode="json")
        if fault == "executor":
            fields["executor_identity_ref"] = "fixture:forged"
        elif fault == "image":
            fields["final_artifact_digest"] = "sha256:" + "b" * 64
        elif fault == "restart":
            fields["restart_count"] = 2
        elif fault == "late_denial":
            fields["ordinary_denials"][0]["denied_at"] = fields["finished_at"]
        fields["result_digest"] = content_digest(
            {k: v for k, v in fields.items() if k not in {"signature", "result_digest"}}
        )
        if fault == "tamper":
            fields["result_digest"] = "b" * 64
        # Preserve typed children while bypassing the outer validators; the
        # accepting adapter must still catch invalid seals and restart bounds.
        fields["ordinary_denials"] = [
            row.model_copy(update={"denied_at": result.finished_at})
            if fault == "late_denial" and i == 0
            else row
            for i, row in enumerate(result.ordinary_denials)
        ]
        fields["observations"] = result.observations
        fields["signature"] = result.signature
        fields["started_at"] = result.started_at
        fields["finished_at"] = result.finished_at
        result = result.model_copy(update=fields)
    elif fault in {"criteria", "plan"}:
        plan = plan.model_copy(
            update={"criteria_refs": ["fixture:omitted"]}
            if fault == "criteria"
            else {"plan_digest": "b" * 64}
        )
    elif fault == "closure":
        closure = closure.model_copy(update={"exit_result_digest": "b" * 64})
    elif fault == "manifest":
        manifest = manifest.model_copy(update={"run_id": "foreign"})
    else:
        receipt = closure.evidence_read_receipt.model_copy(
            update={"authority_ref": "fixture:ordinary-revoked-grant"}
        )
        closure = closure.model_copy(update={"evidence_read_receipt": receipt})
    with pytest.raises(ValueError):
        reconcile_exit(plan, result, manifest, closure, ctx, **ports)
