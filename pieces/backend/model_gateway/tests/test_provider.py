"""Actual pinned SDK request construction through an offline HTTP transport."""

import json

import pytest


def test_pinned_sdk_count_and_inference_use_expected_wire_without_retries(tmp_path, monkeypatch):
    httpx2 = pytest.importorskip("httpx2")  # SDK-wire tests need the pinned SDK venv
    from anthropic import Anthropic

    from pieces.backend.model_gateway.profile import Profile
    from pieces.backend.model_gateway.provider import AnthropicProvider

    seen = []

    def handle(request):
        seen.append((str(request.url), json.loads(request.content)))
        correct_key = (
            request.headers.get("x-api-key") == "sk-ant-synthetic-test-key"
            or request.headers.get("authorization") == "Bearer sk-ant-synthetic-test-key"
        )
        assert correct_key
        if request.url.path.endswith("count_tokens"):
            return httpx2.Response(200, json={"input_tokens": 100})
        return httpx2.Response(
            200,
            headers={"request-id": "req_synthetic"},
            json={
                "id": "msg_synthetic",
                "type": "message",
                "role": "assistant",
                "model": "claude-haiku-5-5",
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "content": [{"type": "text", "text": "synthetic"}],
                "usage": {"input_tokens": 100, "output_tokens": 10},
            },
        )

    key = tmp_path / "private.env"
    key.write_text("ANTHROPIC_API_KEY=sk-ant-synthetic-test-key\n")
    key.chmod(0o600)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.setattr(
        "anthropic.DefaultHttpxClient",
        lambda **kwargs: httpx2.Client(
            transport=httpx2.MockTransport(handle),
            trust_env=False,
            follow_redirects=False,
        ),
    )
    provider = AnthropicProvider(key, Profile())
    assert isinstance(provider.client, Anthropic)
    assert provider.client.max_retries == 0
    wire = {
        "model": "claude-haiku-5-5",
        "max_tokens": 50,
        "messages": [{"role": "user", "content": "synthetic"}],
        "system": "test",
        "tools": [],
        "tool_choice": {"type": "auto"},
        "thinking": {"type": "disabled"},
        "service_tier": "standard_only",
    }
    assert provider.count(wire) == 100
    result = provider.generate(wire)
    assert result["request_id"] == "req_synthetic"
    assert len(seen) == 2
    assert all(url.startswith("https://api.anthropic.com/") for url, _ in seen)


def test_private_custody_rejects_symlink_and_non_private_modes(tmp_path):
    from pieces.backend.model_gateway.secrets import api_key

    target = tmp_path / "key"
    target.write_text("ANTHROPIC_API_KEY=sk-ant-synthetic-test-key\n")
    target.chmod(0o644)
    with pytest.raises(ValueError, match="UNSAFE"):
        api_key(target)
    target.chmod(0o600)
    link = tmp_path / "link"
    link.symlink_to(target)
    with pytest.raises(ValueError, match="UNSAFE"):
        api_key(link)


def test_real_sdk_http_error_retains_safe_request_id_without_body_or_retry(tmp_path, monkeypatch):
    httpx2 = pytest.importorskip("httpx2")  # SDK-wire tests need the pinned SDK venv

    from pieces.backend.model_gateway.profile import Profile
    from pieces.backend.model_gateway.provider import AnthropicProvider, ProviderFailure

    seen = []

    def handle(request):
        seen.append(request.url.path)
        return httpx2.Response(
            400,
            headers={"request-id": "req_failure"},
            json={
                "type": "error",
                "error": {
                    "type": "invalid_request_error",
                    "message": "private body must not escape",
                },
            },
        )

    key = tmp_path / "private.env"
    key.write_text("ANTHROPIC_API_KEY=sk-ant-synthetic-test-key\n")
    key.chmod(0o600)
    monkeypatch.setattr(
        "anthropic.DefaultHttpxClient",
        lambda **kwargs: httpx2.Client(
            transport=httpx2.MockTransport(handle),
            trust_env=False,
            follow_redirects=False,
        ),
    )
    provider = AnthropicProvider(key, Profile())
    with pytest.raises(ProviderFailure) as raised:
        provider.generate(
            {
                "model": "claude-haiku-5-5",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "synthetic"}],
            }
        )
    assert raised.value.diagnostic == {
        "category": "http_error",
        "status": 400,
        "request_id": "req_failure",
        "error_type": "invalid_request_error",
    }
    assert str(raised.value) == "PROVIDER_FAILURE"
    assert len(seen) == 1


