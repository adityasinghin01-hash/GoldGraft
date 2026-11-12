# VJ05 independent exit domain recipe

Local proposed recipe grounded in current VJ05 and atomic IR07. It specifies domain observations for Gupta's qualified merchant executor; it does not create a workflow, use host credentials, restart a merchant shop, sign a result or implement the backend state machine.

## Preconditions supplied by the actual counterparts

- Preexisting/separately approved merchant-account executor with fixed trusted code/image, exact target, current controller approvals and bounded restart/read/current-compatible recovery rights.
- Final tested artifact/config/state/origin evidence and private merchant-owned evidence destination/trust roots.
- Explicit restart/observe/recovery slots, budget/deadline and failure owner. No automatic financial compensation or old-state restore.
- Shared-asset inventory and acknowledgement that ordinary GoldGraft capabilities have actually stopped/revoked; pending revocation stays pending.

## Domain observations after denial and restart

| Check | Required observation | Failure result |
| --- | --- | --- |
| Public shop | Approved merchant URL renders intended deployed version | Hold; public health alone cannot qualify money/state |
| Private state | Order counts/identity-correspondence/origin/idempotency state preserved, privately observed | Hold without exporting customer rows publicly |
| Browser continuity | Required in-flight capture/return still served on correct original rail | Hold; queue alone is insufficient |
| Notifications | Required IPN and actual NEW webhook listener/verification/effect routes remain operating | Hold; simulator does not substitute for actual events |
| Old obligations | Approved historical refund/pending obligations retain account/API/object and required route | Hold; no unapproved fresh transaction/refund |
| New checkout | Qualified one-time USD behaviour continues under merchant-owned runtime credentials | Hold; never revive a revoked GoldGraft capability |
| Restart/recovery | Only the exact approved bounded restart/recovery executes and reads back current state | Unknown/hold; no blind retry or stale database replacement |
| Evidence access | Signed redacted result delivered through the explicitly scoped temporary read-only exit-evidence route | Report pending evidence, not hidden operational access |
| Final disconnect | Remaining evidence-only access expires/revokes, separately acknowledged | Pending acknowledgement remains visible |

GoldGraft must be unable to perform ordinary host/source/worker operations during the independent test. The merchant executor, not a local helper in this repository, performs authorized observations/recovery. No ready executor means hold before a disruptive exit test, not asking the merchant to improvise scripts later. Preserve shared merchant assets and actual financial history.
