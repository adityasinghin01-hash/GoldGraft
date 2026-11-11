# B4 Surveyor — offline component evidence

10 November 2026. Workspace `/Users/aditya/dev/GoldGraft-plan5-build`.
User authorised direct Surveyor construction after the manual baseline returned
56 passes. No other B4 role was built. No sub-agents, staged files, commits,
pushes, merges, deployments, account changes, external messages or paid calls.

## Result and measured scores

| Measure | Observed result | Scope |
|---|---|---|
| Surveyor-specific checks | 61/61 passed | Actual own runtime/validator with persistent scripted counterparts |
| Full offline regression | 2,210 passed, one existing warning | Includes the prior 56 B3 checks and 61 new checks |
| Reference inventory | 5/5 hand-specified indicators preserved | Four tiny synthetic source files; not general recall or model accuracy |
| Lint / shared TypeScript / whitespace | Passed | Exact final commands and log hashes in private evidence |
| Model API calls / project API spend | 0 / $0 | Scripted broker dispatches are not provider calls |
| Real-model quality, financial correctness, live safety | NOT EVALUATED | No invented percentage or readiness score |

Full evidence: `/Users/aditya/reports/goldgraft-b4-surveyor-20261110/`.
Final check records: `checks/10-final-surveyor.json`, `11-final-full.json`,
`12-final-lint.json`, `13-final-types.json`, `14-final-diff.json`.
Each records exact arguments, cwd, exit status, duration, output path and SHA256.
Failed initial attempts are retained: the original missing-backend acceptance
bug, and missing-subject-manifest / >4-file batching regressions were observed
before their corresponding fixes.

## Demonstrated capabilities

- An exclusive versioned Surveyor prompt and policy permit only `survey`,
  `RootMap/1`, `source.read`, `analysis.matches`, and `evidence.read`. Other
  eleven future role policies plus Herald remain unimplemented in B4.
- A collector-labelled SourceSnapshot, omission record, bounded file manifest
  and bytes are checked before inference. Required missing source/components or
  unavailable runtime/site/account lenses hold with no model/tool dispatch.
- Source tree and scope use the actual `SubjectManifest/1` shape. Its immutable
  descriptor/ref/bytes are persisted and resolved; a naked hash cannot replace it.
  Content digests, case/run/generation, authority, custody and lease guards apply.
- All required files must be read. Source batches contain at most four reads;
  a five-file case exercises multiple batches. Intake is bounded to 16 files and
  16,384 source bytes, subject to the existing 24,000-byte context bound,
  4,000-byte final JSON limit, 12 turns and 24 tool calls. A cap holds required
  evidence instead of trimming it into success.
- The synthetic catalog finds five literal indicators: SetExpressCheckout,
  DoExpressCheckoutPayment, RefundTransaction, IPN validation text, and legacy
  paypal.Button.render. RootMap links file/line locations and create/approve/
  capture/refund/notify flow entries. Unobserved mark-paid/recurring flows remain
  empty in this fixture, never asserted operational.
- Final review checks the actual source excerpts, hashes, catalog-match and
  omission observations. Missing reads, omitted indicators, invented locations,
  runtime/live claims, invented API mappings and recall metrics cannot complete.
  TaskControl independently checks the producer, input and output bindings.
- A developer-only read-only inspection view consumes the accepted RootMap.
  It displays five indicators and six evidence refs, input/output refs, subject,
  omitted items and explicit limitations, including after reopening the database.
- Stop, stale leases, revoked scope, secret canaries, expired custody, unknown
  model/tool outcomes and forged output owners/subjects fail closed. Six real
  subprocess crashes exercise the original dispatch identities after restart.
  An intent without a qualified fence-rebinding receipt remains held.

## Files and boundaries

New own modules: `pieces/agents/roles.py`, `surveyor.py`, and
`prompts/surveyor.md`; role tests in `tests/test_roles.py` and
`tests/test_surveyor.py`. Runtime/context/ports/CLI connect these checks to the
existing loop; there is no second scheduler or agent framework.

`fakes/.../surveyor_profile.py` is an explicitly selected developer counterpart.
It uses fixed synthetic source, a hand-authored final response, actual scoped
tool implementations and SQLite TaskControl. It does not substitute a fixed
final answer for the runtime or inventory validator under test. Foundation's
deferred composition loader selects this profile; agents import only their own
piece, contracts and foundation. The B3 fake gains scoped artifact-byte reading.

