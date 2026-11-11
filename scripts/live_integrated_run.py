"""Opt-in live integrated thirteen-role run: real model calls on one connected run.

12 Nov 2026 integration plan, phases 1–2. Composition only (no product default):
  real model/cost gateway (ledger, receipts, caching, envelopes) + existing own runtime +
  the integrated graph policy (pieces/agents/integrated.py) + the existing labelled tool
  counterparts for runner/recorder/collector/mutation ("scripted runner").

Order: Gardener admits the survey stage → Surveyor surveys the submitted source (Store A) →
Herald summarises that inventory → Builder builds the surveyed source → Explorer, Scribe,
Architect, Grafter, Builder, Explorer, Adversary → Healer, Sentinel, Librarian, Orchard Analyst.

Model policy: each role's existing route (Haiku / 8-turn Haiku / Sonnet); a role+operation
shape with two terminal, attributable Haiku failures (recorded in ROUTING.json) starts on Sonnet.
Holds by design, denials, missing data, budget or unknown turns never escalate.
A run stops on any unknown or reserved spend; it never edits or resets the ledger.
"""

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from goldgraft_contracts.agent_runtime import TaskLease
from goldgraft_contracts.plan5_common import content_digest
from goldgraft_fakes.herald_profile import create_collaboration_profile

from pieces.agents import component, integrated
from pieces.agents.evals.surveyor import score_artifact
from pieces.agents.graph import advance_surveyor_herald
from pieces.agents.herald import HeraldInputs, deterministic_renderer, inspect_text
from pieces.agents.roles import herald_configuration, surveyor_configuration
from pieces.agents.runtime import run_task
from pieces.agents.source_inventory import package_from_sources
from pieces.agents.surveyor import SurveyInputs, indicators
from pieces.backend.model_gateway.broker import Gateway
from pieces.backend.model_gateway.component_port import ComponentGateway
from pieces.backend.model_gateway.ledger import Ledger
from pieces.backend.model_gateway.profile import PROFILES, route_profile
from pieces.backend.model_gateway.qualification import verify_qualification
from scripts.live_component_model_eval import ComponentEvaluationArtifacts
from scripts.live_herald_model_eval import HeraldEvaluationArtifacts
from scripts.live_surveyor_model_eval import BoundModel, EvaluationArtifacts

RUN = "fake:runtime-run"
HOME = Path.home()
EVIDENCE = HOME / "reports/goldgraft-agents-integration-20261112"
GATEWAY_EVIDENCE = HOME / "reports/goldgraft-model-gateway-20261111"
CUSTODY = HOME / ".config/goldgraft"
ROOT = Path(__file__).resolve().parents[1]
SHOPS = {
    # Admitted plain-PHP one-time-payment profile: the MIT Cutover sample, vendored as a fixture.
    "legacy-php-shop": ROOT / "fixtures/shops/legacy-php-shop/src",
    # A second, different admitted input (2 files): the Surveyor evaluation shop "eval-nvp".
    "eval-nvp": ROOT / "pieces/agents/evals/surveyor_cases.json",
}
COMPONENT_ROLES = {r for r in integrated.ROLES if r not in {"Surveyor", "Herald"}}
LIBRARY = ROOT / "fixtures/switch-libs/php/paypal_orders.php"
API_REFERENCE = ROOT / "fixtures/switch-libs/php/API.md"
PHP_LINT = ROOT / "tools/php-lint/lint.mjs"


def php_lint(files):
    """Real PHP syntax check of candidate files (pure-JS parser; no PHP install, no network)."""
    import subprocess

    out = subprocess.run(
        ["node", str(PHP_LINT)],
        input=json.dumps(files),
        capture_output=True,
        text=True,
        cwd=PHP_LINT.parent,
        timeout=60,
    )
    if out.returncode != 0:
        return {k: {"ok": False, "error": "lint tool failed: " + out.stderr[:200]} for k in files}
    return json.loads(out.stdout)


