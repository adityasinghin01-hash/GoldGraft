"""Scoped role dispatch and multi-artifact staging over the existing guarded loop."""

from importlib import import_module

from goldgraft_contracts.plan5_common import (
    Digest,
    Id,
    P5Record,
    Positive,
    Refs,
    Role,
    Utc,
    canonical_bytes,
    content_digest,
    reject_secret,
)
from goldgraft_contracts.registry import validate

from .component_agents import IMPLEMENTED_ROLES


class ScopedInputs(P5Record):
    role: Role
    operation: Id
    case_id: Id
    run_id: Id
    generation: Positive
    subject_digest: Digest
    input_refs: Refs
    observed_at: Utc
    data: dict


def implementation(role):
    if role not in IMPLEMENTED_ROLES:
        raise ValueError("DENIED unimplemented component role")
    return import_module("pieces.agents.component_agents." + role.lower().replace(" ", "_"))


def validate_inputs(task, value):
    raw = canonical_bytes(value)
    reject_secret(raw.decode())
    if len(raw) > 12000:
        raise ValueError("MISSING_EVIDENCE bounded role context")
    packet = ScopedInputs.model_validate(value)
    if (
        packet.role,
        packet.operation,
        packet.case_id,
        packet.run_id,
        packet.generation,
        packet.subject_digest,
        packet.input_refs,
    ) != (
        task.task.role,
        task.task.operation,
        task.case_id,
        task.run_id,
        task.generation,
        task.task.expected_subject,
        task.task.input_refs,
    ):
        raise ValueError("DENIED component scope/subject/input")
    module = implementation(packet.role)
    data = module.Input.model_validate(packet.data)
    module.admit(task, data)
    if list(task.task.expected_schemas) != list(module.schemas(task.task.operation, data)):
        raise ValueError("DENIED role output slots")
    return packet


def metadata(task, packet, suffix=""):
    return {
        "id": "draft-"
        + content_digest({"task": task.task.task_id, "input": task.input_digest, "suffix": suffix})[
            :16
        ],
        "graft_id": task.run_id,
        "created_at": packet.observed_at.isoformat(),
        "producer": {
            "kind": "agent",
            "name": task.task.role,
            "version": "1",
            "model": "deterministic-offline",
        },
    }


def requests(task, value):
    packet = validate_inputs(task, value)
    module = implementation(packet.role)
    return module.requests(task, module.Input.model_validate(packet.data))


def synthesize(task, value, observations):
    packet = validate_inputs(task, value)
    module = implementation(packet.role)
    outputs = module.synthesize(
        task, module.Input.model_validate(packet.data), packet, observations
    )
    return outputs[0]["payload"] if len(outputs) == 1 else {"outputs": outputs}


def unpack(task, payload):
    if len(task.task.expected_schemas) == 1:
        return [{"schema": task.task.expected_schemas[0], "payload": payload}]
    if not isinstance(payload, dict) or set(payload) != {"outputs"}:
        raise ValueError("INVALID artifact bundle")
    outputs = payload["outputs"]
    if not isinstance(outputs, list) or not 1 <= len(outputs) <= 16:
        raise ValueError("INVALID artifact bundle cardinality")
    for item in outputs:
        if not isinstance(item, dict) or set(item) != {"schema", "payload"}:
            raise ValueError("INVALID artifact bundle member")
    if set(item["schema"] for item in outputs) != set(task.task.expected_schemas):
        raise ValueError("DENIED output bundle ownership")
    return outputs


def _segments(items, is_read):
    """Split at non-read items: [[reads...], write, [reads...], ...] with positions kept."""
    out, run = [], []
    for item in items:
        if is_read(item):
            run.append(item)
        else:
            out += [run, [item]]
            run = []
    return out + [run]


def paired(planned, observations):
    """Pair observations with planned calls. Non-read calls keep their exact positions;
    within one run of reads, order is free (same multiset of tool+arguments)."""
    from goldgraft_contracts.plan5_tools import TOOL_CATALOG

    def read_call(c):
        return TOOL_CATALOG[c["tool"]].effect == "read"

    def read_obs(o):
        tool = (o.get("value") or {}).get("tool")
        return tool in TOOL_CATALOG and TOOL_CATALOG[tool].effect == "read"

    want, got = _segments(planned, read_call), _segments(observations, read_obs)
    if [len(x) for x in want] != [len(x) for x in got]:
        raise ValueError("DENIED observation tool binding")
    pairs = []
    for calls, seen in zip(want, got, strict=True):
        free = list(seen)
        for call in calls:
            match = next(
                (
                    o
                    for o in free
                    if (o.get("value") or {}).get("tool") == call["tool"]
                    and (
                        "proposal" in call
                        or "patch" in call
                        or "authored" in call
                        or "drafts" in call
                        or (o.get("value") or {}).get("arguments") == call["arguments"]
                    )
                ),
                free[0] if free else None,
            )
            if match is None:
                raise ValueError("DENIED observation tool binding")
            free.remove(match)
            pairs.append((call, match))
    return pairs


def validate_result(task, payload, packet, observations):
    module = implementation(packet.role)
    data = module.Input.model_validate(packet.data)
    planned = module.requests(task, data)
    if len(observations) != len(planned):
        raise ValueError("MISSING_EVIDENCE required tool observations")
    for call, observation in paired(planned, observations):
        if observation.get("evidence_class") != "scripted":
            raise ValueError("DENIED observation evidence class")
        value = observation.get("value", {})
        if value.get("tool") != call["tool"]:
            raise ValueError("DENIED observation tool binding")
        if "proposal" in call:
            if value.get("payload", {}).get("proposal") != call["proposal"]:
                raise ValueError("DENIED execution proposal binding")
        elif "authored" in call:
            # Model-authored content: the custody arguments must match exactly; the content
            # itself is judged by the role's deterministic review, never by equality.
            args = value.get("arguments", {})
            if any(args.get(k) != v for k, v in call["authored"].items()):
                raise ValueError("DENIED authored patch custody")
        elif "patch" in call:
            if value.get("payload", {}).get("patch") != call["patch"]:
                raise ValueError("DENIED candidate patch binding")
        elif "drafts" in call:
            if set(value.get("arguments", {})) != set(call["drafts"]):
                raise ValueError("DENIED staged draft arguments")
        elif value.get("arguments") != call["arguments"]:
            raise ValueError("DENIED observation arguments")
    outputs = unpack(task, payload)
    for item in outputs:
        parsed = validate(item["schema"], item["payload"])
        who = getattr(parsed, "producer", None)
        if who is not None and (who.kind.value, who.name) != ("agent", task.task.role):
            raise ValueError("DENIED output owner")
        if hasattr(parsed, "graft_id") and parsed.graft_id != task.run_id:
            raise ValueError("DENIED output graft")
    module.review(task, data, packet, outputs, observations)
    return outputs


def inspect_outputs(role, outputs):
    module = implementation(role)
    return {
        "role": role,
        "evidence_class": "scripted",
        "model_api_calls": 0,
        "outputs": module.inspect(outputs),
        "real_model_evaluation": "NOT RUN",
    }
