"""Surveyor source completeness through the actual guarded runtime."""

import hashlib

from goldgraft_contracts.agent_runtime import ArtifactDescriptor
from goldgraft_contracts.registry import validate
from goldgraft_fakes._fixtures import example
from goldgraft_fakes.offline_store import encoded

from pieces.agents.runtime import run_task

from .test_runtime import NOW, profile


def test_surveyor_missing_required_backend_holds_before_model(tmp_path):
    ports = profile(tmp_path)
    task = ports.control.snapshot("fake:runtime-run").tasks[0]
    omissions = {
        "items": [
            {
                "component_id": "payment-backend",
                "path": "backend/payments.php",
                "reason_code": "SOURCE_NOT_SUPPLIED",
                "required_for_scope": True,
                "evidence_refs": [],
            }
        ]
    }
    validate("OmissionManifest/1", omissions)
    with ports.control.store.transaction() as db:
        omission_ref = ports.control.artifacts._put(
            db,
            task,
            "OmissionManifest/1",
            omissions,
            task.task.expected_subject,
            trust="collector_observed",
        )
        snapshot = example("SourceSnapshot/1")
        snapshot.update(
            snapshot_id="fixture:input",
            case_id=task.case_id,
            completeness="incomplete",
            omission_manifest_ref=omission_ref,
        )
        validate("SourceSnapshot/1", snapshot)
        payload = encoded(snapshot).encode()
        row = db.execute(
            "SELECT descriptor FROM artifacts WHERE ref=?", ("fixture:input",)
        ).fetchone()
        descriptor = ArtifactDescriptor.model_validate_json(row["descriptor"]).model_copy(
            update={
                "schema_id": "SourceSnapshot/1",
                "payload_digest": hashlib.sha256(payload).hexdigest(),
                "byte_count": len(payload),
                "producer_identity_ref": "fake:collector",
                "trust": "collector_observed",
            }
        )
        db.execute(
            "UPDATE artifacts SET descriptor=?,payload=? WHERE ref=?",
            (encoded(descriptor), payload, "fixture:input"),
        )
    lease = ports.control.claim("surveyor-test-worker", NOW)
    result = run_task(lease, ports.control, ports.artifacts, ports.model, ports.tools, now=NOW)
    assert result.outcome == "blocked"
    assert result.issue.code == "MISSING_EVIDENCE"
    assert result.output_refs == []
    assert ports.model.total_dispatches() == 0
    assert ports.tools.total_dispatches() == 0
    # This counterpart counts all committed results, including a safe held result.
    assert ports.control.accepted_result_count() == 1
    assert ports.control.result("survey").output_refs == []
    assert ports.control.snapshot("fake:runtime-run").tasks[0].state == "held"
