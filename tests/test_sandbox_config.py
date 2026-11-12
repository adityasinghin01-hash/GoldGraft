import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sandbox_config", ROOT / "scripts/sandbox_config.py")
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)


class ConfigTests(unittest.TestCase):
    def test_control_characters_are_invalid_without_exposing_values(self):
        data = {
            "PAYPAL_SANDBOX_CLIENT_ID": "\x16PRIVATE_SENTINEL",
            "PAYPAL_SANDBOX_CLIENT_SECRET": "PRIVATE_SENTINEL",
        }
        result = config.status(data)
        self.assertFalse(result["REST seller"]["configured"])
        self.assertEqual(result["REST seller"]["invalid_names"], ["PAYPAL_SANDBOX_CLIENT_ID"])
        self.assertNotIn("PRIVATE_SENTINEL", json.dumps(result))

    def test_prompt_rejects_control_and_cannot_preserve_corrupted_value(self):
        with (
            patch.object(config.getpass, "getpass", side_effect=["\x16BAD", "", "VALID"]),
            patch("builtins.print"),
        ):
            self.assertEqual(config.prompt_value("FIELD", "\x16OLD"), "VALID")

    def test_status_never_prints_secrets(self):
        data = {
            "PAYPAL_ENVIRONMENT": "sandbox",
            "PAYPAL_SANDBOX_CLIENT_ID": "SECRET_SENTINEL",
            "PAYPAL_SANDBOX_CLIENT_SECRET": "SECRET_SENTINEL",
        }
        self.assertTrue(config.status(data)["REST seller"]["configured"])
        self.assertNotIn("SECRET_SENTINEL", json.dumps(config.status(data)))

    def test_live_unknown_and_non_string_values_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sandbox.json"
            for data in [
                {"PAYPAL_ENVIRONMENT": "live"},
                {"PAYPAL_ENVIRONMENT": "sandbox", "OTHER": "x"},
                {"PAYPAL_ENVIRONMENT": "sandbox", "PAYPAL_SANDBOX_CLIENT_ID": 123},
            ]:
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    config.load_config(path)

    def test_oversized_config_rejected_before_json_parse(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sandbox.json"
            path.write_text(" " * 16385)
            with self.assertRaises(ValueError):
                config.load_config(path)


if __name__ == "__main__":
    unittest.main()
