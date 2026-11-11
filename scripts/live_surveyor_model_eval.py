"""Opt-in actual Surveyor inference through the scoped local gateway.

Composition only: actual model/cost gateway, existing own runtime and explicitly
synthetic control/artifact/source/read-tool counterparts. Never production mode.
"""

import argparse
import json
import re
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from goldgraft_contracts.agent_runtime import ModelBudget, TaskLease
from goldgraft_contracts.plan5_common import canonical_bytes, content_digest
from goldgraft_foundation.offline_profile import load_runtime_profile

from pieces.agents.evals.surveyor import load_cases, score_artifact
from pieces.agents.ports import ModelPolicy
from pieces.agents.roles import surveyor_configuration
from pieces.agents.scheduler import tick
from pieces.agents.source_inventory import package_from_sources
from pieces.agents.surveyor import inspect_inventory
from pieces.backend.model_gateway.broker import Gateway
from pieces.backend.model_gateway.ledger import Ledger
from pieces.backend.model_gateway.profile import PROFILES, route_profile
from pieces.backend.model_gateway.qualification import verify_qualification


class EvaluationArtifacts:
    def __init__(self, base, gateway, batch):
        self.base, self.gateway, self.batch = base, gateway, batch
        self.port = None
        self.grant = None
        self.last_lease = None

    def __getattr__(self, name):
        return getattr(self.base, name)

    def fresh_lease(self):
        old = self.last_lease
        task = self.base.control.snapshot("fake:runtime-run").tasks[0]
        if old is None or (
            task.task.task_id,
            task.generation,
            task.lease_epoch,
            task.lease_owner,
        ) != (old.task_id, old.generation, old.lease_epoch, old.worker_id):
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

    def check(self, scope):
        lease = self.fresh_lease()
        task = self.base.control.load(lease)
        if (
            scope["task_id"],
            scope["case_id"],
            scope["run_id"],
            scope["generation"],
            scope["lease_epoch"],
            scope["input_digest"],
            scope["subject"],
            scope["prompt_digest"],
            scope["policy_digest"],
        ) != (
            task.task.task_id,
            task.case_id,
            task.run_id,
            task.generation,
            task.lease_epoch,
            task.input_digest,
            task.task.expected_subject,
            task.prompt_digest,
            task.policy_digest,
        ):
            raise ValueError("DENIED evaluation scope")

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
            }
            self.grant = self.gateway.grant(self.batch, scope)
            self.port = self.gateway.port(self.grant, self)
        context = ticket.context.model_copy(update={"budget_ref": self.batch})
        # Persist the new checkpoint context alongside the unchanged synthetic
        # lease context, so recovery can verify its actual budget/profile binding.
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

    def model_admission(self, lease):
        self.last_lease = lease
        if self.grant is None:
            raise ValueError("DENIED missing gateway grant")
        self.check(self.gateway.verify(self.grant))
        self.gateway.ledger.check(self.batch)
        profile = self.gateway.profile
        return ModelPolicy(
            profile.ref, self.batch, profile.input_cap, profile.output_cap, profile.max_turns
        )

    def model_context(self, lease, context, observation_refs):
        self.last_lease = lease
        return self.base.model_context(lease, context, observation_refs)

    def context_bytes(self, request):
        self.fresh_lease()
        with self.base.control.store.transaction() as db:
            row = db.execute(
                "SELECT body FROM contexts WHERE ref=?", (request.context_ref,)
            ).fetchone()
        if row is None:
            raise ValueError("MISSING_EVIDENCE model context")
        context = json.loads(row["body"])
        scope = self.gateway.verify(self.grant)
        bound = context.get("task_context", {})
        if (
            bound.get("task_ref"),
            bound.get("generation"),
            bound.get("lease_epoch"),
            bound.get("budget_ref"),
        ) != (
            "fake:task:" + scope["task_id"],
            scope["generation"],
            scope["lease_epoch"],
            self.batch,
        ):
            raise ValueError("DENIED scoped model context")
        return context

    def stage(self, *args):
        # Called either by ModelPort for untrusted inline bytes or by the own
        # runtime to validate/stage the final artifact; these are distinct calls.
        if len(args) == 1:
            return self.base.control.stage_untrusted(self.fresh_lease(), args[0])
        return self.base.stage(*args)

    def raw(self, ref, lease):
        self.last_lease = lease
        if ref.startswith("local:model-result:") and self.port:
            self.check(self.gateway.verify(self.grant))
            return self.port.result_bytes(ref)
        return self.base.raw(ref, lease)

    def tool_budget_ref(self, lease):
        self.last_lease = lease
        self.check(self.gateway.verify(self.grant))
        return "fake:zero-budget"  # Read tools are explicitly free synthetic counterparts.


class BoundModel:
    def __init__(self, artifacts):
        self.artifacts = artifacts

    def turn(self, request):
        if self.artifacts.port is None:
            raise ValueError("DENIED unqualified model port")
        return self.artifacts.port.turn(request)

    def reconcile(self, turn_id):
        if self.artifacts.port is None:
            raise ValueError("NOT_FOUND")
        return self.artifacts.port.reconcile(turn_id)


class EvaluationPorts:
    def __init__(self, base, artifacts):
        self.base, self.artifacts = base, artifacts
        self.control, self.tools, self.clock = base.control, base.tools, base.clock
        self.model = BoundModel(artifacts)

    def context_for(self, name):
        return self.base.context_for(name)


