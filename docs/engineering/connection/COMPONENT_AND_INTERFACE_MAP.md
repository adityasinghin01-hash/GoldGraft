> Reviewed team baseline, 6 November 2026: this connection proposal is subject to the review addendum, implementation bridge and lifecycle atomic protocols linked from [engineering START](../START_HERE.md). Earlier programme status/owner restrictions in this frozen source are historical. No current API/implemented capability is created by this text.

# Components and proposed file map

Status: paper engineering specification, 6 November 2026. Nothing here is a deployed feature or current API unless explicitly labelled CURRENT. Proposed components/interfaces require later implementation and contract approval. Plan 1 ends at verified first sandbox operation; agent internals and Plans 2–6 remain outside scope.

Every target below is PROPOSED except listed inspection anchors. A new connector piece is a proposed repo-guidance/table addition requiring approval with the format change; not silently present today. Singh owns new integration work; Singhal may review evidence/fixtures. Gupta/Vijay receive no new tasks.

| Component / proposed path | Responsibility and external interface |
|---|---|
| pieces/connector/api.py + sessions.py | BFF routes, WorkOS exchange, opaque session; no repository execution. |
| pieces/connector/cases.py + authority.py | Membership, controller binding, provider roles, private projection and invitation/continuation state. |
| pieces/connector/providers/github_reader.py | Read-only selected-repo acquisition, provider callback/event verification; vault credential handle only. |
| pieces/connector/providers/render_reader.py | Scoped metadata reads, current user/admin/workspace identity, selected service/env and deploy correspondence inputs. |
| pieces/connector/acquisition.py + custody.py | Safe archive quarantine, exclusion manifests, storage region/access/expiry. |
| pieces/connector/correspondence.py | Source/provenance/image/deploy/runtime/config chain; required facts versus limits. |
| pieces/connector/readiness.py | Deterministic preflight predicate and invalidation; no model/shop execution. |
| pieces/connector/acceptance.py + cancellation.py | Durable actions/receipts/tombstones, transaction/outbox and actor-authorised status. |
| pieces/connector/dispatch.py + worker_evidence.py | Job/generation lease and external assignment/operation receipt; no agent orchestration. |
| pieces/connector/brokers/{source,dependency,payment,model,evidence}.py | Typed least-authority boundary; no arbitrary credential/URL/tool proxy. |
| pieces/connector/adapters/runner_http.py | Proposed authenticated downstream execution adapter; reuse JobSpec/Result only where semantics fit, separate supervisor operation receipt. |
| pieces/connector/storage.py + migrations/001_connection.sql | Postgres repositories/locking, immutable bindings, outbox and encrypted credential handles. No runtime secret values in migration. |
| pieces/web/src/connection/* | Future saved-case UI/copy/status/Details; existing frontend layout must be reconciled before build; no frontend files changed. |
| contracts/src/goldgraft_contracts/connection_control.py + connection_routes.py | Proposed authoritative formats/routes, Python validation. |
| fakes/src/goldgraft_fakes/connection_control.py | Offline fixture-based case/provider/queue/worker stand-ins, clearly synthetic; no network. |
| plugtests/test_connection_*.py; pieces/connector/tests/* | Independent boundary conformance, state/race/security checks. Live scripts scripts/live_connection_*.py separate and opt-in. |

CURRENT foundation ledger/tracker may store validated new artifacts only after explicit integration review. Existing tracker can discard timed-out worker returns but cannot kill arbitrary sync code; do not adopt its semantics as actual termination. Downstream backend adapter requires proposed service identity/scope enforcement and idempotent dispatch; no undocumented v1 fallback. Full agent work and later proof/publish/deploy outcomes remain opaque external responsibilities outside Plan 1.

## Provider-independent additions (proposed)
`pieces/connector/providers/base.py` / `registry.py` define the shared capability/connection/revalidation protocol and approved provider registry; `pieces/connector/resource_graph.py` resolves source/frontend/backend/data/callback dependencies. Proposed `contracts/src/goldgraft_contracts/connector_adapters.py` owns shared adapter/resource/evidence formats. GitHub and Render implementations plug into this protocol; neither is hard-coded into case identity or Start. See CONNECTOR_EXTENSIBILITY_SPEC.md.
