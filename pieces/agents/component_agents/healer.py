"""Operational diagnosis only; a hold request is never performed recovery."""

import re
from typing import Literal

from goldgraft_contracts.common import StagePct
from goldgraft_contracts.plan5_common import P5Record, Ref
from pydantic import Field, StrictBool

from ..component import metadata
from .execution import valid_metadata
from .sentinel import FALSE_CLAIMS


class Input(P5Record):
    synthetic_observation: StrictBool
    stage_pct: StagePct
    anomaly: Literal["unknown_effect", "callback_gap", "current_state_incompatible", "none"]
    current_state_compatible: StrictBool
    legacy_available: StrictBool
    evidence: dict[Ref, dict] = Field(min_length=1, max_length=4)
    status: dict


def admit(task, data):
    if not data.synthetic_observation:
        raise ValueError("UNSUPPORTED live observation profile not qualified")
    if (
        type(data.status.get("generation")) is not int
        or data.status["generation"] != task.generation
    ):
        raise ValueError("DENIED stale operational status")


def schemas(operation, data):
    return ["HealNote/1"]


def requests(task, data):
    calls = [
        dict(tool="status.read", arguments={"run_ref": "fake:runtime-run"}),
        *[
            dict(tool="evidence.read", arguments={"ref": r, "max_bytes": 4096})
            for r in data.evidence
        ],
    ]
    if data.anomaly != "none" or not data.current_state_compatible:
        calls.append(
            dict(
                tool="safety.request_hold",
                arguments={
                    "run_ref": "fake:runtime-run",
                    "reason_code": "OPERATIONAL_REVIEW_REQUIRED",
                    "evidence_refs": task.task.input_refs,
                },
            )
        )
    return calls


def synthesize(task, data, packet, observations):
    pause = data.anomaly != "none" or not data.current_state_compatible
    text = "Synthetic operational observation: " + data.anomaly + ". "
    text += (
        "Hold requested; current-state-compatible recovery requires independent review. "
        "No restoration or compensation performed."
        if pause
        else "No listed anomaly in this bounded synthetic window; no live safety claim."
    )
    value = {
        **metadata(task, packet),
        "stage_pct": data.stage_pct,
        "text": text,
        "pause_requested": pause,
        "cutback_requested": False,
        "evidence_refs": list(data.evidence),
    }
    return [dict(schema="HealNote/1", payload=value)]


def review(task, data, packet, outputs, observations):
    got = outputs[0]["payload"]
    want = synthesize(task, data, packet, observations)[0]["payload"]
    text = got.get("text", "")
    if (
        not valid_metadata(got, want)
        or any(got.get(k) != want[k] for k in ("stage_pct", "pause_requested", "cutback_requested"))
        or sorted(got.get("evidence_refs", [])) != sorted(want["evidence_refs"])
        or not 1 <= len(text) <= 1000
        or (
            data.anomaly != "none"
            and data.anomaly not in text
            and data.anomaly.replace("_", " ") not in text.lower()
        )
        or FALSE_CLAIMS.search(text)
        or re.search(
            r"\b(restored|rolled back|cut back|compensated|recovered|switched traffic)\b",
            text,
            re.I,
        )
        or (want["pause_requested"] and not re.search(r"\bhold\b", text, re.I))
    ):
        raise ValueError("DENIED ungrounded recovery/cutback")
    if outputs[0]["payload"]["pause_requested"]:
        v = observations[-1]["value"]["payload"]
        if v.get("requested") is not True or v.get("termination") != "pending":
            raise ValueError("DENIED false termination claim")


PROGRESS = True


def route(data):
    return "sonnet" if len(data.evidence) >= 4 else "haiku8"


def facts(task, data):
    return {
        "run_ref": "fake:runtime-run",
        "hold_reason_code": "OPERATIONAL_REVIEW_REQUIRED",
        "hold_request_refs": list(task.task.input_refs),
        "observation_refs": list(data.evidence),
        "max_bytes": 4096,
        "call_policy": "Read status.read and every evidence ref using unread_reads; at most "
        "four reads per response, never repeat a read. Diagnose the current supplied anomaly "
        "and state compatibility yourself. If operational review is needed, request "
        "safety.request_hold alone using hold_reason_code and evidence_refs=hold_request_refs. "
        "Then submit HealNote/1 with reference_metadata, unchanged stage_pct, observed "
        "diagnosis in text, your pause_requested decision, cutback_requested false, and "
        "evidence_refs exactly equal to observation_refs (never hold_request_refs, run refs "
        "or hold receipt ids). A hold "
        "request must have a requested:true receipt with termination:pending. Mention the "
        "anomaly by its supplied name and a requested hold where relevant. Never perform "
        "recovery, traffic changes, compensation or old-database restoration. Literal "
        "word guards ignore negation: avoid restored, rolled back, cut back, compensated, "
        "recovered, switched traffic, is safe and is terminated; state independent review "
        "is required and recovery remains unperformed.",
    }


def inspect(outputs):
    v = outputs[0]["payload"]
    return dict(
        diagnosis=v["text"],
        hold_requested=v["pause_requested"],
        cutback_requested=v["cutback_requested"],
        recovery_performed=False,
    )


def sample(operation):
    return dict(
        synthetic_observation=True,
        stage_pct=0,
        anomaly="current_state_incompatible",
        current_state_compatible=False,
        legacy_available=True,
        evidence={
            "fixture:state-observation": {"new_economic_state": True, "legacy_restore_safe": False}
        },
        status={"generation": 1, "state": "operational_review"},
    )
