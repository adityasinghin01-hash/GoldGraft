"""Opt-in actual inference for one component agent through the scoped local gateway.

Composition only: actual model/cost gateway + existing own runtime + explicitly
synthetic component control/tools/collector counterparts. Never production mode.
"""

import argparse
import json
import re
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from goldgraft_contracts.agent_runtime import ModelBudget
from goldgraft_contracts.plan5_common import canonical_bytes, content_digest
from goldgraft_contracts.plan5_tools import TOOL_CATALOG
from goldgraft_contracts.registry import REGISTRY
from goldgraft_foundation.offline_profile import load_component_profile

from pieces.agents import component
from pieces.agents.evals.components import load_catalog, score
from pieces.agents.roles import COMPONENT_POLICIES, component_configuration
from pieces.agents.scheduler import tick
from pieces.backend.model_gateway.component_port import ComponentGateway
from pieces.backend.model_gateway.ledger import Ledger
from pieces.backend.model_gateway.profile import PROFILES
from pieces.backend.model_gateway.qualification import verify_qualification
from scripts.live_surveyor_model_eval import EvaluationArtifacts, EvaluationPorts


class ComponentEvaluationArtifacts(EvaluationArtifacts):
    def presentation_context(self, context):
        """Synthetic tool-fault controls are not evidence or model-visible answers.

        The authenticated stored context remains intact. Only the provider's
        presentation excludes this fixture switch; observed receipts remain visible.
        """
        field = {
            "Grafter": "collector_receipt_fault",
            "Orchard Analyst": "aggregate_receipt_fault",
        }.get(context.get("role_inputs", {}).get("role"))
        if field is None:
            return context
        packet = dict(context["role_inputs"])
        packet["data"] = {k: v for k, v in packet["data"].items() if k != field}
        return dict(context, role_inputs=packet)

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

    def reference_metadata(self, request):
        lease = self.fresh_lease()
        task = self.base.control.load(lease)
        packet = component.ScopedInputs.model_validate(self.base.role_inputs(lease))
        meta = component.metadata(task, packet)
        meta["producer"]["model"] = self.gateway.profile.model  # honest producer label
        schemas = list(task.task.expected_schemas)
        if len(schemas) == 1:  # only hint fields the output schema actually has
            fields = REGISTRY[schemas[0]].model_fields
            meta = {k: v for k, v in meta.items() if k in fields}
        return meta

    def inline_fields(self):
        """Role-declared staged refs the model sends as inline content: {tool: {ref: (name,
        schema)}}. The port validates and stages that content; it never trusts a raw ref."""
        lease = self.fresh_lease()
        packet = component.ScopedInputs.model_validate(self.base.role_inputs(lease))
        return getattr(component.implementation(packet.role), "INLINE", {})

    def call_facts(self, request):
        """Role-declared scoped argument values and call policy (never outputs)."""
        lease = self.fresh_lease()
        task = self.base.control.load(lease)
        packet = component.ScopedInputs.model_validate(self.base.role_inputs(lease))
        module = component.implementation(packet.role)
        if not hasattr(module, "facts"):
            return {"run_ref": "fake:runtime-run"}
        data = module.Input.model_validate(packet.data)
        facts = module.facts(task, data)
        if getattr(module, "PROGRESS", False):
            # Derived progress (Surveyor playbook #5): remaining planned READS only, never
            # outputs or non-read decisions such as holds or execution requests.
            context = self.context_bytes(request)
            done = [
                ((o.get("value") or {}).get("tool"), (o.get("value") or {}).get("arguments"))
                for o in context.get("observations", [])
                if isinstance(o, dict)
            ]
            unread = []
            for call in module.requests(task, data):
                if TOOL_CATALOG[call["tool"]].effect != "read":
                    continue
                key = (call["tool"], call["arguments"])
                if key in done:
                    done.remove(key)
                else:
                    unread.append({"tool": call["tool"], "arguments": call["arguments"]})
            facts = dict(facts, unread_reads=unread, reads_complete=not unread)
        return facts


def compose(path, role, operation, data, gateway, batch):
    module = component.implementation(role)
    typed = module.Input.model_validate(data)
    base = load_component_profile(
        "offline",
        path,
        configuration=component_configuration(role),
        operation=operation,
        data=typed.model_dump(mode="json"),
        schemas=module.schemas(operation, typed),
        planner=component.requests,
        renderer=component.synthesize,
        clock=lambda: datetime.now(UTC),
        output_policy="candidate_child" if role == "Grafter" else "same_subject",
        workspace_ref=typed.workspace_ref if role == "Grafter" else None,
    )
    ports = EvaluationPorts(base, ComponentEvaluationArtifacts(base.artifacts, gateway, batch))
    ports.run_ref = base.run_ref
    return base, ports


