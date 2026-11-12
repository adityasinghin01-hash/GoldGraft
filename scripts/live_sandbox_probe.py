"""Explicitly opted-in, non-payment sandbox credential probes. Never auto-run in tests.

Sources: https://developer.paypal.com/api/rest/authentication/
https://developer.paypal.com/api/nvp-soap/get-balance-nvp/
The NVP version/endpoint match the pinned reference config.php. Auth success alone
does not establish checkout, refund, notification or business-account eligibility.
"""

import argparse
import base64
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode
from urllib.request import HTTPRedirectHandler, HTTPSHandler, ProxyHandler, Request, build_opener

ENDPOINTS = {
    "oauth": "https://api-m.sandbox.paypal.com/v1/oauth2/token",
    "nvp-balance": "https://api-3t.sandbox.paypal.com/nvp",
}
REQUIRED = {
    "oauth": ("PAYPAL_SANDBOX_CLIENT_ID", "PAYPAL_SANDBOX_CLIENT_SECRET"),
    "nvp-balance": ("PAYPAL_NVP_USER", "PAYPAL_NVP_PWD", "PAYPAL_NVP_SIGNATURE"),
}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Do not forward credentials, even to another PayPal URL.


def send(probe, headers, body):
    # Fixed HTTPS destinations, system TLS validation, no ambient proxy or retries.
    opener = build_opener(ProxyHandler({}), HTTPSHandler(), NoRedirect())
    request = Request(ENDPOINTS[probe], data=body, headers=headers, method="POST")
    try:
        with opener.open(request, timeout=20) as response:
            payload = response.read(65_537)
            if len(payload) > 65_536:
                raise ValueError("bounded_response_limit")
            return response.status, payload
    except HTTPError as error:
        status = error.code
        error.close()  # Never print/persist provider error bodies.
        return status, b""


def run_probe(probe, environ, *, live=False, authority_ref=None, transport=send):
    if probe not in REQUIRED:
        raise ValueError("unsupported_probe")
    result = {
        "document_kind": "local_sandbox_probe_not_shared_capture",
        "probe": probe,
        "environment": "sandbox",
        "status": "BLOCKED",
        "evidence_level": "NOT_RUN",
        "http_attempts": 0,
        "payment_operations": 0,
        "checkout_qualified": False,
        "checked_at": datetime.now(UTC).isoformat(),
    }
    missing = [name for name in REQUIRED[probe] if not environ.get(name, "").strip()]
    if not live:
        result["reason"] = "explicit_live_opt_in_required"
        result["missing_names"] = missing
        return result
    if environ.get("PAYPAL_ENVIRONMENT") != "sandbox":
        result["reason"] = "explicit_sandbox_environment_required"
        return result
    # A local operator's audit reference, not a fabricated service authority/Start record.
    if not authority_ref or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}", authority_ref):
        result["reason"] = "local_authority_reference_required"
        return result
    if missing:
        result.update(reason="credentials_not_configured", missing_names=missing)
        return result
    invalid = [
        name for name in REQUIRED[probe] if any(ord(c) < 32 or ord(c) == 127 for c in environ[name])
    ]
    if invalid:
        result.update(reason="invalid_local_credential_format", invalid_names=invalid)
        return result
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    if probe == "oauth":
        identity = environ[REQUIRED[probe][0]] + ":" + environ[REQUIRED[probe][1]]
        headers["Authorization"] = "Basic " + base64.b64encode(identity.encode()).decode("ascii")
        body = b"grant_type=client_credentials"
    else:
        body = urlencode(
            {
                "METHOD": "GetBalance",
                "VERSION": "204.0",
                "RETURNALLCURRENCIES": "0",
                "USER": environ["PAYPAL_NVP_USER"],
                "PWD": environ["PAYPAL_NVP_PWD"],
                "SIGNATURE": environ["PAYPAL_NVP_SIGNATURE"],
            }
        ).encode("ascii")
    result.update(
        evidence_level=("SANDBOX_CREDENTIAL_PROBE" if transport is send else "SYNTHETIC_TRANSPORT"),
        http_attempts=1,
    )
    try:
        status, payload = transport(probe, headers, body)
        result["http_status"] = status
        if status in (401, 403):
            result.update(status="FAIL", reason="authentication_or_permission_rejected")
        elif status != 200:
            result.update(status="UNVERIFIED", reason="provider_response_not_qualified")
        else:
            if len(payload) > 65_536:
                raise ValueError("bounded_response_limit")
            if probe == "oauth":
                data = json.loads(payload)
                valid = (
                    isinstance(data, dict)
                    and isinstance(data.get("access_token"), str)
                    and bool(data["access_token"])
                    and data.get("token_type", "").lower() == "bearer"
                    and type(data.get("expires_in")) is int
                    and data["expires_in"] > 0
                )
            else:
                data = parse_qs(payload.decode("utf-8"), strict_parsing=True, max_num_fields=100)
                valid = data.get("ACK") in (["Success"], ["SuccessWithWarning"])
            result.update(
                status="PASS" if valid else "UNVERIFIED",
                reason="credential_probe_only" if valid else "unexpected_provider_payload",
            )
    except (OSError, URLError, ValueError, TypeError, AttributeError):
        # Exception strings/provider bodies can contain credentials and are never logged.
        result.update(status="UNVERIFIED", reason="transport_or_payload_unverified")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", choices=sorted(REQUIRED), required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--authority-ref", help="local operator approval reference; no secrets")
    parser.add_argument(
        "--config", type=Path, help="explicit local sandbox JSON file; never tracked"
    )
    args = parser.parse_args()
    environment = dict(os.environ)
    if args.config:
        from sandbox_config import load_config

        try:
            environment.update(load_config(args.config))
        except (OSError, ValueError):
            print(json.dumps({"status": "BLOCKED", "reason": "local_sandbox_config_invalid"}))
            return 2
    result = run_probe(args.probe, environment, live=args.live, authority_ref=args.authority_ref)
    print(json.dumps(result, indent=2))
    return {"PASS": 0, "FAIL": 1}.get(result["status"], 2)


if __name__ == "__main__":
    raise SystemExit(main())
