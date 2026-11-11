# Sentinel qualification report — 11 November2026

Claude, agent 3 in the accepted order. **Sentinel is qualified to its contract
ceiling, deterministically, for $0.** It reports every anomaly in any audit window
of up to 32 events, with counts, sequence numbers and the window range. It requests
a hold only on a policy breach and never claims termination or safety.

## Before → after

| Check | Result |
|---|---|
| Existing tests | 6 passed |
| 01 ceiling red | **31 failed / 5 passed**: mixed windows reported only the most severe kind (e.g. a stale output beside a pending termination was missed); no counts or sequence links |
| Fix | `describe()`: the same severity rules and lead sentence, then every detected kind (most severe first) with count and sequences, the audit window range, and truthful pending/stale notes |
| 04 ceiling green | **42/42** (all 30 kind mixes ×1/×3, empty window, full 32-event window, 33 refused at creation, 4 untrustworthy-window holds) |
| Full regression | 813 passed; Ruff lint/format and `git diff --check` clean |

## Output use

Alert/1 was consumed by the actual inspector for 5 windows (breach mix, pending only,
stale only, empty, full 32). The hold stays advisory and `halted_agent` is never set.
A fresh instance reopened the persisted state and re-ticked: no new dispatch and no
state change. Evidence: `~/reports/goldgraft-sentinel-qualification-20261111/`.

## Phase decisions

- **Model: not used (N/A for this contract).** Events are structured and redacted
  (4 kinds, digests only), and review requires exact agreement with the rules, so a
  model can add no detection value, only cost and risk. This is the playbook's
  "no paid calls where reasoning adds nothing". The $0.40 envelope stays unspent.
- **Sponsor: Elastic is conditional** (approved redacted audit search). It needs an
  account and Aditya's decision; not connected.
- A higher ceiling would need a richer audit format (free-text security events,
  behaviour patterns). That is a shared-contract change owned by Aditya, not started.
- Mandatory guards stay on with Sentinel absent (`test_sentinel_absence_does_not_disable_guards`).

Preservation: only `sentinel.py` changed among Sentinel files. 454 frozen inputs, 327
original hashes, HEAD/status and `pieces/web` are unchanged; the ledger is unchanged
($1.160890 spent, no unknown requests). Spend: $0.
