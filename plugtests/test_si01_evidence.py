"""SI01 actual accepting adapters; injected custody is component evidence only."""

from datetime import UTC, datetime, timedelta

import pytest
from goldgraft_contracts.agent_runtime import ArtifactDescriptor, SubjectManifest
from goldgraft_contracts.plan5_common import canonical_bytes, content_digest
from goldgraft_contracts.proof_evidence import ProofCheck, ProofPlan
from goldgraft_contracts.registry import validate
from pydantic import ValidationError
from pydantic_core import to_jsonable_python

from integration.proof_evidence import EvidenceContext, StoredArtifact, evaluate_plan

NOW = datetime(2026, 11, 12, tzinfo=UTC)
D = "a" * 64
EPOCHS = {"resource": 1}


def seal(model, **fields):
    fields = to_jsonable_python(fields)
    return model.model_validate({**fields, "plan_digest": content_digest(fields)})


def setup_evidence():
    subject = SubjectManifest(
        source_snapshot_refs=["fixture:source"],
        source_tree_digest=D,
        oci_manifest_digest="sha256:" + D,
        config_digest=D,
        runtime_profile_digest=D,
        scope_digest=D,
    )
    sd = content_digest(subject)
    records = {}

    def store(ref, schema, payload, subject_digest=sd):
        raw = canonical_bytes(payload)
        descriptor = ArtifactDescriptor(
            ref=ref,
            case_id="case",
            run_id="run",
            generation=1,
            schema=schema,
            payload_digest=content_digest(payload),
            byte_count=len(raw),
            subject_digest=subject_digest,
            input_digest=D,
            derivation_ref=None,
            producer_identity_ref="fixture:collector",
            trust="collector_observed",
            evidence_class="component_offline",
            created_at=NOW,
            expires_at=NOW + timedelta(hours=1),
        )
        records[ref] = StoredArtifact(descriptor, raw)

    store("fixture:subject", "SubjectManifest/1", subject)
    checks = []
    for kind in ["baseline", "candidate", "scenario", "domain_rule", "security"]:
        ref = "fixture:" + kind
        # Existing BaselineEvidence is used as a typed component-only receipt.
        from goldgraft_fakes._fixtures import example

        payload = example("BaselineEvidence/1")
        payload.update(run_id="run", package_digest=D)
        store(ref, "BaselineEvidence/1", payload)
        checks.append(
            ProofCheck(
                check_id=ref,
                flow_id="checkout",
                kind=kind,
                rule_ids=[],
                subject_manifest_ref="fixture:subject",
                subject_manifest_digest=sd,
                required_schema="BaselineEvidence/1",
                required_evidence_class="component_offline",
                critical=True,
                owner_role="collector",
                input_digest=D,
                required_trust="collector_observed",
            )
        )
    plan = seal(
        ProofPlan,
        plan_id="plan",
        case_id="case",
        run_id="run",
        generation=1,
        resource_epochs=EPOCHS,
        scope_digest=D,
        work_package_digest=D,
        policy_digest=D,
        checks=checks,
        exclusions=[],
        created_at=NOW,
        expires_at=NOW + timedelta(hours=1),
    )
    context = EvidenceContext(
        tenant_id="tenant",
        case_id="case",
        run_id="run",
        generation=1,
        resource_epochs=EPOCHS,
        scope_digest=D,
        work_package_digest=D,
        policy_digest=D,
        plan_digest=plan.plan_digest,
        required_checks=tuple(checks),
        now=NOW,
    )
    return plan, context, records


def evaluate(plan, context, records, authenticate=lambda *args: True):
    return evaluate_plan(
        plan,
        context,
        resolve=records.get,
        authenticate=authenticate,
        verify_check=lambda payload, *args: payload.outcome == "reproduced",
    )


def test_current_complete_component_inventory_is_only_component_ready():
    plan, context, records = setup_evidence()
    result = evaluate(plan, context, records)
    assert result.outcome == "ready"
    assert result.plan_digest == plan.plan_digest
    assert all(x.state == "verified" for x in result.results)
    validate("ProofResult/1", result.model_dump(mode="json"))


