"""Read and re-evaluate local PHP evidence without executing code or calling providers.

Digests bind local files for drift detection; they do not authenticate a collector
or qualify a provider. No certificate, strength score or promotion is produced.
"""

import hashlib
import json

from goldgraft_contracts.api import CmelView, ScenarioList
from goldgraft_contracts.proof import Grade
from goldgraft_contracts.registry import validate

from integration.local_shop import ROOT, SCENARIOS, order_listing
from pieces.proof.proof import Proof

EVIDENCE_CLASS = "local-php-simulated-paypal"
REFERENCE = ROOT / "fixtures/proof/legacy-php-shop"


def output_payload(outputs, task, schema):
    rows = outputs.get(task + "-retry1", outputs.get(task, []))
    payloads = [row["payload"] for row in rows if row.get("schema") == schema]
    if len(payloads) != 1:
        raise ValueError("exact committed output unavailable")
    return payloads[0]


def _read(path, expected):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("local proof input drift")
    return json.loads(raw)


class LocalProof:
    def __init__(self, directory):
        self.graft_id = directory.name
        evidence = directory / "local-proof"
        report = json.loads((evidence / "REPORT.json").read_bytes())
        if (
            report["run_id"] != self.graft_id
            or report["evidence_class"] != "local_php_execution_simulated_paypal"
            or any(
                report[key] is not False
                for key in (
                    "real_payment_qualified",
                    "isolated_execution_qualified",
                    "merchant_delivery_qualified",
                )
            )
        ):
            raise ValueError("local proof subject or qualification mismatch")
        _read(directory / "CHANGES.json", report["changes_sha256"])
        outputs = _read(directory / "OUTPUTS.json", report["outputs_sha256"])
        contract = validate(
            "Contract/1", _read(REFERENCE / "contract.json", report["normative_contract_sha256"])
        )
        plan = validate("TargetPlan/1", output_payload(outputs, "architect", "TargetPlan/1"))
        names = {f"{s}.{v}.json" for s in SCENARIOS for v in ("OLD", "OLD_TWIN", "NEW")}
        if set(report["capture_sha256"]) != names:
            raise ValueError("local proof recording set incomplete")
        proof = Proof()
        self.rows, self.streams = [], {}
        for scenario in SCENARIOS:
            captures = []
            for variant in ("OLD", "OLD_TWIN", "NEW"):
                name = f"{scenario}.{variant}.json"
                capture = validate(
                    "RawCapture/1", _read(evidence / name, report["capture_sha256"][name])
                )
                if (
                    capture.graft_id != self.graft_id
                    or capture.run_id != self.graft_id + "-local-php"
                    or capture.scenario_id != scenario
                    or capture.variant != variant
                ):
                    raise ValueError("local proof recording subject mismatch")
                captures.append(capture)
            streams = [proof.to_cmel(c) for c in captures]
            self.streams[scenario] = streams
            verdict = proof.judge(
                *streams, contract, plan, old_capture=captures[0], new_capture=captures[2]
            )
            if scenario == "PARITY_EXTRA" and "order_listing_parity_passed" in report:
                listings = [order_listing(capture) for capture in captures]
                if not listings[0] == listings[1] == listings[2]:
                    verdict.grade = Grade.PROBLEM
                    verdict.parity_diff.append(
                        {"feature": "order listing", "observations": listings}
                    )
            definition = json.loads((REFERENCE / "scenarios" / f"{scenario}.json").read_bytes())
            # The imported scenario describes this local simulated profile. It is
            # not evidence of authentic PayPal approval, signing or collection.
            definition["expect"]["evidence_class"] = EVIDENCE_CLASS
            definition["assured"] = {
                "passes_on_old": verdict.grade == "PASS",
                "flake_free_runs": 0,
            }
            self.rows.append({"scenario": definition, "verdict": verdict})

    def scenarios(self):
        return ScenarioList(graft_id=self.graft_id, scenarios=self.rows)

    def cmel(self, scenario):
        if scenario not in self.streams:
            raise LookupError("unknown local PHP scenario")
        old, old_twin, new = self.streams[scenario]
        return CmelView(
            graft_id=self.graft_id, scenario_id=scenario, old=old, old_twin=old_twin, new=new
        )
