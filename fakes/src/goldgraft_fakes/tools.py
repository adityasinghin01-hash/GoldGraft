"""Offline tool dispatcher. Permissions apply to every tool, regardless of effect.

Read tools return labelled fixture evidence. Other tools record redacted intent and
acknowledge a dry run; no shell, network, repository write or controller is invoked.
"""

import copy
import re

from goldgraft_contracts.tools import SideEffect
from goldgraft_contracts.tools import tool as tool_spec
from jsonschema import Draft202012Validator

from ._fixtures import PROOF, SHOP, boundary, example, ledger_entries, read
from .runner import FakeRunner

_SECRET_KEY = re.compile(
    r"secret|password|passwd|(?:^|[_-])(?:pwd|key)(?:$|[_-])|token|authorization|cookie|"
    r"api[_-]?key|private[_-]?key|credential|signature",
    re.I,
)
_SECRET_VALUE = re.compile(
    r"\[REDACTED\]|\b(?:Bearer|Basic)\s+\S+|\bsk[-_]|github_pat_|gh[pousr]_|"
    r"AKIA[0-9A-Z]{12}|-----BEGIN [A-Z ]*PRIVATE KEY|"
    r"(?:secret|password|passwd|access[_-]?token|api[_-]?key)\s*[\"']?\s*[:=]\s*\S+",
    re.I,
)


def redact(value):
    """Copy recursively; redact entire sensitive values, including embedded credentials."""
    if isinstance(value, dict):
        return {key: "[REDACTED]" if _SECRET_KEY.search(str(key)) else redact(child)
                for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(child) for child in value]
    if isinstance(value, str) and _SECRET_VALUE.search(value):
        return "[REDACTED]"
    return copy.deepcopy(value)


def contains_secret(value):
    if isinstance(value, dict):
        return any(_SECRET_KEY.search(str(key)) or contains_secret(child)
                   for key, child in value.items())
    if isinstance(value, (list, tuple)):
        return any(contains_secret(child) for child in value)
    return isinstance(value, str) and bool(_SECRET_VALUE.search(value))


class FakeToolbox:
    def __init__(self):
        self.audit: list[dict] = []
        self.effects: list[dict] = []

    def call(self, agent: str, tool: str, args: dict) -> dict:
        record = {"agent": agent, "tool": tool, "args": redact(args), "allowed": False}
        self.audit.append(record)
        spec = tool_spec(tool)
        if agent not in spec.allowed_agents:
            raise PermissionError(f"{agent!r} is not allowed to call {tool!r}")
        Draft202012Validator(spec.input_schema).validate(args)
        record["allowed"] = True
        if spec.side_effect != SideEffect.READ:
            self.effects.append(copy.deepcopy(record))
            result = {"ok": True, "dry_run": True, "tool": tool}
        else:
            result = self._read(tool, args)
        Draft202012Validator(spec.output_schema).validate(result)
        return result

    def _read(self, tool, args):
        if tool == "repo.read":
            # Both sides are fixtures; NEW source is the C4 illustrative rewrite.
            base = SHOP if args.get("side", "OLD") == "OLD" else PROOF / "new_sample"
            path = (base / args["path"]).resolve()
            if not path.is_relative_to(base.resolve()) or not path.is_file():
                raise LookupError("repo.read path is outside the fixture shop or does not exist")
            content = path.read_bytes()
            if "max_bytes" in args:
                content = content[:args["max_bytes"]]
            return {"path": args["path"], "content": content.decode(errors="replace")}
        if tool == "capture.read":
            return FakeRunner().fetch_capture(args["ref"]).model_dump(mode="json")
        if tool == "cmel.query":
            result = [event for path in sorted((PROOF / "cmel").glob("*.json"))
                      for event in read(path)]
            return {"events": [event for event in result if all(
                event[field] == args[field]
                for field in ("graft_id", "scenario_id", "variant", "kind") if field in args)]}
        if tool == "ledger.read":
            return {"entries": [e for e in ledger_entries()
                                if e["graft_id"] == args["graft_id"]
                                and e["seq"] > args.get("after_seq", 0)
                                and ("schema" not in args or e["schema"] == args["schema"])]}
        if tool == "heal.read":
            cases = []
            for path in sorted((PROOF / "heal").glob("*.events.json")):
                events = [e for e in read(path) if e["graft_id"] == args["graft_id"]]
                if events:
                    cases.append({"case": path.name.removesuffix(".events.json"), "events": events,
                                  "evidence": read(path.with_name(
                                      path.name.replace(".events.", ".evidence.")))})
            return {"cases": cases}
        if tool == "audit.read":
            return {"calls": copy.deepcopy(self.audit[args.get("since_seq", 0):])}
        if tool == "mock.catalogue":
            return {"codes": ["INSTRUMENT_DECLINED", "PAYER_ACTION_REQUIRED",
                              "FAKE_CAPTURE_PENDING"],
                    "label": "FAKE_CAPTURE_PENDING is a fake-only extension"}
        if tool == "budget.read":
            return {"graft_id": args["graft_id"], "budget": example("BudgetRecord"),
                    "label": "Synthetic example, not measured usage"}
        if tool == "astgrep.run":
            return {"matches": read(SHOP / "goldgraft-shop.yaml")["answer_key"]["touchpoints"],
                    "label": "Fixture touchpoints, not an executed ast-grep rule"}
        if tool == "site.crawl":
            return {"url": args["url"], "touchpoints": read(
                SHOP / "goldgraft-shop.yaml")["answer_key"]["touchpoints"],
                "label": "Fixture evidence; no live crawl"}
        if tool == "paypal.txsearch.read":
            return {"events": [e for p in sorted((PROOF / "cmel").glob("*.json"))
                               for e in read(p) if e["source"] == "PAYPAL_LEDGER"],
                    "label": "C4 synthetic ledger observations, not Transaction Search results"}
        if tool == "paypal.buttons.read":
            return {"buttons": [], "label": "No hosted buttons in legacy-php-shop"}
        if tool == "trace.mine":
            return {"contract": boundary("Contract/1", PROOF / "contract.json").model_dump(
                mode="json"), "label": "C4 fixture contract; no inference"}
        if tool in {"ruleshub.lookup", "docs.lookup"}:
            return {"target_plan": read(PROOF / "target_plan.json"),
                    "label": "C4 mappings with public doc URLs; no online lookup"}
        if tool == "recipes.lookup":
            recipe = example("Recipe")
            matches = all(recipe["fingerprint"].get(k) == v for k, v in args.items())
            return {"recipes": [recipe] if matches else []}
        if tool == "sdk.reflect":
            return {"classes": [], "label": "No SDK installed by this stand-in"}
        if tool == "deps.check":
            return {"allowed": False, "label": "No dependency allowlist evidence in fixtures"}
        if tool == "fleet.read":
            entries = ledger_entries()
            return {"grafts": sorted({e["graft_id"] for e in entries}),
                    "label": "Synthetic demo fleet"}
        raise LookupError(f"No offline read implementation for {tool!r}")
