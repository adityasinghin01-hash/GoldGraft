"""Opt-in actual inference for Herald through the scoped local component gateway.

Composition only: Surveyor runs deterministically, then Herald's own runtime task uses
the gateway. Herald's validators are unchanged: the text must be an exact closed-catalog
sentence and every number must carry its exact ledger entry. Never production mode.
"""

import argparse
import json
import re
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from goldgraft_contracts.agent_runtime import ModelBudget, TaskLease
from goldgraft_contracts.plan5_common import canonical_bytes, content_digest
from goldgraft_fakes.herald_profile import create_collaboration_profile

from pieces.agents.graph import advance_surveyor_herald
from pieces.agents.herald import (
    HeraldInputs,
    deterministic_renderer,
    inspect_text,
    model_facts,
    render_text,
)
from pieces.agents.roles import herald_configuration, surveyor_configuration
from pieces.agents.runtime import run_task
from pieces.backend.model_gateway.component_port import ComponentGateway
from pieces.backend.model_gateway.ledger import Ledger
from pieces.backend.model_gateway.profile import PROFILES
from pieces.backend.model_gateway.qualification import verify_qualification
from scripts.live_surveyor_model_eval import BoundModel, EvaluationArtifacts

RUN = "fake:runtime-run"
OBSERVED_TOOL = {"status_projection": "status.read", "evidence_summary": "evidence.summary"}
HERALD_SETTINGS = {"status", "reason_code", "kind", "retained", "removed", "pending"}


class HeraldEvaluationArtifacts(EvaluationArtifacts):
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

    def ticket(self, lease):
        self.last_lease = lease
        ticket = self.base.ticket(lease)
        task = self.base.control.load(lease)
        if self.grant is None:
            scope = {
                "task_id": task.task.task_id,
                "case_id": task.case_id,
                "run_id": task.run_id,
                "generation": task.generation,
                "lease_epoch": lease.lease_epoch,
                "input_digest": task.input_digest,
                "subject": task.task.expected_subject,
                "prompt_digest": task.prompt_digest,
                "policy_digest": task.policy_digest,
                "deadline": task.deadline.isoformat(),
                "role": task.task.role,
                "allowed_tools": task.task.allowed_tool_ids,
                "schemas": list(task.task.expected_schemas),
            }
            self.grant = self.gateway.grant(self.batch, scope)
            self.port = self.gateway.port(self.grant, self)
        context = ticket.context.model_copy(update={"budget_ref": self.batch})
        with self.base.control.store.transaction() as db:
            db.execute(
                "INSERT OR IGNORE INTO contexts VALUES(?,?)",
                ("local:context:" + content_digest(context), canonical_bytes(context).decode()),
            )
        balance = self.gateway.ledger.snapshot()
        budget = ModelBudget(
            budget_id=self.batch,
            target_micro_usd=balance["active_cap_micro_usd"],
            ceiling_micro_usd=balance["active_cap_micro_usd"],
            spent_micro_usd=balance["spent_micro_usd"],
            outstanding_micro_usd=balance["outstanding_micro_usd"],
            unknown_micro_usd=balance["unknown_micro_usd"],
            pricing_ref=self.gateway.profile.ref,
        )
        return replace(ticket, context=context, budget=budget, evidence_class="real_model")

    def _facts(self):
        lease = self.fresh_lease()
        task = self.base.control.load(lease)
        return task, self.base.role_inputs(lease)

    def reference_metadata(self, request):
        task, facts = self._facts()
        reference = render_text(task, HeraldInputs.model_validate(facts))
        meta = {k: reference[k] for k in ("id", "graft_id", "created_at", "producer", "kind")}
        meta["producer"] = dict(meta["producer"], model=self.gateway.profile.model)
        return meta

    def call_facts(self, request):
        return model_facts(self._facts()[1])

    def tool_progress(self, context):
        """Herald observations carry a projection kind, not a tool name; map it."""
        names = []
        for o in context.get("observations", []):
            value = o.get("value") if isinstance(o, dict) else None
            inner = value.get("value") if isinstance(value, dict) else None
            names.append(OBSERVED_TOOL.get(inner.get("kind")) if isinstance(inner, dict) else None)
        return names


