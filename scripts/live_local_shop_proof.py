"""Opt-in host PHP execution of the saved sample candidate, using simulated PayPal only.

No model or external provider calls. This is a local diagnostic, not isolation,
merchant delivery, a certificate, or PayPal sandbox qualification.
"""

import argparse
import hashlib
import json
from pathlib import Path

from goldgraft_contracts.registry import validate

from integration.local_mutants import build_mutants, scenario_for
from integration.local_proof import output_payload
from integration.local_shop import (
    ROOT,
    SCENARIOS,
    SHOP_SRC,
    order_listing,
    resolve_php,
    run_scenario,
    validate_candidate,
)
from pieces.proof.mutation import apply_mutant, mutation_coverage
from pieces.proof.proof import Proof


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_candidate(directory):
    """Admit only the existing MIT sample and exact before/after paths, before execution."""
    result = json.loads((directory / "RESULT.json").read_bytes())
    if result.get("shop") != "legacy-php-shop" or result.get("status") != "completed":
        raise ValueError("only a completed legacy-php-shop run is admitted")
    changes = json.loads((directory / "CHANGES.json").read_bytes())
    rows = changes["files"]
    files = {row["path"]: row["after"] for row in rows}
    validate_candidate(files)
    if len(files) != len(rows) or not files:
        raise ValueError("candidate requires distinct changed paths")
    for row in rows:
        source = SHOP_SRC / row["path"]
        if row["before"] != (source.read_text() if source.exists() else ""):
            raise ValueError("candidate baseline drift")
    library = (ROOT / "fixtures/switch-libs/php/paypal_orders.php").read_text()
    if files.get("lib/paypal_orders.php") != library:
        raise ValueError("candidate library drift")
    return files, changes


