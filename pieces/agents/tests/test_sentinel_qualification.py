"""Sentinel ceiling qualification: complete, grounded detection over every event mix.

Actual runtime + Sentinel component, deterministic (no model). Independent
expectations are computed here from the window, never from Sentinel's code.
"""

import itertools

import pytest

from pieces.agents.component_agents.sentinel import sample
from pieces.agents.component_cli import create
from pieces.agents.scheduler import tick

from .test_runtime import NOW

KINDS = ["secret_attempt", "denied_tool", "stale_output", "termination_pending"]
LABEL = {
    "secret_attempt": "secret access attempt",
    "denied_tool": "denied tool request",
    "stale_output": "stale output",
    "termination_pending": "pending termination",
}


def window(kinds, after=0):
    base = sample("audit")["events"][0]
    return {
        "after_seq": after,
        "events": [
            dict(base, sequence=after + i + 1, kind=kind, fingerprint=f"{i:064x}")
            for i, kind in enumerate(kinds)
        ],
    }


def run(tmp_path, data, name="s"):
    p = create("Sentinel", tmp_path / f"{name}.sqlite", data=data, clock=lambda: NOW)
    done = tick(p.run_ref, NOW, p).completed
    task = p.control.snapshot(p.run_ref).tasks[0]
    alert = None
    if done:
        alert = p.artifacts.inspect_outputs(task, p.context_for(task.task.task_id))[0]["payload"]
    return p, done, alert


def expected_severity(kinds):
    if {"secret_attempt", "denied_tool"} & set(kinds):
        return "CRITICAL"
    return "MAJOR" if kinds else "MINOR"


MIXES = [
    list(itertools.chain.from_iterable([kind] * reps for kind in subset))
    for size in range(1, 5)
    for subset in itertools.combinations(KINDS, size)
    for reps in (1, 3)
]


@pytest.mark.parametrize("kinds", MIXES, ids=lambda k: "+".join(sorted(set(k))) + f"x{len(k)}")
def test_every_event_mix_is_fully_and_exactly_reported(tmp_path, kinds):
    p, done, alert = run(tmp_path, window(kinds, after=7))
    assert done == 1
    message = alert["message"]
    assert alert["severity"] == expected_severity(kinds)
    assert alert["halted_agent"] is None
    critical = {"secret_attempt", "denied_tool"} & set(kinds)
    assert p.tools.total_dispatches() == (2 if critical else 1)  # hold requested only on breach
    for kind in KINDS:
        sequences = [8 + i for i, k in enumerate(kinds) if k == kind]
        if sequences:
            label = LABEL[kind] + ("s" if len(sequences) > 1 else "")
            assert f"{len(sequences)} {label} (seq {', '.join(map(str, sequences))})" in message
        else:
            assert LABEL[kind] not in message
    assert f"Audit window: seq 8-{7 + len(kinds)}." in message
    if critical:
        assert "Termination is not confirmed" in message
    if "termination_pending" in kinds:
        assert "timeout is not confirmed shutdown" in message
    assert "safe" not in message.replace("safety is not established", "")


def test_empty_window_never_claims_safety(tmp_path):
    _, done, alert = run(tmp_path, {"after_seq": 3, "events": []})
    assert done == 1 and alert["severity"] == "MINOR"
    assert "safety is not established" in alert["message"]


def test_full_32_event_window_is_reported_and_33_is_refused(tmp_path):
    kinds = [KINDS[i % 4] for i in range(32)]
    _, done, alert = run(tmp_path, window(kinds), "full")
    assert done == 1 and "8 secret access attempts" in alert["message"]
    # A 33-event window is refused when the task is created: nothing can dispatch.
    with pytest.raises(ValueError, match="at most 32"):
        run(tmp_path, window(kinds + ["stale_output"]), "over")


@pytest.mark.parametrize("change", ["duplicate", "reordered", "wrong_run", "skip_start"])
def test_untrustworthy_windows_hold_before_any_dispatch(tmp_path, change):
    data = window(["denied_tool", "stale_output", "termination_pending"], after=4)
    events = data["events"]
    if change == "duplicate":
        events[1]["sequence"] = events[0]["sequence"]
    elif change == "reordered":
        events[0], events[1] = events[1], events[0]
    elif change == "wrong_run":
        events[2]["run_id"] = "run-other"
    else:
        data["after_seq"] = 3
    p, done, _ = run(tmp_path, data, change)
    assert done == 0 and p.model.total_dispatches() == p.tools.total_dispatches() == 0


