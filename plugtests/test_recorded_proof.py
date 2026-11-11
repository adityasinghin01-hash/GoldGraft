"""Replay the proof engine from a sealed recording export."""

import json

import pytest
from goldgraft_foundation.blobs import LocalBlobStore

from integration.offline import FIXTURE, fixture_spec
from pieces.runner.container_runner import ContainerRunner
from scripts.replay_recorded_proof import replay


def test_replay_checks_capture_bytes_and_run_binding(tmp_path):
    spec = fixture_spec().model_copy(update={"scenario_ids": ["HAPPY"]})
    store = LocalBlobStore(tmp_path / "blobs")
    runner = ContainerRunner(blob_store=store)
    result = runner.run_job(spec)
    records = [
        runner.fetch_capture(ref).model_copy(update={"run_id": spec.job_id})
        for ref in result.raw_capture_refs
    ]

    def write_export():
        refs = [store.put(record.model_dump_json().encode()) for record in records]
        exported = result.model_copy(update={"raw_capture_refs": refs})
        (tmp_path / "job-result.json").write_text(exported.model_dump_json())
        return refs

    (tmp_path / "job-spec.json").write_text(spec.model_dump_json())
    (tmp_path / "contract.json").write_bytes((FIXTURE / "contract.json").read_bytes())
    (tmp_path / "target-plan.json").write_bytes((FIXTURE / "target_plan.json").read_bytes())
    refs = write_export()
    assert replay(tmp_path) == {
        "evidence_class": "recorded_export",
        "provider_calls": 0,
        "merchant_delivery_qualified": False,
        "verdicts": {"HAPPY": "PASS"},
    }

    store.path_for(refs[0]).write_text(json.dumps({"tampered": True}))
    with pytest.raises(ValueError, match="blob digest"):
        replay(tmp_path)

    records[0] = records[0].model_copy(update={"run_id": "different-run"})
    write_export()
    with pytest.raises(ValueError, match="capture run binding"):
        replay(tmp_path)