def check(directory, output, *, php="php"):
    files, changes = load_candidate(directory)
    php = str(resolve_php(php))
    outputs_bytes = (directory / "OUTPUTS.json").read_bytes()
    outputs = json.loads(outputs_bytes)
    model_plan = validate("TargetPlan/1", output_payload(outputs, "architect", "TargetPlan/1"))
    model_contract = validate("Contract/1", output_payload(outputs, "scribe-final", "Contract/1"))
    reference = ROOT / "fixtures/proof/legacy-php-shop"
    contract_bytes = (reference / "contract.json").read_bytes()
    reference_plan_bytes = (reference / "target_plan.json").read_bytes()
    # The fixed normative policy is an independent audit, not Scribe output or
    # evidence of model-discovered rules. Its historic fixture provenance is retained.
    contract = validate("Contract/1", json.loads(contract_bytes))
    reference_plan = validate("TargetPlan/1", json.loads(reference_plan_bytes))
    supported = {rule.id for rule in contract.rules}
    unsupported_rules = sorted({rule.id for rule in model_contract.rules} - supported)
    proof = Proof()
    output.mkdir(parents=True, exist_ok=False)
    report = {
        "run_id": directory.name,
        "evidence_class": "local_php_execution_simulated_paypal",
        "changes_sha256": digest((directory / "CHANGES.json").read_bytes()),
        "outputs_sha256": digest(outputs_bytes),
        "normative_contract_sha256": digest(contract_bytes),
        "reference_plan_sha256": digest(reference_plan_bytes),
        "real_payment_qualified": False,
        "isolated_execution_qualified": False,
        "merchant_delivery_qualified": False,
        "provider_calls": 0,
        "model_calls": 0,
        "open_items": changes["open_items"],
        "model_rule_ids_unsupported_by_judge": unsupported_rules,
        "parity_extra_coverage": "actual unchanged GET /api/orders.php response",
        "scenarios": [],
        "capture_sha256": {},
    }
    recorded = {}
    for scenario in SCENARIOS:
        captures = []
        for variant in ("OLD", "OLD_TWIN", "NEW"):
            raw = run_scenario(
                scenario,
                variant,
                files if variant == "NEW" else {},
                graft_id=directory.name,
                run_id=directory.name + "-local-php",
                php=php,
            )
            name = f"{scenario}.{variant}.json"
            data = (json.dumps(raw, indent=2) + "\n").encode()
            (output / name).write_bytes(data)
            report["capture_sha256"][name] = digest(data)
            captures.append(validate("RawCapture/1", raw))
        recorded[scenario] = captures
        streams = [proof.to_cmel(capture) for capture in captures]
        row = {"scenario": scenario, "exchange_counts": [len(c.exchanges) for c in captures]}
        for name, plan in (
            ("actual_model_plan", model_plan),
            ("reviewed_reference_plan_diagnostic_only", reference_plan),
        ):
            row[name] = proof.judge(
                *streams, contract, plan, old_capture=captures[0], new_capture=captures[2]
            ).model_dump(mode="json")
        if scenario == "PARITY_EXTRA":
            listings = [order_listing(capture) for capture in captures]
            report["order_listing_parity_passed"] = listings[0] == listings[1] == listings[2]
            report["order_listing_observations"] = listings
        report["scenarios"].append(row)
        print(
            scenario,
            {
                k: row[k]["grade"]
                for k in ("actual_model_plan", "reviewed_reference_plan_diagnostic_only")
            },
            flush=True,
        )
    mutants, missing = build_mutants(files)
    report["unsupported_candidate_mutations"] = missing
    report["candidate_mutations"] = []
    mutation_runs = {}
    (output / "mutants").mkdir()
    verdicts = {row["scenario"]: row["actual_model_plan"] for row in report["scenarios"]}
    for mutant in mutants:
        scenario = scenario_for(mutant.rule)
        if verdicts[scenario]["grade"] not in {"PASS", "PASS_FIXED"}:
            report["unsupported_candidate_mutations"].append(
                {"id": mutant.id, "reason": "baseline does not pass; no kill can be attributed"}
            )
            continue
        changed = apply_mutant(files[mutant.location.file], mutant)
        patched = {**files, mutant.location.file: changed}
        capture = validate(
            "RawCapture/1",
            run_scenario(
                scenario,
                "NEW",
                patched,
                graft_id=directory.name,
                run_id=directory.name + "-local-php-" + mutant.id.lower(),
                php=php,
            ),
        )
        filename = mutant.id + ".NEW.json"
        raw = (capture.model_dump_json(indent=2) + "\n").encode()
        (output / "mutants" / filename).write_bytes(raw)
        old, twin, _ = recorded[scenario]
        streams = [proof.to_cmel(c) for c in (old, twin, capture)]
        verdict = proof.judge(*streams, contract, model_plan, old_capture=old, new_capture=capture)
        mutation_runs[mutant.id] = {scenario: verdict.grade}
        report["candidate_mutations"].append(
            {
                "mutant": mutant.model_dump(mode="json"),
                "scenario_id": scenario,
                "capture_file": filename,
                "capture_sha256": digest(raw),
                "mutated_source_sha256": digest(changed.encode()),
                "verdict": verdict.model_dump(mode="json"),
                "evidence_class": "executed_ai_candidate_mutation_simulated_paypal",
            }
        )
        print("MUTANT", mutant.id, scenario, verdict.grade, flush=True)
    executed = [m for m in mutants if m.id in mutation_runs]
    # Only a PROBLEM verdict is a kill; PASS/UNVERIFIED/anything else survived.
    report["candidate_mutations_survived"] = sorted(
        m.id for m in executed if str(mutation_runs[m.id][scenario_for(m.rule)]) != "PROBLEM"
    )
    strength = proof.proof_strength(executed, mutation_runs)
    report["candidate_mutation_strength"] = strength.model_dump(mode="json")
    scenarios = [
        validate(
            "Scenario/1", json.loads((reference / "scenarios" / f"{scenario}.json").read_bytes())
        )
        for scenario in SCENARIOS
    ]
    coverage = mutation_coverage(contract, scenarios, executed, mutation_runs)
    report["candidate_mutation_coverage"] = [row.model_dump(mode="json") for row in coverage]
    critical = {rule.id for rule in contract.rules if rule.severity == "CRITICAL"}
    report["unguarded_critical_rule_ids"] = sorted(
        critical - {row.rule_id for row in coverage if row.killed}
    )
    report["local_php_checks_complete"] = (
        not unsupported_rules
        and report.get("order_listing_parity_passed") is True
        and not report["unsupported_candidate_mutations"]
        and all(v["grade"] in {"PASS", "PASS_FIXED"} for v in verdicts.values())
        and len(executed) == len(mutants)
        and not report["candidate_mutations_survived"]
    )
    report["status"] = (
        "LOCAL_PHP_CHECKS_COMPLETE" if report["local_php_checks_complete"] else "HELD"
    )
    report["certificate"] = {
        "issued": False,
        "reasons": [
            "Local simulated PayPal is not authenticated sandbox evidence",
            "Required critical-rule mutation coverage is incomplete",
            "No qualified signing/workflow/transparency or merchant certificate binding",
        ],
    }
    # Local completion covers this bounded PHP profile only. Browser, isolation,
    # full required-flow coverage, providers and delivery remain separate gates.
    (output / "REPORT.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-local", action="store_true", required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--php", default="php")
    args = parser.parse_args(argv)
    report = check(args.run_dir.resolve(), args.output_dir.resolve(), php=args.php)
    print(json.dumps({"status": report["status"], "report": str(args.output_dir / "REPORT.json")}))
    return 0 if report["local_php_checks_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
