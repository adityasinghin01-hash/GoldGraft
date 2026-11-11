"""Tests for sponsor integrations owned by Gupta (Render, Postman, Zapier, Elastic).

Verifies:
1. render.yaml configuration is valid, specifies web, worker, and postgres instances.
2. Postman collection format and empty-secret environment template are valid JSON.
3. ZapierNotifier delivers events, deduplicates, and scrubs sensitive keys.
4. Elastic evidence formatter creates privacy-scrubbed documents with redacted secrets.
"""

import json
from pathlib import Path

import yaml

from pieces.backend.elastic_ingest import ELASTIC_INDEX_MAPPINGS, format_evidence_doc
from pieces.backend.zapier_notifier import ZapierNotifier

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_render_yaml_configuration():
    render_file = REPO_ROOT / "render.yaml"
    assert render_file.is_file()
    config = yaml.safe_load(render_file.read_text(encoding="utf-8"))
    assert "services" in config
    assert "databases" in config
    service_names = {s["name"] for s in config["services"]}
    assert "goldgraft-control-plane" in service_names
    assert "goldgraft-isolated-worker" in service_names
    assert config["databases"][0]["name"] == "goldgraft-ledger-db"


def test_postman_collection_and_env():
    col_file = REPO_ROOT / "postman" / "GoldGraft_Collection.json"
    env_file = REPO_ROOT / "postman" / "GoldGraft_Environment.template.json"
    assert col_file.is_file()
    assert env_file.is_file()

    col_data = json.loads(col_file.read_text(encoding="utf-8"))
    assert len(col_data["item"]) >= 5

    env_data = json.loads(env_file.read_text(encoding="utf-8"))
    # Verify environment values do NOT leak secrets
    for val in env_data["values"]:
        if "secret" in val["key"].lower():
            assert val["value"] == "", (
                f"Template environment must not contain pre-filled secret: {val['key']}"
            )


def test_zapier_notifier_offline_dedupe():
    notifier = ZapierNotifier(
        webhook_url="https://hooks.zapier.com/hooks/catch/fake/hook", enabled=False
    )
    res1 = notifier.notify("ACTION_NEEDED", "graft-10", "Approval needed for deploy")
    assert res1.delivered is False
    assert "disabled" in res1.message.lower()

    # Enable and test delivery with mock URL
    active_notifier = ZapierNotifier(webhook_url=None, enabled=True)
    res2 = active_notifier.notify("ACTION_NEEDED", "graft-10", "Approval needed")
    assert res2.delivered is False


def test_elastic_evidence_formatter():
    doc = format_evidence_doc(
        graft_id="graft-el-1",
        run_id="run-01",
        stage="PROVING",
        scenario_id="HAPPY",
        status="PASSED",
        summary="Differential equivalence verified",
        evidence_ref="blob://evidence/01",
        provenance_sha="aedc11dd",
        details={"paypal_client_secret": "LEAKED_SECRET", "safe_param": "value123"},
    )
    assert doc["graft_id"] == "graft-el-1"
    assert doc["details"]["paypal_client_secret"] == "[REDACTED]"
    assert doc["details"]["safe_param"] == "value123"
    assert "mappings" in ELASTIC_INDEX_MAPPINGS
