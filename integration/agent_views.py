"""API views of integrated thirteen-role runs (real models, connected graph, scripted runner).

Reads one run's evidence directory written by scripts/live_integrated_run.py (RESULT.json,
OUTPUTS.json) and projects it into the published v1 shapes the frontend already consumes:
Graft, the hash-chained ledger (StageChange/1, BudgetRecord/1, Alert/1, HealNote/1), RootMap.
The ledger is built with the foundation Ledger, so every entry is schema-validated and chained.
It grows as the run's RESULT.json grows (live progress by SSE reconnect).

Honest labels: no independent SH proof or certificate is produced by this graph yet, so
proof/scenario views are not served for these runs; the card says so.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from goldgraft_contracts.api import Graft
from goldgraft_foundation.blobs import LocalBlobStore
from goldgraft_foundation.ledger import Ledger

PRODUCER = {"kind": "service", "name": "integrated-agent-run", "version": "1"}
MODELS = {"haiku": "claude-haiku-5-5", "haiku8": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5"}
# Task → lifecycle stage it completes (only the published Stage names; nothing past PROVING
# is claimed, because no independent proof runs in this graph).
STAGE_OF = {
    "gardener:propose_plan": "GATED",
    "survey": "SURVEYED",
    "builder:build_baseline": "BUILT",
    "baseline-old-twin": "RECORDED",
    "scribe-final": "CONTRACTED",
    "adversary-guards": "ATTACK_PLANNED",
    "grafter": "GRAFTED",
    "adversary-mutant": "PROVING",
}
WORDS = {
    "gardener:propose_plan": "Gardener admitted the survey stage",
    "survey": "Surveyor mapped the old PayPal code",
    "builder:build_baseline": "Builder built the surveyed shop",
    "baseline-old-twin": "Explorer recorded the old shop twice",
    "scribe-final": "Scribe wrote the money rules",
    "grafter": "Grafter wrote the new checkout",
    "adversary-guards": "Adversary planned the attacks",
    "adversary-mutant": "Adversary ran a planted bug",
}
# What each step's input really was (shown beside every agent in the app). "real" = this shop's
# own data; "mixed" = real run data plus a recorded/controlled part; "sample" = qualified sample.
RECORDED = "recorded runner, not a live shop"
INPUTS = {
    "gardener:propose_plan": ("mixed", "Admits this run's first stage; plan ids are the sample's"),
    "survey": ("real", "The submitted shop's own source files"),
    "herald": ("real", "The Surveyor's committed map of this shop"),
    "builder:build_baseline": ("mixed", f"This shop's surveyed source; the build is a {RECORDED}"),
    "baseline-old": ("sample", f"Old-shop payment capture from the {RECORDED}"),
    "baseline-old-twin": ("sample", f"Second old-shop capture from the {RECORDED}"),
    "followup-0": ("sample", f"Follow-up capture asked for by the Scribe, {RECORDED}"),
    "scribe-draft": ("mixed", "Recorded traces and the sample checkout's facts"),
    "scribe-final": ("mixed", "Recorded traces and the sample checkout's facts"),
    "architect": ("real", "The Surveyor's real map, scoped to the supported PayPal calls"),
    "grafter": ("real", "The shop's real payment files and the Architect's plan"),
    "candidate-build": ("mixed", f"The AI-written files (PHP checked); build is a {RECORDED}"),
    "candidate-new": ("sample", f"New-checkout capture from the {RECORDED}"),
    "adversary-guards": ("sample", "The sample checkout's money rule, not yet the AI-written code"),
    "adversary-mutant": ("sample", "A planted bug in the sample checkout, recorded runner"),
    "healer-golive": ("mixed", "A controlled go-live fault on this run's new-checkout capture"),
    "sentinel-audit": ("mixed", "This run's real step outcomes plus one controlled hostile event"),
    "librarian-recipe": ("sample", "The qualified de-identified recipe template (quarantined)"),
    "orchard-aggregate": ("mixed", "Counts over this machine's test runs, small groups hidden"),
}


def _clip(text, n=420):
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def summarize(schema, p):
    """One plain sentence for an agent output (the app shows it beside the agent)."""
    name = schema.split("/")[0]
    if name == "PlanProposal":
        steps = [t.get("task_id") or t.get("role") for t in p.get("tasks", [])]
        return f"Plan of {len(steps)} step(s): {', '.join(map(str, steps))}"
    if name == "RootMap":
        spots = p.get("touchpoints", [])
        files = {t.get("location", {}).get("file") for t in spots}
        return f"Found {len(spots)} old PayPal spots in {len(files)} files"
    if name == "HeraldText":
        return _clip(p.get("text"))
    if name == "ExecutionProposal":
        variant = f" ({p['variant']})" if p.get("variant") else ""
        return f"Asked the runner to {str(p.get('operation', '')).replace('_', ' ')}{variant}"
    if name == "Contract":
        rules = p.get("rules", [])
        titles = "; ".join(f"{r.get('title')} [{r.get('severity')}]" for r in rules)
        return f"{len(rules)} money rule(s): {titles}"
    if name == "TriangleRequest":
        return _clip(f"Asked for more evidence on rule {p.get('rule_id')}: {p.get('reason')}")
    if name == "TargetPlan":
        items = p.get("items", [])
        ops = sorted({i.get("target_op") for i in items if i.get("target_op")})
        return f"Planned {len(items)} change(s) to {', '.join(ops)}"
    if name == "ChangeList":
        changes = p.get("changes", [])
        ids = {i for c in changes for i in c.get("plan_item_ids", [])}
        lead = _clip(changes[0].get("summary"), 220) if changes else ""
        return f"Wrote code for {len(ids)} planned item(s). {lead}".strip()
    if name == "ScenarioSet":
        sc = p.get("scenarios", [])
        preds = "; ".join(s.get("expect", {}).get("predicate", s.get("id", "")) for s in sc)
        return f"{len(sc)} attack scenario(s): {preds}"
    if name == "MutantSet":
        ms = p.get("mutants", [])
        return f"{len(ms)} planted bug(s): " + "; ".join(str(m.get("patch")) for m in ms)
    if name == "HealNote":
        asks = [
            w
            for w, k in (("pause", "pause_requested"), ("cut back", "cutback_requested"))
            if p.get(k)
        ]
        ask = f" Asked to {' and '.join(asks)} go-live." if asks else ""
        return _clip(p.get("text"), 360) + ask
    if name == "Alert":
        return _clip(p.get("message"))
    if name == "Recipe":
        fp = p.get("fingerprint", {})
        return f"Recipe for {fp.get('lang')} {fp.get('family')}: {p.get('status')} (not activated)"
    if name == "DetectionRule":
        return f"Detection rule for {p.get('language')} {p.get('operation')}: {p.get('pattern')}"
    if name == "DashboardSpec":
        return f"{p.get('title')}: {p.get('question')}"
    return name


class IntegratedRunViews:
    def __init__(self, directory: Path, *, ledger_directory: Path | None = None):
        self.directory = Path(directory)
        self.graft_id = self.directory.name
        result = self._result()
        self.shop_id = result.get("shop", "legacy-php-shop")
        # HTTP readers can keep derived state separate from read-only run evidence.
        ledger_directory = (
            Path(ledger_directory) if ledger_directory is not None else self.directory
        )
        self.store = LocalBlobStore(ledger_directory / "views-blobs")
        self.ledger = Ledger(
            f"sqlite:///{ledger_directory / 'views.sqlite'}", blob_store=self.store
        )

    # -- evidence ---------------------------------------------------------------------------
    def _result(self):
        path = self.directory / "RESULT.json"
        return json.loads(path.read_text()) if path.exists() else {"tasks": [], "status": "running"}

    def _outputs(self):
        path = self.directory / "OUTPUTS.json"
        return json.loads(path.read_text()) if path.exists() else {}

    def _sync(self):
        """Append ledger entries for tasks recorded since the last sync (idempotent keys)."""
        result, outputs = self._result(), self._outputs()
        stage = "CREATED"
        with self.ledger.transaction(self.graft_id) as tx:
            tx.append(
                type="STAGE",
                producer=PRODUCER,
                schema="StageChange/1",
                payload=self._change(None, "CREATED", "Integrated run started", "service"),
                idempotency_key="created",
            )
            for row in result.get("tasks", []):
                task = row.get("task", "").removesuffix("-retry1")
                if row.get("cost_micro_usd") is not None and row.get("model") in MODELS:
                    tx.append(
                        type="COST",
                        producer=PRODUCER,
                        schema="BudgetRecord/1",
                        payload={
                            "graft_id": self.graft_id,
                            "agent": row["role"],
                            "model": MODELS[row["model"]],
                            "tokens_in": 0,
                            "tokens_cached": 0,
                            "tokens_out": 0,
                            "usd": round(row["cost_micro_usd"] / 1_000_000, 6),
                            "cap_usd": round(result.get("cap_micro_usd", 0) / 1_000_000, 6),
                        },
                        idempotency_key="cost:" + task,
                    )
                if task == "sentinel-audit" and row.get("passed"):
                    for out in outputs.get(task, []):
                        if out.get("schema") == "Alert/1":
                            tx.append(
                                type="ALERT",
                                producer=PRODUCER,
                                schema="Alert/1",
                                payload=out["payload"],
                                idempotency_key="alert:" + task,
                            )
                if task == "healer-golive" and row.get("passed"):
                    for out in outputs.get(task, []):
                        if out.get("schema") == "HealNote/1":
                            tx.append(
                                type="ARTIFACT",
                                producer=PRODUCER,
                                schema="HealNote/1",
                                payload=out["payload"],
                                idempotency_key="heal:" + task,
                            )
                target = STAGE_OF.get(task)
                if target and row.get("passed"):
                    tx.append(
                        type="STAGE",
                        producer=PRODUCER,
                        schema="StageChange/1",
                        payload=self._change(stage, target, WORDS[task], row["role"]),
                        idempotency_key="stage:" + task,
                    )
                    stage = target
            # A held run stays at the last stage it reached; nothing past PROVING is claimed.

    def _change(self, before, after, reason, actor):
        return {
            "graft_id": self.graft_id,
            "from_stage": before,
            "to_stage": after,
            "attempt": 1,
            "reason": reason,
            "actor": {"kind": "agent" if actor not in {"service"} else "service", "name": actor},
            "evidence_refs": [],
        }

    # -- published views ---------------------------------------------------------------------
    def events(self, after=0):
        self._sync()
        return [e for e in self.ledger.read(self.graft_id) if e.seq > after]

    def graft(self):
        self._sync()
        result, outputs = self._result(), self._outputs()
        rows = result.get("tasks", [])
        entries = self.ledger.read(self.graft_id)
        stages, last = [], "CREATED"
        for e in entries:
            if e.schema_ == "StageChange/1":
                last = e.payload["to_stage"]
                stages.append({"stage": last, "minutes": 0.0, "usd": 0.0})
        for row in rows:
            target = STAGE_OF.get(row.get("task"))
            for s in stages:
                if s["stage"] == target:
                    s["minutes"] = round(s["minutes"] + row.get("seconds", 0) / 60, 2)
                    s["usd"] = round(s["usd"] + row.get("cost_micro_usd", 0) / 1_000_000, 6)
        survey = (outputs.get("survey") or [{}])[0].get("payload") or {}
        found = len(survey.get("touchpoints", [])) or next(
            (r.get("touchpoints", 0) for r in rows if r.get("task") == "survey"), 0
        )
        changes = (outputs.get("grafter") or [{}])[0].get("payload") or {}
        started = (self.directory / "RESULT.json").stat().st_ctime if rows else None
        return Graft.model_validate(
            {
                "graft_id": self.graft_id,
                "shop_id": self.shop_id,
                "stage": last,
                "lane": "FULL",
                "started_at": datetime.fromtimestamp(started or datetime.now(UTC).timestamp(), UTC),
                "stages": stages,
                "card": {
                    "old_pieces_found": found,
                    "pieces_upgraded": len(
                        {i for c in changes.get("changes", []) for i in c.get("plan_item_ids", [])}
                    ),
                    "scenarios_total": 0,
                    "scenarios_pass": 0,
                    "problems": sum(1 for r in rows if r.get("passed") is False),
                    "proof_strength_score": None,
                    "cost_usd": round(result.get("spent_micro_usd", 0) / 1_000_000, 6),
                    "minutes": round(sum(r.get("seconds", 0) for r in rows) / 60, 2),
                    "notes": {
                        "_label": "REAL MODELS · connected 13-role run · scripted runner, "
                        "no independent proof yet",
                        "old_pieces_found": "Old PayPal code spots the Surveyor found",
                        "problems": "Agent steps that held instead of finishing",
                        "cost_usd": "Real AI cost of this run",
                    },
                },
                "ledger_root": entries[-1].entry_hash if entries else "0" * 64,
            }
        )

    def rootmap(self):
        survey = (self._outputs().get("survey") or [None])[0]
        if not survey:
            raise LookupError("no committed RootMap yet")
        return survey["payload"]

    def summary_text(self):
        herald = (self._outputs().get("herald") or [None])[0]
        return (herald or {}).get("payload")

    def agents(self):
        """Every agent step of the run: model, cost, outcome, what its input was, what it made."""
        result, outputs = self._result(), self._outputs()
        rows = []
        for t in result.get("tasks", []):
            task = t["task"]
            base = task.removesuffix("-retry1")
            source, note = INPUTS.get(base, ("sample", "Qualified sample input"))
            rows.append(
                {
                    "task": base,
                    "attempt": 2 if task.endswith("-retry1") else 1,
                    "role": t["role"],
                    "operation": t.get("operation"),
                    "model": MODELS.get(t.get("model"), t.get("model")),
                    "escalated": bool(t.get("escalated")),
                    "passed": bool(t.get("passed")),
                    "issue": t.get("issue"),
                    "cost_usd": round((t.get("cost_micro_usd") or 0) / 1e6, 6),
                    "seconds": t.get("seconds"),
                    "input": source,
                    "input_note": note,
                    "outputs": [
                        {"schema": o["schema"], "summary": summarize(o["schema"], o["payload"])}
                        for o in outputs.get(task, [])
                    ],
                }
            )
        return {"graft_id": self.graft_id, "status": result.get("status"), "agents": rows}

    def outputs_of(self, schema):
        """Committed payloads of one schema across the run's steps (latest attempt wins)."""
        found = {}
        for task, items in self._outputs().items():
            for item in items:
                if item["schema"] == schema:
                    found[task.removesuffix("-retry1")] = item["payload"]
        return list(found.values())

    def scenarios(self):
        raise LookupError("scenario evidence comes from the scripted runner; not served")

    def cmel(self, scenario_id):
        raise LookupError("scenario evidence comes from the scripted runner; not served")

    def proof(self):
        raise LookupError("no independent proof in the integrated graph yet")

    def start(self, key, request):
        return self.graft()


def run_views(runs_dir: Path, graft_id: str):
    directory = Path(runs_dir) / graft_id
    if not (directory / "RESULT.json").exists():
        return None
    return IntegratedRunViews(directory)