The old B3 no-agent-prompt profile remains an explicit scripted compatibility
path; it is not a B4 role acceptance. New Surveyor tasks require pinned B4
prompt/policy identities and evidence checks. Shared schemas, types, routes,
fixtures and frozen frontend inputs were not changed. Generated exporters were
not invoked because they rewrite frozen inputs; current frozen hashes are
checked instead, and shared TypeScript was checked without emitting files.

## Actual demonstration

Developer state:
`/Users/aditya/reports/goldgraft-b4-surveyor-20261110/demo/surveyor.sqlite`.
One run committed one Surveyor result using three **scripted** model turns and
six read-tool dispatches. The separate inspect command read that actual output.
Observed input refs: `fake:survey-source`, `fake:survey-omissions`.
Subject manifest ref: `fake:survey-subject-manifest`.
Full output/evidence refs are in private `checks/09-demo-inspect.json`; its bytes
and code hashes are linked by `B4_SURVEYOR_MANIFEST.json`.

From the isolated root (these commands reuse the named completed synthetic run):

```sh
uv run --locked --no-sync python -m pieces.agents.cli status --mode offline --fixture surveyor_inventory --state-file /Users/aditya/reports/goldgraft-b4-surveyor-20261110/demo/surveyor.sqlite
uv run --locked --no-sync python -m pieces.agents.cli inspect --mode offline --fixture surveyor_inventory --state-file /Users/aditya/reports/goldgraft-b4-surveyor-20261110/demo/surveyor.sqlite
```

For a new demonstration choose a new explicitly named state path and use `run`;
never delete unknown-state databases to force a retry. `resume` rechecks current
state; it does not override Stop, held results or unknown reservations.

## Decisions, limitations and unresolved gates

1. This is a source-only offline Surveyor component, not acceptance of the full
   multi-lens real-model agent. No local or remote reasoning model is running.
   A scripted fixture cannot prove real interpretation, injection resistance,
   broad recall, patch quality or realistic-shop competence. Literal matches
   can occur in comments/strings and miss dynamic behaviour. Only five indicators
   in three families are exercised; no all-PayPal-family coverage claim.
2. RootMap/1 has no explicit nullable runtime-recall fields. In this offline
   source profile its required counters remain zero placeholders. The inspection
   explicitly says NOT MEASURED; zero is not observed absence or 100% recall.
   Live is false, confidence at most 0.5, paypal_only false, and target operations
   are `unqualified`. Target mapping qualification belongs to VJ/Architect work.
3. Initial Start/BASELINE_READ, custody and all evidence provenance are synthetic
   preconditions at fake ports. Acceptance is not real GU/Postgres, provider,
   runner or payment qualification. GU owns actual mechanisms; VJ owns recipes;
   SH owns mapping/proof. No sponsor integration was connected by this work.
4. The first proposed test incorrectly assumed `accepted_result_count()` counts
   successful outputs only; it actually counts committed held results too. The
   corrected test requires one held result, no output refs and zero dispatches.
5. Herald is the next construction role, but is not started. Its future B4
   demonstration must consume this grounded inventory and prove automatic
   Surveyor→Herald advancement/restart; the old B3 demo does not close that gate.

## When API access is needed

The next real-model step is a separately qualified Surveyor evaluation on this
synthetic licensed source. A key is not needed for further offline construction.
Do not paste a key in chat. Configure `ANTHROPIC_API_KEY` locally or through the
approved GU secret store only when the following profile is ready:

- GU supplies the actual qualified broker/processing/custody boundary and evidence.
- The official Anthropic Python client is pinned behind that broker, with hidden
  retries disabled. Runtime and provider tokenizer/deadline/tool/schema limits
  must qualify before enabling a paid path; no alternate framework/provider.
- Exact available model ID, entitlement, pricing, retention/region/no-training
  processing conditions and permitted synthetic data scope are reviewed.
- A durable cumulative reservation ledger enforces spent + outstanding + unknown
  costs before dispatch and reconciles original identities/usage. Typed ModelBudget
  records alone are not that ledger. All paid evaluation, calibration, retries,
  regression and demos consume the same project allowance; no training job is planned.
- User's first active paid cap is $5 cumulative. Raise to $10, $15, then at most
  $20 only at reviewed approved checkpoints. Retain the $15 target/$20 project
  hard ceiling; never reset spent or unknown reservations or auto-upgrade models.
- A calculated, named trial with independent expected outputs is reviewed before
  paid dispatch. Broader 20-case ×3 evaluation and remaining role checks stay open.

Current paid/service admission remains disabled, including when a nonzero budget
or real-model evidence class is injected. Paid checks are **NOT RUN**. Remaining
roles, B5, B6, combined B7, Plan6 and real merchant outcomes remain separate.
