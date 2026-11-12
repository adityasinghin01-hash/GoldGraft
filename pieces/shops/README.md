# Shop recipes — Vijay's piece (VJ01–VJ05)

A shop recipe is one folder, `pieces/shops/<shop_id>/`. When it passes the
conformance check it plugs into the connected run with no other code change.

| File | Format | What it is |
|---|---|---|
| `goldgraft-shop.yaml` | `ShopPack/1` | Shop identity, source pin, start command, supported scenarios |
| `scenarios/<ID>.json` | `Scenario/1` | One file per id in `scenarios_supported`; `rules` names the money rules it exercises |
| `contract.json` | `Contract/1` | The normative money rules |
| `target_plan.json` | `TargetPlan/1` | The reference upgrade plan |
| `source/` + `LICENSE`/`NOTICE` | — | The shop source the recipe runs, with its licence |
| `recipe.py` | Python, imports `contracts/` only | `execute(run_dir, output, *, php)` and, when ready, `state_recipe`, `finalisation_recipe`, `exit_check_recipe` |

`execute` runs OLD, OLD_TWIN and NEW for every scenario (NEW uses the agents'
candidate in `run_dir/CHANGES.json`) and writes into `output/`:

- `<ID>.<VARIANT>.json` — one `RawCapture/1` per pair, `graft_id = run_dir.name`,
  one shared `run_id` that starts with `run_dir.name`;
- `REPORT.json` — `run_id`, `capture_sha256` for every file,
  `normative_contract_sha256` of `contract.json`, and the three qualification
  flags set to `false`. Qualification is never self-declared; it comes from
  separately verified evidence (PayPal sandbox, isolation, exit).

Optional: `post_judge(scenario, captures, verdict, report)` for a shop-specific
parity check. Missing later recipes are reported as holds, never as success.

## Check and plug in

```sh
.venv/bin/python -m integration.shop_socket --agent-run <agent run folder> --workdir <new folder>
.venv/bin/python -m integration.connected_run <agent run folder> --state-dir <new folder>
```

`plugtests/test_shop_socket.py` shows a complete conforming folder and the
failures a broken one gets (self-declared qualification, missing recording,
missing licence, unknown rule). Until a recipe lands here, the vendored MIT
reference shop (`fixtures/shops/legacy-php-shop`) is wired through the same
socket and labelled `reference_stand_in`.
