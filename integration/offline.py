"""Compose submitted runner, actual proof and synthetic payment recorder without network."""

import argparse
import json
from pathlib import Path

from goldgraft_contracts.interfaces import Runner
from goldgraft_contracts.registry import validate
from goldgraft_contracts.runner import JobSpec
from goldgraft_foundation.blobs import LocalBlobStore

from pieces.backend.custody_broker import CustodyBroker
from pieces.backend.payment_broker import PaymentBroker
from pieces.proof.proof import Proof
from pieces.runner.container_runner import ContainerRunner
from pieces.runner.sandbox_recorder import SandboxRecorder

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/proof/legacy-php-shop"
VARIANTS = ("OLD", "OLD_TWIN", "NEW")


def fixture_proof(runner: Runner, proof: Proof, spec: JobSpec) -> dict:
    """Use submitted capture retrieval and independent mapper/judge on synthetic fixtures."""
    if (
        spec.kind != "RECORD"
        or set(spec.variants) != set(VARIANTS)
        or len(spec.variants) != 3
        or not spec.scenario_ids
        or len(spec.scenario_ids) != len(set(spec.scenario_ids))
    ):
        raise ValueError("MISSING_EVIDENCE unique scenarios and OLD/OLD_TWIN/NEW required")
    result = runner.run_job(spec)
    if result.status != "OK" or result.job_id != spec.job_id:
        raise ValueError("MISSING_EVIDENCE exact completed recording job")
    expected = {(s, v) for s in spec.scenario_ids for v in VARIANTS}
    if len(result.raw_capture_refs) != len(expected) or len(set(result.raw_capture_refs)) != len(
        expected
    ):
        raise ValueError("MISSING_EVIDENCE exact distinct recording set")
    captures = {}
    for ref in result.raw_capture_refs:
        capture = runner.fetch_capture(ref)
        key = (capture.scenario_id, capture.variant)
        if capture.graft_id != spec.graft_id or key not in expected or key in captures:
            raise ValueError("DENIED capture case/scenario/variant binding")
        captures[key] = capture
    if set(captures) != expected:
        raise ValueError("MISSING_EVIDENCE complete recording set")
    contract = validate("Contract/1", json.loads((FIXTURE / "contract.json").read_text()))
    plan = validate("TargetPlan/1", json.loads((FIXTURE / "target_plan.json").read_text()))
    verdicts = []
    mapped = {}
    for scenario in spec.scenario_ids:
        old, twin, new = (captures[scenario, variant] for variant in VARIANTS)
        streams = [proof.to_cmel(c) for c in (old, twin, new)]
        mapped[scenario] = {
            variant: [e.model_dump(mode="json") for e in events]
            for variant, events in zip(VARIANTS, streams, strict=True)
        }
        verdict = proof.judge(*streams, contract, plan, old_capture=old, new_capture=new)
        verdicts.append(verdict.model_dump(mode="json"))
    return {
        "evidence_class": "scripted",
        "real_payment_qualified": False,
        "capture_refs": result.raw_capture_refs,
        "verdicts": verdicts,
        "cmel": mapped,
        "captures": [c.model_dump(mode="json") for c in captures.values()],
        "job_result": result.model_dump(mode="json"),
        "runner": "Gupta ContainerRunner: fixture replay",
        "proof": "Singhal deterministic Proof: actual implementation",
    }


def fixture_spec() -> JobSpec:
    return validate(
        "JobSpec/1",
        {
            "job_id": "integration-fixture",
            "graft_id": "synthetic-c4",
            "stage": "RECORDED",
            "kind": "RECORD",
            "shop_pack_ref": "fixtures://shops/legacy-php-shop/goldgraft-shop.yaml",
            "scenario_ids": sorted(
                p.name.removesuffix(".verdict.json")
                for p in (FIXTURE / "expected").glob("*.verdict.json")
            ),
            "mutant_ids": [],
            "variants": list(VARIANTS),
            "timeouts": {"build_s": 10, "run_s": 10, "total_s": 30},
            "secrets_ref": "secret://offline/unused",
            "signature": None,
        },
    )


def run_offline(directory: Path, *, mode: str = "offline") -> dict:
    if mode != "offline":
        raise ValueError("UNQUALIFIED real team/provider integration")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    store = LocalBlobStore(directory / "blobs")
    proof = Proof()
    spec = fixture_spec()
    fixture_result = fixture_proof(ContainerRunner(blob_store=store), proof, spec)
    custody = CustodyBroker()
    ref = custody.store_credentials("integration-synthetic", {"paypal_client_id": "synthetic"})
    broker = PaymentBroker(custody_broker=custody)
    recorder = SandboxRecorder(broker=broker, blob_store=store)
    simulated_spec = spec.model_copy(
        update={"scenario_ids": ["HAPPY"], "secrets_ref": ref.to_uri()}
    )
    result = recorder.run_job(simulated_spec)
    reopened = SandboxRecorder(broker=broker, blob_store=store)
    captures = [reopened.fetch_capture(r) for r in result.raw_capture_refs]
    events = [proof.to_cmel(c) for c in captures]
    # Empty/unpaired generated exchanges must not acquire a fabricated scenario or verdict.
    if any(events):
        raise ValueError("INVALID synthetic recorder profile changed; review required")
    report = {
        "evidence_class": "scripted",
        "provider_calls": 0,
        "merchant_delivery_qualified": False,
        "fixtures": fixture_result,
        "payment_recorder": {
            "evidence_class": "scripted",
            "proof_status": "MISSING_EVIDENCE",
            "reason": "PR6 generates exchanges without complete payment/ledger witnesses",
            "cmel_events": sum(map(len, events)),
            "captures_reopened": len(captures),
            "capture_refs": result.raw_capture_refs,
        },
        "remaining": [
            "Real sandbox transport and isolated execution are outside this pushed fixture profile",
            "Real GU payment transport, isolation and authenticated callbacks unqualified",
        ],
    }
    (directory / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(run_offline(args.state_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
