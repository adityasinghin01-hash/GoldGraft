# Antigravity frontend construction handoff

Specification only. **Do not paste this as an execution instruction until Aditya explicitly starts Phase5.3.** No visual palette or styling direction is approved here. Antigravity builds the frontend; terminal agent/delivery assembly has a separate plan.

## Complete frontend start prompt

Use [ANTIGRAVITY_FRONTEND_START_PROMPT.txt](ANTIGRAVITY_FRONTEND_START_PROMPT.txt) for the whole AG1–AG6 construction scope. Pasting it is the explicit frontend start; do not ask for the same start again. Read [TWO_TERMINAL_WORKFLOW](TWO_TERMINAL_WORKFLOW.md) for exact folder/readiness/ownership. The named-step prompt below remains useful for a deliberately restricted step; it does not require Aditya to re-paste six prompts after authorising the complete frontend prompt.

Codex must first create the isolated `/Users/aditya/dev/GoldGraft-plan5-build` workspace and check/publish FRONTEND_READY.json with actual interface/fixture/spec hashes. Antigravity opens that root, writes only pieces/web, checks the ready revision and records INTERFACE_STATUS/INTERFACE_REQUESTS/FRONTEND_BUILD_REPORT in pieces/web/docs. Root/shared generated inputs and final combined handoff are Codex-owned. Missing readiness holds dependent work; it does not permit guessed contracts or a separate frontend project.

## Required input and precedence

Read repository AGENTS, engineering START, this Plan5 START, FRONTEND_SPEC, SHARED_BOOTSTRAP_PLAN and COMPONENT_TEST_PLAN. Use implemented SI01 generated schema/API/types/fixtures at one exact version manifest. Current Python remains actual wire; do not implement guessed fields from Markdown as though APIs exist. Obtain the explicit build workspace from the manual plan and re-inspect current contributions. No original-main reset, Desktop edits, blanket staging or publication.

Historical Desktop files supply safe copy/provenance only: `05_WORDS_AND_LABELS.md` and screen source material per the inventory. Do not copy its AGENTS wholesale: old no-login, key forms, localStorage-only cases, three-pop-up limit, fixed screen count, automatic old-cutback and PR-as-Done rules are superseded. Never edit `reference/` or generated contracts by hand.

## Build prompts, one reviewable step at a time

The common prompt prefix for each step:

> Build only this named step in pieces/web after the explicit Phase5.3 start. Use the approved isolated workspace, current project guidance and implemented SI01 versions. Do not modify contracts, other pieces, Desktop/personal/reference files, accounts or provider settings. Keep the synthetic adapter visibly labelled. No external source/model/payment/provider call, deploy or publication. Missing contracts/fixtures are a named dependency hold, not a fabricated endpoint. Preserve concise useful copy; styling/palette is the later visual decision. End with changed files, actual commands/results, screenshots/routes/states reviewed, deviations and unresolved gates.

| Step | Concrete prompt suffix | Required check before next step |
|---|---|---|
| AG1 scaffold and adapters | Keep React18/Vite/strictTS/Router/Query/CSS Modules. Create src/api/{contracts,http,sse,caseAdapter}.ts, state/caseProjection.ts, copy/messages.ts, lib/format.ts, main/App/route config and fixtureAdapter. Use generated SI01 types; fixture mode on by default, same-origin API behind explicit configuration. | Typecheck/lint; unknown schema/mode denies; synthetic banner on every route; no other-piece import or browser secret persistence |
| AG2 saved case and setup | Implement CaseShell, case list, URL draft, identity/current controller and recipient views, SourceRoutePicker/upload resume, ResourceConnectionCard and ProcessingDisclosure exactly from state table. No generic secret form. Show qualified J06 intake only as trusted backend flow. | Cold return/session expiry/wrong account/controller unavailable/missing backend/stale upload/required policy missing, keyboard error/focus checks |
| AG3 readiness, Start and progress | Implement ReadinessChecks, durable action-intent/acceptance/current WorkStatus, receipt, StopControl, event cursor/snapshot resync and relevant waits. Browser close must not be work cancellation. | Lost response→same action lookup; claimed≠operation_started; Stop before receipt/running/unknown; malformed/gapped event disables consequential actions |
| AG4 evidence and review | Implement private RootMap/test/proof views, source/evidence class labels and exact ApplyReview with split controllers/direct-artifact route. Keep missing proof and subject drift blocking. | Missing flow/high score, wrong image, viewer denied, expired/revoked authority, no private IDs on public-safe view |
| AG5 delivery, recovery and exit | Implement DeliveryStatus, RecoveryPanel, ExitChecklist and private result record. Read backend outcomes; no local deploy retry/financial rollback. Merchant retained assets never generic cleanup choices. | Deploy accepted/queued/no ID≠live; persistent config mismatch; executor missing; revocation/delete pending; all show honest hold/unknown and no manual finishing instructions |
| AG6 browser review | Run named actual-browser scenarios against deterministic fixtures. Capture entry/setup/progress/review/unknown/exit-pending/complete synthetic views at narrow and wide widths. Inspect keyboard/focus/status announcements/overflow and unsafe API text. | Actual checks logged, screenshots inspected and defects fixed. All synthetic “complete” remains visibly synthetic. Palette work waits for separate visual pass |

## Fixture modes and result report

`VITE_GOLDGRAFT_WEB_MODE=fixture` uses Vite's explicit public environment prefix and local synthetic adapter; `same_origin` is enabled only for an explicitly supplied compatible backend. The mode value is public nonsecret configuration; provider/key values must never use the VITE_ prefix. This is a proposed config setting with closed allowed values, not a live connection. Never default to a remote public URL or quietly switch endpoints. Fixtures include `ready`, `controller_wait`, `missing_source`, `start_response_lost`, `claimed_no_operation`, `cancel_before_accept`, `cancel_pending`, `event_gap`, `proof_missing`, `apply_split_controllers`, `deploy_unknown_no_id`, `persistent_config_mismatch`, `exit_executor_missing`, `cleanup_pending`, `synthetic_complete`. Fixture selection is developer-only and excluded from merchant service build.

For each step record source/interface/fixture versions; changed files; commands/results (not anticipated output); browser states inspected; screenshots with synthetic labels; accessibility/manual observations; remaining real boundary/provider gates. Do not report provider/payment/live merchant validation from fake responses. Any required missing route/type stops only its dependent step; independent approved views can continue.

Final frontend handoff includes actual `npm --prefix pieces/web` typecheck/build/test/browser results, implementation limitations, and exact hookup list for Plan6. It does not claim same-site operating exit until actual integration/qualification. No publish/deploy command belongs in this handoff.
