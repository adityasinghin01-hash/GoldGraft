"""Agent tools as DATA: every tool in design 06's "Allowed tools" column.

Aditya's agents mount these (stand-in implementations in goldgraft_fakes.tools, real
ones later). A tool may only be called by the agents listed in ``allowed_agents``;
PRIVILEGED tools are additionally checked by code, never trusted to an LLM
(design 00 §3: verdicts, signing, PRs and switch moves are decided by code).
"""

from dataclasses import dataclass, field
from enum import StrEnum

from .plan5_tools import TOOL_CATALOG as V2_TOOL_CATALOG
from .plan5_tools import V2_TOOLS, validate_tool_arguments

__all__ = [
    "AGENTS",
    "TOOLS",
    "SideEffect",
    "ToolSpec",
    "tool",
    "tools_for",
    "V2_TOOL_CATALOG",
    "V2_TOOLS",
    "validate_tool_arguments",
]


class SideEffect(StrEnum):
    READ = "READ"            # reads data only
    SANDBOXED = "SANDBOXED"  # acts only inside the locked box / sandbox / own artifact
    PRIVILEGED = "PRIVILEGED"  # changes merchant code, buyers' path or stops an agent


def _obj(required: dict[str, dict] | None = None, optional: dict[str, dict] | None = None):
    props = {**(required or {}), **(optional or {})}
    return {"type": "object", "properties": props, "required": sorted(required or {}),
            "additionalProperties": False}


S = {"type": "string", "minLength": 1}
INT = {"type": "integer", "minimum": 0}
ARR_S = {"type": "array", "items": S}
ANY = {}


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    side_effect: SideEffect
    allowed_agents: tuple[str, ...]
    input_schema: dict = field(default_factory=lambda: _obj())
    output_schema: dict = field(default_factory=lambda: {"type": "object"})


T = ToolSpec
R, X, P = SideEffect.READ, SideEffect.SANDBOXED, SideEffect.PRIVILEGED

