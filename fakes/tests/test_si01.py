"""Synthetic SI01 custody is explicit and cannot assert external qualification."""

import json
from dataclasses import replace

import pytest
from goldgraft_fakes.si01 import FakeEvidenceCustody

from integration.proof_evidence import evaluate_plan
from plugtests.test_si01_evidence import setup_evidence


def test_custody_scope_revocation_and_external_class_denial():
    plan, context, records = setup_evidence()
    fake = FakeEvidenceCustody("tenant", "case", "run", 1, {"resource": 1})
    for record in records.values():
        fake.register(record.descriptor, json.loads(record.payload), "collector")
    ports = dict(
        resolve=fake.resolve,
        authenticate=fake.authenticate,
        verify_check=lambda payload, *args: payload.outcome == "reproduced",
    )
    assert evaluate_plan(plan, context, **ports).outcome == "ready"
    assert evaluate_plan(plan, replace(context, tenant_id="foreign"), **ports).outcome == "hold"
    rec = records["fixture:candidate"]
    with pytest.raises(ValueError, match="external"):
        fake.register(
            rec.descriptor.model_copy(update={"evidence_class": "real_payment"}),
            json.loads(rec.payload),
            "collector",
        )
    fake.revoked = True
    assert evaluate_plan(plan, context, **ports).outcome == "hold"