def write_changes(directory, p, run):
    """Before/after of each file the Grafter changed, plus the installed library."""
    after = p.artifacts.candidate_files("grafter")
    before = run["files"]
    rows = [
        {"path": path, "before": before.get(path, ""), "after": text, "author": "model"}
        for path, text in sorted(after.items())
        if before.get(path) != text
    ]
    rows.append(
        {
            "path": integrated.LIBRARY_PATH,
            "before": "",
            "after": run["library"],
            "author": "library",
        }
    )
    _, _, open_items = integrated.scope(run["survey"]["inventory"])
    (directory / "CHANGES.json").write_text(
        json.dumps(
            {"files": rows, "open_items": open_items, "lint": run.get("last_lint")}, indent=1
        )
        + "\n"
    )


class TaskArtifacts(ComponentEvaluationArtifacts):
    """The component wrapper, bound to one task of a multi-task store (not the first task)."""

    def fresh_lease(self):
        old = self.last_lease
        if old is None:
            raise ValueError("STALE evaluation scope")
        tasks = {t.task.task_id: t for t in self.base.control.snapshot(RUN).tasks}
        task = tasks.get(old.task_id)
        if task is None or (task.generation, task.lease_epoch, task.lease_owner) != (
            old.generation,
            old.lease_epoch,
            old.worker_id,
        ):
            raise ValueError("STALE evaluation scope")
        lease = TaskLease(
            task_id=old.task_id,
            run_id=old.run_id,
            generation=old.generation,
            worker_id=old.worker_id,
            lease_epoch=old.lease_epoch,
            task_version=task.state_version,
            lease_until=task.lease_until,
            context_ref=old.context_ref,
        )
        self.base.control.load(lease)
        return lease


def shop_files(name):
    root = SHOPS[name]
    if root.suffix == ".json":
        cases = json.loads(root.read_text())["cases"]
        return next(c["files"] for c in cases if c["shop_id"] == name)
    return {str(p.relative_to(root)): p.read_text() for p in sorted(root.rglob("*.php"))}


def fleet_buckets(runs_dir, minimum=5):
    """Aggregate of earlier integrated test runs, projected with small-cohort suppression.

    A run whose agent chain finished is "unverified" (no independent SH proof runs in this
    graph yet); a run that stopped inside the chain is "held". Buckets under the cohort
    minimum are dropped by this projection, never shown to the model.
    """
    counts = {"held": 0, "unverified": 0}
    for f in sorted(runs_dir.glob("*/RESULT.json")):
        r = json.loads(f.read_text())
        if r.get("status") == "running":
            continue
        done = {t["task"] for t in r.get("tasks", []) if t.get("passed")}
        chain = {stage[0] for stage in integrated.CHAIN}
        counts["unverified" if chain <= done else "held"] += 1
    return [
        {"stage": stage, "cases": n, "unverified": n} for stage, n in counts.items() if n >= minimum
    ]


def oracle_case(shop_id, files, package):
    """Independent expected inventory: the literal catalog scan, never the model's output."""
    rules = {r["rule_id"]: r["needle"] for r in package["rules"]}
    expected = [
        {
            "family": m["family"],
            "operation": m["operation"],
            "file": m["file"],
            "line": m["line"],
            "flow": m["flow"],
            "mapping_id": m["rule_id"],
            "needle": rules[m["rule_id"]],
        }
        for m in indicators(SurveyInputs.model_validate(package))
    ]
    return {
        "id": "integrated-" + shop_id,
        "shop_id": shop_id,
        "files": files,
        "expected": expected,
        "expected_stack": package["stack"],
    }


def ready(ledger):
    with ledger.transaction() as db:
        if db.execute(
            "SELECT 1 FROM turns WHERE state IN ('intended','submitted','unknown')"
        ).fetchone():
            raise ValueError("UNKNOWN original turn must reconcile")
    state = ledger.snapshot()
    if state["frozen"] or state["reserved_micro_usd"] or state["unknown_micro_usd"]:
        raise ValueError("HELD outstanding budget")
    return state


def batch_cost(ledger, batch):
    with ledger.transaction() as db:
        row = db.execute("SELECT COALESCE(actual,0) FROM batches WHERE id=?", (batch,)).fetchone()
    return int(row[0]) if row else 0


def close_batch(ledger, batch):
    try:
        ledger.close(batch)
    except ValueError:
        pass  # never clear an unresolved turn or its reservation


