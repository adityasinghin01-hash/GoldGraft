"""Meaningful negative cases for local repeatability and evidence separation."""

import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "phase2_baseline", ROOT / "scripts/phase2_baseline.py"
)
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)


class BaselineTests(unittest.TestCase):
    def runs(self):
        return [
            {
                "variant": variant,
                "repeat": repeat,
                "run_id": f"{variant}-{repeat}",
                "work_directory": f"run/{variant}/{repeat}",
                "source_sha256": {"app.php": "synthetic"},
                "status": "PASS",
                "evidence": "LOCAL_WINDOWS_COMPONENT_CHECKS",
                "node_22_component_check": True,
                "node_version": "v22.0.0",
                "payment_tests_run": False,
                "runtime_qualified": False,
                "browser": {"status": "PASS"},
                "order_store": {"status": "PASS", "payment_operations": 0},
            }
            for variant, repeat in baseline.EXPECTED
        ]

    def test_local_success_never_qualifies_purchases_or_full_phase(self):
        result = baseline.summarize(self.runs())
        self.assertEqual(result["component_status"], "PASS")
        self.assertEqual(result["qualified_purchases"], 0)
        self.assertEqual(result["phase2_gate"], "HOLD")

    def test_duplicate_state_or_run_identity_rejected(self):
        for field in ("run_id", "work_directory"):
            rows = self.runs()
            rows[1][field] = rows[0][field]
            self.assertEqual(baseline.summarize(rows)["component_status"], "HOLD")

    def test_missing_repetition_and_source_drift_rejected(self):
        rows = self.runs()
        self.assertEqual(baseline.summarize(rows[:-1])["component_status"], "HOLD")
        rows[-1]["source_sha256"] = {"app.php": "changed"}
        self.assertEqual(baseline.summarize(rows)["component_status"], "HOLD")

    def test_health_only_and_financial_labels_rejected(self):
        for field, value in [
            ("order_store", None),
            ("browser", {}),
            ("runtime_qualified", True),
            ("payment_tests_run", True),
            ("node_version", "v24.0.0"),
        ]:
            rows = copy.deepcopy(self.runs())
            rows[0][field] = value
            self.assertEqual(baseline.summarize(rows)["component_status"], "HOLD")


if __name__ == "__main__":
    unittest.main()
