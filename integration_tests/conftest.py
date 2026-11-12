"""Offline boundary suite: refuse external sockets even if a test is misconfigured."""

import socket

import pytest


@pytest.fixture(autouse=True)
def loopback_only(monkeypatch):
    original = socket.socket.connect

    def connect(sock, address):
        if isinstance(address, tuple) and address[0] not in (
            "127.0.0.1",
            "::1",
            "localhost",
        ):
            raise RuntimeError("external_network_forbidden_in_offline_suite")
        return original(sock, address)

    monkeypatch.setattr(socket.socket, "connect", connect)
