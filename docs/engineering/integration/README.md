# Integration of current pushed work — 11 November 2026

Scope: the seven GitHub branch heads in [SOURCE_PINS.json](SOURCE_PINS.json), plus the code needed to connect their existing features. Every pushed branch is covered by main or proof-library; this integration combines both histories. Unpublished Plan5 work from the earlier broader attempt is preserved separately and excluded from this branch.

## Working flow

The existing backend API starts the published synthetic fixture pack, calls Gupta's submitted Runner, runs Singhal's actual deterministic CMEL mapper/judge, commits captures/events/verdicts into the foundation ledger, and serves those committed records from the existing graft/scenario/CMEL/proof/event routes. Restart returns the same ledger root and result without running the job again. Concurrent starts commit one run; conflicting requests are rejected; failed execution rolls back the run. Archived proof inputs are checked by hash.

The fixture pack deliberately includes negative cases. Its nine actual verdicts remain five PASS, one PASS_FIXED, two PROBLEM and one UNVERIFIED. The reference flow completes successfully with a PARTIAL evidence state; it does not turn those negatives into payment success or claim a source upgrade.

The PR6 synthetic payment recorder also implements the shared Runner entry point and reopens captures using real blob references. Its generated exchanges remain insufficient economic proof, and that result is explicit. Backend certificate verification uses the independent proof adapter and rejects the unsigned sample. Unqualified callback receivers are disabled in the reference app. The Node switch, Postman collection, disabled notification helper and evidence-document formatter are checked within their implemented scope. This is a fixture-backed reference implementation; no provider/account/deployment work is part of this scoped integration.

## Run the combined reference

```sh
uv sync --locked
npm ci
uv run python -m integration.check --state-dir .goldgraft/reference-check
uv run uvicorn integration.app:app --host 127.0.0.1 --port 8700
```

The first command below starts the seeded reference shop and returns `graft_id: synthetic-c4`. Subsequent reads come from the persisted run:

```sh
curl -X POST http://127.0.0.1:8700/shops/shop-cutover-legacy/graft -H 'Content-Type: application/json' -H 'Idempotency-Key: pushed-reference-v1' -d '{}'
curl http://127.0.0.1:8700/grafts/synthetic-c4
curl http://127.0.0.1:8700/grafts/synthetic-c4/scenarios
curl 'http://127.0.0.1:8700/grafts/synthetic-c4/cmel?scenario=HAPPY'
curl http://127.0.0.1:8700/grafts/synthetic-c4/proof
curl http://127.0.0.1:8700/grafts/synthetic-c4/events
```

Use the same start key/body to reopen the immutable reference run. The revised Postman collection targets this seeded fixture profile and checks the actual numeric `proof_strength` object. Its create-shop step is a separate metadata smoke check; it does not claim to acquire or execute a submitted repository. Template secrets stay empty and the custody smoke check uses literal synthetic values.

## Verification

```sh
GOLDGRAFT_PROOF=pieces.proof.proof:Proof GOLDGRAFT_API_APP=integration.app:create_app uv run pytest -q
uv run ruff check .
uv run python scripts/check_spec_coverage.py
scripts/check_generated.sh
npm run check:types
node pieces/switch-libs/node/run_cases.mjs
```

PHP CLI is required to execute the checkout mutation test; set `GOLDGRAFT_PHP` when it is not on PATH. CI keeps Singhal's PHP proof check and runs the composed backend, reference-flow command and Node boundary. See [fresh verification](VERIFICATION.md) for the exact results.

The published Render blueprint remains a deployment proposal, not a deployment result; the local integrated entry point is `integration.app:app`. Work not present in the pinned GitHub revisions is outside this completion scope and is not a blocker for the reference flow above.
