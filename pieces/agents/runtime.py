"""Bounded guarded loop; model/provider clients and effects remain behind ports."""

import hashlib
import json
import threading
from datetime import UTC, datetime

from goldgraft_contracts.agent_runtime import (
    AgentResult,
    ControlFailure,
    ModelTurnRequest,
    ModelTurnResult,
    TaskCheckpoint,
    ToolInvocation,
)
from goldgraft_contracts.plan5_common import Issue, content_digest, reject_secret
from goldgraft_contracts.plan5_tools import TOOL_CATALOG, validate_tool_arguments
from goldgraft_contracts.registry import validate

from . import component, herald
from .context import build_context
from .ports import ModelPolicy
from .roles import validate_role_task
from .surveyor import validate_inputs, validate_inventory
from .tools import validate_invocation


def parse_json(raw):
    if len(raw) > 24000:
        raise ValueError("INVALID oversized context/output")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("INVALID duplicate key")
            result[key] = value
        return result

    def constant(value):
        raise ValueError("INVALID nonfinite JSON")

    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)

    def scan(item):
        if isinstance(item, str):
            reject_secret(item)
        elif isinstance(item, dict):
            for key, child in item.items():
                reject_secret(key)
                scan(child)
        elif isinstance(item, list):
            for child in item:
                scan(child)

    scan(value)
    return value


