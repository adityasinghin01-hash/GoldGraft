"""All tool permissions, audit hygiene and fixture-backed reads work offline."""

import json
from pathlib import Path

import pytest
from goldgraft_contracts.tools import AGENTS, TOOLS
from goldgraft_fakes.tools import FakeToolbox
from jsonschema import ValidationError

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("spec", TOOLS, ids=lambda s: s.name)
def test_every_tool_refuses_unlisted_agents_and_audits(spec):
    toolbox = FakeToolbox()
    for agent in (*AGENTS, "Unknown"):
        if agent not in spec.allowed_agents:
            with pytest.raises(PermissionError):
                toolbox.call(agent, spec.name, {})
            assert toolbox.audit[-1] == {
                "agent": agent, "tool": spec.name, "args": {}, "allowed": False}


def test_recursive_redaction_on_success_refusal_and_invalid_args():
    toolbox = FakeToolbox()
    arguments = {"path": "x", "content": "Bearer synthetic-credential", "message": "test"}
    toolbox.call("Grafter", "repo.write", arguments)
    assert toolbox.audit[-1]["args"]["content"] == "[REDACTED]"
    assert toolbox.effects[-1]["args"]["content"] == "[REDACTED]"
    assert arguments["content"] == "Bearer synthetic-credential"
    nested = {"filter": {"nested": [{"client_secret": "synthetic", "safe": "ok"}]}}
    toolbox.call("Orchard Analyst", "fleet.read", nested)
    nested["filter"]["nested"][0]["safe"] = "mutated"
    assert toolbox.audit[-1]["args"]["filter"]["nested"][0] == {
        "client_secret": "[REDACTED]", "safe": "ok"}
    with pytest.raises(PermissionError):
        toolbox.call("Surveyor", "repo.write", {"api_key": "synthetic"})
    assert toolbox.audit[-1]["args"] == {"api_key": "[REDACTED]"}
    with pytest.raises(ValidationError):
        toolbox.call("Herald", "ledger.read", {"graft_id": "demo-1", "token": "synthetic"})
    assert toolbox.audit[-1]["args"]["token"] == "[REDACTED]"
    assert toolbox.audit[-1]["allowed"] is False
    with pytest.raises(KeyError):
        toolbox.call("Surveyor", "unknown", {})
    assert toolbox.audit[-1]["allowed"] is False


def test_fixture_reads_filters_and_inert_writes():
    toolbox = FakeToolbox()
    path = ROOT / "fixtures/shops/legacy-php-shop/src/index.php"
    original = path.read_text()
    assert toolbox.call("Surveyor", "repo.read", {"path": "src/index.php"})["content"] == original
    assert toolbox.call("Scribe", "repo.read", {"path": "src/index.php", "max_bytes": 12})[
        "content"] == original.encode()[:12].decode()
    result = toolbox.call("Grafter", "repo.write", {
        "path": "src/index.php", "content": "changed", "message": "test"})
    assert result["ok"] and result["dry_run"] and path.read_text() == original
    capture = toolbox.call("Explorer", "capture.read", {
        "ref": "fixtures://proof/legacy-php-shop/raw/HAPPY.NEW.json"})
    assert capture["scenario_id"] == "HAPPY" and capture["variant"] == "NEW"
    events = toolbox.call("Scribe", "cmel.query", {
        "graft_id": "synthetic-c4", "scenario_id": "REFUND", "variant": "NEW", "kind": "REFUND"})[
            "events"]
    assert events and all(e["kind"] == "REFUND" and e["variant"] == "NEW" for e in events)
    assert toolbox.call("Scribe", "cmel.query", {"graft_id": "missing"}) == {"events": []}
    entries = toolbox.call("Herald", "ledger.read", {"graft_id": "demo-1"})["entries"]
    assert entries == [json.loads(s) for s in (
        ROOT / "fixtures/events/demo_graft_events.jsonl").read_text().splitlines()]
    filtered = toolbox.call("Herald", "ledger.read", {
        "graft_id": "demo-1", "after_seq": 1, "schema": "StageChange/1"})["entries"]
    assert filtered and all(e["seq"] > 1 and e["schema"] == "StageChange/1" for e in filtered)
    assert toolbox.call("Herald", "ledger.read", {"graft_id": "missing"}) == {"entries": []}
    assert toolbox.call("Healer", "heal.read", {"graft_id": "synthetic-c4"})["cases"]
    assert "INSTRUMENT_DECLINED" in toolbox.call("Adversary", "mock.catalogue", {})["codes"]
    audit = toolbox.call("Sentinel", "audit.read", {})["calls"]
    audit.clear()
    assert toolbox.audit


@pytest.mark.parametrize("path", ["../NOTICE.md", "/etc/passwd", "../../../../AGENTS.md"])
def test_repo_read_cannot_escape_vendored_shop(path):
    toolbox = FakeToolbox()
    with pytest.raises(LookupError):
        toolbox.call("Surveyor", "repo.read", {"path": path})
    assert len(toolbox.audit) == 1


@pytest.mark.parametrize("value", ["sk-live-SYNTHETIC", "github_pat_SYNTHETIC", "ghp_SYNTHETIC"])
def test_secret_looking_values_are_redacted_even_under_plain_keys(value):
    toolbox = FakeToolbox()
    toolbox.call("Orchard Analyst", "fleet.read", {"filter": {"note": value}})
    assert toolbox.audit[-1]["args"]["filter"]["note"] == "[REDACTED]"


@pytest.mark.parametrize("key", ["private_key", "credentials", "key"])
def test_secret_key_names_are_redacted_recursively(key):
    toolbox = FakeToolbox()
    toolbox.call("Orchard Analyst", "fleet.read", {"filter": {key: "synthetic"}})
    assert toolbox.audit[-1]["args"]["filter"][key] == "[REDACTED]"
