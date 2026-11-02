# GoldGraft contracts

Python 3.12 / Pydantic v2 is the source of truth. Start with `registry.REGISTRY` for
all 41 independent boundary formats; nested helpers are in the containing JSON
Schema's `$defs`. The same names exist in `examples/Name.1.json` and
`schemas/Name.1.json`; TypeScript exports `NameV1` from
`ts/goldgraft-contracts.d.ts`.

```python
from goldgraft_contracts.registry import validate

payment = validate("Money/1", {"minor": 1999, "currency": "USD"})
assert payment.minor == 1999
wire_json = payment.model_dump_json()  # aliases and omitted optional fields preserved
```

`MoneyEvent` / `CMEL` and `MoneyContract` / `Contract` are Python aliases. Wire
versions are CMEL/1 and Contract/1. Each registered model has `schema_name`.

For HeraldText numbers, supply the ledger entries used as evidence:

```python
result = validate("HeraldText/1", payload, context={"ledger_entries": entries_by_hash})
```

LedgerEntry validates inline bodies. For payload_ref, the ledger must fetch the
body, check its hash, and call `validate(entry.schema_, fetched_body)` before
acceptance. Contracts do not fetch artifacts or verify signatures/hash chains.

Data packs: `base_rules.BASE_RULES`, `cmel_mapping.CMEL_MAPPING`,
`mutant_ops.MMO_12` / `MUTANT_OPERATORS`, `currencies.CURRENCY_MINOR_DIGITS` /
`PAYPAL_ZERO_DECIMAL`. Monetary minor units are strict integers. Currency data
comes from [PayPal's currency codes](https://developer.paypal.com/api/codes/currency/).
These starter examples contain synthetic shop data and placeholder attestations;
none is a claimed live payment or certificate. Scenario mock code
INSTRUMENT_DECLINED is from
https://developer.paypal.com/tools/sandbox/negative-testing/request-headers/.
The RawCapture example is browser-to-shop HTTP; no invented PayPal response shape
is used. Mapping rows reproduce design 01 §3 as data, not sample API responses.

```sh
uv sync --python 3.12
npm ci --ignore-scripts
uv run pytest -q
uv run ruff check .
uv run python scripts/check_spec_coverage.py
uv run python scripts/export_schemas.py
node scripts/gen_ts.mjs
scripts/check_generated.sh
node_modules/.bin/tsc --project contracts/tsconfig.json
```

Run commands from the repository root with Node 22. Network is needed only for
initial dependency installation. Review all wire decisions and the change
process in [FORMAT_CHANGES.md](../docs/FORMAT_CHANGES.md).
