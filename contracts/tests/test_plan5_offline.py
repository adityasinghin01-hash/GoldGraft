"""The normal pytest entry point must deny IP connections without an optional plugin."""

import socket

import pytest


def test_ordinary_tests_deny_ip_connections_before_dispatch():
    assert getattr(socket.socket.connect, "_goldgraft_offline", False)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        with pytest.raises(AssertionError, match="offline"):
            connection.connect(("192.0.2.1", 9))


def test_safe_validation_errors_do_not_echo_input():
    from goldgraft_contracts.agent_runtime import ControlFailure
    from goldgraft_contracts.plan5_validation import validate_service_payload

    canary = "SYNTHETIC_PRIVATE_INPUT_CANARY"
    with pytest.raises(ControlFailure) as error:
        validate_service_payload("TaskContext/1", {"unexpected": canary})
    assert canary not in str(error.value)
    assert canary not in repr(error.value.error.model_dump())
    assert error.value.error.code == "INVALID"
