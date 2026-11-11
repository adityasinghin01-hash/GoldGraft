"""Opt-in synthetic 13-role check: real Surveyor→Herald plus component samples.

The first two roles share one actual durable graph/artifact handoff. The other
roles run independent representative component tasks with labelled stand-ins;
this is not a merchant migration, provider acceptance or full thirteen-role graph.
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from goldgraft_contracts.plan5_common import content_digest
from goldgraft_fakes.herald_profile import create_collaboration_profile

from pieces.agents.evals.surveyor import score_artifact
from pieces.agents.graph import advance_surveyor_herald
from pieces.agents.herald import HeraldInputs, deterministic_renderer, inspect_text
from pieces.agents.roles import herald_configuration, surveyor_configuration
from pieces.agents.runtime import run_task
from pieces.agents.source_inventory import package_from_sources
from pieces.backend.model_gateway.broker import Gateway
from pieces.backend.model_gateway.component_port import ComponentGateway
from pieces.backend.model_gateway.ledger import Ledger
from pieces.backend.model_gateway.profile import Profile
from pieces.backend.model_gateway.qualification import verify_qualification
from scripts.live_herald_model_eval import HeraldEvaluationArtifacts
from scripts.live_surveyor_model_eval import BoundModel, EvaluationArtifacts

SOURCE_CASE = {
    "id": "combined-refund",
    "shop_id": "test-refund",
    "files": {"refund.php": "<?php\n$m='RefundTransaction';\n"},
    "expected": [
        {
            "family": "EC_NVP",
            "operation": "RefundTransaction",
            "file": "refund.php",
            "line": 2,
            "flow": "refund",
            "mapping_id": "nvp-refund",
            "needle": "RefundTransaction",
        }
    ],
}
REPRESENTATIVES = [
    ("Sentinel", "s-breach-denied"),
    ("Gardener", "gd-single"),
    ("Builder", "b-baseline"),
    ("Explorer", "e-old"),
    ("Scribe", "sc-final-traced"),
    ("Architect", "ar-1-touch"),
    ("Grafter", "gr-1-files"),
    ("Adversary", "ad-guard"),
    ("Healer", "he-unknown-effect"),
    ("Librarian", "li-quarantine"),
    ("Orchard Analyst", "or-counts"),
]


def close_batch(gateway, batch):
    try:
        gateway.ledger.close(batch)
    except ValueError:
        pass  # Never clear an unresolved turn or its reservation.


def run_dual(path, source_gateway, herald_gateway, source_batch, herald_batch):
    """Run both models on one actual graph; failed source cannot admit Herald."""
    p = create_collaboration_profile(
        path,
        configuration=surveyor_configuration(),
        herald_configuration=herald_configuration(),
        renderer=deterministic_renderer,
        inputs=package_from_sources(shop_id=SOURCE_CASE["shop_id"], files=SOURCE_CASE["files"]),
        clock=lambda: datetime.now(UTC),
    )
    artifacts = EvaluationArtifacts(p.artifacts, source_gateway, source_batch)
    lease = p.control.claim("combined-source", p.clock())
    result = run_task(lease, p.control, artifacts, BoundModel(artifacts), p.tools, now=p.clock())
    source = p.control.snapshot("fake:runtime-run").tasks[0]
    report = {
        "surveyor": {"outcome": result.outcome, "inventory": None, "check": None},
        "herald": None,
        "binding": {},
        "passed": False,
    }
    close_batch(source_gateway, source_batch)
    if source.state != "succeeded":
        return report
    descriptor, inventory = p.artifacts.inspect_output(source, p.context_for("survey"))
    check = score_artifact(SOURCE_CASE, inventory)
    report["surveyor"].update(inventory=inventory, check=check, output_ref=descriptor.ref)
    if not check["passed"]:
        return report
    advance_surveyor_herald("fake:runtime-run", p)
    lease = p.control.claim("combined-herald", p.clock())
    if lease is None or lease.task_id != "herald":
        raise ValueError("MISSING_EVIDENCE admitted Herald task")
    artifacts = HeraldEvaluationArtifacts(p.artifacts, herald_gateway, herald_batch)
    result = run_task(lease, p.control, artifacts, BoundModel(artifacts), p.tools, now=p.clock())
    task = next(
        t for t in p.control.snapshot("fake:runtime-run").tasks if t.task.task_id == "herald"
    )
    payload = view = None
    if task.state == "succeeded":
        payload, facts = p.artifacts.inspect_herald(task, p.context_for("herald"))
        view = inspect_text(payload, HeraldInputs.model_validate(facts))
    close_batch(herald_gateway, herald_batch)
    report["herald"] = {"outcome": result.outcome, "payload": payload, "view": view}
    report["binding"] = {
        "surveyor_output_refs": list(source.output_refs),
        "herald_input_refs": list(task.task.input_refs),
        "source_payload_digest": content_digest(inventory),
    }
    report["passed"] = bool(
        payload
        and task.task.input_refs == source.output_refs
        and len(payload["numbers_used"]) == 1
        and payload["numbers_used"][0]["value"] == len(inventory["touchpoints"])
        and not view["notifications_sent"]
        and not view["authoritative_status_changed"]
    )
    return report


def ready(ledger):
    with ledger.transaction() as db:
        if db.execute(
            "SELECT 1 FROM turns WHERE state IN ('intended','submitted','unknown')"
        ).fetchone():
            raise ValueError("UNKNOWN original turn must reconcile")
    state = ledger.snapshot()
    if state["frozen"] or state["reserved_micro_usd"]:
        raise ValueError("HELD outstanding budget")
    return state


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--round", required=True)
    args = parser.parse_args(argv)
    if not args.live or not re.fullmatch(r"c[1-9][0-9]?", args.round):
        parser.error("explicit --live and a stable c-number identity required")
    evidence = Path.home() / "reports/goldgraft-all-agents-20261111"
    gateway_evidence = Path.home() / "reports/goldgraft-model-gateway-20261111"
    directory = evidence / "combined" / args.round
    if directory.exists():
        raise ValueError("CONFLICT combined identity already exists")
    profile = Profile()
    # Fresh shared qualification binds this script and the Surveyor path too;
    # do not rewrite or bypass the older, stale whole-tree Surveyor certificate.
    verify_qualification(gateway_evidence / "qualification-components-haiku.json", profile)
    from pieces.backend.model_gateway.provider import AnthropicProvider

    custody = Path.home() / ".config/goldgraft"
    ledger = Ledger(custody / "model-budget.sqlite")
    start = ready(ledger)
    with ledger.transaction() as db:
        total_ag = db.execute(
            "SELECT COALESCE(SUM(actual),0) FROM batches WHERE id LIKE 'ag-%'"
        ).fetchone()[0]
        survey_ag = db.execute(
            "SELECT COALESCE(SUM(actual),0) FROM batches WHERE id LIKE 'ag-surveyor-%'"
        ).fetchone()[0]
        herald = db.execute(
            "SELECT COALESCE(SUM(actual),0) FROM batches WHERE id LIKE 'ag-herald-%'"
        ).fetchone()[0]
    survey = start["spent_micro_usd"] - total_ag + survey_ag
    # Historical Surveyor ceiling was explicitly extended to $1.25; no change here.
    if survey + profile.batch_reservation > 1250000 or herald + profile.batch_reservation > 250000:
        raise ValueError("BUDGET_EXHAUSTED role envelope")
    if start["spent_micro_usd"] + 2 * profile.batch_reservation > start["active_cap_micro_usd"]:
        raise ValueError("BUDGET_EXHAUSTED project")
    source_batch = "ag-surveyor-combined-refund-" + args.round
    herald_batch = "ag-herald-combined-refund-" + args.round
    with ledger.transaction() as db:
        if db.execute(
            "SELECT 1 FROM batches WHERE id IN (?,?)", (source_batch, herald_batch)
        ).fetchone():
            raise ValueError("CONFLICT original model identity")
    directory.mkdir(parents=True)
    provider = AnthropicProvider(custody / "anthropic.env", profile)
    signing = custody / "model-gateway-signing.key"
    dual = run_dual(
        directory / "state.sqlite",
        Gateway(ledger, signing, profile, provider),
        ComponentGateway(ledger, signing, profile, provider, roles={"Herald"}),
        source_batch,
        herald_batch,
    )
    with ledger.transaction() as db:
        ids = db.execute(
            "SELECT batch,id FROM turns WHERE batch IN (?,?)", (source_batch, herald_batch)
        ).fetchall()
    dual["turns"] = [ledger.turn(b, t) for b, t in ids]
    dual["evidence_class"] = "two_real_models_one_actual_graph_synthetic_tools"
    (directory / "SURVEYOR_HERALD.json").write_text(json.dumps(dual, indent=2, default=str) + "\n")
    ready(ledger)
    rows = [
        {
            "role": "Surveyor",
            "passed": bool(dual["surveyor"]["check"] and dual["surveyor"]["check"]["passed"]),
        },
        {"role": "Herald", "passed": bool(dual["passed"])},
    ]
    for role, case_id in REPRESENTATIVES:
        ready(ledger)
        # Existing series enforces exact role route, qualification and envelope.
        subprocess.run(
            [
                sys.executable,
                "-u",
                str(evidence / "series.py"),
                role,
                args.round,
                "auto",
                case_id,
            ],
            cwd=Path(__file__).resolve().parents[1],
            check=True,
        )
        batch = f"ag-{role.lower().replace(' ', '-')}-{case_id}-{args.round}"
        result = json.loads((gateway_evidence / "live" / batch / "result.json").read_text())
        rows.append({"role": role, "case_id": case_id, "batch": batch, "passed": result["passed"]})
        (directory / "PROGRESS.json").write_text(json.dumps(rows, indent=2) + "\n")
    end = ready(ledger)
    summary = {
        "evidence_class": "synthetic_combined_sample_not_merchant_workflow",
        "rows": rows,
        "passed": sum(r["passed"] for r in rows),
        "of": 13,
        "spent_micro_usd": end["spent_micro_usd"] - start["spent_micro_usd"],
        "ledger": end,
        "limit": "Connected Surveyor→Herald; eleven independent component tasks, "
        "not a full delivery graph.",
    }
    (directory / "RESULT.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))
    return 0 if summary["passed"] == 13 else 1


if __name__ == "__main__":
    raise SystemExit(main())
