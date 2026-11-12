import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "sponsor_assets", ROOT / "scripts/check_sponsor_assets.py"
)
assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assets)


class SponsorAssetTests(unittest.TestCase):
    def collection(self):
        return json.loads(
            (ROOT / "tools/sponsors/postman/offline-shop.postman_collection.json").read_text()
        )

    def test_only_loopback_template_is_permitted(self):
        assets.validate_local_collection(self.collection())
        data = self.collection()
        data["item"][0]["request"]["url"] = "https://api-m.sandbox.paypal.com/"
        with self.assertRaises(ValueError):
            assets.validate_local_collection(data)

    def test_unknown_payment_route_is_rejected(self):
        data = self.collection()
        data["item"][0]["request"]["url"] = "{{base_url}}/api/refund.php"
        with self.assertRaises(ValueError):
            assets.validate_local_collection(data)

    def test_extra_script_request_is_rejected(self):
        data = self.collection()
        data["item"][0]["event"][0]["script"]["exec"].append(
            'pm.sendRequest("https://example.invalid")'
        )
        with self.assertRaises(ValueError):
            assets.validate_local_collection(data)

    def test_inline_lab_secret_is_rejected(self):
        data = self.collection()
        data["item"][2]["request"]["header"][0]["value"] = "PRIVATE_SENTINEL"
        with self.assertRaises(ValueError):
            assets.validate_local_collection(data)

    def scope(self):
        scenarios = json.loads(
            (ROOT / "pieces/shops/legacy-php-shop/phase1/scenarios.json").read_text()
        )["scenarios"]
        payment = json.loads(
            (ROOT / "tools/sponsors/postman/payment-plan.postman_collection.json").read_text()
        )
        kernel = json.loads((ROOT / "tools/sponsors/kernel/scenario-plan.json").read_text())
        return scenarios, payment, kernel

    def test_scope_is_exactly_fourteen_and_no_live_session_is_claimed(self):
        args = self.scope()
        assets.validate_scope(*args)
        bad = copy.deepcopy(args)
        bad[2]["permitted_external_sessions"] = 1
        with self.assertRaises(ValueError):
            assets.validate_scope(*bad)

    def test_real_payment_request_cannot_be_hidden_in_planning_collection(self):
        args = self.scope()
        args[1]["item"][0]["item"] = [{"request": {"method": "POST"}}]
        with self.assertRaises(ValueError):
            assets.validate_scope(*args)

    def test_added_scenario_is_not_silently_accepted(self):
        args = self.scope()
        args[2]["scenario_ids"].append("S15")
        with self.assertRaises(ValueError):
            assets.validate_scope(*args)
