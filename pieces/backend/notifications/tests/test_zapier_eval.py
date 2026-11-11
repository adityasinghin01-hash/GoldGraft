"""Zapier evaluation sender: opt-in, dedupe, retry, unknown, quota, custody. No network."""

import json
import socket

import pytest

from pieces.backend.notifications.zapier_eval import ZapierSender

URL = "https://hooks.zapier.com/hooks/catch/123456/abcDEF1/"


def preview(key="a" * 64, **changes):
    value = {
        "event_key": key,
        "text": "The source inventory is accepted. Inventory contains 2 source indicators.",
        "projection": "private_status",
        "delivery": "NOT SENT",
        "authority": "NONE",
    }
    return dict(value, **changes)


def sender(tmp_path, responses, *, url=URL, mode=0o600):
    hook = tmp_path / "zapier.env"
    hook.write_text(f"ZAPIER_HOOK_URL={url}\n")
    hook.chmod(mode)
    calls = []

    def post(target, body, timeout):
        calls.append((target, json.loads(body)))
        outcome = responses.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    return ZapierSender(tmp_path / "outbox.sqlite", hook, post=post), calls


def test_requires_explicit_opt_in_and_stops_after_opt_out(tmp_path):
    s, calls = sender(tmp_path, [(200, b'{"status":"success","id":"abc"}')])
    with pytest.raises(ValueError, match="opt-in"):
        s.send(preview())
    s.opt_in("my inbox")
    assert s.send(preview())["state"] == "sent"
    s.opt_out()
    with pytest.raises(ValueError, match="opt-in"):
        s.send(preview(key="b" * 64))
    assert len(calls) == 1


def test_one_minimal_notification_per_event_and_dedupe_on_resend(tmp_path):
    s, calls = sender(tmp_path, [(200, b'{"status":"success","id":"z1","request_id":"r1"}')])
    s.opt_in("my inbox")
    first = s.send(preview())
    again = s.send(preview())
    assert first["state"] == "sent" and again["deduplicated"] is True and len(calls) == 1
    target, body = calls[0]
    assert target == URL and set(body) == {
        "event_key",
        "text",
        "projection",
        "source",
        "notice",
        "destination",
    }
    assert "not an approval" in body["notice"]
    assert json.loads(first["receipt"]) == {"status": "success", "id": "z1", "request_id": "r1"}


def test_quota_or_server_errors_retry_same_key_then_close(tmp_path):
    s, calls = sender(tmp_path, [(429, b""), (503, b""), (429, b"")])
    s.opt_in("my inbox")
    assert s.send(preview())["state"] == "retryable"
    assert s.send(preview())["state"] == "retryable"
    final = s.send(preview())
    assert final["state"] == "failed" and final["attempts"] == 3 and final["last_status"] == 429
    with pytest.raises(ValueError, match="closed"):
        s.send(preview())
    assert {c[1]["event_key"] for c in calls} == {"a" * 64}


def test_possible_delivery_is_unknown_and_never_resent_but_refused_connect_is_retryable(tmp_path):
    s, calls = sender(tmp_path, [TimeoutError(), ConnectionRefusedError(), (200, b"{}")])
    s.opt_in("my inbox")
    assert s.send(preview())["state"] == "unknown"
    with pytest.raises(ValueError, match="UNKNOWN"):
        s.send(preview())
    assert s.send(preview(key="c" * 64))["state"] == "retryable"
    assert s.send(preview(key="c" * 64))["state"] == "sent"
    assert len(calls) == 3


def test_rejects_unapproved_shapes_secrets_and_unsafe_hook_custody(tmp_path):
    s, calls = sender(tmp_path, [])
    s.opt_in("my inbox")
    for bad in [
        preview(delivery="SENT"),
        preview(authority="APPROVED"),
        preview(projection="raw"),
        preview(text="token " + "sk-" + "ant-" + "x" * 8),
        dict(preview(), extra="payload"),
        preview(key="not-a-digest"),
    ]:
        with pytest.raises(ValueError):
            s.send(bad)
    for url, mode in [("https://evil.example.com/hooks/catch/1/a/", 0o600), (URL, 0o644)]:
        (tmp_path / "x").mkdir(exist_ok=True)
        bad_sender, _ = sender(tmp_path / "x", [], url=url, mode=mode)
        bad_sender.opt_in("my inbox")
        with pytest.raises(ValueError, match="ZAPIER_HOOK_UNAVAILABLE"):
            bad_sender.send(preview())
        assert bad_sender.status("a" * 64) is None  # nothing recorded before custody passes
    assert calls == []


def test_dns_failure_is_retryable_and_sender_never_touches_agent_state(tmp_path):
    s, calls = sender(tmp_path, [socket.gaierror(), (200, b"not json")])
    s.opt_in("my inbox")
    assert s.send(preview())["state"] == "retryable"
    result = s.send(preview())
    assert result["state"] == "sent" and json.loads(result["receipt"]) == {
        "status": "accepted_unparsed"
    }
