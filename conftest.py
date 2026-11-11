"""Ordinary tests are offline; provider/model qualification uses separate live_ scripts."""

import socket

import pytest


@pytest.fixture(autouse=True)
def deny_ip_network(monkeypatch):
    connect = socket.socket.connect
    connect_ex = socket.socket.connect_ex

    def guarded_connect(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            raise AssertionError("ordinary tests are offline: IP connection denied")
        return connect(sock, address)

    def guarded_connect_ex(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            raise AssertionError("ordinary tests are offline: IP connection denied")
        return connect_ex(sock, address)

    guarded_connect._goldgraft_offline = True
    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
