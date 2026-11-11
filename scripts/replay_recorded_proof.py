"""Run the deterministic judge on a previously recorded, content-addressed job export."""

import argparse
import json
from hashlib import sha256
from pathlib import Path

from goldgraft_contracts.registry import validate
from goldgraft_foundation.blobs import LocalBlobStore

from integration.offline import evaluate_recordings
from pieces.proof.proof import Proof


def replay(directory: Path) -> dict:
    def load(schema: str, filename: str):
        return validate(schema, json.loads((directory / filename).read_bytes()))

    blob_dir = directory / "blobs"
    if not blob_dir.is_dir():
        raise ValueError("MISSING_EVIDENCE export has no blobs directory")
    store = LocalBlobStore(blob_dir)

    def capture(ref: str):
        payload = store.get(ref)
        if ref != "blob://" + sha256(payload).hexdigest():
            raise ValueError("DENIED capture blob digest mismatch")
        return validate("RawCapture/1", json.loads(payload))

    report = evaluate_recordings(
        Proof(),
        load("JobSpec/1", "job-spec.json"),
        load("JobResult/1", "job-result.json"),
        capture,
        load("Contract/1", "contract.json"),
        load("TargetPlan/1", "target-plan.json"),
        require_run_binding=True,
    )
    return {
        "evidence_class": "recorded_export",
        "provider_calls": 0,
        "merchant_delivery_qualified": False,
        "verdicts": {item["scenario_id"]: item["grade"] for item in report["verdicts"]},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export_dir", type=Path)
    args = parser.parse_args()
    try:
        summary = replay(args.export_dir)
    except (OSError, ValueError, KeyError):
        parser.exit(1, "Replay failed. Check the job, blob integrity and required proof inputs.\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
