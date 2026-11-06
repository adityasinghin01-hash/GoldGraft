> Reviewed team baseline, 6 November 2026: this connection proposal is subject to the review addendum, implementation bridge and lifecycle atomic protocols linked from [engineering START](../START_HERE.md). Earlier programme status/owner restrictions in this frozen source are historical. No current API/implemented capability is created by this text.

# Decision ledger

Status: paper engineering specification, 6 November 2026. Nothing here is a deployed feature or current API unless explicitly labelled CURRENT. Proposed components/interfaces require later implementation and contract approval. Plan 1 ends at verified first sandbox operation; agent internals and Plans 2–6 remain outside scope.

| Decision | Selected design, rejected alternative and reopen condition |
|---|---|
| T01 operator | URL-only owner initiates; actual controllers contribute within same case. Do not require every owner to be a developer. Reopen on observed target-user evidence. |
| T02 reference | Existing pinned Cutover plain PHP, PHP 8.3/Apache, flat-file synthetic data, one-time USD sandbox loop. Not Zen Cart/all PHP/full subscriptions. Qualification must pin base/packages and protect sample helpers before hosting. |
| T03 host | Render explicitly chosen by Aditya. Scoped workspace Services/Deploys/Workspaces reads, secrets denied; image-backed digest path. Classic key/automatic inferred OAuth rejected. Beta availability/endpoint and controller proof qualification are release gates. |
| T04 identity | WorkOS AuthKit Magic Auth code + opaque BFF session; separate GitHub/Render controller identity/role. Email-link-only rejected due scanner reliability. Provider account and session conformance gates open. |
| T05 source | Dedicated selected-repo GitHub Reader read only, separate Publisher later. No hidden writes or ambient PAT. Read authority and explicit relation approval both needed. |
| T06 custody | Trusted bounded archive → quarantine → manifest/exclusion → isolated snapshot. No repo execution/history/data dump. Missing essential excluded code/config holds. |
| T07 match | Verified build provenance + Render actual image SHA/current live deploy + trusted runtime challenge/config chain, with stated assumptions. Commit label/HTML/DNS alone rejected. Runtime wrapper/provenance absent today. |
| T08 processing | Anthropic commercial Messages gateway, eligible model/account ZDR required, no consumer/files/tools/fallback. Model/region/terms remain account qualification inputs, not guarantees. |
| T09 isolation | E2B per-job Firecracker managed VM, deny default egress except typed brokers. Container-only fallback rejected. Vendor/network/retention/escape tests required. |
| T10 preflight | Deterministic static intake only; model inference/executable shop work after Start. Fixture readiness separate from actual payment proof. |
| T11 persistence | PostgreSQL 18 transaction/outbox, service-owned polling lease/fence. No new Redis/queue dependency initially. At-least-once dispatch with external dedupe/reconciliation, no external exactly-once claim. |
| T12 evidence | Current authenticated supervisor BaselineRead verified against accepted manifest is initial operation evidence; lease alone not Started. Model inference requires separate gateway evidence before stronger claim. |
| T14 operations | Render API + worker + managed Postgres, S3/KMS/Secrets Manager, service-scoped AWS OIDC, external Ed25519 receipt signer. Plan/region/term qualification required; no broad static-key fallback. See SERVICE_AND_STORAGE_SPEC.md. |
| T13 integration | Additive proposed /v2 connection namespace + new shared formats/new connector piece; legacy Start protected or disabled. Types/fakes/fixtures migrate together. |

Costs/availability: no free-tier sufficiency assumed. Render scoped beta, image hosting/persistent data, WorkOS identity, managed Postgres/storage/KMS, E2B and model usage require then-current entitlement/quota/billing checks before provisioning. No spend or account change authorised by this paper. Operational owner Singh must set budget and maintenance policy; unset budget blocks readiness. No latency estimate or deadline invented.

Provider evidence and limits are linked from focused specs and SOURCE_REGISTER.md. Paper-selected technology is not an installed dependency or real service. Beta/API/model changes reopen relevant qualification, policy binding and acceptance fixtures. No technical choice here determines internal agent prompts/topology/algorithms.

## T15 — Provider-independent resource graph
Latest user clarification: GoldGraft must be extensible across source/hosting locations. Select common adapter/capability contracts and complete per-case resource graph; Render is first reference only. Reject hard-coded single-host readiness or claims of 70%/universal tested coverage. Require adapter-swap/split-host conformance tests and second real qualified provider before demonstrating multi-host operation. No new provider/account build authorised here.

## T16 — Stable journey; variable source location
Keep Enter shop, Sign in, Controller permission, Connect code, Connect running components, Prepare, Review/Start and verified progress stable. GitHub default is replaceable; non-Git source uses typed snapshots. Local browser folder read/upload avoids mandatory ZIP/install/terminal. Cloud direct integration only after narrow genuine read-only authority; provider-native transfer/local folder selection is conditional fallback. Owner-no-code routes to maintainer; no source/controller means honest hold, not backend reconstruction from public site. Broad coverage is a validation target.

## T17 — Deliver the working site, not an unfinished artifact
Full product outcome is a verified upgraded website that remains operational after GoldGraft disengages. Plan1 supplies complete declared WorkPackage/correspondence and safe Start handoff; Plan3 must engineer unchanged baseline reproduction, isolated modifications, authorised deployment/state continuity and successful exit. No source-copy/test-run alone proves website matching. Earlier current-controller merge rule is preserved; any automation change is a labelled separately authorised proposal, not implied new rights. See ../../DELIVERY_REQUIREMENTS_UPDATE.md.

## T18 — Closure consistency fixes
Canonical connection-control proposal replaces stale single-host/Git-only draft assumptions. WorkPackage/resource graph is common to all source routes. Persist pre-Start ActionIntent; cancellation can precede work/generation allocation. Immutable acceptance and current status are separate. Do not infer reproduction/model/payment completion from first baseline read. Existing current contracts remain unchanged.