def test_diagnostics_reject_arbitrary_identifiers_and_exception_text():
    from pieces.backend.model_gateway.provider import (
        ProviderFailure,
        failure_metadata,
        response_metadata,
    )

    assert failure_metadata(ValueError("private body"))["category"] == "sdk_error"
    diagnostic = ProviderFailure(
        {"category": "private body", "status": True, "request_id": "private body"}
    ).diagnostic
    assert diagnostic == {"category": "sdk_error", "status": None, "request_id": None}
    receipt = response_metadata(
        {
            "id": "private body",
            "model": "private body",
            "usage": {"input_tokens": True, "output_tokens": -1},
        }
    )
    assert receipt["message_id"] is None and receipt["model"] is None and receipt["usage"] == {}


@pytest.mark.parametrize(
    "value,expected",
    [
        ("17", 17),
        ("0", 0),
        ("86400", 86400),
        ("86401", None),
        ("-1", None),
        ("1.5", None),
        ("private body", None),
        ("9" * 100, None),
    ],
)
def test_sdk_rate_limit_retains_only_bounded_retry_after(tmp_path, monkeypatch, value, expected):
    httpx2 = pytest.importorskip("httpx2")  # SDK-wire tests need the pinned SDK venv

    from pieces.backend.model_gateway.profile import Profile
    from pieces.backend.model_gateway.provider import AnthropicProvider, ProviderFailure

    calls = []

    def handle(request):
        calls.append(request.url.path)
        return httpx2.Response(
            429,
            headers={"request-id": "req_rate", "retry-after": value},
            json={
                "type": "error",
                "error": {"type": "rate_limit_error", "message": "private body"},
            },
        )

    key = tmp_path / "private.env"
    key.write_text("ANTHROPIC_API_KEY=sk-ant-synthetic-test-key\n")
    key.chmod(0o600)
    monkeypatch.setattr(
        "anthropic.DefaultHttpxClient",
        lambda **kwargs: httpx2.Client(
            transport=httpx2.MockTransport(handle), trust_env=False, follow_redirects=False
        ),
    )
    provider = AnthropicProvider(key, Profile())
    with pytest.raises(ProviderFailure) as caught:
        provider.generate(
            {
                "model": "claude-haiku-5-5",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "synthetic"}],
            }
        )
    diagnostic = caught.value.diagnostic
    assert diagnostic.get("retry_after_seconds") == expected
    assert ("retry_after_seconds" in diagnostic) == (expected is not None)
    assert len(calls) == 1 and "private body" not in json.dumps(diagnostic)


@pytest.mark.parametrize("status", [400, 401, 500])
def test_other_errors_cannot_claim_a_rate_limit_reset(status):
    from pieces.backend.model_gateway.provider import ProviderFailure

    diagnostic = ProviderFailure(
        {
            "category": "http_error",
            "status": status,
            "request_id": "req_test",
            "retry_after_seconds": 1,
        }
    ).diagnostic
    assert "retry_after_seconds" not in diagnostic


def test_error_reason_is_closed_and_never_copies_provider_message():
    from pieces.backend.model_gateway.provider import rejection_reason

    assert rejection_reason(
        {
            "error": {
                "type": "invalid_request_error",
                "message": "tools.3.input_schema: $ref unsupported; private body",
            }
        }
    ) == {"error_type": "invalid_request_error", "reason": "tool_schema_rejected"}
    assert (
        rejection_reason(
            {
                "type": "invalid_request_error",
                "message": "This API key is not scoped to a workspace",
            }
        )["reason"]
        == "workspace_required"
    )
    assert rejection_reason({"type": "private body", "message": "private body"}) == {}
