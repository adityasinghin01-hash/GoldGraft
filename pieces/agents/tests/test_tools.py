"""Guarded arguments and refs never become host commands or financial authority."""

from dataclasses import replace

import pytest
from goldgraft_contracts.plan5_common import content_digest

from .test_runtime import NOW, profile


@pytest.mark.parametrize(
    "arguments",
    [
        {"snapshot_ref": "fixture:input", "path": "../secret", "max_bytes": 32},
        {"snapshot_ref": "fixture:input", "path": "/etc/passwd", "max_bytes": 32},
        {"snapshot_ref": "fixture:input", "path": "ok.php", "max_bytes": 32769},
        {
            "snapshot_ref": "fixture:input",
            "path": "ok.php",
            "max_bytes": 32,
            "shell": "echo unsafe",
        },
    ],
)
def test_bad_arguments_never_reach_tool(tmp_path, arguments):
    from pieces.agents.scheduler import tick

    ports = profile(tmp_path)
    turn = "turn:" + content_digest(
        {"run": "run-demo", "generation": 1, "task": "survey", "attempt": 1, "turn": 0}
    )
    ports.model.script(
        turn, {"kind": "tool_calls", "calls": [{"tool": "source.read", "arguments": arguments}]}
    )
    assert tick("fake:runtime-run", NOW, ports).completed == 0
    assert ports.tools.total_dispatches() == 0


def test_revocation_between_intent_and_dispatch_is_rechecked(tmp_path):
    from pieces.agents.runtime import run_task

    ports = profile(tmp_path)
    lease = ports.control.claim("worker", NOW)

    def fault(point):
        if point == "before_tool":
            ports.control.set_authority("fake:runtime-run", False)

    with pytest.raises(ValueError, match="DENIED"):
        run_task(
            lease, ports.control, ports.artifacts, ports.model, ports.tools, now=NOW, fault=fault
        )
    assert ports.tools.total_dispatches() == 0
    assert ports.control.accepted_result_count() == 0


def test_forbidden_cross_role_tool_is_denied_before_dispatch(tmp_path):
    from pieces.agents.scheduler import tick

    ports = profile(tmp_path)
    turn = "turn:" + content_digest(
        {"run": "run-demo", "generation": 1, "task": "survey", "attempt": 1, "turn": 0}
    )
    ports.model.script(
        turn,
        {
            "kind": "tool_calls",
            "calls": [{"tool": "status.read", "arguments": {"run_ref": "fake:runtime-run"}}],
        },
    )
    assert tick("fake:runtime-run", NOW, ports).completed == 0
    assert ports.tools.total_dispatches() == 0


def test_forged_tool_argument_ref_is_denied(tmp_path):
    from pieces.agents.scheduler import tick

    ports = profile(tmp_path)
    original = ports.model.turn

    def turn(request):
        response = original(request)
        response.calls[0].arguments_ref = "fake:blob:another-task"
        return response

    wrapped = replace(
        ports,
        model=type(
            "ForgedModel", (), {"turn": staticmethod(turn), "reconcile": ports.model.reconcile}
        )(),
    )
    assert tick("fake:runtime-run", NOW, wrapped).completed == 0
    assert ports.tools.total_dispatches() == 0


def test_cross_case_snapshot_ref_denies_before_dispatch(tmp_path):
    from pieces.agents.scheduler import tick

    ports = profile(tmp_path)
    turn = "turn:" + content_digest(
        {"run": "run-demo", "generation": 1, "task": "survey", "attempt": 1, "turn": 0}
    )
    ports.model.script(
        turn,
        {
            "kind": "tool_calls",
            "calls": [
                {
                    "tool": "source.read",
                    "arguments": {
                        "snapshot_ref": "fake:another-case-source",
                        "path": "checkout.php",
                        "max_bytes": 32,
                    },
                }
            ],
        },
    )
    assert tick("fake:runtime-run", NOW, ports).completed == 0
    assert ports.tools.total_dispatches() == 0


def test_invalid_second_read_denies_entire_batch(tmp_path):
    from pieces.agents.scheduler import tick

    ports = profile(tmp_path)
    turn = "turn:" + content_digest(
        {"run": "run-demo", "generation": 1, "task": "survey", "attempt": 1, "turn": 0}
    )
    ports.model.script(
        turn,
        {
            "kind": "tool_calls",
            "calls": [
                {
                    "tool": "source.read",
                    "arguments": {
                        "snapshot_ref": "fixture:input",
                        "path": "checkout.php",
                        "max_bytes": 32,
                    },
                },
                {
                    "tool": "source.read",
                    "arguments": {
                        "snapshot_ref": "fake:other-case",
                        "path": "checkout.php",
                        "max_bytes": 32,
                    },
                },
            ],
        },
    )
    assert tick("fake:runtime-run", NOW, ports).completed == 0
    assert ports.tools.total_dispatches() == 0


def test_forged_tool_receipt_case_does_not_advance(tmp_path):
    from pieces.agents.scheduler import tick

    ports = profile(tmp_path)
    original = ports.tools.invoke

    def invoke(invocation):
        receipt = original(invocation)
        return receipt.model_copy(update={"case_id": "another-case"})

    tools = type(
        "ForgedTools", (), {"invoke": staticmethod(invoke), "reconcile": ports.tools.reconcile}
    )()
    assert tick("fake:runtime-run", NOW, replace(ports, tools=tools)).completed == 0
    assert ports.control.result("survey").outcome == "blocked"
