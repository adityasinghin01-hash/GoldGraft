"""Agent calling convention, artifacts and code-enforced tool ownership (no LLM).

GOLDGRAFT_AGENTS=pieces.agents.registry:AGENTS uv run pytest plugtests/test_agents.py
The registry exposes AgentRunner.run(agent, inputs, tools).
"""

import json

import pytest
from goldgraft_contracts.agents import AgentArtifact
from goldgraft_contracts.interfaces import AgentRunner
from goldgraft_contracts.registry import validate
from goldgraft_contracts.tools import AGENTS as NAMES
from goldgraft_contracts.tools import tool
from goldgraft_fakes.tools import FakeToolbox

from .conftest import ROOT, load

EXPECTED = {
    "Gardener": {"Assignment/1", "LaneChange/1"}, "Surveyor": {"RootMap/1"},
    "Builder": {"RunnableShop/1", "Driver/1"}, "Explorer": {"CMEL/1"},
    "Scribe": {"Contract/1"}, "Architect": {"TargetPlan/1"}, "Grafter": {"ChangeList/1"},
    "Adversary": {"ScenarioSet/1", "MutantSet/1"}, "Healer": {"HealNote/1"},
    "Librarian": {"Recipe/1", "DetectionRule/1"}, "Herald": {"HeraldText/1"},
    "Orchard Analyst": {"DashboardSpec/1"}, "Sentinel": {"Alert/1"},
}


def ledger_context():
    entries = [json.loads(line) for line in (
        ROOT / "fixtures/events/demo_graft_events.jsonl").read_text().splitlines()]
    return {"ledger_entries": {entry["entry_hash"]: entry for entry in entries}}


@pytest.fixture(scope="module")
def agents():
    obj, _ = load("GOLDGRAFT_AGENTS", "goldgraft_fakes.agents:AGENTS")
    return obj


def test_calling_convention(agents):
    assert isinstance(agents, AgentRunner)
    assert len(NAMES) == 13  # each name is exercised by the parametrized test below


@pytest.mark.parametrize("agent", NAMES)
def test_artifacts_and_allowed_calls(agents, agent):
    toolbox = FakeToolbox()
    artifacts = agents.run(agent, {"graft_id": "demo-1"}, toolbox)
    assert artifacts
    assert EXPECTED[agent] <= {schema for schema, _ in artifacts}
    for schema, payload in artifacts:
        artifact = validate(schema, payload, context=ledger_context())
        if "graft_id" in type(artifact).model_fields:
            assert artifact.graft_id == "demo-1"
        if isinstance(artifact, AgentArtifact):
            assert artifact.producer.kind == "agent" and artifact.producer.name == agent
        if schema == "HeraldText/1":
            assert artifact.numbers_used, "Herald must copy a real demo-feed payload number"
            assert all(str(n.value) in artifact.text for n in artifact.numbers_used)
    assert toolbox.audit, "Every agent must use at least one allowed tool"
    for call in toolbox.audit:
        assert call["agent"] == agent and call["allowed"]
        assert agent in tool(call["tool"]).allowed_agents
    writers = {call["agent"] for call in toolbox.audit if call["tool"] == "repo.write"}
    assert writers == ({"Grafter"} if agent == "Grafter" else set())


def test_sentinel_critical_on_refused_call(agents):
    toolbox = FakeToolbox()
    with pytest.raises(PermissionError):
        toolbox.call("Surveyor", "repo.write", {
            "path": "checkout.php", "content": "planted", "message": "refused"})
    artifacts = agents.run("Sentinel", {"graft_id": "demo-1", "audit": toolbox.audit}, toolbox)
    alerts = [validate(schema, payload) for schema, payload in artifacts if schema == "Alert/1"]
    assert alerts and any(alert.severity == "CRITICAL" for alert in alerts)
