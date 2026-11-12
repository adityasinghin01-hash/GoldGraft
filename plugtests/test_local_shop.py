"""Pure checks of the opt-in local PHP harness; no sockets or providers."""

import pytest

from integration import local_shop


def test_oauth_form_body_is_not_parsed_as_json():
    fields, body = local_shop.decode_request(
        "/v1/oauth2/token", "application/x-www-form-urlencoded", "grant_type=client_credentials"
    )
    assert fields == {"grant_type": "client_credentials"}
    assert body == {}
    assert local_shop.decode_request(
        "/v2/checkout/orders", "application/json", '{"intent":"CAPTURE"}'
    ) == ({}, {"intent": "CAPTURE"})


@pytest.mark.parametrize("value,expected", [("25.00", 2500), ("0.29", 29), ("12.50", 1250)])
def test_amount_conversion_has_exact_integer_minor_units(value, expected):
    assert local_shop.minor(value) == expected


@pytest.mark.parametrize("value", ["NaN", "Infinity", "0.001"])
def test_amount_conversion_refuses_unrepresentable_values(value):
    with pytest.raises(ValueError):
        local_shop.minor(value)


def test_candidate_path_escape_is_refused_before_writing(tmp_path):
    with pytest.raises(ValueError, match="candidate path"):
        local_shop.validate_candidate({"../outside.php": "<?php echo 1;"})
    assert not (tmp_path / "outside.php").exists()


def test_sample_runner_resolves_php_before_using_its_minimal_environment(tmp_path, monkeypatch):
    # Shop's child environment deliberately omits the user's PATH and credentials.
    executable = tmp_path / "php"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    assert local_shop.resolve_php("php") == executable.resolve()


def test_extra_parity_observes_actual_order_listing_and_rejects_missing_response():
    from goldgraft_contracts.registry import validate

    raw = {
        "graft_id": "g",
        "run_id": "r",
        "variant": "NEW",
        "scenario_id": "PARITY_EXTRA",
        "exchanges": [
            {
                "seq": 0,
                "t_ms": 0,
                "direction": "BROWSER_TO_SHOP",
                "method": "GET",
                "url": "http://127.0.0.1:1234/api/orders.php",
                "headers": {},
                "status": 200,
                "body_json": [{"token": "noise", "amount": "25.00", "status": "PAID"}],
            }
        ],
    }
    capture = validate("RawCapture/1", raw)
    assert local_shop.order_listing(capture) == [(2500, "PAID")]
    capture.exchanges[0].status = 500
    with pytest.raises(ValueError, match="order listing"):
        local_shop.order_listing(capture)
