# Surveyor model access — GitHub inspection and offline preparation

10 November 2026. User confirmed the $20 cap covers the complete thirteen-agent
project's API work, including calibration, evaluation, retries, regression and
demos. It is not $20 per role. First cumulative checkpoint $5; reviewed approved
increases to $10/$15/$20; project target $15 and absolute ceiling $20. Nothing in
this report enables paid dispatch or replaces GU's accounting authority.

## Current GitHub evidence

Read-only `gh api` inspection found main at
`0365c5e1adcb1875a7f72c99dc7c63631501e131`. Gupta's backend branch
`faed52d3794630ecb73b2ec66aca4aa1122b5a54` is four commits behind main;
the integration branch `e14e7de017f46103f89b4db27f11e3afe10763f2` is three
behind. Neither has newer ahead commits. PRs4/5 are already merged. No source
fetch/merge/reset/staging/push or teammate message was performed.

GitHub's exact blob IDs for app.py, custody_broker.py, lifecycle.py and
container_runner.py match the inspected local bytes, independently recomputed
using Git's blob hash framing. The custody implementation stores credentials in
an in-memory dictionary; the runner reads saved capture fixtures. No qualified
Anthropic ModelPort, pinned inference profile, tokenizer/pricing calibration or
durable cumulative model-cost reservation/reconciliation mechanism was found in
the published GU code inspected. A title saying GU01–GU05 is not qualification.

Sources:
- [Merged GU PR4](https://github.com/adityasinghin01-hash/GoldGraft/pull/4)
- [Merged integration PR5](https://github.com/adityasinghin01-hash/GoldGraft/pull/5)
- [Pinned custody source](https://github.com/adityasinghin01-hash/GoldGraft/blob/0365c5e1adcb1875a7f72c99dc7c63631501e131/pieces/backend/custody_broker.py)
- [Pinned runner source](https://github.com/adityasinghin01-hash/GoldGraft/blob/0365c5e1adcb1875a7f72c99dc7c63631501e131/pieces/runner/container_runner.py)

Private evidence: `/Users/aditya/reports/goldgraft-b4-surveyor-20261110/github/`
contains branch/PR metadata and verified_source_blobs.json. A transient sandbox
network failure was retried read-only through the normal escalation mechanism;
the successful metadata was saved. This inspection says nothing about another
person's unpushed work or separately hosted private service.

## Own preparation completed

`pieces/agents/model_readiness.py` adds a read-only doctor diagnostic: SDK package
version, key presence without value, all-project budget scope, current $5
checkpoint, $15 target, $20 maximum and missing qualifications. It does not import
an inference client, contact a provider, install dependencies, authenticate a
broker, reserve money or accept a profile. Service mode remains refused even
with ANTHROPIC_API_KEY present. The report is not a durable budget ledger.

`pieces/agents/evals/surveyor_cases.json` supplies the four source-inventory cases
from the planned larger evaluation: NVP create/capture/refund, browser/IPN,
changed layout/Unicode/untrusted instructions, and no known payment indicators.
Sources are new synthetic MIT project snippets. Each has hand-labelled locations
and expected flows, independent of Surveyor's detector and scripted final fixture.
`evals/surveyor.py` validates those labels and checks RootMap artifact content.
An empty indicator list is not proof of absence of dynamic payment integrations.

The scorer grades only artifact quality. It does not authenticate artifacts or
broker receipts, prove zero effects, evaluate real injection resistance, grade
runtime/site/account behaviour or replace the runtime's mandatory safety tests.
Its tests use reference and mutated artifacts, not paid or simulated inference
scores. The real-model four-case results and all three repeats remain NOT RUN.
No actual model was chosen, trained, installed or invoked.

## Checks and next owner action

12 new tests passed for diagnostic/redaction/service refusal and independent
checker behaviour. Full offline regression: **2,222 passed**, one pre-existing
TestClient/httpx deprecation warning. Ruff passed. Exact commands, durations,
statuses and output hashes are in private checks/15-preflight-checkers.json,
16-preflight-full.json, 17-preflight-lint.json and 18-preflight-doctor.json.

GU must supply a reviewed ModelPort.turn/reconcile implementation and processing/
custody profile with authenticated evidence, not merely a credentials store.
Its broker must pin the official Anthropic Python client with hidden retries
disabled, exact allowed model/pricing/tokenizer and processing scope, and retain
turn identities and billed-unknown outcomes across restart. Before each call it
must atomically reserve against **spent + outstanding + unknown** across all
thirteen agents and every API check, under the active cumulative cap. Local
ModelBudget shape validation does not establish these mechanisms.

Singh then adapts and evaluates Surveyor through the approved ports on synthetic
licensed data, with an independently specified calculated trial under $5. Shared
changes require the existing frozen-input pause/revision protocol; none were made
here. No ad hoc direct-client route, framework change, provider/model upgrade or
reimplementation of GU mechanisms was added.

Only after that profile qualifies should Aditya configure ANTHROPIC_API_KEY in
the local server environment or approved GU secret store; never paste it in
chat. Key presence does not prove entitlement, terms or budget controls. Current
actual model calls/spend remain **0 / $0**, and paid checks remain **NOT RUN**.

Interpretation of user's “124”: steps1/2/4 in the preceding message. Step1's
read-only inspection and own offline preparation are complete; qualification
itself is blocked on the missing GU counterpart. Step2 awaits local configuration
at the qualified boundary. Step4's model-driven improvements require observations
from step3 and cannot be scored or claimed in advance. Surveyor remains the only
B4 role constructed; Herald is not started.
