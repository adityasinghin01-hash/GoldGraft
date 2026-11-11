# Copy-paste prompt for Singhal's AI — complete SH01–SH03

You are working for Aditya Singhal on GoldGraft. Finish Singhal's deterministic
proof/evidence/certificate component and make it integration-ready. FIRST write
the concrete plan below; THEN execute it phase by phase. Complete everything in
your scope independently, reuse existing correct work, report after each phase,
and record genuine external blockers precisely.

## 1. Scope and current GitHub starting point

You own SH01–SH03: deterministic mapping/judging/maths; exact-subject evidence
completeness; safe private/public proof projection; certificate issuance and
verification; proof-side integration and negative tests.

Do NOT implement Gupta's backend, identity, custody, payment broker, runner,
callbacks, upload/effect stores, deployment or state/recovery engine. Do NOT
implement Vijay's shop recipes, payment scenarios or real recordings. Do NOT
change Singh's agents/model routing or Claude's frontend. Consume their outputs
through accepted contracts; finish your validators/adapters even if an external
input is temporarily missing. Do not turn a dependency into another owner's code.

Use your own existing checkout/PR branch. Do not touch the integrator's active
`/Users/aditya/dev/GoldGraft-plan5-build` workspace or unpublished files. This
owner-specific prompt is the current assignment for this run; older broad
"Codex owns all non-frontend" wording does not expand your scope.

Last verified snapshot, 12 November 2026:

