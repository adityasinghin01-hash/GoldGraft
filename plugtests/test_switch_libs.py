"""Every Graft Switch library gives the same answers as the reference on the shared cases.

A library in pieces/switch-libs/<name>/ declares how to run the cases in plug.json:
  {"language": "php", "test": "php run_cases.php ../../../plugtests/switch_cases.json"}
The command runs inside the library folder and must exit 0 only if every case matches.
"""

import json
import shutil
import subprocess
from datetime import datetime

import pytest
from goldgraft_fakes.switch import decide

from .conftest import ROOT

CASES = json.loads((ROOT / "plugtests" / "switch_cases.json").read_text())
LIBS = sorted(p for p in (ROOT / "pieces" / "switch-libs").glob("*/plug.json"))


def test_reference_matches_shared_cases():
    now = datetime.fromisoformat(CASES["now"])
    for case in CASES["cases"]:
        got = decide(case["config"], CASES["public_key_b64"], graft_id=CASES["graft_id"],
                     order_ref=case["order_ref"], now=now, action=case["action"],
                     origin=case["origin"])
        assert got == case["expect"], case["name"]


def test_cases_cover_the_safety_rules():
    names = {c["name"]: c["expect"] for c in CASES["cases"]}
    assert names["no-config"] == names["expired"] == names["tampered-pct"] == "OLD"
    assert names["other-graft"] == "OLD"
    assert names["legacy-refund-at-100"] == names["legacy-refund-invalid-config"] == "OLD"
    assert names["new-refund-at-0"] == "NEW"


@pytest.mark.parametrize("plug", LIBS, ids=lambda p: p.parent.name)
def test_library_passes_shared_cases(plug):
    spec = json.loads(plug.read_text())
    tool = spec["test"].split()[0]
    if shutil.which(tool) is None:
        pytest.skip(f"{tool} not installed here (CI runs it)")
    if tool == "php" and subprocess.run(
        ["php", "-r", 'exit(function_exists("sodium_crypto_sign_verify_detached") ? 0 : 1);'],
        capture_output=True,
    ).returncode:
        # Without sodium the PHP switch fails closed to OLD (correct), so the NEW cases cannot pass.
        pytest.skip("PHP here lacks the sodium extension (CI's PHP has it)")
    result = subprocess.run(spec["test"], shell=True, cwd=plug.parent, capture_output=True,
                            text=True, timeout=120)
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]
