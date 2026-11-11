# Herald qualification report — 11 November2026

Started by Codex and finished by Claude after the complete handover. **The
deterministic closed-catalog Herald is offline-qualified.** Its actual-model phase
is not needed for the closed catalog and stays unqualified. Zapier is deferred.
No API call, notification, account change or spend.

## Before → after

| Check | Result |
|---|---|
| 01 consumer red (Codex) | 12 failures reproduced: previews/inspection bypassed fact validation |
| 02 consumer green (Codex) | 92 passed after `_validated_facts` extraction |
| 03 matrix (Codex, uninspected at handover) | 1 failed: `bool_count` accepted |
| Cause (Claude) | Render/preview reparsed facts as JSON, which turns an unchecked `True` into `1` |
| Fix | `_reparsed()`: strict Python-mode revalidation before every JSON reparse (render, preview, inspection) |
| 05 Herald green | **97 passed** (80 existing + 17 qualification; 704-combination matrix inside) |
| Affected regression | 620 passed, with Ruff lint/format and diff checks |

## Output use (actual CLI, both projections)

Surveyor→Herald ran, the committed text was inspected (“Inventory contains 5 source
indicators…”, number grounded to the journal entry), then run/resume/status/inspect
ran again in fresh processes. Results, artifacts, model turns, tools, effects and
outbox were unchanged. The public view has no ref/hash/markup leaks. The opt-in
preview says `NOT SENT`, authority `NONE`.

## Phase decisions

P1–P4, P8, P9 done (above). P5 Zapier **deferred**: no destination/opt-in chosen.
P6 actual model **not pursued**: the catalog is closed, the free deterministic
fallback covers it, the gateway admits Surveyor only, and Surveyor grants are never
used for Herald. This is not a model-competence claim. P7: one grounded offline
correction.

Preservation: Herald changed only `herald.py` and its new test file. All other
protected-file changes come from Surveyor continuation-04. Herald made no ledger
writes. Evidence: `~/reports/goldgraft-herald-qualification-20261111/` and
[manifest](HERALD_QUALIFICATION_MANIFEST_2026-11-11.json). Next in the accepted
order: **Sentinel (#3)**.

## Update — Surveyor → Herald and the Zapier sender (11 November2026)

- **Real chain:** 9 accepted Surveyor model inventories (0–11 indicators, Haiku and
  Sonnet) were replayed through the actual runtime into Herald: **18/18** passed
  across both projections. Numbers are exact, uncertainty is kept, the public view
  has no leaks, previews are NOT SENT, and re-ticking changed nothing. $0, no inference.
  Evidence: `SURVEYOR_TO_HERALD_REAL.json`.
- **Zapier sender** (`pieces/backend/notifications/zapier_eval.py`, a local evaluation
  sender that Gupta's GU connector may adopt): explicit opt-in/opt-out; one minimal
  notification per event key; dedupe on resend; retries of the same key for
  429/5xx (max 3, then closed); timeouts/resets become *unknown* and are never
  resent; secret, shape and authority checks; the hook URL is read from a 0600
  file, host-checked, and never logged. 6 offline tests. `scripts/live_herald_zapier_send.py
  --dry-run` passed the full chain (11 indicators → sent receipt).
- Checks: 777 tests (agents, gateway, notifications, fakes), Ruff clean.
- **Waiting on Aditya:** a Zapier Catch Hook URL saved privately, and the destination.
  No real notification has been sent.

## Final status — 11 November2026

**Herald complete for this phase.** Live Zapier evidence: one real notification
(about the 16-file Surveyor result, "11 source indicators … remain unverified")
was accepted by Zapier's Catch Hook with HTTP 200 and receipt `01a1c9d4-…`
(`zapier/SENDS.jsonl`). Zapier's own Gmail step test delivered an email to
Aditya's inbox. Zap publishing (always-on forwarding) is **not done**: the
Gmail retest showed an empty-To/"Network Error", then the Zapier site stopped
loading. Account: Zapier Pro trial ends 25 Nov2026; no payment was made, and
Aditya was advised not to use "Pay now" (₹3,399.72/month, non-refundable).
Remaining when Zapier loads: fix the Gmail To/Body, publish, then one real send
plus a same-key resend to show dedupe. Notifications stay optional and never
block the job. Spend: $0.

## Zapier completed — 11 November2026

Aditya published the Zap (Catch Hook → Gmail). Live sends after publishing:
`4ce8…` and `fa66…` were the same Surveyor result (8-file case) sent twice
(HTTP 200 both), so a **duplicate email** reached Aditya. Cause: the composition
script stamped each replay with the wall clock, giving one result two event keys.
Fix: the event time is now the committed result's own recorded time (`event_time`),
covered by `test_herald_event_identity.py`. Live proof after the fix: `ee97…` sent
(HTTP 200, receipt `01a1c9f1…`), and the same send again was **deduplicated**
(no request, same receipt). Herald + Zapier is complete end to end. Spend $0.