- Main: `f2c86ef832ae2506bf3cc5fa36379eebd3b72ee6`.
- Your [PR #12](https://github.com/adityasinghin01-hash/GoldGraft/pull/12):
  head `4ce2fdb836a8c3fd560257691078e4370752d1fd`.
- It is based on `feat/aditya-gupta-live-providers-and-recovery` and depends on
  [PR #13](https://github.com/adityasinghin01-hash/GoldGraft/pull/13), whose observed
  head is `150ad893ba0998b05593860c980e93ff1a9c04c6`.
- Your PR says no qualified PayPal recording export was available in Gupta's
  CI artifacts; current replay/certificate tests use offline fixtures.
- No completed Actions result was found for your latest head during the check.
  Recheck current statuses before treating this as still true.

Recheck actual heads/diffs first. Continue your existing owner PR without a new
integration branch or force push. You may commit/push your checked proof branch
and update its PR description. Keep the stacked-base dependency explicit.
After Gupta lands, reconcile onto current main so the final proof diff contains
your changes only; do not blindly retarget a stacked PR and present Gupta's
changes as your work. The integrator performs the final main merge.

## 2. Read these inputs before planning

1. Current AGENTS.md and `docs/engineering/START_HERE.md`.
2. `docs/START_Aditya_Singhal_proof.md`, all SH01–SH03 packages.
3. `docs/PROOF_HANDOFF.md` at your actual current revision.
4. `docs/engineering/work/SHARED_INTERFACES_AND_DEPENDENCIES.md`,
   `DONE_AND_TEST_MATRIX.md`, `VIJAY_TEAM_INPUTS_REPLY.md`, and
   `SPONSOR_UTILISATION_AND_OWNERSHIP.md`.
5. `docs/engineering/lifecycle/ATOMIC_DELIVERY_PROTOCOLS.md`,
   `OPERATIONAL_GATES.md`, and `ACCEPTANCE_CASES.md` for proof-owned requirements.
6. Actual Python contracts/registry and canonical schemas for RawCapture, CMEL,
   Contract, TargetPlan, Verdict, certificate/witnesses, artifact subjects,
   ReviewBundle, lifecycle, private/public projections and authority context.
7. `pieces/proof/*`, your actual integration helpers/replay script, existing
   proof/recording/lifecycle/projection tests, current PR diff and CI reports.

Preserve valid maths, normative rule severity and the existing deterministic
judge. Current Python wire support wins over older proposed Markdown.

## 3. FIRST create the plan, then execute it

Create `docs/engineering/work/SINGHAL_COMPLETION_PLAN_2026-11-12.md` before
product edits. Include:

- SH01–SH03 implemented/partial/missing status with exact files and evidence.
- A precise producer→record→validator→consumer matrix for every proof input and
  output, including current authority/authenticity responsibilities.
- Exact source/test changes, red tests, commands, expected results, phase gates
  and final handoff artifacts.
- A dependency table separating your unfinished code from unavailable GU/VJ
  records. State the required schema, identity, bytes/provenance and rejection
  behaviour for each missing input.
- A shared-file resolution plan. Backend upload/effect implementation belongs
  to Gupta. Preserve your previously supplied fixes as a reviewable scoped
  patch for his adoption; do not continue competing backend implementations.
- The difference between code-complete, boundary-tested, recorded-export replay,
  fixture signing and qualified live proof/certification.

Then execute the plan. Do not stop at design or announce everything complete
because a fixture passed. Finish all owned code/tests/handoff while preserving
honest held status for genuinely unavailable external verification.

## 4. Phase S1 — retain deterministic proof and close actual code gaps

1. Inventory mapper, judge, posterior, mutation, lifecycle and certificate APIs.
   Preserve sufficient implementations; fix demonstrated gaps rather than
   replacing the proof system or using model opinions as verdicts.
2. Map actual RawCapture inputs to CMEL and judge OLD/OLD_TWIN/NEW against the
   exact Contract/TargetPlan. Required flows/scenarios cannot disappear because
   they are inconvenient or their observations are missing.
3. Distinguish baseline defects, permitted deltas, unsupported behaviour and
   candidate regressions. Normative money/state rules cannot be waived because
   OLD is defective. Keep integer money/currency semantics and precise counts.
4. Keep independent executed mutation outcomes separate from supplied fixture
   answer keys. Bind guards/mutants to required rules and exact candidate/forks;
   no self-declared equivalence or survivor deletion to improve coverage.
5. Reject malformed, conflicting, duplicate or incomplete required input and
   preserve UNKNOWN/UNVERIFIED/HOLD. A high score cannot replace missing proof.

Gate: deterministic positive/negative cases pass against independent labels;
historical failures and distinct mutation denominators remain visible.

## 5. Phase S2 — exact subject, provenance and replay

1. Validate exact case/run/graft/job/scenario/variant identity using current
   record/envelope support, plus generation/fence/scope/source/package/image/
   config/runtime/origin and seed/catalog versions where required.
2. Resolve trusted collector records and authenticity through the approved
   boundary. Matching bytes prove integrity, not who observed those bytes.
   Never trust caller-selected producer names or evidence_class strings alone.
3. Bind baseline, candidate, full required scenario/mutation set and witness
   set to the same accepted subject. A changed candidate invalidates dependent
   proof; mixed versions, stale subjects and cross-case refs must hold.
4. Finish the recorded-export verifier. Verify exact sealed capture bytes and
   export identities before mapping/judging. Reject missing/swapped blobs,
   substituted JobResult, wrong run/variant/scenario, partial exports and
   truncated required sets. No proof consumer should rerun a payment to replay it.
5. The existing replay layout is `job-spec.json`, `job-result.json`,
   `contract.json`, `target-plan.json` and content-addressed `blobs/`.
   Reconcile that layout with Gupta's actual export, then document the exact
   accepted format and invocation. Do not invent unsupported metadata fields.
6. A recorded export may contain fixtures. Do not promote it automatically to
   real-payment, isolation-qualified, merchant-certified or delivered evidence.
   Preserve origin/evidence class and qualification limitations after reopening.
7. Where current wire cannot honestly carry a required binding, follow the
   accepted shared-format/version process and document the exact gap. Do not
   fabricate Git/workflow/SHA values for local or E2B execution.

Gate: real input/consumer compatibility is demonstrated for the available
records; missing external producer evidence is identified separately. All
substitution, incomplete-set, stale and reopening negatives pass.

## 6. Phase S3 — private/public views and evidence retrieval

1. Finish the proof-side adapter using actual host-supplied current case access
   and authenticated evidence records. The backend owns authentication and
   grants; your code must enforce its boundary, not implement a second identity
   system or trust email/actor headers as authority.
2. Authorise BEFORE loading private evidence. Test missing, wrong-case,
   wrong-tenant and revoked access with a load counter that stays zero. Recheck
   current access at disclosure where a long operation could outlive its grant.
3. Validate payload digests, subject identity, completeness and producer trust
   before review. Missing/invalid critical evidence produces HOLD; noncritical
   gaps preserve the required partial status. Do not silently erase requirements.
4. Private output retains required diagnostics behind current access control.
   Public output contains only the approved aggregate schema/reason codes and
   explicitly permitted public refs. No raw captures, customer/transaction IDs,
   private check names, secrets or internal evidence refs may escape.
5. Public availability requires its actual publication/consent policy; a guessed
   case URL is not blanket permission. Use safe cache policy for private data.
6. Finish SH-owned Elastic exact-subject retrieval/query/result validation where
   access exists, consuming Gupta's redacted ingestion and ACL boundary. Test
   stale/missing index, revoked/cross-case access and canonical-artifact drilldown.
   Search is derived evidence, never the proof/state authority.
7. Supply safe proof/evidence/aggregate projection data and negatives for
   Postman and Claude's AG Grid/Bryntum consumers. Do not implement the UI or
   Gupta's ingestion/control mechanism. Keep optional vendor failure explicit.

Gate: actual projection/retrieval functions pass denied/stale/tamper/privacy
tests with exact denominators and truthful unknowns. Unavailable external
search qualification stays marked; a formatter is not a working search service.

## 7. Phase S4 — certificate issuance and independent verification

1. Enforce eligibility from complete ledger-backed evidence for the exact final
   subject. Require the specified smoke/full proof and coverage. Fixture-only,
   missing, stale, failed or unknown mandatory evidence must prevent issuance.
2. Derive the complete eligible PayPal witness set from canonical evidence.
   Before signing, re-fetch every required witness through the authorised
   account/app/environment-scoped read client and validate the required economic
   and origin bindings. A convenient single order/capture is not the whole set.
3. During verification, require exactly the signed/ledger-backed witness set.
   Reject missing, altered, duplicated/substituted or foreign witnesses before
   contacting PayPal wherever the inconsistency is locally decidable.
4. Validate signature, trusted signer/workflow identity and revision, ledger
   chain/root, subject and re-fetched facts. Do not accept an arbitrary caller's
   signer identity or a valid signature on an ineligible proof bundle.
5. Never fill required GitHub provenance with invented values for non-Git/local
   jobs. Unsupported signing/provenance profiles must be held or go through the
   explicit approved format process.
6. Preserve the existing successful fixture-signing/tamper demonstration as
   fixture evidence. It does not issue a merchant certificate. A real signing
   or transparency-log publication needs its actual permitted workflow/scope;
   do not publish private payloads or alter account grants to manufacture proof.
7. Test wrong amount/currency/account/environment, wrong image/config/run,
   missing callbacks/required flow, unsigned fixture, tampered ledger/payload,
   incomplete witness set, remote lookup failure and stale authorisation.
8. Verification reads do not authorise a charge, capture, refund or any other
   financial effect. Do not implement Gupta's transport or Vijay's recordings.

Gate: issuance and verification are fail-closed and reproduce from a saved
exact-subject bundle. Label real signer/provider checks only if actually run
with proper authority; otherwise record the precise held prerequisite.

## 8. Phase S5 — integration tests and deliverables

Use Python 3.12 and locked dependencies; inspect the current test/CLI names
before running. These entry points are present in the observed proof branch:

```sh
uv sync --locked
uv run --locked python -m scripts.demo_proof
GOLDGRAFT_PROOF=pieces.proof.proof:Proof uv run --locked pytest -q plugtests/test_proof.py plugtests/test_proof_rules.py plugtests/test_proof_posterior.py plugtests/test_proof_certificate.py plugtests/test_lifecycle_evidence.py plugtests/test_evidence_api.py plugtests/test_recorded_proof.py
php --version
GOLDGRAFT_PROOF=pieces.proof.proof:Proof GOLDGRAFT_PHP=php uv run --locked pytest -q plugtests/test_proof_mutations.py
uv run --locked python -m scripts.replay_recorded_proof --help
GOLDGRAFT_PROOF=pieces.proof.proof:Proof GOLDGRAFT_API_APP=integration.app:create_app uv run --locked pytest -q
uv run --locked python scripts/check_spec_coverage.py
bash scripts/check_generated.sh
npm run check:types
git diff --check
```

The replay CLI accepts a positional export directory; `--help` creates no live
provider action. Run the actual validated export path only after inspecting its
manifest and provenance. No placeholder path is evidence of a successful replay.
PHP-dependent tests must execute for that claim; missing PHP is not a green gate.
Ordinary tests make zero network calls and use clearly labelled substitutes.
Add new meaningful negatives for remaining gaps. Lint/format your owned files
only. Do not update unrelated goldens or weaken independent expectations.

Write `docs/SINGHAL_INTEGRATION_READY_2026-11-12.md` containing:

- Exact commit/PR, dependency revision and tested main/base.
- SH01–SH03 results with commands, counts, failures, evidence classes and limits.
- Exact mapper/judge/review/certificate imports and callable signatures; one
  minimal valid offline invocation and representative rejected input.
- The source→capture→CMEL→verdict→review→certificate consumer sequence, current
  schemas, required bindings and safe private/public projection boundary.
- A recorded-export specification and independently reopened replay result.
- All GU/VJ inputs required for live verification: exact schema/layout, source
  and subject bindings, authenticity/witness requirements, allowed lookup scope
  and the expected hold when missing. Include a valid labelled contract sample.
- Separate status for owned component code, actual counterpart compatibility,
  fixture signing, real signing, real witness re-fetch and merchant eligibility.
- A proof-only changed-file list and shared backend fixes handed to Gupta, so
  the integrator does not overwrite either owner's work.

Push the checked owner PR revision and obtain fresh CI on that exact head. Return
the handoff, exact integration command and one current mergeable proof delta.
If the stacked base cannot be flattened until Gupta merges, finish your own
work and state that Git dependency explicitly instead of editing Gupta's code.

## 9. How to be independent without making false completion claims

Finish all proof algorithms, adapters, rejection paths, replay tooling, offline
tests and docs using valid labelled existing fixtures and any available qualified
recordings. Missing producer data is not a reason to leave these unfinished.

You cannot manufacture the missing live acceptance evidence. If GU/VJ captures,
current authority, signer scope or provider-read access are absent, return
component-ready plus an exact live-verification blocker. Do not describe the
whole merchant proof as complete. An integrator should be able to connect the
documented records and either obtain a verified result or the correct typed hold,
without rewriting your component or guessing a private invocation.

Pieces import only contracts/foundation across boundaries; root integration may
compose them. New shared shapes follow `docs/FORMAT_CHANGES.md`, approved schema
versioning, generated exports and compatibility fixtures. Preserve frozen inputs.
No new accounts, external messages, unapproved live signing/payments/deployments,
private-data transfers or budget/grant changes. Never print/copy/hash API keys,
the model signing key or a Zapier URL. Do not touch the shared live cost ledger.
