"""The only actual inference SDK/credential boundary in this local test gateway."""

import logging
import re
from importlib.metadata import version

from .secrets import api_key


def safe_id(value, prefix):
    return (
        value
        if isinstance(value, str) and re.fullmatch(prefix + r"[A-Za-z0-9_-]{1,160}", value)
        else None
    )


ERROR_TYPES = {
    "invalid_request_error",
    "authentication_error",
    "permission_error",
    "not_found_error",
    "rate_limit_error",
    "api_error",
    "overloaded_error",
}
ERROR_REASONS = {
    "workspace_required",
    "tool_schema_rejected",
    "thinking_rejected",
    "speed_rejected",
    "service_tier_rejected",
    "usage_limit_reached",
}


def rejection_reason(body):
    """Map provider error text to closed labels; never retain the text itself."""
    if not isinstance(body, dict):
        return {}
    error = body.get("error", body)
    if not isinstance(error, dict) or error.get("type") not in ERROR_TYPES:
        return {}
    result = {"error_type": error["type"]}
    message = error.get("message")
    if not isinstance(message, str) or len(message) > 8192:
        return result
    text = message.lower()
    for needle, reason in [
        ("not scoped to a workspace", "workspace_required"),
        ("input_schema", "tool_schema_rejected"),
        ("thinking", "thinking_rejected"),
        ("service_tier", "service_tier_rejected"),
        ("speed", "speed_rejected"),
        ("usage limits", "usage_limit_reached"),
    ]:
        if needle in text:
            result["reason"] = reason
            break
    return result


class ProviderFailure(Exception):
    """Closed fields only; one bounded rate-delay integer, never raw headers/body."""

    def __init__(self, diagnostic):
        category = diagnostic.get("category")
        self.diagnostic = {
            "category": category
            if category in {"http_error", "timeout", "connection", "sdk_error"}
            else "sdk_error",
            "status": diagnostic.get("status")
            if type(diagnostic.get("status")) is int and 400 <= diagnostic["status"] <= 599
            else None,
            "request_id": safe_id(diagnostic.get("request_id"), "req_"),
        }
        delay = diagnostic.get("retry_after_seconds")
        if (
            self.diagnostic["category"] == "http_error"
            and self.diagnostic["status"] == 429
            and type(delay) is int
            and 0 <= delay <= 86400
        ):
            self.diagnostic["retry_after_seconds"] = delay
        if diagnostic.get("error_type") in ERROR_TYPES:
            self.diagnostic["error_type"] = diagnostic["error_type"]
        if diagnostic.get("reason") in ERROR_REASONS:
            self.diagnostic["reason"] = diagnostic["reason"]
        super().__init__("PROVIDER_FAILURE")


def failure_metadata(error):
    if isinstance(error, ProviderFailure):
        return dict(error.diagnostic)
    return {"category": "sdk_error", "status": None, "request_id": None}


def response_metadata(response):
    """Receipt metadata survives later validation failure; content stays untrusted."""
    if not isinstance(response, dict):
        return {"shape": "invalid"}
    usage = response.get("usage")
    model = response.get("model")
    return {
        "message_id": safe_id(response.get("id"), "msg_"),
        "request_id": safe_id(response.get("request_id"), "req_"),
        "model": safe_id(model, "claude-"),
        "speed": usage.get("speed")
        if isinstance(usage, dict) and usage.get("speed") in {"standard", "fast"}
        else None,
        "usage": {
            key: usage[key]
            for key in (
                "input_tokens",
                "output_tokens",
                "cache_read_input_tokens",
                "cache_creation_input_tokens",
            )
            if isinstance(usage, dict)
            and type(usage.get(key)) is int
            and 0 <= usage[key] <= 1000000000
        },
    }


class AnthropicProvider:
    def __init__(self, key_path, profile):
        if version("anthropic") != profile.sdk:
            raise ValueError("SDK_VERSION_MISMATCH")
        from anthropic import Anthropic, DefaultHttpxClient

        for name in ["anthropic", "httpx2", "httpcore2"]:
            logging.getLogger(name).disabled = True
        self.client = Anthropic(
            api_key=api_key(key_path),
            base_url="https://api.anthropic.com",
            timeout=profile.timeout_seconds,
            max_retries=0,
            http_client=DefaultHttpxClient(
                trust_env=False,
                follow_redirects=False,
                timeout=profile.timeout_seconds,
            ),
        )

    def count(self, wire):
        kwargs = {
            k: v for k, v in wire.items() if k not in {"max_tokens", "service_tier", "tool_choice"}
        }
        return self._invoke(lambda: self.client.messages.count_tokens(**kwargs).input_tokens)

    def generate(self, wire):
        def generate():
            message = self.client.messages.create(**wire)
            return dict(message.model_dump(mode="json"), request_id=message._request_id)

        return self._invoke(generate)

    def _invoke(self, operation):
        from anthropic import APIConnectionError, APIStatusError, APITimeoutError

        try:
            return operation()
        except Exception as error:
            category = "sdk_error"
            if isinstance(error, APIStatusError):
                category = "http_error"
            elif isinstance(error, APITimeoutError):
                category = "timeout"
            elif isinstance(error, APIConnectionError):
                category = "connection"
            delay = None
            if category == "http_error" and error.status_code == 429:
                value = error.response.headers.get("retry-after", "")
                if re.fullmatch(r"[0-9]{1,5}", value) and int(value) <= 86400:
                    delay = int(value)
            raise ProviderFailure(
                {
                    "category": category,
                    "status": getattr(error, "status_code", None)
                    if category == "http_error"
                    else None,
                    "request_id": getattr(error, "request_id", None)
                    if category == "http_error"
                    else None,
                    "retry_after_seconds": delay,
                    **(rejection_reason(error.body) if category == "http_error" else {}),
                }
            ) from None
