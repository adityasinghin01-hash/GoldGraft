# Surveyor offline readiness improvement plan — 10 November 2026

> Execute sequentially in this existing isolated workspace using the executing-plans
> workflow. No sub-agents, Git mutations, paid calls or backend implementation.

**Goal:** Close the observed source-reference admission gap and prepare an honest,
independently checked Surveyor diagnostic before asking for local API access.

**Architecture:** Keep the Python runtime, GU ports and scripted offline profile.
An agent-owned bounded lexical source check identifies unresolved PHP source
references; it neither executes PHP nor supplies VJ payment/API recipes. Existing
RootMap schemas, frontend inputs and counterpart interfaces remain unchanged.

**Stack:** Existing Python 3.12, pytest, Ruff and project contracts; no installs.

## Constraints

- One $20 total API ceiling for all13 agents and every calibration/retry/eval/demo;
  $15 target, active $5 cumulative checkpoint. No paid dispatch in this phase.
- GU owns authentication/custody/model/budget/durable-control mechanisms. VJ owns
  qualified payment detection/recipes; SH owns independent proof.
- Never infer runtime absence from zero literal matches. A RootMap is a literal
  source-indicator proposal, not a complete payment implementation inventory.
- Preserve original checkout, pieces/web, all454 frozen inputs and old evidence.
- Context limits remain16 files/16,384 source bytes/12 turns/24 tools/4 reads per
  batch/4,000 final JSON bytes; required overflow holds.

## Task 1 — Recheck unresolved source references before inference

Files: create `pieces/agents/source_references.py` and
`pieces/agents/tests/test_source_references.py`; modify `source_inventory.py`
and `surveyor.py` in the same piece.

- [x] Write failing behavior cases: variable/concatenated/interpolated/computed
  includes must hold; comments and quoted documentation must not invent missing
  dependencies; parent-relative and __DIR__ literal paths retain bounds.
- [x] Confirm failures against current code and save the command/log.
- [x] Implement a conservative bounded PHP lexical recognizer. Resolve only
  supported complete literal expressions against supplied bytes; mark all other
  include expressions, eval and unsupported lexical forms unresolved. Never read
  a host path or fetch a target. Not a PHP parser, reachability or runtime claim.
- [x] Call the same source check during role input admission so a caller's
  `complete_for_declared_scope` declaration cannot bypass it.
- [x] Run affected source/Surveyor tests; inspect accepted and held outputs.

## Task 2 — Independent named diagnostic and meaningful output use

Files: create `pieces/agents/evals/surveyor_readiness_cases.json`,
`surveyor_readiness.py` and `pieces/agents/tests/test_surveyor_readiness.py`;
modify the existing independent artifact scorer only for a demonstrated gap.

- [x] Hand-label20 source-readiness cases, incorporating the existing four
  source inventories without changing their bytes or expected answers. Include
  unresolved and hostile source-reference cases, and context/required-lens holds.
- [x] Build a closed offline diagnostic CLI over actual runtime and explicit
  labelled counterparts. Expected outputs go only to the checker, never into
  the analyzer or scripted model's proposed output.
- [x] Check accepted RootMap content and inspect the committed artifact; for
  required holds assert no accepted output and zero scripted/tool dispatches.
- [x] Exercise three fresh repeat identities plus same-state resume, recording
  outcome, hashes, latency and dispatch counts. This is not the20-case/60-run
  real-model acceptance design in COMPONENT_TEST_PLAN and cannot replace it.

## Task 3 — API handoff and preservation evidence

Files: own model-readiness diagnostic if needed; new
`SURVEYOR_READINESS_REPORT.md` and manifest; update BUILD_STATUS with dated delta.

- [x] Inspect current official Anthropic SDK/model/token-count/pricing sources.
  Record exact observed candidates separately from qualified/approved profiles;
  no entitlement, processing or token-count calibration can be inferred offline.
- [x] Prepare agent-owned model-evaluation input/output/tool expectations and the
  exact GU evidence required to admit a service adapter. Keep service disabled.
- [x] Run relevant tests and lint, then full own-agent regression because shared
  role admission affects the Surveyor→Herald path. Do not repeat the whole suite
  without a failure or broader change that warrants it.
- [x] Verify frozen/frontend/original preservation and all evidence hashes.
  Report recorded $0 spend; no qualified ledger exists to certify external usage.
- [x] State when local API configuration becomes useful. If GU prerequisites
  remain missing, identify that dependency; do not ask for a key prematurely.

## Acceptance limits

Completion means this named offline scope works and actual outputs were used.
General Surveyor reasoning, additional PayPal families, AST/call-graph coverage,
real GU tools, runtime/site/account observations and model safety/quality remain
unqualified until the corresponding evidence is actually collected. No further
agent advances before Surveyor's scoped check/use report is complete.
