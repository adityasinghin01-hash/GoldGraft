"""Offline readiness cannot be mistaken for payment or service qualification."""

import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("phase1_status", SCRIPTS / "phase1_status.py")
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class PhaseStatusTests(unittest.TestCase):
    def inputs(self):
        scenarios = {
            "scenarios": [{"id": f"S{i:02}", "title": "Synthetic case"} for i in range(1, 15)]
        }
        dependencies = {
            "team_revision": "synthetic",
            "required": [{"id": "GU03", "status": "NOT_READY"}],
        }
        probes = {
            "environment": "sandbox",
            "checks": [
                {
                    "probe": p,
                    "status": "PASS",
                    "http_status": 200,
                    "payment_operations": 0,
                    "checkout_qualified": False,
                    "reason": "credential_probe_only",
                }
                for p in ("oauth", "nvp-balance")
            ],
        }
        component = {
            "status": "PASS",
            "evidence": "LOCAL_WINDOWS_COMPONENT_CHECKS",
            "node_22_component_check": True,
            "node_version": "v22.0.0",
            "browser": {"status": "PASS"},
            "payment_tests_run": False,
            "runtime_qualified": False,
        }
        return (
            scenarios,
            dependencies,
            probes,
            {"status": "SOURCE_MATCH"},
            {"group": {"configured": True}},
            component,
        )

    def test_green_preparation_never_passes_payment_or_phase(self):
        result = report.summarize(*self.inputs())
        self.assertEqual(result["preparation_gate"], "READY_FOR_COUNTERPART")
        self.assertEqual(result["phase1_gate"], "HOLD")
        self.assertEqual(len(result["required_flows"]), 14)
        self.assertTrue(
            all(not s["attempted"] and s["status"] == "BLOCKED" for s in result["required_flows"])
        )
        self.assertFalse(result["checkout_qualified"])

    def test_node24_cannot_claim_team_node22(self):
        inputs = list(self.inputs())
        inputs[-1]["node_version"] = "v24.0.0"
        self.assertEqual(report.summarize(*inputs)["preparation_gate"], "INCOMPLETE")

    def test_provider_simulation_or_missing_probe_not_credential_pass(self):
        inputs = list(self.inputs())
        inputs[2]["checks"][0]["reason"] = "mock"
        inputs[2]["checks"].pop()
        result = report.summarize(*inputs)
        self.assertTrue(all(p["status"] == "UNVERIFIED" for p in result["credential_checks"]))

    def test_source_drift_blocks_preparation(self):
        inputs = list(self.inputs())
        inputs[3]["status"] = "HOLD"
        self.assertEqual(report.summarize(*inputs)["preparation_gate"], "INCOMPLETE")


if __name__ == "__main__":
    unittest.main()