def compose(path, package, gateway, batch):
    base = load_runtime_profile(
        "offline",
        path,
        fixture="surveyor_inventory",
        configuration=surveyor_configuration(),
        inputs=package,
        clock=lambda: datetime.now(UTC),
    )
    return EvaluationPorts(base, EvaluationArtifacts(base.artifacts, gateway, batch))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True)
    parser.add_argument("--case-file", type=Path)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--independent-review", type=Path)
    parser.add_argument("--profile", choices=["haiku", "sonnet", "auto"], default="haiku")
    args = parser.parse_args(argv)
    if not args.live or not re.fullmatch(r"[a-z0-9-]{1,80}", args.batch_id):
        parser.error("explicit --live and stable bounded batch identity required")
    cases = {case["id"]: case for case in load_cases(args.case_file)}
    if args.case not in cases:
        parser.error("unknown synthetic evaluation case")
    home = Path.home()
    evidence = home / "reports/goldgraft-model-gateway-20261111"
    if args.profile == "auto":
        args.profile = route_profile(cases[args.case]["files"])
    profile = PROFILES[args.profile]()
    # Each model profile has its own separately qualified evidence document.
    name = "qualification.json" if args.profile == "haiku" else f"qualification-{args.profile}.json"
    qualification = verify_qualification(evidence / name, profile)
    if len(qualification["checks"]) < 3:
        raise ValueError("QUALIFICATION_INCOMPLETE")
    from pieces.backend.model_gateway.provider import AnthropicProvider

    # One fixed ledger and private signing identity for the entire13-agent project.
    custody = home / ".config/goldgraft"
    case = cases[args.case]
    if args.independent_review is not None:
        from pieces.backend.model_gateway.independent_review import IndependentTestLedger

        ledger = IndependentTestLedger(
            custody / "model-budget.sqlite",
            review_path=args.independent_review,
            signing_path=custody / "model-gateway-signing.key",
            profile=profile,
            case_id=args.case,
            case_digest=content_digest(case),
            batch=args.batch_id,
        )
    else:
        ledger = Ledger(custody / "model-budget.sqlite")
    provider = AnthropicProvider(custody / "anthropic.env", profile)
    gateway = Gateway(ledger, custody / "model-gateway-signing.key", profile, provider)
    package = package_from_sources(shop_id=case["shop_id"], files=case["files"])
    directory = evidence / "live" / args.batch_id
    directory.mkdir(parents=True, exist_ok=True)
    started = datetime.now(UTC)
    ports = compose(directory / "state.sqlite", package, gateway, args.batch_id)
    tick("fake:runtime-run", ports.clock(), ports)
    task = ports.control.snapshot("fake:runtime-run").tasks[0]
    result = ports.control.result("survey")
    checked, inspection, payload = None, None, None
    if task.state == "succeeded":
        descriptor, payload = ports.artifacts.inspect_output(task, ports.context_for("survey"))
        checked = score_artifact(case, payload)
        inspection = inspect_inventory(
            payload,
            input_refs=task.task.input_refs,
            output_ref=descriptor.ref,
            subject=descriptor.subject_digest,
            evidence_refs=result.evidence_refs,
            omissions=package["omissions"],
        )
        # The collector/control/tool counterpart label remains explicit; actual
        # inference is proved by gateway usage/request receipts, not that label.
        inspection["inference"] = "actual_Anthropic_API; synthetic_control_tools_collector"
        inspection["limitations"][0] = (
            "Actual model inference for this task; control/tools/collector remain synthetic."
        )
    try:
        ledger.close(args.batch_id)
    except ValueError:
        pass  # Submitted/unknown reservations remain; absent pre-admission batch is harmless.
    with ledger.transaction() as db:
        turn_ids = [
            row[0] for row in db.execute("SELECT id FROM turns WHERE batch=?", (args.batch_id,))
        ]
    turns = [ledger.turn(args.batch_id, turn) for turn in turn_ids]
    report = {
        "evidence_class": "real_model_component_with_scripted_tool_control_boundaries",
        "case_id": args.case,
        "case_digest": content_digest(case),
        "batch_id": args.batch_id,
        "model": profile.model,
        "sdk": profile.sdk,
        "model_profile": profile.ref,
        "profile_name": args.profile,
        "prompt_digest": surveyor_configuration()["prompt_digest"],
        "policy_digest": surveyor_configuration()["policy_digest"],
        "outcome": result.outcome if result else task.state,
        "issue": result.issue.model_dump(mode="json") if result and result.issue else None,
        "artifact_check": checked,
        "inventory": payload,
        "inspection": inspection,
        "turns": turns,
        "ledger": ledger.snapshot(),
        "actual_inference_calls": sum(
            row["state"] in {"submitted", "unknown", "observed"} for row in turns
        ),
        "latency_seconds": (datetime.now(UTC) - started).total_seconds(),
        "passed": bool(checked and checked["passed"]),
        "limits": "Synthetic sample; source/runner/payment/merchant services remain unqualified.",
    }
    (directory / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: report[key]
                for key in [
                    "case_id",
                    "batch_id",
                    "model",
                    "outcome",
                    "passed",
                    "actual_inference_calls",
                    "ledger",
                ]
            }
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
