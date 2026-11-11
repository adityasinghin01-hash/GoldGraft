# Surveyor — offline readiness delta, 10 November 2026

Scoped agent-side improvement completed in `/Users/aditya/dev/GoldGraft-plan5-build`.
**Real-model evaluation remains NOT RUN.** No backend, payment, provider, merchant
or frontend implementation was performed. Surveyor remains a bounded literal
source-inventory implementation, not a general code-understanding model.

## Changed behavior

The old include regex could miss a computed PHP dependency entirely, or accept
the literal prefix of a computed expression when a same-named file was supplied.
It also treated quoted documentation and comments as required includes.

`source_references.py` now recognizes PHP code regions, comment/string boundaries,
complete literal includes, optional outer parentheses, __DIR__ concatenation,
multiline syntax and case-insensitive include keywords. It resolves only supplied
manifest paths, including parent-relative paths that remain inside the package.
It never executes source, reads a host target or fetches a URL.

Computed/variable/interpolated references, eval, __halt_compiler and unsupported
lexical forms hold. Attributes, heredoc/backticks and incomplete quotes/comments
are conservatively unsupported. All double-quoted interpolation is conservative
unresolved input, even if a particular expression would be harmless. This favors
an explicit scope hold over claiming coverage the recognizer does not provide.
Literal include resolution retains the synthetic file-relative convention;
actual PHP include_path, cwd and runtime semantics remain unqualified.

Surveyor admission independently reruns the check against hash-verified supplied
bytes. Clearing the omission list and claiming a complete snapshot no longer
bypasses a visible unresolved dependency. The original resource/subject/producer/
lease/tool/Stop/secret/overflow guards remain active.

The independent RootMap artifact scorer now also rejects invented stack identity.
No payment detector, VJ API mapping, shared schema, GU mechanism or SH proof was
invented. The existing five literal indicators/three families and exact-match
validator remain bounded: comments/strings can still be indicators; indirect
payment calls and unsupported families can be missed. Zero matches still do not
prove payment absence. Broader detection requires separately grounded evidence
and the corresponding qualified catalog/validator design.

## Actual checks and output use

Private commands/logs/SQLite states/results:
`/Users/aditya/reports/goldgraft-surveyor-readiness-20261110/`.
The accompanying `SURVEYOR_READINESS_MANIFEST.json` binds final source/check bytes.

| Check | Actual observed result |
|---|---|
| New reference behavior before implementation |24 failed/1 passed; failures retained in01-source-gaps-red |
| Attribute/interpolation refinement before fix |2 failures retained in06-lexical-context-red |
| All affected Surveyor/source/evaluator/readiness checks |121 passed in17.75s |
| Full own-agent runtime/role/workflow regression |508 passed in94.57s |
| Named20-case diagnostic,3 fresh repeat identities each |60/60 matched independently specified outcomes |
| Accepted inventory artifacts actually checked and inspected |30; expected labels stayed outside analysis/model inputs |
| Required evidence holds before scripted/tool dispatch |30; no accepted output,0 scripted/model/tool dispatches |
| Reopened persisted state |0 additional dispatches; original results retained |
| Separate-process second CLI run over all60 saved states |60/60 still matched; dispatch counts unchanged |
| Ruff / tracked diff whitespace |Passed |
| Real API calls / recorded project spend |0 /$0; actual model competence untested |

The initial508-check regression preceded a report-only rename from result_ref to
result_digest, to avoid suggesting that a hash was a stored reference. Its14
affected evaluator/CLI checks and the saved60-state diagnostic were rechecked
afterward. Product admission logic did not change after that full regression.
Counts overlap; do not add them. The old2,570 whole-repository result remains a
dated B4 snapshot; the entire repository suite was not unnecessarily rerun for
these agent-only changes. No new TypeScript/generated checks were needed because
all454 frozen contract/spec/fixture bytes stayed unchanged.

The diagnostic's20 source-readiness cases do **not** replace COMPONENT_TEST_PLAN's
reviewed20-case/three-repeat real-model acceptance sample. Its passing count is
offline conformance evidence, not a model score, safety rate or measured variance.
The60 fresh runs used90 scripted turns and105 scoped read-tool dispatches; no
provider inference occurred. Same-state reopening reused those identities.

## API/model preparation and remaining gate

`SURVEYOR_MODEL_GATE_HANDOFF.md` lists exact existing port types, agent-side
acceptance requirements, current official SDK/model/token-count/pricing sources,
and a concrete four-case paid proposal. `SURVEYOR_MODEL_CANDIDATES.json` records
unselected/unqualified candidates and integer micro-USD arithmetic. It authorizes
no dispatch. Neither an SDK nor a key was installed/configured.

The read-only doctor still reports key ABSENT in the checked project process,
no installed Anthropic package, service profile unqualified and paid dispatch
disabled. This says nothing about credentials elsewhere on the machine. Current
published GU branch pins were inspected read-only; no newer qualified broker or
shared model-cost mechanism was established. No absence of unpushed work is claimed.

GU must supply authenticated model/tool/artifact/control evidence and a durable
shared reservation/reconciliation boundary. Own service adaptation must then
consume that evidence; current admission and runtime deliberately remain scripted
and fake-profile-only. The agent preparation is complete for this offline scope,
but service adaptation and actual model acceptance remain pending. No backend
implementation was taken over to get around this dependency.

One cumulative$20 ceiling covers all13 roles and every paid calibration/retry/
evaluation/regression/demo, with$15 target and active$5 checkpoint. Recorded spend
is$0 and this phase made no reservations. No qualified ledger exists locally to
certify current external/outstanding/unknown project usage. The public candidate
cost arithmetic is not a reservation or new spending authority.

**API access becomes useful after the model/cost/custody boundary and own service
adapter qualify, and the concrete batch is reviewed.** Then configure the key
locally in the approved process/secret store, check presence only, calibrate the
approved token counter and reconcile/reserve before dispatch. Never paste the key
in chat. It would be premature to request/configure it against the present path.

Surveyor's later connections remain those in MANUAL_CONNECTIONS_AND_GATES:
authorized source/account/site scopes and shared model access; GU source/custody/
readiness plus VJ-qualified detection/catalog coverage. Other agents' deferred
connections remain unchanged. Herald has not received a new improvement phase.

## Preservation and decisions

All454 frozen inputs still match frontend revision2; pieces/web remains only its
existing .gitkeep. All327 original tracked hashes, original status and HEAD match
the before snapshot. New source, tests, evaluations and documentation stayed in
the isolated agent workspace; private evidence stayed under reports.

No sub-agents, commits/staging/push/merge/reset/clean, installations, publication,
deployment, teammate messages, account/billing changes, private-source transfer,
provider/payment/merchant jobs, B5/B6 or Plan6 actions occurred.

The chosen scope is conservative source-reference uncertainty plus independent
agent-side evaluation preparation. It does not claim exhaustive PHP parsing,
JavaScript/module dependency analysis, runtime reachability, new PayPal family
support, real-model injection resistance, qualified isolation or payment proof.

## Reproduce the offline diagnostic

From the isolated root, reuse the saved matching states (do not delete unknown
state to force a retry):

```sh
.venv/bin/python -B -m pieces.agents.evals.surveyor_readiness --state-dir /Users/aditya/reports/goldgraft-surveyor-readiness-20261110/diagnostic-state --repeats 3
.venv/bin/python -B -m pytest -q pieces/agents/tests
.venv/bin/python -B -m pieces.agents.cli doctor --mode offline
```

There is no service-mode or arbitrary merchant-source switch in the diagnostic.
