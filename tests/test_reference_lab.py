"""Offline tests; real Docker/HTTP checks are explicit reference_lab.py commands."""

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("reference_lab", ROOT / "scripts/reference_lab.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class LabTests(unittest.TestCase):
    def test_original_source_bytes_and_license_preserved(self):
        vendor = ROOT / "pieces/shops/legacy-php-shop/vendor"
        manifest = json.loads((vendor / "source.json").read_text())
        self.assertEqual(len(manifest["files"]), 15)
        for entry in manifest["files"]:
            data = (vendor / entry["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"])
            self.assertEqual(
                hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest(),
                entry["git_blob_sha1"],
            )
        self.assertIn("Copyright (c) 2026 jeretc", (vendor / "LICENSE.cutover").read_text())

    def test_lab_key_reused_and_invalid_key_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path, first = lab.prepare_key(Path(directory))
            self.assertEqual(lab.prepare_key(Path(directory))[1], first)
            self.assertEqual(len(first), 64)
            path.write_text("invalid")
            with self.assertRaises(lab.LabHold):
                lab.prepare_key(Path(directory))
            self.assertEqual(path.read_text(), "invalid")

    def test_unavailable_engine_cannot_dispatch_build(self):
        with patch.object(lab, "run_docker", side_effect=lab.LabHold("failed")) as run:
            with self.assertRaisesRegex(lab.LabHold, "DOCKER_ENGINE_UNAVAILABLE"):
                lab.execute("up", Path("docker"), {}, "synthetic-key")
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[1][0], "info")

    def test_auth_bypass_fails_actual_check_component(self):
        def response(path, key=None, method="GET"):
            if path == "/__lab/health":
                return 200, b'{"payments":"disabled"}'
            return 200, b"fake unprotected page"

        with patch.object(lab, "request", side_effect=response):
            with self.assertRaisesRegex(lab.LabHold, "UNAUTHENTICATED_ROUTE_NOT_DENIED"):
                lab.check_http("synthetic-key")

    def test_redirect_does_not_send_lab_key_elsewhere(self):
        self.assertIsNone(
            lab.NoRedirect().redirect_request(
                None, None, 302, "redirect", {}, "https://example.invalid"
            )
        )


if __name__ == "__main__":
    unittest.main()
