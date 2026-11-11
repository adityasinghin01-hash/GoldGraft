"""Operational diagnosis only; a hold request is never performed recovery."""

from typing import Literal

from goldgraft_contracts.common import StagePct
from goldgraft_contracts.plan5_common import P5Record, Ref
from pydantic import Field, StrictBool

from ..component import metadata


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
    if data.status.get("generation") != task.generation:
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
    if outputs != synthesize(task, data, packet, observations):
        raise ValueError("DENIED ungrounded recovery/cutback")
    if outputs[0]["payload"]["pause_requested"]:
        v = observations[-1]["value"]["payload"]
        if v.get("requested") is not True or v.get("termination") != "pending":
            raise ValueError("DENIED false termination claim")


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