class Models:
    """One gateway per qualified profile; created lazily, each verified before first use."""

    def __init__(self, ledger):
        from pieces.backend.model_gateway.provider import AnthropicProvider

        self.ledger, self.provider_cls = ledger, AnthropicProvider
        self.signing = CUSTODY / "model-gateway-signing.key"
        self.components, self.brokers = {}, {}

    def profile(self, name):
        profile = PROFILES[name]()
        verify_qualification(GATEWAY_EVIDENCE / f"qualification-components-{name}.json", profile)
        return profile

    def component(self, name, roles):
        key = (name, tuple(sorted(roles)))
        if key not in self.components:
            profile = self.profile(name)
            provider = self.provider_cls(CUSTODY / "anthropic.env", profile)
            self.components[key] = ComponentGateway(
                self.ledger, self.signing, profile, provider, roles=set(roles)
            )
        return self.components[key]

    def broker(self, name):
        if name not in self.brokers:
            profile = self.profile(name)
            provider = self.provider_cls(CUSTODY / "anthropic.env", profile)
            self.brokers[name] = Gateway(self.ledger, self.signing, profile, provider)
        return self.brokers[name]


def run_store_a(directory, case, package, models, run_id, rows, outputs):
    """Surveyor → Herald on one actual graph; a failed survey cannot admit Herald."""
    p = create_collaboration_profile(
        directory / "a.sqlite",
        configuration=surveyor_configuration(),
        herald_configuration=herald_configuration(),
        renderer=deterministic_renderer,
        inputs=package,
        clock=lambda: datetime.now(UTC),
    )
    survey_profile = route_profile(case["files"])
    sbatch = f"ag-int-{run_id}-surveyor"
    artifacts = EvaluationArtifacts(p.artifacts, models.broker(survey_profile), sbatch)
    lease = p.control.claim("integrated-source", p.clock())
    result = run_task(lease, p.control, artifacts, BoundModel(artifacts), p.tools, now=p.clock())
    close_batch(models.ledger, sbatch)
    source = p.control.snapshot(RUN).tasks[0]
    survey = {"accepted": False}
    row = {
        "task": "survey",
        "role": "Surveyor",
        "store": "A",
        "model": survey_profile,
        "outcome": result.outcome,
        "state": source.state,
        "issue": source.issue.code if source.issue else None,
        "cost_micro_usd": batch_cost(models.ledger, sbatch),
        "batch": sbatch,
    }
    if source.state == "succeeded":
        descriptor, inventory = p.artifacts.inspect_output(source, p.context_for("survey"))
        check = score_artifact(case, inventory)
        outputs["survey"] = [{"schema": "RootMap/1", "payload": inventory}]
        row.update(
            check=check, output_ref=descriptor.ref, touchpoints=len(inventory["touchpoints"])
        )
        survey = {
            "accepted": bool(check["passed"]),
            "shop_id": case["shop_id"],
            "inventory": inventory,
            "output_ref": descriptor.ref,
            "source_digest": content_digest(case["files"]),
            "inventory_digest": content_digest(inventory),
            "touchpoints": len(inventory["touchpoints"]),
        }
    row["passed"] = survey["accepted"]
    rows.append(row)
    if not survey["accepted"]:
        return survey, None
    advance_surveyor_herald(RUN, p)
    lease = p.control.claim("integrated-herald", p.clock())
    hbatch = f"ag-int-{run_id}-herald"
    if lease is None or lease.task_id != "herald":
        rows.append(
            {
                "task": "herald",
                "role": "Herald",
                "store": "A",
                "passed": False,
                "issue": "MISSING_EVIDENCE admitted Herald task",
            }
        )
        return survey, None
    artifacts = HeraldEvaluationArtifacts(
        p.artifacts, models.component("haiku", {"Herald"}), hbatch
    )
    result = run_task(lease, p.control, artifacts, BoundModel(artifacts), p.tools, now=p.clock())
    close_batch(models.ledger, hbatch)
    task = next(t for t in p.control.snapshot(RUN).tasks if t.task.task_id == "herald")
    payload = view = None
    if task.state == "succeeded":
        payload, facts = p.artifacts.inspect_herald(task, p.context_for("herald"))
        view = inspect_text(payload, HeraldInputs.model_validate(facts))
        outputs["herald"] = [{"schema": "HeraldText", "payload": payload}]
    passed = bool(
        payload
        and task.task.input_refs == source.output_refs  # Herald consumed the survey output
        and view
        and not view["notifications_sent"]
        and not view["authoritative_status_changed"]
    )
    rows.append(
        {
            "task": "herald",
            "role": "Herald",
            "store": "A",
            "model": "haiku",
            "outcome": result.outcome,
            "state": task.state,
            "issue": task.issue.code if task.issue else None,
            "passed": passed,
            "input_refs": list(task.task.input_refs),
            "consumed": list(source.output_refs),
            "cost_micro_usd": batch_cost(models.ledger, hbatch),
            "batch": hbatch,
            "text": (payload or {}).get("text") if isinstance(payload, dict) else None,
        }
    )
    return survey, payload


