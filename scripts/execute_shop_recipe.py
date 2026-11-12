"""Reviewed host adapter for the accepted shop socket; actual PHP, simulated PayPal.

Never executes an unreviewed agent patch on this host. Imports actual team
orchestration/recorder; does not copy or recreate backend/proof infrastructure.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from check_team_boundaries import team_revision

ROOT = Path(__file__).resolve().parents[1]
# Run as a child process by recipe.py: make the team packages importable without
# relying on the caller's PYTHONPATH (pytest, CI and the API do not set it).
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PACK = ROOT / "pieces/shops/vijay-php-reference"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute-reviewed-host", action="store_true", required=True)
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--php", type=Path, required=True)
    args = p.parse_args()
    team = Path(os.environ.get("GOLDGRAFT_TEAM_ROOT", ROOT)).resolve()
    actual = team_revision(team)
    from goldgraft_contracts.registry import validate

    from integration import local_shop as host
    from integration.local_mutants import build_mutants
    from pieces.proof.mutation import apply_mutant
    from pieces.proof.proof import Proof

    expected_source = json.loads(
        (ROOT / "pieces/shops/legacy-php-shop/phase1/source_inventory.json").read_bytes()
    )
    expected = {
        entry["path"][4:]: entry["git_blob_sha1"]
        for entry in expected_source["files"]
        if entry["path"].startswith("src/")
    }
    actual_files = {
        p.relative_to(PACK / "source").as_posix(): p
        for p in (PACK / "source").rglob("*")
        if p.is_file()
    }
    if set(actual_files) != set(expected):
        raise ValueError("pinned_source_file_set_changed")
    for name, source in actual_files.items():
        raw = source.read_bytes()
        if (
            hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            != expected[name]
        ):
            raise ValueError("pinned_source_bytes_changed")

    pack = validate("ShopPack/1", json.loads((PACK / "goldgraft-shop.yaml").read_bytes()))
    rows = json.loads((args.run_dir / "CHANGES.json").read_bytes())["files"]
    approved = json.loads((PACK / "reviewed_candidate.json").read_bytes())
    files = {row["path"]: row["after"] for row in rows}
    if len(files) != len(rows) or set(files) != set(approved):
        raise ValueError("protected_runner_required_for_unreviewed_candidate")
    for row in rows:
        rel = row["path"]
        if hashlib.sha256(row["after"].encode()).hexdigest() != approved[rel]:
            raise ValueError("protected_runner_required_for_unreviewed_candidate")
        original = PACK / "source" / rel
        if row["before"] != (original.read_text(encoding="utf-8") if original.exists() else ""):
            raise ValueError("baseline_drift")
    host.validate_candidate(files)
    # This is a Windows flags/environment adapter around the actual team runner,
    # not a patched team source file or a claim of host isolation.
    original_popen = subprocess.Popen
    found = shutil.which(str(args.php))
    if not found:
        raise ValueError("native_php_required")
    php = Path(found).resolve()

    def php_process(command, **kwargs):
        if Path(command[0]).resolve() != php:
            raise ValueError("only_reviewed_php_process_allowed")
        env = {k: os.environ[k] for k in ("SystemRoot", "WINDIR", "TEMP", "TMP") if k in os.environ}
        env.update(kwargs.pop("env", {}))  # Team runner supplies placeholders only.
        runtime = (
            [
                "-n",
                "-d",
                "extension_dir=" + str(php.parent / "ext"),
                "-d",
                "extension=curl",
                "-d",
                "extension=openssl",
            ]
            if os.name == "nt"
            else []
        )
        command = [str(php), *runtime, *command[1:]]
        return original_popen(
            command,
            env=env,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            **kwargs,
        )

    args.output.mkdir(parents=True, exist_ok=False)
    report = {
        "run_id": args.run_dir.name,
        "evidence_class": "local_php_execution_simulated_paypal",
        "real_payment_qualified": False,
        "isolated_execution_qualified": False,
        "merchant_delivery_qualified": False,
        "provider_calls": 0,
        "model_calls": 0,
        "capture_sha256": {},
        "normative_contract_sha256": hashlib.sha256(
            (PACK / "contract.json").read_bytes()
        ).hexdigest(),
        "candidate_producer": "reviewed_operator_fixture_not_an_agent_run",
        "team_commit": actual,
        "later_qualification": {
            "state": "HOLD",
            "finalisation": "HOLD",
            "exit": "HOLD",
        },
    }
    before = {
        str(p.relative_to(PACK / "source")): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (PACK / "source").rglob("*")
        if p.is_file()
    }
    recorded = {}
    proof = Proof()
    contract = validate("Contract/1", json.loads((PACK / "contract.json").read_bytes()))
    plan = validate("TargetPlan/1", json.loads((PACK / "target_plan.json").read_bytes()))
    with (
        patch.object(host, "SHOP_SRC", PACK / "source"),
        patch.object(host.subprocess, "Popen", php_process),
    ):
        for sid in pack.scenarios_supported:
            recorded[sid] = []
            for variant in ("OLD", "OLD_TWIN", "NEW"):
                capture = host.run_scenario(
                    sid,
                    variant,
                    files if variant == "NEW" else {},
                    graft_id=args.run_dir.name,
                    run_id=args.run_dir.name + "-local-php",
                    php=str(php),
                )
                recorded[sid].append(validate("RawCapture/1", capture))
                name = f"{sid}.{variant}.json"
                raw = (json.dumps(capture, indent=2) + "\n").encode()
                (args.output / name).write_bytes(raw)
                report["capture_sha256"][name] = hashlib.sha256(raw).hexdigest()
        mutants, missing = build_mutants(files)
        report["candidate_mutations"] = []
        report["unsupported_candidate_mutations"] = missing
        guarded = set()
        (args.output / "mutants").mkdir()
        for mutant in mutants:
            sid = "PENDING" if mutant.rule == "R01" else "HAPPY"
            old, twin, candidate = recorded[sid]
            base = proof.judge(
                *[proof.to_cmel(c) for c in (old, twin, candidate)],
                contract,
                plan,
                old_capture=old,
                new_capture=candidate,
            )
            if str(base.grade) not in ("PASS", "PASS_FIXED"):
                report["unsupported_candidate_mutations"].append(
                    {"id": mutant.id, "reason": "base scenario does not pass"}
                )
                continue
            changed = apply_mutant(files[mutant.location.file], mutant)
            mutated = validate(
                "RawCapture/1",
                host.run_scenario(
                    sid,
                    "NEW",
                    {**files, mutant.location.file: changed},
                    graft_id=args.run_dir.name,
                    run_id=args.run_dir.name + "-mutation-" + mutant.id.lower(),
                    php=str(php),
                ),
            )
            verdict = proof.judge(
                *[proof.to_cmel(c) for c in (old, twin, mutated)],
                contract,
                plan,
                old_capture=old,
                new_capture=mutated,
            )
            name = mutant.id + ".NEW.json"
            raw = mutated.model_dump_json(indent=2).encode()
            (args.output / "mutants" / name).write_bytes(raw)
            report["candidate_mutations"].append(
                {
                    "mutant": mutant.model_dump(mode="json"),
                    "scenario_id": sid,
                    "capture_file": name,
                    "capture_sha256": hashlib.sha256(raw).hexdigest(),
                    "verdict": verdict.model_dump(mode="json"),
                    "evidence_class": "executed_operator_fixture_mutation_simulated_paypal",
                }
            )
            if str(verdict.grade) == "PROBLEM":
                guarded.add(mutant.rule)
        report["unguarded_critical_rule_ids"] = sorted(
            {r.id for r in contract.rules if str(r.severity) == "CRITICAL"} - guarded
        )
    after = {
        str(p.relative_to(PACK / "source")): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (PACK / "source").rglob("*")
        if p.is_file()
    }
    if before != after:
        raise ValueError("frozen_source_changed")
    report["source_unchanged"] = True
    (args.output / "REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "LOCAL_CAPTURE_COMPLETE",
                "capture_count": len(report["capture_sha256"]),
            }
        )
    )


if __name__ == "__main__":
    main()
