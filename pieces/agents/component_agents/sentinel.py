"""Sentinel audits redacted events; mandatory fencing remains deterministic GU code."""

import re
from datetime import datetime
from typing import Literal

from goldgraft_contracts.plan5_common import Count, Digest, Id, P5Record, Positive
from pydantic import Field

from ..component import metadata


class Event(P5Record):
    sequence: Positive
    case_id: Id
    run_id: Id
    generation: Positive
    kind: Literal["denied_tool", "secret_attempt", "stale_output", "termination_pending"]
    fingerprint: Digest


class Input(P5Record):
    after_seq: Count
    events: list[Event] = Field(max_length=32)


def admit(task, data):
    if [e.sequence for e in data.events] != list(
        range(data.after_seq + 1, data.after_seq + 1 + len(data.events))
    ):
        raise ValueError("MISSING_EVIDENCE audit gap")
    if any(
        (e.case_id, e.run_id, e.generation) != (task.case_id, task.run_id, task.generation)
        for e in data.events
    ):
        raise ValueError("DENIED audit tenancy/generation")


def schemas(operation, data):
    return ["Alert/1"]


def requests(task, data):
    calls = [
        {
            "tool": "audit.summary",
            "arguments": {"run_ref": "fake:runtime-run", "after_seq": data.after_seq},
        }
    ]
    if any(e.kind in {"denied_tool", "secret_attempt"} for e in data.events):
        calls.append(
            {
                "tool": "safety.request_hold",
                "arguments": {
                    "run_ref": "fake:runtime-run",
                    "reason_code": "AUDIT_POLICY_BREACH",
                    "evidence_refs": list(task.task.input_refs),
                },
            }
        )
    return calls


def facts(task, data):
    """Exact scoped argument values and the call policy; never the alert itself."""
    return {
        "run_ref": "fake:runtime-run",
        "after_seq": data.after_seq,
        "evidence_refs": list(task.task.input_refs),
        "hold_reason_code": "AUDIT_POLICY_BREACH",
        "call_policy": "Call audit.summary first. Then call safety.request_hold only if the "
        "window has a denied_tool or secret_attempt event (a policy breach). stale_output "
        "and termination_pending are reported in the alert, not held. Severity: CRITICAL "
        "for any policy breach, else MAJOR for any event, else MINOR. The runtime already "
        "refuses gapped, cross-case or stale-generation windows before you run, so a window "
        "you receive with no events is complete evidence: submit a MINOR alert, not a hold. "
        "Alert evidence_refs: "
        "the evidence_refs above plus, if a hold was requested, its returned request_id; "
        "event fingerprints are digests, not refs. Wording guard (literal, ignores "
        "negation): never write 'is/are/all/now/fully safe', 'no risk', 'no threat' or "
        "'is/was/has been terminated/halted/stopped/shut down/fenced'; write 'safety is "
        "not established' and 'termination is pending/not confirmed' instead.",
    }


# Every detected kind is reported, most severe first, with count and sequences.
ORDER = ["secret_attempt", "denied_tool", "stale_output", "termination_pending"]
LABEL = {
    "secret_attempt": "secret access attempt",
    "denied_tool": "denied tool request",
    "stale_output": "stale output",
    "termination_pending": "pending termination",
}


def describe(data):
    critical = any(e.kind in {"denied_tool", "secret_attempt"} for e in data.events)
    pending = any(e.kind == "termination_pending" for e in data.events)
    stale = any(e.kind == "stale_output" for e in data.events)
    if critical:
        parts = ["Policy breach observed; scoped hold requested. Termination is not confirmed."]
    elif pending:
        parts = ["Termination remains pending; timeout is not confirmed shutdown."]
    elif stale:
        parts = ["Stale output requires review; mandatory guards remain active."]
    else:
        return critical, ("No anomalies in the supplied audit window; safety is not established.")
    if critical and pending:
        parts.append("Termination remains pending; timeout is not confirmed shutdown.")
    if (critical or pending) and stale:
        parts.append("Stale output requires review.")
    found = []
    for kind in ORDER:
        sequences = [e.sequence for e in data.events if e.kind == kind]
        if sequences:
            label = LABEL[kind] + ("s" if len(sequences) > 1 else "")
            found.append(f"{len(sequences)} {label} (seq {', '.join(map(str, sequences))})")
    first, last = data.after_seq + 1, data.after_seq + len(data.events)
    parts.append("Detected: " + "; ".join(found) + f". Audit window: seq {first}-{last}.")
    return critical, " ".join(parts)


