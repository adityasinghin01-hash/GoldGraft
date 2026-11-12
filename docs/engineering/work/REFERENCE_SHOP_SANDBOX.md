# Reference PHP shop: opt-in real PayPal sandbox

This mode executes the saved AI candidate's NEW checkout against PayPal sandbox
(play money). It does not qualify production money, isolation, merchant delivery,
notifications, signing or a certificate. No live run was performed by Codex.
Default local proof and all ordinary tests remain simulated/offline.

## Live command for Claude

Run from `/Users/aditya/dev/GoldGraft-codex-sandbox` with an admitted, completed
reference-shop agent run. Replace the two absolute paths below. Output must be a
new directory; the runner refuses to overwrite existing evidence.

```sh
PYTHONPATH="$PWD" .venv/bin/python -m scripts.live_shop_sandbox \
  --authorize-sandbox-payment \
  --run-dir /absolute/path/to/agent-run \
  --output /absolute/path/to/new-shop-sandbox-output \
  --scenarios HAPPY,REFUND,REFUND_TWICE,DOUBLE
```

The default credential file is
`~/.config/goldgraft/paypal-sandbox.env`, with `PAYPAL_CLIENT_ID` and
`PAYPAL_CLIENT_SECRET`. Use `--env-file /private/path` to select another file.
Neither the file nor credentials are copied. PHP receives placeholders; the
loopback proxy substitutes client authentication only in memory. Real OAuth
access tokens reach PHP in memory, and OAuth token fields and authorization
headers are redacted in recordings. No credentials appear in command arguments,
PHP source, captures, journal or reports. Keep evidence private: actual provider
payment bodies can include sandbox buyer details.

The runner prints a real sandbox approval link for each NEW scenario. Log in as
the sandbox buyer and approve; the driver polls GET order for APPROVED (default
600 seconds, configurable with `--approval-timeout`). It never captures on a
browser return alone. Do not manually call the shop's execute endpoint from the
approval return page. The Python driver calls it after recorded approval.
Approval polling tolerates up to three consecutive transport-failed GET reads
within the same deadline. Capture/refund writes are never retried after an
unknown outcome; the failure is latched before another PHP write can dispatch.

Append `,DECLINE` for the optional sandbox **negative test**. The proxy adds
`PayPal-Mock-Response: {"mock_application_codes":"INSTRUMENT_DECLINED"}` only
to capture; it requires PayPal's actual HTTP 422 / INSTRUMENT_DECLINED response.
An unexpectedly successful capture stops the run and is retained/re-fetched.
See [PayPal negative testing](https://developer.paypal.com/negative-testing/request-headers/).

## Evidence and failures

- `<scenario>.OLD.json` and `.OLD_TWIN.json`: RawCapture/1, stand-in only.
- `<scenario>.NEW.json`: RawCapture/1 from the real proxy for supported scenarios.
  Real upstream URL, method, body, status and monotonic `t_ms`; no invented IDs.
  OAuth secrets are redacted. Added `Prefer: return=representation` requests
  actual capture/refund amounts; the PHP library and candidate are unchanged.
- `REFETCH.json`: independent, uncached PaymentBroker capture/refund GET results,
  keyed by scenario, including provider body, ID, status and timing; read failures
  are retained by error type. No write authority is granted to this broker.
- `refetch-journal.sqlite`: broker-required durable journal; GETs create no payment
  request rows. It contains no credentials and is not qualification evidence.
- `REPORT.json`: exact candidate input hashes, capture/read hashes, original run
  IDs, per-variant evidence labels, progress/errors and computed payment check.

A fault stops subsequent scenarios and preserves partial recordings and known
resource re-fetches. There are no automatic payment retries or compensating
refunds. Inspect provider state before any new invocation: a transport failure
can leave an unknown effect. Error details are fixed local diagnostics, never
provider exception text containing credentials. CLI exit 0 requires the payment
check to verify; otherwise exit 2, including a recorded run whose re-fetch fails.

## Connected proof

After recording, a separate read-only connected run imports this exact candidate:

```sh
PYTHONPATH="$PWD" GOLDGRAFT_PROOF=pieces.proof.proof:Proof \
  GOLDGRAFT_API_APP=integration.app:create_app \
  .venv/bin/python -m integration.connected_run /absolute/path/to/agent-run \
  --state-dir /absolute/path/to/new-connected-output \
  --shop-sandbox-dir /absolute/path/to/new-shop-sandbox-output
```

`payment:shop-checkout-paypal-sandbox` is critical, with evidence class
`real_provider`. The host seals an existing CheckResult/1 after validating the
actual NEW recordings and re-fetch bytes; no shared contract was changed and no
original run ID is relabelled. Candidate CHANGES/OUTPUTS hashes must match.
Approval must precede capture. Every distinct recorded capture/refund must have
exactly one independent, non-simulated GET result with matching provider ID,
integer minor-unit amount/currency, and status **COMPLETED**. A successful capture
must exist: DECLINE alone cannot qualify checkout. Missing evidence stays MISSING;
invalid, drifted or incomplete evidence becomes FAILED. The standalone sandbox
app recording (`--sandbox-capture`) still cannot qualify the shop checkout.

These files have the existing local host trust boundary: hashes detect drift;
they do not authenticate an independent collector. Import is an explicit operator
selection, and other release holds remain. All selected real scenarios must
satisfy the check. Unselected scenarios receive no real-provider coverage claim.

## Decisions (AGENTS.md rule 10)

1. Fix the reference cart at 2500 minor units USD, matching one fixture tee.
   Reject altered create amounts and refund amounts outside the recorded capture.
2. Keep OLD/OLD_TWIN on the stand-in. PENDING, NOTIFY_DUP, NOTIFY_FORGED and
   PARITY_EXTRA also stay there; deterministic state/notification/parity behavior
   is not a real provider claim. They may be explicitly selected and are labelled.
3. Send no synthetic webhook/IPN in real runs. No public listener or verified
   notification exists for this local reference run.
4. Preserve the requested exact COMPLETED predicate. PayPal can report a refunded
   capture as REFUNDED; that holds this gate even when the refund is COMPLETED.
   No normalization or pre-refund read is substituted. A HAPPY-only run can test
   the successful-capture path separately. See [capture details](https://developer.paypal.com/api/payments/v2/captures-get).
5. Add only existing-contract CheckResult/1 evidence. Keep simulated scenario and
   mutation judgments separate from sandbox provider qualification.

## Offline verification

```sh
PYTHONPATH="$PWD" GOLDGRAFT_PROOF=pieces.proof.proof:Proof \
  GOLDGRAFT_API_APP=integration.app:create_app \
  .venv/bin/python -m pytest -q -p no:cacheprovider
.venv/bin/ruff check .
```

New tests use injected HTTP transports and an in-process HTTP handler/driver;
no ordinary test calls PayPal or binds a loopback port. This Codex sandbox denies
socket binding, so actual PHP-to-proxy sockets and buyer approval remain Claude's
live check. Negative tests were observed red before the corresponding change.
Additional in-memory guard removals made authority, approval, missing-ID,
unexpected-status, endpoint, stand-in-only, unknown-duplicate-error, redaction,
CLI and all 13 evidence-corruption cases fail. No source mutation was left behind.

Verified on this worktree: **3294 passed, 17 skipped**, with two existing warnings
(Starlette/httpx deprecation and the Herald float-count negative fixture).
`ruff check .` and `git diff --check` pass. Added 58 sandbox cases and 2 connected
cases; all 29 in-memory weakened controls were caught. No live call, commit,
contract edit or frontend edit was made. The pre-existing `.venv` symlink remains.