def mutated(tmp_path, kinds, change, name):
    from pieces.agents.component_agents.sentinel import sample as _sample  # noqa: F401

    p = create("Sentinel", tmp_path / f"{name}.sqlite", data=window(kinds), clock=lambda: NOW)
    original = p.model.renderer

    def renderer(*args):
        value = original(*args)
        change(value)
        return value

    p.model.renderer = renderer
    done = tick(p.run_ref, NOW, p).completed
    return done


def test_a_model_paraphrase_that_keeps_every_fact_is_accepted(tmp_path):
    def paraphrase(v):
        v["message"] = (
            "Breach: a denied tool request and a secret access attempt appeared; a scoped "
            "hold was requested, but termination is not confirmed. A stale output and a "
            "pending termination also need review."
        )
        v["producer"]["model"] = "claude-haiku-5-5"

    kinds = ["denied_tool", "secret_attempt", "stale_output", "termination_pending"]
    assert mutated(tmp_path, kinds, paraphrase, "para") == 1


@pytest.mark.parametrize(
    ("change", "kinds"),
    [
        (
            lambda v: v.update(message="Policy breach; the agent has been terminated."),
            ["denied_tool"],
        ),
        (lambda v: v.update(message="Everything is safe now."), []),
        (
            lambda v: v.update(message="Policy breach observed; hold requested."),
            ["denied_tool", "stale_output"],
        ),
        (lambda v: v.update(severity="MINOR"), ["secret_attempt"]),
        (lambda v: v.update(evidence_refs=["fake:invented"]), ["stale_output"]),
        (lambda v: v["producer"].update(name="Herald"), ["stale_output"]),
    ],
    ids=[
        "claims_termination",
        "claims_safe",
        "omits_stale",
        "wrong_severity",
        "invented_evidence",
        "wrong_producer",
    ],
)
def test_model_outputs_that_break_an_invariant_are_rejected(tmp_path, change, kinds):
    assert mutated(tmp_path, kinds, change, "bad") == 0


def mutated_with_observations(tmp_path, kinds, change, name):
    p = create("Sentinel", tmp_path / f"{name}.sqlite", data=window(kinds), clock=lambda: NOW)
    original = p.model.renderer

    def renderer(task, value, observations):
        out = original(task, value, observations)
        change(out, observations)
        return out

    p.model.renderer = renderer
    return tick(p.run_ref, NOW, p).completed


def add_hold_receipt(v, observations):
    receipt = observations[1]["value"]["payload"]["request_id"]
    v["evidence_refs"] = v["evidence_refs"] + [receipt]


def zulu_time(v, observations):
    v["created_at"] = v["created_at"].replace("+00:00", "Z")


def test_live_model_variants_that_stay_grounded_are_accepted(tmp_path):
    # Seen on real Haiku runs (11 Nov): the returned hold receipt cited as evidence,
    # and the same timestamp written with "Z".
    assert mutated_with_observations(tmp_path, ["secret_attempt"], add_hold_receipt, "r") == 1
    assert mutated_with_observations(tmp_path, [], zulu_time, "z") == 1


@pytest.mark.parametrize(
    ("change", "kinds"),
    [
        (lambda v, o: v.update(evidence_refs=v["evidence_refs"] + [f"{0:064x}"]), ["stale_output"]),
        (
            lambda v, o: v.update(evidence_refs=v["evidence_refs"] + ["fake:hold:x"]),
            ["stale_output"],
        ),
        (lambda v, o: v.update(evidence_refs=[]), ["denied_tool"]),
        (lambda v, o: (add_hold_receipt(v, o), add_hold_receipt(v, o)), ["denied_tool"]),
        (lambda v, o: v.update(created_at="2026-01-01T00:00:00Z"), []),
    ],
    ids=["fingerprint_as_ref", "receipt_without_hold", "drops_input", "duplicate", "other_time"],
)
def test_ungrounded_refs_and_other_instants_are_rejected(tmp_path, change, kinds):
    assert mutated_with_observations(tmp_path, kinds, change, "bad") == 0