def synthesize(task, data, packet, observations):
    critical, message = describe(data)
    return [
        {
            "schema": "Alert/1",
            "payload": dict(
                metadata(task, packet),
                severity="CRITICAL" if critical else "MAJOR" if data.events else "MINOR",
                message=message,
                evidence_refs=list(task.task.input_refs),
                halted_agent=None,
            ),
        }
    ]


KEYWORDS = {
    "secret_attempt": ("secret",),
    "denied_tool": ("denied", "tool"),
    "stale_output": ("stale",),
    "termination_pending": ("pending",),
}
FALSE_CLAIMS = re.compile(
    r"\b(is|was|were|has been|have been|been)\s+(terminated|shut\s*down|halted|stopped|fenced)\b"
    r"|\b(all|fully|now|is|are)\s+safe\b|\bno\s+(risks?|threats?)\b",
    re.I,
)


def same_instant(got, want):
    try:
        return datetime.fromisoformat(got) == datetime.fromisoformat(want)
    except (TypeError, ValueError):
        return False


def grounded_refs(refs, inputs, observations):
    """All input refs, plus only receipt refs a tool actually returned; nothing invented."""
    receipts = {
        o["value"]["payload"].get("request_id")
        for o in observations[1:]
        if o["value"].get("tool") == "safety.request_hold"
    } - {None}
    return (
        isinstance(refs, list)
        and len(refs) == len(set(refs)) <= len(inputs) + len(receipts)
        and set(inputs) <= set(refs) <= set(inputs) | receipts
    )


def review(task, data, packet, outputs, observations):
    """Invariants, not wording: a model may explain differently but never misstate."""
    if observations[0]["value"]["payload"].get("events") != data.model_dump(mode="json")["events"]:
        raise ValueError("DENIED audit observation")
    want = synthesize(task, data, packet, observations)[0]["payload"]
    if len(outputs) != 1 or outputs[0]["schema"] != "Alert/1":
        raise ValueError("MISSING_EVIDENCE unsupported audit claim")
    got = outputs[0]["payload"]
    producer = dict(got.get("producer") or {})
    model = producer.pop("model", None)
    expected_producer = {k: v for k, v in want["producer"].items() if k != "model"}
    if (
        any(got.get(k) != want[k] for k in ("id", "graft_id"))
        or not same_instant(got.get("created_at"), want["created_at"])
        or producer != expected_producer
        or not isinstance(model, str)
        or not model
    ):
        raise ValueError("DENIED alert metadata")
    message = got.get("message") or ""
    present = {e.kind for e in data.events}
    if (
        got.get("severity") != want["severity"]
        or not grounded_refs(got.get("evidence_refs"), want["evidence_refs"], observations)
        or got.get("halted_agent") is not None
        or len(message) > 1200
        or FALSE_CLAIMS.search(message)
        or any(not any(k in message.lower() for k in KEYWORDS[kind]) for kind in present)
    ):
        raise ValueError("MISSING_EVIDENCE unsupported audit claim")
    if (
        len(observations) == 2
        and observations[1]["value"]["payload"].get("termination") != "pending"
    ):
        raise ValueError("MISSING_EVIDENCE halt receipt is not termination")


def inspect(outputs):
    p = outputs[0]["payload"]
    return {
        "severity": p["severity"],
        "message": p["message"],
        "halted_agent": p.get("halted_agent"),
        "hold_is_advisory": True,
    }


def sample(operation):
    return {
        "after_seq": 0,
        "events": [
            {
                "sequence": 1,
                "case_id": "case-demo",
                "run_id": "run-demo",
                "generation": 1,
                "kind": "denied_tool",
                "fingerprint": "a" * 64,
            }
        ],
    }
