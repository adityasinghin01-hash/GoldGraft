"""Runner plug-in tests; a real runner uses GitHub Actions + sandbox and is opt-in.

GOLDGRAFT_RUNNER=pieces.runner.runner:Runner uv run pytest plugtests/test_runner.py
Set GOLDGRAFT_LIVE=1 as well to execute the real runner. No class is imported before
pytest applies the live skip, so the documented command is safe with an absent piece.
"""

import json
import os

import pytest
from goldgraft_contracts.registry import validate
from goldgraft_contracts.runner import SECRET_HEADERS

from .conftest import ROOT, load

pytestmark = pytest.mark.live if os.environ.get("GOLDGRAFT_RUNNER") else []


@pytest.fixture(scope="module")
def runner():
    cls, _ = load("GOLDGRAFT_RUNNER", "goldgraft_fakes.runner:FakeRunner")
    return cls()


def job(**updates):
    data = json.loads((ROOT / "contracts/examples/JobSpec.1.json").read_text())
    data.update(shop_pack_ref="fixtures://shops/legacy-php-shop/goldgraft-shop.yaml",
                scenario_ids=["HAPPY", "REFUND"], variants=["OLD", "OLD_TWIN", "NEW"])
    data.update(updates)
    return validate("JobSpec/1", data)


@pytest.mark.parametrize("kind", ["RECORD", "PROVE"])
def test_job_and_every_capture(runner, kind):
    spec = job(kind=kind)
    result = validate("JobResult/1", runner.run_job(spec))
    assert result.job_id == spec.job_id and result.status == "OK"
    assert result.error is None
    assert result.raw_capture_refs
    seen = []
    for ref in result.raw_capture_refs:
        capture = validate("RawCapture/1", runner.fetch_capture(ref))
        seen.append((capture.scenario_id, capture.variant))
        for exchange in capture.exchanges:
            for name, value in exchange.headers.items():
                name = name.lower()
                if name in SECRET_HEADERS or any(s in name for s in ("secret", "token", "api-key",
                                                                      "api_key")):
                    assert value == "[REDACTED]", f"unredacted secret header: {name}"
    assert sorted(seen) == sorted((s, v) for s in spec.scenario_ids for v in spec.variants)


def test_timeout(runner):
    result = validate("JobResult/1", runner.run_job(job(scenario_ids=["HAPPY__timeout"])))
    assert result.status == "TIMEOUT"
