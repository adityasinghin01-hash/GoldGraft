"""Thirteen offline agent stand-ins. No SDK, LLM, network or external writes.

Payloads use the unchanged example schemas. Formats without producer fields obtain
attribution when the caller appends them to LedgerEntry/1 (design 01 section 1).
"""

from collections.abc import Mapping

from goldgraft_contracts.interfaces import ToolCaller
from goldgraft_contracts.registry import validate
from goldgraft_contracts.tools import AGENTS as AGENT_NAMES

from ._fixtures import example
from .tools import contains_secret

OUTPUTS = {
    "Gardener": ("Assignment", "LaneChange"),
    "Surveyor": ("RootMap",),
    "Builder": ("RunnableShop", "Driver"),
    "Explorer": ("CMEL",),
    "Scribe": ("Contract", "TriangleRequest"),
    "Architect": ("TargetPlan",),
    "Grafter": ("ChangeList",),
    "Adversary": ("ScenarioSet", "MutantSet"),
    "Healer": ("HealNote",),
    "Librarian": ("Recipe", "DetectionRule"),
    "Herald": ("HeraldText",),
    "Orchard Analyst": ("DashboardSpec",),
    "Sentinel": ("Alert",),
}


def numeric_leaves(value, pointer=""):
    """Resolve actual payload numbers, keeping JSON Pointer escaping exact."""
    if type(value) in (int, float):
        yield pointer, value
    elif isinstance(value, dict):
        for key, child in value.items():
            token = key.replace("~", "~0").replace("/", "~1")
            yield from numeric_leaves(child, f"{pointer}/{token}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from numeric_leaves(child, f"{pointer}/{index}")


class FakeAgents:
    def __iter__(self):
        return iter(AGENT_NAMES)

    def __len__(self):
        return len(AGENT_NAMES)

    def run(self, agent: str, inputs: Mapping[str, object],
            tools: ToolCaller) -> list[tuple[str, dict]]:
        if agent not in OUTPUTS:
            raise LookupError(f"Unknown agent: {agent!r}")
        graft_id = inputs.get("graft_id", "demo-1")
        if not isinstance(graft_id, str) or not graft_id:
            raise ValueError("graft_id must be a nonempty string")
        # Explicit, valid fixture calls; each agent exercises its own tool allowlist.
        calls = {
            "Gardener": ("ledger.read", {"graft_id": graft_id}),
            "Surveyor": ("repo.read", {"path": "src/index.php"}),
            "Builder": ("compose.up", {"compose_file": "docker-compose.yml"}),
            "Explorer": ("capture.read", {
                "ref": "fixtures://proof/legacy-php-shop/raw/HAPPY.OLD.json"}),
            "Scribe": ("cmel.query", {"graft_id": "synthetic-c4"}),
            "Architect": ("docs.lookup", {"query": "Orders v2"}),
            "Grafter": ("repo.write", {"path": "payments.php", "content": "// FAKE change",
                                      "message": "FAKE graft intent"}),
            "Adversary": ("mock.catalogue", {}),
            "Healer": ("heal.read", {"graft_id": "synthetic-c4"}),
            "Librarian": ("selfcheck.run", {"recipe_id": "recipe-1"}),
            # Demo feed is the source even when the output targets a different graft.
            "Herald": ("ledger.read", {"graft_id": "demo-1"}),
            "Orchard Analyst": ("fleet.read", {}),
            "Sentinel": ("audit.read", {}),
        }
        name, args = calls[agent]
        evidence = tools.call(agent, name, args)
        context = {}
        result = []
        for schema in OUTPUTS[agent]:
            payload = example(schema)
            if "graft_id" in payload:
                payload["graft_id"] = graft_id
            if "producer" in payload:
                payload["producer"].update(kind="agent", name=agent)
            if schema == "HeraldText":
                entries = evidence["entries"]
                context = {"ledger_entries": {e["entry_hash"]: e for e in entries}}
                candidates = [(entry, pointer, value) for entry in entries
                              for pointer, value in numeric_leaves(entry["payload"], "/payload")]
                if not candidates:
                    raise LookupError("Herald needs a numeric payload in the demo ledger feed")
                # Prefer meaningful proof metrics over tracker attempt counts.
                chosen = next((c for c in candidates if c[1].endswith("/score")), candidates[0])
                entry, pointer, value = chosen
                payload["numbers_used"] = [{"entry_hash": entry["entry_hash"],
                                            "json_pointer": pointer, "value": value}]
                payload["text"] = f"Demo ledger {entry['schema']} records {pointer}: {value}."
            if schema == "Alert":
                calls_seen = [*evidence["calls"], *inputs.get("audit", [])]
                breaches = [call for call in calls_seen
                            if not call.get("allowed", False)
                            or contains_secret(call.get("args", {}))]
                payload.update(
                    severity="CRITICAL" if breaches else "MINOR",
                    message="Tool policy breach" if breaches else "No tool policy breach",
                    evidence_refs=[f"fake://audit/{i}" for i, call in enumerate(calls_seen)
                                   if call in breaches])
            artifact = validate(f"{schema}/1", payload, context=context)
            result.append((f"{schema}/1", artifact.model_dump(mode="json")))
        if agent == "Explorer":
            twin = result[0][1].copy()
            twin.update(variant="OLD_TWIN", run_id="run-1-twin")
            result.append(("CMEL/1", twin))
        return result


AGENTS = FakeAgents()
