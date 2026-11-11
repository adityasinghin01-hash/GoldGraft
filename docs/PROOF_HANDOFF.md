# GoldGraft Proof + maths handoff

The proof implementation is in `pieces/proof/`. The existing contracts and wire
formats still apply. Ordinary verification is offline. Checkout fixtures and
PayPal replies are synthetic. The PHP mutation run executes code and measures
outcomes against local storage and HTTP stand-ins.

## Reproduce the checks

From the repo root with Python 3.12, uv, and PHP CLI installed:

```sh
uv sync --locked
uv run --locked python -m scripts.demo_proof
export GOLDGRAFT_PROOF=pieces.proof.proof:Proof
export GOLDGRAFT_PHP="$(command -v php)"
test -n "$GOLDGRAFT_PHP"
uv run --locked pytest -q plugtests/test_proof*.py
uv run --locked pytest -q
uv run --locked ruff check .
uv run --locked python scripts/check_spec_coverage.py
```

GitHub CI additionally checks generated schemas and TypeScript and starts the
legacy shop in Docker.

## Demonstration checklist

| Demonstration | Command | Observed result |
|---|---|---|
| CMEL and verdicts | `uv run --locked python -m scripts.demo_proof` | HAPPY PASS, REFUND_TWICE PASS_FIXED with OLD/R11, PENDING PROBLEM with NEW/R01 and R07, NOTIFY_DUP UNVERIFIED, explicit N/A |
| Noise, deltas and lifecycle | Demo above, plus `uv run --locked pytest -q plugtests/test_proof_rules.py` | HAPPY masks volatile IDs and accepts declared read fan-out. Regression checks cover duplicate notifications, changed receipts, unrelated or failed ledger reads, repeat-old drift, pending resolution, timeout, restart and legacy refund routing |
| Executed checkout mutations | `uv run --locked pytest -q plugtests/test_proof_mutations.py` | Original passed all scenarios. All 12 patched checkouts caught. 12/12, zero exclusions or survivors. Linked scenarios drive rule coverage and incomplete evidence is rejected |
| Fixture-only mutation comparison | `uv run --locked python -m scripts.demo_proof` | 4/11 after reviewed exclusion M03. Seven fixture survivors M01, M04, M05, M09, M10, M11 and M12. These are supplied answer-key outcomes |
| Go-live maths | Demo above, plus `uv run --locked pytest -q plugtests/test_proof_posterior.py` | Healthy STEP_UP to 50%, thin HOLD at 10%, hard stops and strong regression CUTBACK to 0%. Slight regression HOLD. Duplicate events leave decisions unchanged. A healthy 100% stage stays at 100%. Exact arithmetic matches 900 reference comparisons |
| Recipe confidence and metrics | `uv run --locked python -m scripts.demo_proof` | 3 passes and 2 fails gives 0.571429. Negative counts rejected. Fleet aggregation and time/cost collection are outside the proof START checklist. Certificate time/cost fields are supplied by the runner |
| Certificate and evidence | `uv run --locked pytest -q plugtests/test_proof_certificate.py` | 12 passed. Eligible ledger-backed input reaches the signer. Failed gates stop signing. Exact payload, tampering, workflow pins, Rekor reference, PayPal amount mismatch, ledger tampering and missing evidence are tested with offline substitutes |

The fixture hash demo returns `hash=True, verified=False` for the original
synthetic certificate, and `hash=False, verified=False` for the edited one.
The certificate fixture has no authentic signature.

## Adapter handoff for the reference shop

