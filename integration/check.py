"""One-command verification of the current pushed, synthetic reference flow."""

import argparse
import json
from pathlib import Path

from fastapi.testclient import TestClient
from goldgraft_contracts.api_routes import route
from goldgraft_fakes import data

from integration.app import create_app
from integration.service import FixtureRun
from pieces.backend.elastic_ingest import format_evidence_doc
from pieces.backend.zapier_notifier import ZapierNotifier


def check(directory: Path):
    service = FixtureRun(directory)
    client = TestClient(create_app(service=service))
    request = f"/shops/{service.shop_id}/graft"
    headers = {"Idempotency-Key": "pushed-reference-v1"}
    response = client.post(request, json={}, headers=headers)
    response.raise_for_status()
    graft = route("start_graft").response.model_validate(response.json())
    verdicts = route("get_scenarios").response.model_validate(
        client.get(f"/grafts/{service.graft_id}/scenarios").json()
    )
    cmel = []
    for row in verdicts.scenarios:
        response = client.get(
            f"/grafts/{service.graft_id}/cmel", params={"scenario": row.scenario.id}
        )
        view = route("get_cmel").response.model_validate(response.json())
        cmel.extend(view.old + view.old_twin + view.new)
    proof = route("get_proof").response.model_validate(
        client.get(f"/grafts/{service.graft_id}/proof").json()
    )
    certificate = route("verify_certificate").response.model_validate(
        client.post(f"/certificates/{data.CERT_ID}/verify").json()
    )
    entries = service.events()
    root = graft.ledger_root
    reopened = FixtureRun(directory)

    def no_dispatch(_):
        raise AssertionError("completed fixture run must not execute on restart")

    reopened.runner.run_job = no_dispatch
    restart = TestClient(create_app(service=reopened))
    repeated = restart.post(request, json={}, headers=headers)
    if repeated.status_code != 200 or repeated.json() != graft.model_dump(mode="json"):
        raise ValueError("restart result changed")
    if reopened.ledger.root_hash(service.graft_id) != root or certificate.ok:
        raise ValueError("unexpected ledger mutation or synthetic signature acceptance")
    diagnostic = format_evidence_doc(
        service.graft_id,
        "pushed-reference-v1",
        graft.stage,
        "fixture-pack",
        "COMPLETE",
        "Published fixture proof flow completed",
        root,
        "synthetic-fixtures",
        details={"scenario_count": len(verdicts.scenarios)},
    )
    notification = ZapierNotifier(enabled=False).notify(
        "BLOCKED", service.graft_id, "Synthetic fixture evidence; no merchant apply authority"
    )
    report = {
        "scope": "current pushed GitHub reference implementation",
        "evidence_class": "scripted",
        "pipeline_status": "PASS",
        "path": "backend start → submitted runner → actual proof → ledger → API → reopen",
        "graft_id": service.graft_id,
        "merchant_stage": graft.stage,
        "scenario_count": len(verdicts.scenarios),
        "verdicts": {r.scenario.id: r.verdict.grade for r in verdicts.scenarios},
        "cmel_events": len(cmel),
        "ledger_entries": len(entries),
        "ledger_chain_valid": service.ledger.verify_chain(service.graft_id).ok,
        "ledger_root": root,
        "fixture_mutants": proof.proof_strength.total,
        "fixture_mutation_score": proof.proof_strength.score,
        "unsigned_certificate_accepted": certificate.ok,
        "new_execution_on_restart": False,
        "external_provider_calls": 0,
        "elastic_document": diagnostic,
        "zapier_delivery": {"enabled": False, "delivered": notification.delivered},
    }
    directory = Path(directory)
    (directory / "end-to-end.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(check(args.state_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