def compose(path, case, gateway, batch, clock=None):
    settings = {k: v for k, v in case["settings"].items() if k in HERALD_SETTINGS}
    config = dict(herald_configuration(projection=case.get("projection", "private_status")))
    config.update(settings)
    clock = clock or (lambda: datetime.now(UTC))
    p = create_collaboration_profile(
        path,
        configuration=surveyor_configuration(),
        herald_configuration=config,
        renderer=deterministic_renderer,
        clock=clock,
    )
    return p, HeraldEvaluationArtifacts(p.artifacts, gateway, batch)


def run_case(case, gateway, directory, batch, clock=None):
    p, artifacts = compose(directory / "state.sqlite", case, gateway, batch, clock)
    lease = p.control.claim("source-worker", p.clock())
    survey = run_task(lease, p.control, p.artifacts, p.model, p.tools, now=p.clock())
    if survey.outcome != "completed":
        raise ValueError("MISSING_EVIDENCE Surveyor predecessor")
    advance_surveyor_herald(RUN, p)
    lease = p.control.claim("herald-worker", p.clock())
    if lease is None or lease.task_id != "herald":
        raise ValueError("MISSING_EVIDENCE Herald task")
    result = run_task(lease, p.control, artifacts, BoundModel(artifacts), p.tools, now=p.clock())
    task = next(t for t in p.control.snapshot(RUN).tasks if t.task.task_id == "herald")
    payload = view = None
    if task.state == "succeeded":
        payload, facts = p.artifacts.inspect_herald(task, p.context_for("herald"))
        view = inspect_text(payload, HeraldInputs.model_validate(facts))
    return task, result, payload, view, p


def main(argv=None):
    from pieces.agents.evals.components import load_catalog, score

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True)
    parser.add_argument("--case-file", type=Path, required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--profile", choices=sorted(PROFILES), default="haiku")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live or not re.fullmatch(r"[a-z0-9-]{1,80}", args.batch_id):
        parser.error("explicit --live and stable bounded batch identity required")
    case = {c["id"]: c for c in load_catalog(args.case_file)}[args.case]
    if case["role"] != "Herald":
        parser.error("Herald case required")
    home = Path.home()
    evidence = home / "reports/goldgraft-model-gateway-20261111"
    profile = PROFILES[args.profile]()
    verify_qualification(evidence / f"qualification-components-{args.profile}.json", profile)
    from pieces.backend.model_gateway.provider import AnthropicProvider

    custody = home / ".config/goldgraft"
    ledger = Ledger(custody / "model-budget.sqlite")
    provider = AnthropicProvider(custody / "anthropic.env", profile)
    gateway = ComponentGateway(
        ledger, custody / "model-gateway-signing.key", profile, provider, roles={"Herald"}
    )
    directory = evidence / "live" / args.batch_id
    directory.mkdir(parents=True, exist_ok=True)
    started = datetime.now(UTC)
    task, result, payload, view, _ = run_case(case, gateway, directory, args.batch_id)
    try:
        ledger.close(args.batch_id)
    except ValueError:
        pass
    with ledger.transaction() as db:
        ids = [r[0] for r in db.execute("SELECT id FROM turns WHERE batch=?", (args.batch_id,))]
    turns = [ledger.turn(args.batch_id, t) for t in ids]
    outputs = [{"schema": "HeraldText/1", "payload": payload}] if payload else None
    checked = score(case, outputs, None) if outputs else None
    report = {
        "evidence_class": "real_model_component_with_scripted_tool_control_boundaries",
        "role": "Herald",
        "case_id": case["id"],
        "case_digest": content_digest(case),
        "batch_id": args.batch_id,
        "model": profile.model,
        "profile_name": args.profile,
        "model_profile": profile.ref,
        "outcome": result.outcome,
        "issue": result.issue.model_dump(mode="json") if result.issue else None,
        "outputs": outputs,
        "view": view,
        "check": checked,
        "turns": turns,
        "ledger": ledger.snapshot(),
        "latency_seconds": (datetime.now(UTC) - started).total_seconds(),
        "passed": bool(checked and checked["passed"]),
    }
    (directory / "result.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    print(
        json.dumps(
            {k: report[k] for k in ["role", "case_id", "batch_id", "model", "outcome", "passed"]}
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        token = str(error).split()[0] if str(error).split() else "CLOSED_GATEWAY_ERROR"
        reason = token if re.fullmatch(r"[A-Z_]{1,64}", token) else "CLOSED_GATEWAY_ERROR"
        print(
            json.dumps({"outcome": "held", "error_class": type(error).__name__, "reason": reason})
        )
        raise SystemExit(1) from None