Status as of 11 November 2026: **ready for fixture replay**. PR #1 is merged
into `main` at [`4f9bf0c`](https://github.com/adityasinghin01-hash/GoldGraft/commit/4f9bf0c7f88dd811ba58cba856ff91ae226db172).
Use `pieces.proof.proof:Proof` from that revision. The adapter accepts
`RawCapture/1` for OLD, OLD_TWIN and NEW, maps each capture to `CMEL/1`,
and judges the three streams with `Contract/1` and `TargetPlan/1`. The
composition in `integration.offline.fixture_proof` checks the recording job,
graft, scenario and variant before calling the mapper and judge. It supplies
the OLD and NEW captures for payment-evidence checks and returns `Verdict/1`.

From that checkout with Python 3.12 and uv, use a fresh local state directory:

```sh
uv sync --locked
uv run --locked python -m integration.check --state-dir .goldgraft/proof-handoff
```

The [main CI run](https://github.com/adityasinghin01-hash/GoldGraft/actions/runs/42979872863)
passed this boundary check and the PHP mutation step. The
[recorded results](engineering/integration/VERIFICATION.md) show nine
scenarios, 208 CMEL events and 272 ledger entries. Evidence remains partial:
five PASS, one PASS_FIXED, two PROBLEM and one UNVERIFIED. Restart reads the
same result without rerunning the job. The integration app exposes the stored
scenario, CMEL and proof records via the routes in the
[reference flow](engineering/integration/README.md#run-the-combined-reference).

**Real sandbox runs are on hold.** Gupta owns the qualified broker,
isolated runner and authenticated callback path. Vijay owns the actual
reference-shop recordings and payment witnesses. Singh owns the accepted
SI01 schemas and integration. Until those inputs are available, the fixture
adapter is the supported invocation. The verifier rejects the unsigned
sample certificate.

**Sponsor evidence.** The published Elastic path formats diagnostic
documents. Exact-subject retrieval with access checks and an approved
redacted index still needs a qualified Elastic profile and Gupta's
ingestion/access-control integration. The Postman assertions have an
offline replay result. The private/public projection negatives depend on
the accepted SI01 projection schema. Search and UI projections consume
proof results without issuing verdicts.

## Lifecycle review and demo signing

`pieces.proof.lifecycle_evidence.review_lifecycle` consumes an independently
authenticated set of observations and a trusted, current set of required checks.
The baseline and candidate requirements bind case, run, generation, fence, scope,
package, image, config, runtime and origin. Missing, duplicate, mismatched,
unverified or fixture-only critical observations result in HOLD. Noncritical
gaps result in PARTIAL. READY refers to the supplied review plan.

The internal review retains the check names and gap reasons. The public summary
from `pieces.proof.review_projection.public_review` contains only the disposition,
counts and fixed reason codes. Keep the internal review behind the case-access
boundary. This local API awaits SI01 and the authenticated lifecycle adapters
before wiring into merchant review or certificate issuance.

The **Fixture proof signing** workflow replays the deterministic fixture path,
then signs only the aggregate verdict counts and the workflow revision. The
workflow requires a valid signature for the original bytes and rejects a
modified copy before uploading the report, Sigstore bundle and verification
output. Rekor records the GitHub workflow identity and payload hash publicly.
The fixture summary includes problem verdicts and is ineligible for a
`Certificate/1` merchant certificate. Live sandbox evidence remains required
for that certificate and its PayPal re-fetch check.

## Integration and live checks

The [reviewed START guide](START_Aditya_Singhal_proof.md) defines SH01–SH03.
This handoff covers the current Proof/Certificate interfaces. Exact deployment
image, package, runtime, state and authority binding, and private/public
projections await Singh's shared interface bootstrap (SI01) and actual evidence
from Gupta and Vijay. The current certificate does not close those gates.
Store normalized events as `CMEL/1` and final scenario verdicts as `Verdict/1` entries under the graft.
Use `mutation_coverage` with the final scenario plan and executed outcomes to
report rule guards. The 12/12 offline run does not establish coverage of every
critical rule on a live merchant. Populate the contract's triangle using that
merchant's verified scenario and mutation evidence.

Call `issue_certificate_from_ledger(..., smoke_verdicts=smoke, signer=sign_payload)`
on the runner after the smoke and full proof rounds. Call
`verify_certificate_evidence` with the certificate, graft ID, ledger, trusted
workflow identity/SHA and the shop-specific sandbox `PayPalClient`. The client
needs permission to read the signed order and capture. Aditya Vijay's real
recordings and Aditya Gupta's runner and sandbox client are needed to run this
against merchant evidence. Aditya Singh owns API wiring and deployment.

From the intended signing workflow step, after installing Cosign and enabling
GitHub Actions `id-token: write`, run:

```sh
uv run --locked python -m scripts.live_proof_sigstore \
  --workflow-identity "https://github.com/$GITHUB_WORKFLOW_REF" \
  --workflow-sha "$GITHUB_SHA"
```

This writes a synthetic payload's real keyless signature to the public
transparency log and tests verification and tamper rejection. It requires the
authorized signing workflow and network access. The live command was prepared
and its CLI checked. The actual live run and merchant PayPal re-fetch remain
open. Ordinary CI uses a simulated Cosign process and synthetic PayPal replies.