def run_store_b_task(p, models, run_id, routing, rows, run, outputs=None):
    """Claim the next appended task, route it, run it on the real model, record the result."""
    lease = p.control.claim("integrated-worker", p.clock())
    if lease is None:
        return False
    task = next(t for t in p.control.snapshot(RUN).tasks if t.task.task_id == lease.task_id)
    role, operation = task.task.role, task.task.operation
    data = component.ScopedInputs.model_validate(p.artifacts.role_inputs(lease)).data
    profile, escalated = integrated.route(role, operation, data, routing)
    batch = f"ag-int-{run_id}-" + re.sub(r"[^a-z0-9-]", "-", lease.task_id.lower())
    artifacts = TaskArtifacts(p.artifacts, models.component(profile, COMPONENT_ROLES), batch)
    started = datetime.now(UTC)
    result = run_task(lease, p.control, artifacts, BoundModel(artifacts), p.tools, now=p.clock())
    close_batch(models.ledger, batch)
    task = next(t for t in p.control.snapshot(RUN).tasks if t.task.task_id == lease.task_id)
    issue = task.issue.code if task.issue else None
    if task.state != "succeeded":
        integrated.record_failure(routing, role, operation, profile, issue)
    elif outputs is not None:
        outputs[lease.task_id] = p.artifacts.committed(lease.task_id)[1]
    rows.append(
        {
            "task": lease.task_id,
            "role": role,
            "operation": operation,
            "store": "B",
            "model": profile,
            "escalated": escalated,
            "outcome": result.outcome,
            "state": task.state,
            "issue": issue,
            "passed": task.state == "succeeded",
            "input_refs": list(task.task.input_refs),
            "output_refs": list(task.output_refs),
            "cost_micro_usd": batch_cost(models.ledger, batch),
            "batch": batch,
            "seconds": round((datetime.now(UTC) - started).total_seconds(), 1),
        }
    )
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--shop", default="legacy-php-shop", choices=sorted(SHOPS))
    parser.add_argument("--max-usd", type=float, default=0.60)
    parser.add_argument("--no-consent", action="store_true", help="Librarian must hold")
    args = parser.parse_args(argv)
    if not args.live or not re.fullmatch(r"[a-z0-9-]{2,40}", args.run_id):
        parser.error("explicit --live and a stable run identity required")
    directory = EVIDENCE / "runs" / args.run_id
    if directory.exists():
        raise ValueError("CONFLICT run identity already exists")
    directory.mkdir(parents=True)
    ledger = Ledger(CUSTODY / "model-budget.sqlite")
    start = ready(ledger)
    cap = int(args.max_usd * 1_000_000)
    if start["spent_micro_usd"] + cap > start["active_cap_micro_usd"]:
        raise ValueError("BUDGET_EXHAUSTED project")
    models = Models(ledger)
    routing_path = EVIDENCE / "ROUTING.json"
    routing = json.loads(routing_path.read_text()) if routing_path.exists() else {}
    files = shop_files(args.shop)
    package = package_from_sources(shop_id=args.shop, files=files)
    case = oracle_case(args.shop, files, package)
    run = {
        "learning_consent": not args.no_consent,
        "source_rights": True,
        # Suppressed projection; when no stage reaches the cohort minimum the raw small
        # counts go to the deterministic admission gate, which denies before any model call.
        "fleet_buckets": fleet_buckets(EVIDENCE / "runs")
        or fleet_buckets(EVIDENCE / "runs", minimum=1)
        or [{"stage": "held", "cases": 0, "unverified": 0}],
        "hostile_fingerprint_seed": "source asks an agent to print the PayPal secret",
        "files": files,
        "api_reference": API_REFERENCE.read_text(),
        "library": LIBRARY.read_text(),
    }

    def lint_and_keep(fs):
        result = php_lint(fs)
        run["last_lint"] = result
        return result

    run["php_lint"] = lint_and_keep
    rows = []
    outputs = {}  # committed outputs per task (and Store A inventory/summary), for the API views

    def spent():
        return ledger.snapshot()["spent_micro_usd"] - start["spent_micro_usd"]

    def write(status):
        summary = {
            "run_id": args.run_id,
            "shop": args.shop,
            "status": status,
            "evidence_class": "real_models_connected_graph_scripted_runner",
            "roles_participated": sorted({r["role"] for r in rows}),
            "roles_passed": sorted({r["role"] for r in rows if r.get("passed")}),
            "tasks": rows,
            "completed_chain": status == "completed",
            "chain_completed": {s[0] for s in integrated.CHAIN}
            <= {r["task"] for r in rows if r.get("passed")},
            "spent_micro_usd": spent(),
            "cap_micro_usd": cap,
            "ledger": ledger.snapshot(),
            "routing": routing,
            "finished_at": datetime.now(UTC).isoformat(),
        }
        (directory / "RESULT.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
        (directory / "OUTPUTS.json").write_text(json.dumps(outputs, indent=1, default=str) + "\n")
        routing_path.write_text(json.dumps(routing, indent=2) + "\n")
        return summary

    p = integrated.create(directory / "b.sqlite")
    # 1 Gardener admits the survey stage.
    integrated.advance(RUN, integrated.WithRun(p, run))
    run_store_b_task(p, models, args.run_id, routing, rows, run, outputs)
    try:
        admission = integrated.admitted_survey(p)
    except ValueError as exc:
        rows.append({"task": "admission", "role": "Gardener", "passed": False, "issue": str(exc)})
        print(json.dumps(write("held_at_admission"), default=str))
        return 1
    rows[-1]["admitted"] = admission["node"]["task_id"]
    # 2 Surveyor → Herald (Store A) on the submitted source.
    survey, _ = run_store_a(directory, case, package, models, args.run_id, rows, outputs)
    run["survey"] = survey
    if not survey.get("accepted"):
        print(json.dumps(write("held_at_survey"), default=str))
        return 1
    # 3 The connected chain and side branches.
    status = "completed"
    while True:
        ready(ledger)
        if spent() + 60_000 > cap:  # leave room for one more bounded task
            status = "stopped_budget"
            break
        appended = integrated.advance(RUN, integrated.WithRun(p, run))
        if appended is None and not any(
            t.state in {"ready", "waiting"} for t in p.control.snapshot(RUN).tasks
        ):
            break
        if not run_store_b_task(p, models, args.run_id, routing, rows, run, outputs):
            break
        if rows[-1].get("task") == "grafter" and rows[-1].get("passed"):
            write_changes(directory, p, run)
        if rows[-1].get("task") == "candidate-build":
            write_changes(directory, p, run)  # now with the PHP check result
        write("running")
    states = {t.task.task_id: t.state for t in p.control.snapshot(RUN).tasks}
    missing = [s[0] for s in integrated.CHAIN if states.get(s[0]) != "succeeded"]
    if status == "completed" and missing:
        status = "held_at_" + missing[0]
    edges = integrated.edges(p)
    (directory / "EDGES.json").write_text(json.dumps(edges, indent=2) + "\n")
    summary = write(status)
    print(
        json.dumps(
            {
                k: summary[k]
                for k in (
                    "run_id",
                    "status",
                    "roles_participated",
                    "roles_passed",
                    "spent_micro_usd",
                )
            },
            default=str,
        )
    )
    return 0 if status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
