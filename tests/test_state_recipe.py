import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "shop_state_recipe", ROOT / "pieces/shops/legacy-php-shop/state_recipe/inspect.py"
)
state = importlib.util.module_from_spec(spec)
spec.loader.exec_module(state)


class StateRecipeTests(unittest.TestCase):
    def inspect(self, content):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / "orders.json"  # macOS: /var is a symlink
            path.write_text(content, encoding="utf-8")
            before = path.read_bytes()
            result = state.report(path)
            self.assertEqual(before, path.read_bytes())
            return result

    def test_private_data_is_never_emitted_and_no_actions_run(self):
        row = {
            "token": "PRIVATE_SENTINEL",
            "status": "PAID",
            "amount": "25.00",
            "payer_email": "PRIVATE_SENTINEL",
            "transaction_id": "PRIVATE_SENTINEL",
        }
        result = self.inspect(json.dumps({"PRIVATE_SENTINEL": row}))
        self.assertNotIn("PRIVATE_SENTINEL", json.dumps(result))
        self.assertEqual(result["actions_executed"], [])
        self.assertEqual(result["migration_gate"], "HOLD")

    def test_corruption_duplicates_and_oversize_hold_without_empty_success(self):
        for content in [
            "{corrupt",
            '{"a":{},"a":{}}',
            " " * (state.MAX_BYTES + 1),
            '[{"token":"x"}]',
        ]:
            self.assertEqual(self.inspect(content)["local_state"]["status"], "HOLD")

    def test_legacy_empty_array_is_not_migration_readiness(self):
        result = self.inspect("[]")
        self.assertEqual(result["local_state"]["records"], 0)
        self.assertEqual(result["migration_gate"], "HOLD")

    def test_pending_and_missing_identity_remain_findings(self):
        result = self.inspect('{"a":{"token":"wrong","status":"PENDING","amount":"1e2"}}')
        self.assertEqual(result["local_state"]["status_counts"], {"UNKNOWN": 1})
        self.assertEqual(len(result["local_state"]["finding_counts"]), 3)

    def test_paid_without_origin_or_transaction_never_becomes_ready(self):
        result = self.inspect('{"a":{"token":"a","status":"PAID","amount":"1.00"}}')
        self.assertIn("original_transaction_id_missing", result["local_state"]["finding_counts"])
        self.assertEqual(result["migration_gate"], "HOLD")
