"""Behavior at boundaries; no network, service clients, or LLM calls."""

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
from goldgraft_contracts.agents import HeraldText
from goldgraft_contracts.base_rules import BASE_RULES
from goldgraft_contracts.cmel_mapping import CMEL_MAPPING
from goldgraft_contracts.currencies import CURRENCY_MINOR_DIGITS, PAYPAL_ZERO_DECIMAL
from goldgraft_contracts.money import Kind, Money, MoneyEvent, Source, StatusNorm
from goldgraft_contracts.mutant_ops import MMO_12
from goldgraft_contracts.registry import REGISTRY, validate
from goldgraft_contracts.runner import RawExchange
from goldgraft_contracts.survey import Location, Step
from hypothesis import given
from hypothesis import strategies as st
from jsonschema import Draft202012Validator
from pydantic import TypeAdapter, ValidationError

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "contracts/examples"


def example(name):
    return json.loads((EXAMPLES / f"{name}.1.json").read_text())


@pytest.mark.parametrize("name", sorted(REGISTRY))
def test_example_schema_and_roundtrip(name):
    payload = example(name.split("/")[0])
    schema = REGISTRY[name].model_json_schema(by_alias=True)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)
    result = validate(name, payload)
    validate(name, json.loads(result.model_dump_json()))


@pytest.mark.parametrize("minor", [1.0, 1.5, True, "100", None])
def test_money_rejects_non_integer(minor):
    with pytest.raises(ValidationError):
        Money(minor=minor, currency="USD")


@pytest.mark.parametrize("currency", ["usd", "US", "USDD", "ZZZ", "INR", 1])
def test_money_rejects_currency(currency):
    with pytest.raises(ValidationError):
        Money(minor=1, currency=currency)


@pytest.mark.parametrize("code", sorted(CURRENCY_MINOR_DIGITS))
def test_currency_digits(code):
    value = Money(minor=1999, currency=code)
    assert value.minor == 1999
    assert CURRENCY_MINOR_DIGITS[code] == (0 if code in PAYPAL_ZERO_DECIMAL else 2)
    assert Money.model_validate_json(value.model_dump_json()) == value


def test_money_float_in_event_rejected():
    payload = example("CMEL")
    payload["money"]["minor"] = 19.99
    with pytest.raises(ValidationError):
        validate("CMEL/1", payload)


@pytest.mark.parametrize(
    "name,field",
    [
        ("CMEL", "variant"),
        ("Scenario", "family"),
        ("Mutant", "op"),
        ("Verdict", "grade"),
        ("JobSpec", "kind"),
        ("GuardEvent", "event"),
    ],
)
def test_wrong_enums(name, field):
    payload = example(name)
    payload[field] = "not-a-real-enum"
    with pytest.raises(ValidationError):
        validate(f"{name}/1", payload)


@pytest.mark.parametrize("pct", [2, -1, 101, 1.0, True, "10"])
def test_stage_percent(pct):
    payload = example("SwitchConfig")
    payload["stage_pct"] = pct
    with pytest.raises(ValidationError):
        validate("SwitchConfig/1", payload)


def test_ledger_payload_validation_and_size():
    payload = example("LedgerEntry")
    payload["schema"] = "Money/1"
    payload["payload"] = {"minor": 1.0, "currency": "USD"}
    with pytest.raises(ValidationError):
        validate("LedgerEntry/1", payload)
    payload["schema"] = "RootMap/1"
    # Non-ASCII characters must count as UTF-8 bytes, not code points.
    payload["payload"] = {"extra": "€" * 6000}
    with pytest.raises(ValidationError, match="16384"):
        validate("LedgerEntry/1", payload)


def test_ledger_exact_size_limit():
    payload = example("LedgerEntry")
    # Use a valid large RootMap so byte checking and registry validation both run.
    base = payload["payload"]
    base["stack"]["framework"] = ""
    size = len(json.dumps(base, ensure_ascii=False, separators=(",", ":")).encode())
    base["stack"]["framework"] = "a" * (16384 - size)
    validate("LedgerEntry/1", payload)
    base["stack"]["framework"] += "a"
    with pytest.raises(ValidationError, match="16384"):
        validate("LedgerEntry/1", payload)


def test_ledger_reference_and_xor():
    payload = example("LedgerEntry")
    payload["payload_ref"] = "r2://artifacts/rootmap"
    with pytest.raises(ValidationError, match="exactly one"):
        validate("LedgerEntry/1", payload)
    del payload["payload"]
    result = validate("LedgerEntry/1", payload)
    validate("LedgerEntry/1", json.loads(result.model_dump_json()))
    del payload["payload_ref"]
    with pytest.raises(ValidationError, match="exactly one"):
        validate("LedgerEntry/1", payload)


@pytest.mark.parametrize(
    "value",
    [
        {"file": "a.php", "line": 1},
        {"url": "https://example.test", "selector": "#pay"},
        {"tcode": "T0006"},
    ],
)
def test_location_variants(value):
    TypeAdapter(Location).validate_python(value)
    with pytest.raises(ValidationError):
        TypeAdapter(Location).validate_python({**value, "extra": 1})