def run_task(lease, control, artifacts, model, tools, *, now=None, fault=None):
    fault = fault or (lambda point: None)
    clock = getattr(artifacts, "clock", lambda: datetime.now(UTC))
    now = clock() if now is None else now
    task = control.load(lease)
    state = {"turn": 0, "tools": 0, "malformed": 0, "observations": []}
    role_policy = None
    renewed_at = now
    lease_lock = threading.RLock()

    def guard():
        nonlocal lease, now, renewed_at
        with lease_lock:
            now = clock()
            control.load(lease)
            if (now - renewed_at).total_seconds() >= 15:
                lease = control.renew(lease, now)
                renewed_at = now

    def call_with_heartbeat(call):
        stopped = threading.Event()
        errors = []

        def heartbeat():
            while not stopped.wait(getattr(artifacts, "heartbeat_seconds", 15)):
                try:
                    guard()
                except ValueError as exc:
                    errors.append(exc)
                    return

        worker = threading.Thread(target=heartbeat, daemon=True)
        worker.start()
        try:
            result = call()
            if errors:
                raise errors[0]
            guard()
            return result
        finally:
            stopped.set()
            worker.join(timeout=1)

    def save(next_step="model_turn", invocation_refs=None):
        ref = artifacts.save_state(lease, state)
        checkpoint = TaskCheckpoint(
            task_id=lease.task_id,
            generation=lease.generation,
            lease_epoch=lease.lease_epoch,
            turn=state["turn"],
            committed_message_refs=[ref],
            invocation_refs=invocation_refs or [],
            staged_output_refs=[],
            context_digest=content_digest(ctx),
            policy_digest=task.policy_digest,
            budget_reservation_refs=[ctx.budget_ref],
            wake_condition_ref=None,
            next_step=next_step,
            created_at=now,
        )
        control.checkpoint(lease, checkpoint)

    def finish(outcome, refs, code=None):
        guard()  # Fresh authority/Stop/lease check before accepting output.
        issue = (
            None
            if code is None
            else Issue(
                code=code,
                input_ref=None,
                owner_role=task.task.role.replace(" ", "_") if role_policy else "runtime",
                recovery="reconcile" if code == "UNKNOWN" else "supply_input",
                evidence_refs=[],
            )
        )
        result = AgentResult(
            task_id=lease.task_id,
            request_id=task.request_id,
            case_id=task.case_id,
            run_id=task.run_id,
            generation=lease.generation,
            lease_epoch=lease.lease_epoch,
            input_digest=task.input_digest,
            outcome=outcome,
            output_refs=refs,
            evidence_refs=list(state["observations"]) if role_policy else [],
            issue=issue,
            completed_at=now,
            authenticity_ref=artifacts.result_authenticity(lease),
        )
        control.finish(lease, result)
        fault("after_finish")
        return result

    try:
        ctx = build_context(task, lease, artifacts, now=now)
        model_policy = (
            artifacts.model_admission(lease)
            if hasattr(artifacts, "model_admission")
            else ModelPolicy("fake:scripted", ctx.budget_ref, 24000, 4000, 12)
        )
        if not isinstance(model_policy, ModelPolicy):
            return finish("blocked", [], "DENIED")
        role_policy = validate_role_task(task)
        if role_policy:
            if not hasattr(artifacts, "role_inputs"):
                return finish("blocked", [], "MISSING_EVIDENCE")
            input_check = (
                validate_inputs
                if role_policy.role == "Surveyor"
                else herald.validate_inputs
                if role_policy.role == "Herald"
                else component.validate_inputs
            )
            role_inputs = input_check(task, artifacts.role_inputs(lease))
        if task.checkpoint_ref:
            checkpoint = artifacts.checkpoint_value(task.checkpoint_ref, lease)
            if checkpoint.policy_digest != task.policy_digest:
                raise ValueError("DENIED checkpoint policy")
            state = parse_json(artifacts.raw(checkpoint.committed_message_refs[-1], lease))
            if (
                set(state) != {"turn", "tools", "malformed", "observations"}
                or any(
                    type(state[k]) is not int or state[k] < 0
                    for k in ("turn", "tools", "malformed")
                )
                or not isinstance(state["observations"], list)
                or any(not isinstance(ref, str) for ref in state["observations"])
                or state["tools"] > 24
                or state["turn"] > 12
                or state["malformed"] > 1
            ):
                raise ValueError("INVALID checkpoint")
        while state["turn"] < model_policy.max_turns:
            guard()
            task = control.load(lease)
            turn_id = "turn:" + content_digest(
                {
                    "run": task.run_id,
                    "generation": task.generation,
                    "task": lease.task_id,
                    "attempt": task.attempt,
                    "turn": state["turn"],
                }
            )
            context_ref, context_digest = artifacts.model_context(lease, ctx, state["observations"])
            request = ModelTurnRequest(
                turn_id=turn_id,
                task_id=lease.task_id,
                generation=lease.generation,
                lease_epoch=lease.lease_epoch,
                model_profile_ref=model_policy.model_profile_ref,
                context_ref=context_ref,
                context_digest=context_digest,
                allowed_tool_ids=ctx.allowed_tool_ids,
                output_schema=ctx.expected_schemas[0],
                input_token_cap=model_policy.input_token_cap,
                output_token_cap=model_policy.output_token_cap,
                budget_reservation_ref=model_policy.budget_reservation_ref,
                deadline=ctx.deadline,
            )
            save()
            try:
                existing = model.reconcile(turn_id)
            except ValueError as exc:
                if str(exc).split()[0] != "NOT_FOUND":
                    raise
                existing = None
            if existing is not None and existing.state == "observed":
                response = ModelTurnResult.model_validate(
                    parse_json(artifacts.raw(existing.result_ref, lease))
                )
            elif existing is not None:
                return finish("unknown", [], "UNKNOWN")
            else:
                fault("before_model")
                guard()
                response = call_with_heartbeat(lambda request=request: model.turn(request))
            fault("after_model")
            if (response.turn_id, response.task_id) != (turn_id, lease.task_id):
                return finish("blocked", [], "DENIED")
            if response.kind == "blocked":
                return finish("blocked", [], response.issue.code)
            if response.kind == "final":
                try:
                    raw = artifacts.raw(response.final_artifact_ref, lease)
                    if len(raw) > 4000:
                        raise ValueError("INVALID output cap")
                    payload = parse_json(raw)
                    output_context = (
                        herald.validation_context(role_inputs)
                        if role_policy and role_policy.role == "Herald"
                        else None
                    )
                    if role_policy and role_policy.role not in {"Surveyor", "Herald"}:
                        for item in component.unpack(task, payload):
                            validate(item["schema"], item["payload"])
                    else:
                        validate(ctx.expected_schemas[0], payload, context=output_context)
                except (ValueError, TypeError):
                    state["malformed"] += 1
                    state["turn"] += 1
                    save()
                    if state["malformed"] > 1:
                        return finish("blocked", [], "INVALID_MODEL_OUTPUT")
                    continue
                if role_policy:
                    # Semantic evidence failure holds; it is not a schema-correction turn.
                    input_check = (
                        validate_inputs
                        if role_policy.role == "Surveyor"
                        else herald.validate_inputs
                        if role_policy.role == "Herald"
                        else component.validate_inputs
                    )
                    current_inputs = input_check(task, artifacts.role_inputs(lease))
                    if current_inputs != role_inputs:
                        raise ValueError("STALE projection changed")
                    (
                        validate_inventory
                        if role_policy.role == "Surveyor"
                        else herald.validate_result
                        if role_policy.role == "Herald"
                        else component.validate_result
                    )(
                        task,
                        payload,
                        role_inputs,
                        [parse_json(artifacts.raw(ref, lease)) for ref in state["observations"]],
                    )
                try:
                    if role_policy and role_policy.role not in {"Surveyor", "Herald"}:
                        outputs = artifacts.stage_outputs(lease, component.unpack(task, payload))
                    else:
                        outputs = [
                            artifacts.stage(
                                lease.task_id,
                                ctx.expected_schemas[0],
                                response.final_artifact_ref,
                                ctx.expected_subject,
                            )
                        ]
                except (ValueError, TypeError):
                    state["malformed"] += 1
                    state["turn"] += 1
                    save()
                    if state["malformed"] > 1:
                        return finish("blocked", [], "INVALID_MODEL_OUTPUT")
                    continue
                fault("before_finish")
                return finish("completed", outputs)
            if len(response.calls) > 4 or (
                len(response.calls) > 1
                and any(
                    call.tool not in TOOL_CATALOG or TOOL_CATALOG[call.tool].effect != "read"
                    for call in response.calls
                )
            ):
                return finish("blocked", [], "DENIED")
            # Validate the complete read batch before dispatching its first member.
            for call in response.calls:
                args_raw = artifacts.raw(call.arguments_ref, lease)
                if hashlib.sha256(args_raw).hexdigest() != call.arguments_digest:
                    return finish("blocked", [], "DENIED")
                arguments = validate_tool_arguments(task.task.role, call.tool, parse_json(args_raw))
                artifacts.authorize_tool(lease, call.tool, arguments)
                if call.tool not in task.task.allowed_tool_ids:
                    return finish("blocked", [], "DENIED")
            for index, call in enumerate(response.calls):
                if state["tools"] >= 24:
                    return finish("blocked", [], "TOOL_LIMIT")
                task = control.load(lease)
                args_raw = artifacts.raw(call.arguments_ref, lease)
                if hashlib.sha256(args_raw).hexdigest() != call.arguments_digest:
                    return finish("blocked", [], "DENIED")
                arguments = validate_tool_arguments(task.task.role, call.tool, parse_json(args_raw))
                artifacts.authorize_tool(lease, call.tool, arguments)
                invocation_id = "invocation:" + content_digest({"turn": turn_id, "index": index})
                invocation = ToolInvocation(
                    invocation_id=invocation_id,
                    task_id=lease.task_id,
                    case_id=task.case_id,
                    run_id=task.run_id,
                    generation=task.generation,
                    lease_epoch=lease.lease_epoch,
                    tool_id=call.tool,
                    arguments_ref=call.arguments_ref,
                    arguments_digest=call.arguments_digest,
                    input_digest=task.input_digest,
                    capability_ref="fake:capability:" + lease.task_id,
                    budget_reservation_ref=(
                        artifacts.tool_budget_ref(lease)
                        if hasattr(artifacts, "tool_budget_ref")
                        else ctx.budget_ref
                    ),
                    deadline=ctx.deadline,
                    state="intended",
                    result_refs=[],
                    effect_ref=None,
                    issue=None,
                )
                error = validate_invocation(task, invocation)
                if error:
                    return finish("blocked", [], error.code)
                try:
                    observed = tools.reconcile(invocation_id)
                except ValueError as exc:
                    if str(exc).split()[0] != "NOT_FOUND":
                        raise
                    observed = None
                if observed is None:
                    control.begin_tool(lease, invocation)
                    save("await_tool", [invocation_id])
                    fault("before_tool")
                    guard()
                    observed = call_with_heartbeat(
                        lambda invocation=invocation: tools.invoke(invocation)
                    )
                    fault("after_tool")
                if observed.state in {"submitted", "unknown"}:
                    return finish("unknown", [], "UNKNOWN")
                if (
                    observed.state != "observed"
                    or (
                        observed.invocation_id,
                        observed.task_id,
                        observed.case_id,
                        observed.run_id,
                        observed.generation,
                        observed.tool_id,
                        observed.input_digest,
                        observed.arguments_digest,
                    )
                    != (
                        invocation_id,
                        task.task.task_id,
                        task.case_id,
                        task.run_id,
                        task.generation,
                        call.tool,
                        task.input_digest,
                        call.arguments_digest,
                    )
                    or observed.lease_epoch > lease.lease_epoch
                ):
                    return finish("blocked", [], "DENIED")
                for ref in observed.result_refs:
                    parse_json(artifacts.raw(ref, lease))
                    state["observations"].append(ref)
                state["tools"] += 1
            state["turn"] += 1
            save()
        return finish("blocked", [], "TURN_LIMIT")
    except ControlFailure as exc:
        return finish("blocked", [], exc.error.code)
    except ValueError as exc:
        code = str(exc).split()[0] if str(exc) else "INVALID"
        code = (
            code
            if code
            in {
                "UNKNOWN",
                "DENIED",
                "MISSING_EVIDENCE",
                "BUDGET_EXHAUSTED",
                "EXPIRED",
                "STALE",
                "CANCELLED",
            }
            else "DENIED"
        )
        return finish("unknown" if code == "UNKNOWN" else "blocked", [], code)
