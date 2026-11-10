# Reply to Vijay: inputs needed for the fourteen real scenarios

Checked 10 November 2026 against the current remote repository, not only the older local checkout. This answers `TEAM_INPUTS_NEEDED.md` supplied by Vijay. His reported local PHP/Playwright and credential-probe passes are retained as **reported, not independently rerun here**. No credentials are requested or published.

## Short answer to send

Vijay, your checklist is correct. Please keep the fourteen scenarios and existing scope; do not recreate the backend, broker, recorder or proof. Gupta's contribution is now on main at `317f80b207d7ab1a7eb3f4f815e9f5da35301b22` after PRs4/5. However, inspecting that code shows an in-memory credential store and a runner reading saved fixture captures; those are not yet the real sandbox broker/isolated recorder you need. Its callback route checks header presence/deduplication, not the full qualified IPN/webhook verification and durable receipt path. Therefore your real-payment run is still held on those integrations, not on writing more scenarios.

Singh's new SI01 formats remain proposed: no approved implemented v2/bootstrap revision is available at this inspection. Existing `JobSpec/1`, `JobResult/1`, `RawCapture/1`, `CMEL/1`, `Contract/1`, `TargetPlan/1` and `Verdict/1` are available for compatible offline boundary work only. Singhal's actual proof code is on the still-open `proof-library` PR1 at `e4b2594f5079ba7cac92b5a3a6dcdb447f02cdd0`; inspect its handoff and adapter, but do not automatically merge or claim that branch proves live integration.

Gupta needs to provide a pinned broker/runner/callback handoff with the actual startup and one working boundary command; Singh needs to publish the accepted contract/export/example revision; Singhal needs to confirm the compatible proof invocation. You can continue independent fixture/scenario preparation and offline checks meanwhile. Credentials remain in the approved private mechanism; no production access, live money or unapproved remote dispatch is requested.

## Exact current sources

