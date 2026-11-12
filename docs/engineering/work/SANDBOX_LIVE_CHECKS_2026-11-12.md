# Reference-demo live checks — 12 November 2026

The AI-written PHP candidate from `r9-final-connected` was executed through the
local recording proxy against PayPal's real sandbox. Buyer approval was manual.
All amounts below are 2500 minor units USD, play money; no production money.

| Selected flow | Observed and independently re-fetched state | Qualification scope |
|---|---|---|
| HAPPY | One capture, COMPLETED, matching amount/currency | VERIFIED in the connected proof |
| REFUND | Capture REFUNDED; refund COMPLETED, matching amount/currency | Recorded; strict COMPLETED-capture predicate holds |
| REFUND_TWICE | Two shop refund attempts; one upstream refund resource, COMPLETED; capture REFUNDED | Recorded; same strict predicate holds |
| DOUBLE | Two upstream capture calls returned the same capture resource; independent GET COMPLETED | Recorded in the additional-flow batch, outside the signed HAPPY-only gate |

The connected proof verifies **34/39** critical checks and remains **HOLD**.
The four surviving/unguarded planted bugs and runner isolation remain open.
No qualification certificate, merchant deployment or independent exit is claimed.
The exact held ProofResult is signed by the GitHub workflow at public Rekor
entry [3833925707](https://search.sigstore.dev/?logIndex=3833925707).
Its SHA-256 is `818190d46f9247013326af4e62b58dc9facfd1dc4be469e420a3245c1019566a`.
The signing workflow verified the signature and rejected changed bytes; the
downloaded signature and public-log hash/identity were also checked locally.

The first refund attempt stopped on a transport-failed approval GET. A separate
read-only order re-fetch found APPROVED with no captures. No uncertain payment
write was retried. Bounded retries were added only for approval-status GETs;
an uncertain capture/refund still latches the run and blocks further writes.

Actual sandbox recordings, buyer details, credentials and re-fetch bodies remain
private on the operator's computer. Only redacted scope/results and hashes are
published. The hosted scenario timeline contains executed PHP with **simulated
PayPal**, under original work/run ids and checked capture hashes. It is distinct
from the real-provider checkout evidence.

The public API serves recordings only. The frontend uses that API with a visible
recorded-demo banner; new shop, credential and upgrade forms are disabled.
Comparison and legacy security/certificate examples remain explicitly synthetic.

E2B is still a placeholder adapter in this revision. Creating an E2B account or
providing an API key alone does not establish isolated execution. The video must
retain the isolation and other hold disclosures unless later evidence clears them.
