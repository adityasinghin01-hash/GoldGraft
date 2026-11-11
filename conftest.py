"""Ordinary tests are offline; provider/model qualification uses separate live_ scripts."""

import socket

import pytest


@pytest.fixture(autouse=True)
def deny_ip_network(monkeypatch):
    connect = socket.socket.connect
    connect_ex = socket.socket.connect_ex

    def _is_loopback(address):
        if isinstance(address, tuple) and len(address) >= 1:
            return address[0] in ("127.0.0.1", "localhost", "::1")
        return False

    def guarded_connect(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6) and not _is_loopback(address):
            raise AssertionError("ordinary tests are offline: IP connection denied")
        return connect(sock, address)

    def guarded_connect_ex(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6) and not _is_loopback(address):
            raise AssertionError("ordinary tests are offline: IP connection denied")
        return connect_ex(sock, address)

    guarded_connect._goldgraft_offline = True
    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