def run_case(case, gateway, directory, batch, sink=None):
    role = case["role"]
    operation = case.get("operation") or COMPONENT_POLICIES[role].operation
    base, ports = compose(directory / "state.sqlite", role, operation, case["data"], gateway, batch)
    tick(base.run_ref, ports.clock(), ports)
    if sink is not None and ports.artifacts.port is not None:
        sink.extend(ports.artifacts.port.shapes)
    task = base.control.snapshot(base.run_ref).tasks[0]
    result = base.control.result(task.task.task_id)
    outputs = None
    if task.state == "succeeded":
        outputs = base.artifacts.inspect_outputs(task, base.context_for(task.task.task_id))
    return task, result, outputs, base


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True)
    parser.add_argument("--case-file", type=Path, required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--profile", choices=sorted(PROFILES), default="haiku")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if not args.live or not re.fullmatch(r"[a-z0-9-]{1,80}", args.batch_id):
        parser.error("explicit --live and stable bounded batch identity required")
    cases = {c["id"]: c for c in load_catalog(args.case_file)}
    case = cases[args.case]
    home = Path.home()
    evidence = home / "reports/goldgraft-model-gateway-20261111"
    profile = PROFILES[args.profile]()
    verify_qualification(evidence / f"qualification-components-{args.profile}.json", profile)
    from pieces.backend.model_gateway.provider import AnthropicProvider

    custody = home / ".config/goldgraft"
    ledger = Ledger(custody / "model-budget.sqlite")
    provider = AnthropicProvider(custody / "anthropic.env", profile)
    gateway = ComponentGateway(
        ledger, custody / "model-gateway-signing.key", profile, provider, roles={case["role"]}
    )
    directory = evidence / "live" / args.batch_id
    directory.mkdir(parents=True, exist_ok=True)
    started = datetime.now(UTC)
    shapes = []
    task, result, outputs, base = run_case(case, gateway, directory, args.batch_id, shapes)
    try:
        ledger.close(args.batch_id)
    except ValueError:
        pass
    with ledger.transaction() as db:
        ids = [r[0] for r in db.execute("SELECT id FROM turns WHERE batch=?", (args.batch_id,))]
    turns = [ledger.turn(args.batch_id, t) for t in ids]
    checked = score(case, outputs, base) if outputs is not None else None
    expected_hold = case.get("expected_outcome") == "blocked"
    # model_hold: the model itself must choose report_hold (judgment), never a malformed stop.
    # Turn ids are digests (unordered); a blocked turn only comes from report_hold and ends
    # the task, so any blocked turn means the model itself chose to hold.
    model_held = any((t.get("result") or {}).get("kind") == "blocked" for t in turns)
    if case.get("expected_outcome") == "model_hold":
        passed = task.state != "succeeded" and outputs is None and model_held
    elif case.get("expected_outcome") == "held_any":  # unverifiable by a model: system must hold
        passed = task.state != "succeeded" and outputs is None
    elif case.get("expected_outcome") == "plan_or_hold":  # both are safe; scored as such
        passed = (checked is not None and checked["passed"]) or (outputs is None and model_held)
    else:
        passed = (checked is not None and checked["passed"]) or (
            expected_hold and task.state != "succeeded"
        )
    report = {
        "evidence_class": "real_model_component_with_scripted_tool_control_boundaries",
        "role": case["role"],
        "case_id": case["id"],
        "case_digest": content_digest(case),
        "batch_id": args.batch_id,
        "model": profile.model,
        "profile_name": args.profile,
        "model_profile": profile.ref,
        "outcome": result.outcome if result else task.state,
        "issue": result.issue.model_dump(mode="json") if result and result.issue else None,
        "outputs": outputs,
        "check": checked,
        "turns": turns,
        "tool_call_shapes": shapes,
        "ledger": ledger.snapshot(),
        "latency_seconds": (datetime.now(UTC) - started).total_seconds(),
        "passed": bool(passed),
    }
    (directory / "result.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    print(
        json.dumps(
            {k: report[k] for k in ["role", "case_id", "batch_id", "model", "outcome", "passed"]}
        )
    )
    return 0 if passed else 1


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
