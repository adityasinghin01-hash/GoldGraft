"""Offline fault cases for our Phase 1 components; never call real providers."""

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


readiness = load("readiness", "pieces/shops/legacy-php-shop/phase1/readiness.py")
probe = load("sandbox_probe", "scripts/live_sandbox_probe.py")


class SourceReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = b"<?php echo 'synthetic offline test';\n"
        (self.root / "index.php").write_bytes(self.data)
        digest = hashlib.sha1(
            b"blob " + str(len(self.data)).encode() + b"\0" + self.data
        ).hexdigest()
        self.inventory = {"files": [{"path": "index.php", "git_blob_sha1": digest}]}

    def test_exact_bytes_match_but_runtime_does_not_become_qualified(self):
        self.assertEqual(
            readiness.review_source(self.root, self.inventory)["status"], "SOURCE_MATCH"
        )
        report = readiness.report(environ={})
        self.assertEqual(report["phase_gate"], "HOLD")
        self.assertFalse(report["runtime_qualified"])
        self.assertTrue(all(row["status"] == "UNVERIFIED" for row in report["required_flows"]))

    def test_changed_missing_and_extra_source_hold_lc01(self):
        (self.root / "index.php").write_bytes(self.data + b"changed")
        self.assertIn(
            "changed:index.php", readiness.review_source(self.root, self.inventory)["issues"]
        )
        (self.root / "index.php").unlink()
        (self.root / ".env").write_text("synthetic-test-only")
        issues = readiness.review_source(self.root, self.inventory)["issues"]
        self.assertIn("missing:index.php", issues)
        self.assertIn("unexpected:.env", issues)

    def test_traversal_and_absolute_inventory_rejected_ac13(self):
        for path in ("../outside", "/outside", "C:/outside", "src/../file", "src\\file", "./file"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                readiness.review_source(
                    self.root, {"files": [{"path": path, "git_blob_sha1": "0" * 40}]}
                )

    def test_link_not_read_ac13(self):
        original = readiness.linked
        with patch.object(
            readiness, "linked", side_effect=lambda p: p.name == "index.php" or original(p)
        ):
            with patch.object(Path, "read_bytes", side_effect=AssertionError("linked bytes read")):
                self.assertEqual(
                    readiness.review_source(self.root, self.inventory)["status"], "HOLD"
                )

    def test_environment_values_do_not_leak(self):
        env = {
            name: "SENSITIVE_SENTINEL" for names in readiness.ENV_GROUPS.values() for name in names
        }
        encoded = json.dumps(readiness.credential_presence(env))
        self.assertNotIn("SENSITIVE_SENTINEL", encoded)
        self.assertTrue(all(v["configured"] for v in readiness.credential_presence(env).values()))


class SandboxProbeTests(unittest.TestCase):
    def setUp(self):
        self.env = {name: "SECRET_SENTINEL" for names in probe.REQUIRED.values() for name in names}
        self.env["PAYPAL_ENVIRONMENT"] = "sandbox"

    def never(self, *args):
        self.fail("Network transport must not run")

    def run_live(self, transport, kind="oauth", **kwargs):
        return probe.run_probe(
            kind,
            self.env,
            live=True,
            authority_ref="offline-test-only",
            transport=transport,
            **kwargs,
        )

    def test_default_is_offline(self):
        result = probe.run_probe("oauth", self.env, transport=self.never)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["http_attempts"], 0)

    def test_live_environment_and_missing_authority_deny(self):
        for environment in ("live", "production", "", "Sandbox"):
            env = {**self.env, "PAYPAL_ENVIRONMENT": environment}
            result = probe.run_probe(
                "oauth", env, live=True, authority_ref="test", transport=self.never
            )
            self.assertEqual(result["status"], "BLOCKED")
        result = probe.run_probe("oauth", self.env, live=True, transport=self.never)
        self.assertEqual(result["status"], "BLOCKED")

    def test_empty_credentials_block_without_sending(self):
        self.env["PAYPAL_SANDBOX_CLIENT_SECRET"] = "  "
        self.assertEqual(self.run_live(self.never)["reason"], "credentials_not_configured")

    def test_control_character_in_credentials_blocks_before_network(self):
        for name in probe.REQUIRED["oauth"]:
            with self.subTest(field=name):
                env = {**self.env, name: "\x16PRIVATE_SENTINEL"}
                result = probe.run_probe(
                    "oauth", env, live=True, authority_ref="offline-test-only", transport=self.never
                )
                self.assertEqual(result["reason"], "invalid_local_credential_format")
                self.assertEqual(result["http_attempts"], 0)
                self.assertNotIn("PRIVATE_SENTINEL", json.dumps(result))

    def test_auth_probe_cannot_pass_checkout_lc04(self):
        def transport(kind, headers, body):
            self.assertEqual(kind, "oauth")
            self.assertEqual(body, b"grant_type=client_credentials")
            self.assertTrue(headers["Authorization"].startswith("Basic "))
            return 200, b'{"access_token":"SECRET_TOKEN","token_type":"Bearer","expires_in":300}'

        result = self.run_live(transport)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["evidence_level"], "SYNTHETIC_TRANSPORT")
        self.assertFalse(result["checkout_qualified"])
        self.assertEqual(result["payment_operations"], 0)
        self.assertNotIn("SECRET", json.dumps(result))

    def test_nvp_allows_only_balance_read(self):
        def transport(kind, headers, body):
            self.assertEqual(kind, "nvp-balance")
            fields = probe.parse_qs(body.decode())
            self.assertEqual(fields["METHOD"], ["GetBalance"])
            return 200, b"ACK=Success&L_AMT0=1.00&L_CURRENCYCODE0=USD"

        result = self.run_live(transport, "nvp-balance")
        self.assertEqual(result["status"], "PASS")
        self.assertNotIn("L_AMT", json.dumps(result))
        with self.assertRaises(ValueError):
            probe.run_probe("refund", self.env, live=True, transport=self.never)

    def test_redirect_never_forwards_credentials(self):
        self.assertIsNone(
            probe.NoRedirect().redirect_request(
                None, None, 302, "redirect", {}, "https://example.invalid"
            )
        )
        self.assertEqual(self.run_live(lambda *a: (302, b""))["status"], "UNVERIFIED")

    def test_throttle_auth_error_and_bad_payload_remain_distinct(self):
        for status, payload, expected in [
            (401, b"", "FAIL"),
            (429, b"", "UNVERIFIED"),
            (200, b"[]", "UNVERIFIED"),
            (200, b"bad", "UNVERIFIED"),
            (200, b"x" * 65_537, "UNVERIFIED"),
        ]:
            calls = []

            def transport(*args, calls=calls, status=status, payload=payload):
                calls.append(args[0])
                return status, payload

            with self.subTest(status=status, expected=expected):
                self.assertEqual(self.run_live(transport)["status"], expected)
                self.assertEqual(len(calls), 1)

    def test_ambiguous_transport_never_retries_or_leaks_lc17(self):
        calls = []

        def transport(*args):
            calls.append(1)
            raise TimeoutError("SECRET_SENTINEL in provider diagnostic")

        result = self.run_live(transport)
        self.assertEqual(result["status"], "UNVERIFIED")
        self.assertEqual(len(calls), 1)
        self.assertNotIn("SECRET_SENTINEL", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
