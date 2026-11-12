"""Offline negatives for portable-source admission; no sockets/providers/processes."""

import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("portable_lab", ROOT / "scripts/portable_lab.py")
portable = importlib.util.module_from_spec(spec)
spec.loader.exec_module(portable)


class PortableSourceTests(unittest.TestCase):
    def test_modified_source_rejected_before_start(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = b'<?php echo "offline fixture";'
            (root / "index.php").write_bytes(data)
            digest = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            inventory = {"files": [{"path": "src/index.php", "git_blob_sha1": digest}]}
            portable.verify_vendor(root, inventory)
            (root / "index.php").write_bytes(data + b" changed")
            with self.assertRaisesRegex(portable.lab.LabHold, "PINNED_VENDOR_BYTES_CHANGED"):
                portable.verify_vendor(root, inventory)

    def test_unlisted_source_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "injected.php").write_text("<?php // offline fixture")
            with self.assertRaisesRegex(portable.lab.LabHold, "PINNED_VENDOR_FILE_SET_CHANGED"):
                portable.verify_vendor(root, {"files": []})


if __name__ == "__main__":
    unittest.main()