@pytest.mark.parametrize(
    "value",
    [
        {"driver_step": "pay"},
        {"api_step": "capture"},
        {"paypal_mock_response_code": "INSTRUMENT_DECLINED"},
    ],
)
def test_step_variants(value):
    TypeAdapter(Step).validate_python(value)
    with pytest.raises(ValidationError):
        TypeAdapter(Step).validate_python({**value, "extra": 1})


def test_ambiguous_unions_rejected():
    for adapter, payload in [
        (TypeAdapter(Location), {"file": "a", "line": 1, "tcode": "T0006"}),
        (TypeAdapter(Step), {"driver_step": "a", "api_step": "b"}),
    ]:
        with pytest.raises(ValidationError):
            adapter.validate_python(payload)


@pytest.mark.parametrize(
    "header",
    [
        "Authorization",
        "authorization",
        "COOKIE",
        "Set-Cookie",
        "PayPal-Auth-Assertion",
        "X-Api-Key",
        "X-Custom-Secret",
    ],
)
def test_header_redaction(header):
    exchange = example("RawCapture")["exchanges"][0]
    exchange["headers"] = {header: "synthetic-not-a-secret"}
    with pytest.raises(ValidationError, match="REDACTED"):
        RawExchange.model_validate(exchange)
    exchange["headers"][header] = "[REDACTED]"
    RawExchange.model_validate(exchange)


def test_raw_body_and_db():
    exchange = example("RawCapture")["exchanges"][0]
    exchange["body_json"] = {}
    with pytest.raises(ValidationError, match="mutually exclusive"):
        RawExchange.model_validate(exchange)
    del exchange["body_text"]
    RawExchange.model_validate(exchange)
    exchange["direction"] = "SHOP_DB_WRITE"
    with pytest.raises(ValidationError, match="requires db_change"):
        RawExchange.model_validate(exchange)
    exchange["db_change"] = {
        "table": "orders",
        "key": {"id": "order-1"},
        "before": None,
        "after": {"status": "paid"},
    }
    RawExchange.model_validate(exchange)


def test_heal_transitions():
    payload = example("HealDecision")
    payload["to_stage_pct"] = 100
    with pytest.raises(ValidationError, match="next stage"):
        validate("HealDecision/1", payload)
    payload["action"] = "HOLD"
    with pytest.raises(ValidationError, match="preserve"):
        validate("HealDecision/1", payload)
    payload.update(action="CUTBACK", to_stage_pct=0)
    validate("HealDecision/1", payload)


def test_herald_numbers_need_ledger_evidence():
    payload = example("HeraldText")
    payload["numbers_used"] = [
        {"entry_hash": "0" * 64, "json_pointer": "/payload/count", "value": 12}
    ]
    with pytest.raises(ValidationError, match="ledger_entries"):
        HeraldText.model_validate(payload)
    context = {"ledger_entries": {"0" * 64: {"payload": {"count": 12}}}}
    validate("HeraldText/1", payload, context=context)
    payload["numbers_used"][0]["value"] = 13
    with pytest.raises(ValidationError, match="copied"):
        validate("HeraldText/1", payload, context=context)


def test_data_tables():
    assert [r.id for r in BASE_RULES] == [f"R{i:02d}" for i in range(1, 17)]
    assert {r.id for r in BASE_RULES if r.severity == "CRITICAL"} == {
        "R01",
        "R02",
        "R03",
        "R04",
        "R05",
        "R06",
        "R08",
        "R11",
        "R12",
    }
    assert [r.op for r in MMO_12] == [f"M{i}" for i in range(1, 13)]
    assert len(CMEL_MAPPING) == 21
    assert {r.cmel_kind for r in CMEL_MAPPING} >= {Kind.INTENT, Kind.CAPTURE, Kind.REFUND}
    assert all(r.rules_broken for r in MMO_12)


@given(st.integers(), st.sampled_from(sorted(CURRENCY_MINOR_DIGITS)))
def test_money_json_roundtrip(minor, currency):
    payload = {"minor": minor, "currency": currency}
    wire = json.dumps(payload)
    result = Money.model_validate_json(wire)
    assert json.loads(result.model_dump_json()) == payload


@given(
    minor=st.integers(),
    currency=st.sampled_from(sorted(CURRENCY_MINOR_DIGITS)),
    variant=st.sampled_from(["OLD", "OLD_TWIN", "NEW"]),
    source=st.sampled_from(list(Source)),
    kind=st.sampled_from(list(Kind)),
    status=st.one_of(st.none(), st.sampled_from(list(StatusNorm))),
    seq=st.integers(min_value=0),
    time=st.integers(min_value=0),
)
def test_event_json_roundtrip(minor, currency, variant, source, kind, status, seq, time):
    payload = example("CMEL")
    payload.update(
        money={"minor": minor, "currency": currency},
        variant=variant,
        source=source,
        kind=kind,
        status_norm=status,
        seq=seq,
        t_ms=time,
        items_hash=None,
    )
    result = MoneyEvent.model_validate_json(json.dumps(payload))
    assert json.loads(result.model_dump_json()) == payload