@pytest.mark.parametrize("fault", ["missing", "bytes", "epoch", "auth", "class", "expired"])
def test_untrusted_or_incomplete_critical_evidence_holds(fault):
    plan, context, records = setup_evidence()
    rec = records["fixture:candidate"]

    def auth(*args):
        return fault != "auth"

    if fault == "missing":
        del records["fixture:candidate"]
    elif fault == "bytes":
        records["fixture:candidate"] = StoredArtifact(rec.descriptor, b"{}")
    elif fault == "epoch":
        context = context.__class__(**{**context.__dict__, "resource_epochs": {"resource": 2}})
    elif fault == "auth":
        pass
    else:
        updates = {"evidence_class": "scripted"} if fault == "class" else {"expires_at": NOW}
        records["fixture:candidate"] = StoredArtifact(
            rec.descriptor.model_copy(update=updates), rec.payload
        )
    assert evaluate(plan, context, records, auth).outcome == "hold"


def test_plan_cannot_drop_or_downgrade_current_inventory_even_when_rehashed():
    plan, context, records = setup_evidence()
    fields = plan.model_dump(mode="json", exclude={"plan_digest"})
    fields["checks"] = fields["checks"][:-1]
    changed = seal(ProofPlan, **fields)
    context = context.__class__(**{**context.__dict__, "plan_digest": changed.plan_digest})
    assert evaluate(changed, context, records).outcome == "hold"


def test_digest_and_duplicate_check_ids_rejected_by_contract():
    plan, _, _ = setup_evidence()
    with pytest.raises(ValidationError):
        ProofPlan.model_validate({**plan.model_dump(), "plan_digest": "b" * 64})
    fields = plan.model_dump(mode="json", exclude={"plan_digest"})
    fields["checks"].append(fields["checks"][0])
    with pytest.raises(ValidationError):
        seal(ProofPlan, **fields)


@pytest.mark.parametrize(
    "field,value",
    [
        ("generation", 2),
        ("case_id", "foreign"),
        ("run_id", "foreign"),
        ("schema_id", "RootMap/1"),
        ("trust", "model_proposal"),
        ("subject_digest", "b" * 64),
        ("input_digest", "b" * 64),
    ],
)
def test_descriptor_identity_and_lineage_are_not_self_authenticating(field, value):
    plan, context, records = setup_evidence()
    rec = records["fixture:candidate"]
    records["fixture:candidate"] = StoredArtifact(
        rec.descriptor.model_copy(update={field: value}), rec.payload
    )
    assert evaluate(plan, context, records).outcome == "hold"


def test_no_authenticator_or_no_semantic_verifier_holds():
    plan, context, records = setup_evidence()
    assert evaluate(plan, context, records, None).outcome == "hold"
    assert (
        evaluate_plan(plan, context, resolve=records.get, authenticate=lambda *a: True).outcome
        == "hold"
    )


def test_authenticated_but_failed_receipt_does_not_pass():
    import json

    plan, context, records = setup_evidence()
    rec = records["fixture:candidate"]
    payload = json.loads(rec.payload)
    payload["outcome"] = "failed"
    raw = canonical_bytes(payload)
    descriptor = rec.descriptor.model_copy(
        update={"payload_digest": content_digest(payload), "byte_count": len(raw)}
    )
    records["fixture:candidate"] = StoredArtifact(descriptor, raw)
    assert evaluate(plan, context, records).outcome == "hold"


def test_noncritical_exclusion_requires_current_approval_and_cannot_exclude_critical():
    plan, ctx, records = setup_evidence()
    fields = plan.model_dump(mode="json", exclude={"plan_digest"})
    fields["checks"][-1]["critical"] = False
    fields["exclusions"] = [
        dict(
            check_id="fixture:security",
            reason="Synthetic bounded scope",
            approval_ref="fixture:approval",
            approval_digest=D,
        )
    ]
    plan = seal(ProofPlan, **fields)
    from dataclasses import replace

    ctx = replace(ctx, required_checks=tuple(plan.checks), plan_digest=plan.plan_digest)
    ports = dict(
        resolve=records.get,
        authenticate=lambda *a: True,
        verify_check=lambda payload, *a: payload.outcome == "reproduced",
    )
    assert evaluate_plan(plan, ctx, **ports).outcome == "partial"
    approved = evaluate_plan(plan, ctx, approve_exclusion=lambda *a: True, **ports)
    assert approved.outcome == "ready" and approved.results[-1].state == "excluded"
    fields["checks"][-1]["critical"] = True
    with pytest.raises(ValidationError):
        seal(ProofPlan, **fields)