TOOLS: tuple[ToolSpec, ...] = (
    # Gardener
    T("ledger.read", "Read ledger entries for a graft (summaries or full payloads)", R,
      ("Gardener", "Herald"), _obj({"graft_id": S}, {"after_seq": INT, "schema": S})),
    T("stage.assign", "Assign the current stage's work to an agent (writes Assignment/1)", X,
      ("Gardener",), _obj({"graft_id": S, "agent": S, "task": S})),
    T("lane.set", "Switch a graft to a fallback lane (writes LaneChange/1)", X, ("Gardener",),
      _obj({"graft_id": S, "lane": S, "reason": S})),
    T("budget.read", "Read $ and token use vs caps for a graft", R, ("Gardener",),
      _obj({"graft_id": S})),
    # Surveyor
    T("repo.read", "Read files from the merchant repo (OLD) or the graft branch (NEW)", R,
      ("Surveyor", "Scribe", "Adversary"),
      _obj({"path": S}, {"side": {"enum": ["OLD", "NEW"]}, "max_bytes": INT})),
    T("astgrep.run", "Run an ast-grep rule over the repo; returns matches with file:line", R,
      ("Surveyor",), _obj({"rule": S}, {"lang": S})),
    T("site.crawl", "Crawl the live site for PayPal buttons/forms/scripts", R, ("Surveyor",),
      _obj({"url": S}, {"max_pages": INT})),
    T("paypal.txsearch.read", "PayPal Transaction Search: money by T-code (read-only)", R,
      ("Surveyor",), _obj({"days": INT})),
    T("paypal.buttons.read", "PayPal Button Manager: list hosted buttons (read-only)", R,
      ("Surveyor",)),
    # Builder
    T("cage.shell", "Run a command inside the locked box (BUILD or RUN phase)", X,
      ("Builder",), _obj({"command": S, "phase": {"enum": ["BUILD", "RUN"]}})),
    T("compose.up", "Start the shop's containers in the locked box", X, ("Builder",),
      _obj({"compose_file": S})),
    T("playwright", "Run a browser script against the shop in the locked box", X,
      ("Builder",), _obj({"script": S})),
    T("tunnel.open", "Open a tunnel so PayPal can reach the shop's return/notify URLs", X,
      ("Builder",), _obj({"port": INT})),
    # Explorer
    T("driver.run", "Run the proven checkout driver for one scenario", X, ("Explorer",),
      _obj({"scenario_id": S, "variant": {"enum": ["OLD", "OLD_TWIN", "NEW"]}})),
    T("scenario.run", "Run a scenario on the OLD shop and record it", X, ("Explorer",),
      _obj({"scenario_id": S})),
    T("capture.read", "Read a recorded run (RawCapture/1)", R, ("Explorer",), _obj({"ref": S})),
    # Scribe
    T("cmel.query", "Query money events (CMEL/1) by scenario/variant/kind", R, ("Scribe",),
      _obj({"graft_id": S}, {"scenario_id": S, "variant": S, "kind": S})),
    T("trace.mine", "Mine candidate money rules from recorded money events", R, ("Scribe",),
      _obj({"graft_id": S})),
    # Architect
    T("ruleshub.lookup", "Look up PayPal RulesHub guidance for a language + operation", R,
      ("Architect",), _obj({"lang": S, "topic": S})),
    T("docs.lookup", "Look up PayPal docs (llms.txt / docs.paypal.ai)", R, ("Architect",),
      _obj({"query": S})),
    T("recipes.lookup", "Find Scion Bank recipes by fingerprint", R, ("Architect",),
      _obj({"lang": S, "family": S}, {"framework": S})),
    # Grafter (the only writer)
    T("repo.write", "Write files on the graft branch only (never the default branch)", P,
      ("Grafter",), _obj({"path": S, "content": S, "message": S})),
    T("sdk.reflect", "List classes/methods that really exist in an installed PayPal SDK", R,
      ("Grafter",), _obj({"lang": S, "package": S})),
    T("deps.check", "Check a dependency against the allowlist + licence", R, ("Grafter",),
      _obj({"lang": S, "package": S, "version": S})),
    T("recipe.apply", "Apply an ACTIVE recipe to the graft branch (deterministic)", X,
      ("Grafter",), _obj({"recipe_id": S})),
    # Adversary
    T("mutant.place", "Place one MMO-12 money bug in a COPY of the NEW code", X,
      ("Adversary",), _obj({"op": S, "file": S, "line": INT})),
    T("scenario.write", "Write a scenario (Scenario/1) for a rule", X, ("Adversary",),
      _obj({"scenario": ANY})),
    T("mock.catalogue", "List PayPal-Mock-Response error codes we can trigger", R,
      ("Adversary",)),
    # Healer
    T("heal.read", "Read go-live signals for a graft", R, ("Healer",), _obj({"graft_id": S})),
    T("heal.pause", "Ask the Heal Controller to hold the current stage", P, ("Healer",),
      _obj({"graft_id": S, "reason": S})),
    T("heal.request_cutback", "Ask the Heal Controller to switch buyers back (code decides)",
      P, ("Healer",), _obj({"graft_id": S, "reason": S})),
    # Librarian
    T("recipe.write", "Store a recipe in QUARANTINE", X, ("Librarian",), _obj({"recipe": ANY})),
    T("selfcheck.run", "Re-apply a recipe to its origin shop and re-run the proof", X,
      ("Librarian",), _obj({"recipe_id": S})),
    T("rules.propose", "Propose a new detection rule from a runtime miss", X,
      ("Librarian",), _obj({"rule": ANY})),
    # Orchard Analyst
    T("fleet.read", "Read fleet tables (shops, stages, money by family)", R,
      ("Orchard Analyst",), _obj({}, {"filter": ANY})),
    T("agstudio.agent", "Ask the AG Studio agent to build a dashboard", X,
      ("Orchard Analyst",), _obj({"question": S})),
    # Sentinel
    T("audit.read", "Read every agent's tool calls + outputs", R, ("Sentinel",),
      _obj({}, {"since_seq": INT})),
    T("agent.halt", "Stop an agent on a policy breach", P, ("Sentinel",),
      _obj({"agent": S, "reason": S})),
)

AGENTS = ("Gardener", "Surveyor", "Builder", "Explorer", "Scribe", "Architect", "Grafter",
          "Adversary", "Healer", "Librarian", "Herald", "Orchard Analyst", "Sentinel")


def tool(name: str) -> ToolSpec:
    for spec in TOOLS:
        if spec.name == name:
            return spec
    raise KeyError(name)


def tools_for(agent: str) -> tuple[ToolSpec, ...]:
    return tuple(spec for spec in TOOLS if agent in spec.allowed_agents)