| Component | Inspected revision and location | Actual readiness at inspection |
|---|---|---|
| Shared repository/main | [main pin](https://github.com/adityasinghin01-hash/GoldGraft/tree/317f80b207d7ab1a7eb3f4f815e9f5da35301b22) | Current merged backend/switch contributions present; no new SI01 implementation inferred |
| Gupta backend | [app.py](https://github.com/adityasinghin01-hash/GoldGraft/blob/317f80b207d7ab1a7eb3f4f815e9f5da35301b22/pieces/backend/app.py), [custody_broker.py](https://github.com/adityasinghin01-hash/GoldGraft/blob/317f80b207d7ab1a7eb3f4f815e9f5da35301b22/pieces/backend/custody_broker.py), [lifecycle.py](https://github.com/adityasinghin01-hash/GoldGraft/blob/317f80b207d7ab1a7eb3f4f815e9f5da35301b22/pieces/backend/lifecycle.py) | Existing code to reuse/inspect; in-memory `_vault` and `doppler://` naming are not a verified external secret-provider integration or sandbox payment client |
| Gupta runner/recorder | [container_runner.py](https://github.com/adityasinghin01-hash/GoldGraft/blob/317f80b207d7ab1a7eb3f4f815e9f5da35301b22/pieces/runner/container_runner.py) | `run_job` resolves `fixtures://proof/legacy-php-shop/raw/` captures and returns a fixed workflow/SHA identity; no actual isolated process/payment execution demonstrated by this implementation |
| Existing offline boundary examples | [test_backend_runner.py](https://github.com/adityasinghin01-hash/GoldGraft/blob/317f80b207d7ab1a7eb3f4f815e9f5da35301b22/plugtests/test_backend_runner.py) | Inspection examples; fixture success cannot unblock real payment/isolation gates; tests not rerun for this answer |
| Callback endpoint | `/pp/webhook/{graft_id}` in the pinned app | Header-presence and in-memory delivery deduplication are present; qualified signature validation, durable UNVERIFIED receipt, IPN postback and app/environment/business binding still need the actual mechanism/evidence |
| SI01 current types | [registry.py](https://github.com/adityasinghin01-hash/GoldGraft/blob/317f80b207d7ab1a7eb3f4f815e9f5da35301b22/contracts/src/goldgraft_contracts/registry.py), [runner.py](https://github.com/adityasinghin01-hash/GoldGraft/blob/317f80b207d7ab1a7eb3f4f815e9f5da35301b22/contracts/src/goldgraft_contracts/runner.py), [interfaces.py](https://github.com/adityasinghin01-hash/GoldGraft/blob/317f80b207d7ab1a7eb3f4f815e9f5da35301b22/contracts/src/goldgraft_contracts/interfaces.py) | Existing `/1` shapes remain actual wire; new connection/lifecycle/task/subject records have no implemented approved SI01 revision at this pin |
| Singhal proof | [PR1](https://github.com/adityasinghin01-hash/GoldGraft/pull/1), [proof.py pin](https://github.com/adityasinghin01-hash/GoldGraft/blob/e4b2594f5079ba7cac92b5a3a6dcdb447f02cdd0/pieces/proof/proof.py), [proof handoff](https://github.com/adityasinghin01-hash/GoldGraft/blob/e4b2594f5079ba7cac92b5a3a6dcdb447f02cdd0/docs/PROOF_HANDOFF.md) | Real deterministic mapper/judge source exists on the unmerged branch; its own handoff separates offline results from open live signing/merchant evidence and SI01 binding |

These are dated source-inspection findings, not a review of every teammate's local/unpushed work and not a claim that no newer qualified implementation exists elsewhere. If one exists, its owner should provide the exact repository, branch, commit, handoff and actual result.

## Answer to each requested input

1. **Code location:** use the pinned main and files above for first inspection. Preserve correct existing code; do not assume filenames/docstrings claiming GU01-GU05 or isolation mean the reviewed protocols are implemented. Gupta supplies any newer qualified revision and readiness disposition. No current working command for all fourteen real scenarios is established here.
2. **Payment broker:** Gupta must hand over implemented supported NVP/REST operations, a public typed boundary and actual sandbox account/environment/run binding, credential-reference configuration, request limits, idempotency and unknown-effect reconciliation. The inspected custody class is not that payment broker. A known absent secret must deny, not silently become an empty usable credential set.
3. **Runner and recorder:** existing `Runner.run_job(JobSpec)` and `fetch_capture(ref)` are the compatible interface vocabulary; the current ContainerRunner supplies fixture observations. Gupta must provide actual isolation/profile/template/source/image identities, synthetic OLD/OLD_TWIN/NEW state setup, authenticated collection, termination and artifact-redaction handling. Do not copy the fixed workflow/SHA into local-run evidence; if the current shape cannot honestly represent the run, request a versioned SI01 change before claiming conformance.
4. **Callback gateway:** Gupta owns ingress/receipt/validation/observability; Vijay owns domain expectations and scenarios. Require reachable qualified sandbox ingress, original listener/app/environment binding, durable receipt before acknowledgement where required, appropriate IPN/webhook verification, business checks and redacted delivery evidence. The offline Windows lab and a header-only route do not supply this.
5. **Contracts/proof:** Singh supplies an accepted SI01 revision with generated exports/examples/fakes/compatibility results for new formats. Until then, retain current types unchanged for their limited compatible uses. Singhal confirms the actual mapper/judge invocation at a named proof revision and expected inputs. No piece imports another piece; compose through shared contracts or an approved external adapter boundary.

## Inspection-only setup references

The backend exposes `pieces.backend.app:app`. A local inspection command from an isolated checkout of the pinned main is:

```sh
uv sync --locked
uv run --locked uvicorn pieces.backend.app:app --host 127.0.0.1 --port 8000
```

This is an entry-point reference, not a command executed or a live integration verified in this publication. Keep legacy connect/write routes away from real credentials. Dependency installation remains subject to the executing environment's permissions.

The proof branch's own documented offline checks are:

```sh
uv run --locked python -m scripts.demo_proof
GOLDGRAFT_PROOF=pieces.proof.proof:Proof uv run --locked pytest -q 'plugtests/test_proof.py'
```

The exact existing proof tests should be taken from the pinned `docs/PROOF_HANDOFF.md`, which uses `plugtests/test_proof*.py` and additionally requires a qualified PHP CLI for executable mutations. Confirm the selected test path in the checked-out revision before running; the commands here are documentation references, not newly observed passing results. No live signing command or PayPal payment is authorised by this reply.

## Minimum real-run handoff to unblock Vijay

Gupta, Singh and Singhal should each supply: owner; repository/branch/exact commit; interface/schema version; setup prerequisites; startup command; one safe validated example; exact boundary-check command and actual result; permitted sandbox operations/limits; configuration variable names or opaque secret refs only; evidence/artifact lookup and redaction; cancellation/unknown reconciliation; open gates.

Then perform the separately authorised boundary qualification before Vijay dispatches real sandbox scenarios. Do not call fourteen fixtures fourteen real payment scenarios, broaden scope, work around an unknown effect, expose credentials or make Vijay rebuild the missing counterpart.