def load_coverage():
    spec = importlib.util.spec_from_file_location(
        "coverage_check", ROOT / "scripts/check_spec_coverage.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_spec_coverage():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_spec_coverage.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "old,new",
    [
        ("shop_id, stack", "missing_shop_id, stack"),
        ("legacy_token?", "missing_token?"),
        ("WPS|EC_NVP", "MISSING_FAMILY|EC_NVP"),
        ("[code, runtime, site, account]", "[code, runtime, missing_lens, account]"),
    ],
)
def test_coverage_detects_missing_fields_and_enums(old, new):
    text = (ROOT / "docs/design/01_DATA.md").read_text()
    assert old in text
    errors, _, _ = load_coverage().check_coverage(text.replace(old, new))
    assert errors


def test_nested_unknown_fields_rejected():
    payload = copy.deepcopy(example("RootMap"))
    payload["touchpoints"][0]["target"]["extra"] = True
    with pytest.raises(ValidationError):
        validate("RootMap/1", payload)


@pytest.mark.parametrize("name", sorted(REGISTRY))
def test_exported_schema_matches_python(name):
    schema = json.loads((ROOT / "contracts/schemas" / f"{name.replace('/', '.')}.json").read_text())
    assert schema.pop("$schema") == "https://json-schema.org/draft/2020-12/schema"
    assert schema.pop("$id").endswith(f"/{name.replace('/', '.')}.json")
    schema["title"] = REGISTRY[name].__name__
    assert schema == REGISTRY[name].model_json_schema(by_alias=True, mode="validation")


def test_schema_registry_inventory():
    expected = {f"{name.replace('/', '.')}.json" for name in REGISTRY}
    assert {p.name for p in EXAMPLES.glob("*.json")} == expected
    assert {p.name for p in (ROOT / "contracts/schemas").glob("*.json")} == expected
    assert all(model.schema_name == name for name, model in REGISTRY.items())


def test_schema_xor_and_missing_fields():
    ledger = example("LedgerEntry")
    ledger["payload_ref"] = "r2://map"
    schema = REGISTRY["LedgerEntry/1"].model_json_schema(by_alias=True)
    assert not Draft202012Validator(schema).is_valid(ledger)
    assert not Draft202012Validator(schema).is_valid({"payload_ref": "r2://map"})
    raw = example("RawCapture")
    raw["exchanges"][0]["body_json"] = {}
    schema = REGISTRY["RawCapture/1"].model_json_schema(by_alias=True)
    assert not Draft202012Validator(schema).is_valid(raw)


def test_shop_start_and_env_names():
    payload = example("ShopPack")
    payload["env_needed"] = ["PAYPAL_CLIENT_ID=not-a-value"]
    with pytest.raises(ValidationError):
        validate("ShopPack/1", payload)
    payload["env_needed"] = ["PAYPAL_CLIENT_ID"]
    payload["start"]["command"] = "run-shop"
    with pytest.raises(ValidationError):
        validate("ShopPack/1", payload)
    payload["start"] = {"command": "run-shop"}
    validate("ShopPack/1", payload)


def test_secret_values_are_not_references():
    payload = example("JobSpec")
    payload["secrets_ref"] = "synthetic-inline-value"
    with pytest.raises(ValidationError):
        validate("JobSpec/1", payload)


def test_nested_herald_context_is_preserved_in_ledger():
    herald = example("HeraldText")
    herald["numbers_used"] = [
        {"entry_hash": "0" * 64, "json_pointer": "/payload/count", "value": 12}
    ]
    payload = example("LedgerEntry")
    payload.update(schema="HeraldText/1", payload=herald)
    with pytest.raises(ValidationError, match="ledger_entries"):
        validate("LedgerEntry/1", payload)
    validate(
        "LedgerEntry/1", payload, context={"ledger_entries": {"0" * 64: {"payload": {"count": 12}}}}
    )


def test_rule_and_mutant_data_match_design_tables():
    text = (ROOT / "docs/design/01_DATA.md").read_text()
    rules = {r.id: r for r in BASE_RULES}
    operators = {r.op: r for r in MMO_12}
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        if cells[0] in rules:
            assert rules[cells[0]].plain_text == cells[1]
            assert rules[cells[0]].predicate_idea == cells[2]
        if cells[0] in operators:
            assert operators[cells[0]].fault == cells[1].replace("`", "")
            assert operators[cells[0]].rules_broken == cells[2].split("/")


@given(
    st.fixed_dictionaries(
        {},
        optional={
            key: st.one_of(st.none(), st.text(min_size=1, max_size=30))
            for key in (
                "legacy_token",
                "txn_id",
                "order_id",
                "capture_id",
                "refund_id",
                "profile_id",
                "debug_id",
            )
        },
    ),
    st.booleans(),
)
def test_event_optional_fields_roundtrip(pp, include_money):
    payload = example("CMEL")
    payload["pp"] = pp
    if not include_money:
        del payload["money"]
    result = MoneyEvent.model_validate_json(json.dumps(payload))
    assert json.loads(result.model_dump_json()) == payload
