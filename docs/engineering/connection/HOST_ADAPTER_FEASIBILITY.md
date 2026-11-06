> Reviewed team baseline, 6 November 2026: this connection proposal is subject to the review addendum, implementation bridge and lifecycle atomic protocols linked from [engineering START](../START_HERE.md). Earlier programme status/owner restrictions in this frozen source are historical. No current API/implemented capability is created by this text.

# Render adapter selection and exact boundary

Status: paper engineering specification, 6 November 2026. Nothing here is a deployed feature or current API unless explicitly labelled CURRENT. Proposed components/interfaces require later implementation and contract approval. Plan 1 ends at verified first sandbox operation; agent internals and Plans 2–6 remain outside scope.

Decision T03: Render selected by Aditya; AWS/Fly are not selected. User reports an existing Render account. Account existence is not scoped-key entitlement or shop deployment proof.

## Provider access design
Use Render scoped API keys, not classic creator-wide keys. Official documentation says scoped keys are early access, scoped to a workspace, with Services and Deploys read access and separately controllable secret access. Request: Services configuration read; Deploys read; Workspaces members read for controller-role verification; Projects read only if environment metadata cannot be obtained otherwise. Deny environment/secret values, monitoring/logs, environment groups, database credentials/exports, object downloads, workflows/sandbox execution, deploy Run, service writes, workspace writes and other unrelated resources. Members read necessarily exposes private workspace member metadata to the trusted authority service; minimise to matching controller record, never expose list to requester/model. Exact capability qualification must confirm custom-domain GET availability under these grants.

The provider grant is workspace-level; do not call it selected-service-only. GoldGraft selects one service and its broker rejects all other service IDs. For a strict first reference, use a dedicated workspace with only the authorised shop resources; otherwise disclose and require approval for workspace-wide metadata read or hold. Do not weaken the agreed boundary invisibly.

No documented end-user OAuth installation flow was established for this adapter. Initial supported controller path: remain in saved case → open official Render Account Settings → create named scoped key with displayed minimum permissions → submit once into a dedicated secret intake field → clear browser field → vault only → list permitted service metadata → controller chooses service/environment and explicitly binds recipients. No terminal commands, ZIP or password collection. This one-time provider key step is necessary friction, not automatic sign-in. A connector broker having only GET code does not make a classic write-capable key genuinely read-only.

## Exact read endpoints (CURRENT provider API, not GoldGraft routes)
- GET https://api.render.com/v1/services: bounded pages and owner filter, private server-side selection only.
- GET /v1/services/{serviceId}: selected service configuration, ownerId/environmentId/type/rootDir/serviceDetails; allowlisted projection only.
- GET /v1/services/{serviceId}/deploys and /deploys/{deployId}: identify current successful live deployment; never merely newest build or recently started deploy.
- GET /v1/services/{serviceId}/custom-domains: configured domain relationship; no verify action.
- Denied even though GET: /env-vars, secret files, deploy hooks, logs/exports and other sensitive reads. HTTP method is not sufficient authority.

The downloaded public OpenAPI `deploy` shape has `image.ref` and `image.sha` for image-backed deployments, and `commit.id` for Git-backed deployments. Local metadata extract and whole-download digest are in evidence/RENDER_API_EXTRACT.json. Field presence is not guaranteed in every response. Missing image SHA/current-live identity blocks correspondence. No presumed current-byte fingerprint from commit alone.

## No-mutation qualification protocol, future only
Inspect official scoped-key UI/permissions with an authorised controller; record resource class grants without saving key values. Use read endpoints against a disposable authorised reference. Prove denied writes on disposable resources only, with explicit mutation-test authority: never send a destructive request to a merchant merely hoping for 403. Likewise prove secret GET denied with synthetic canary values. Verify expiry/revoke/role downgrade behaviour and cross-service broker denial. No such tests occurred here.

## Gate H1
Live entitlement, exact endpoint coverage, credential assurance and image/current-runtime chain remain open. If scoped access is absent: show Setup needed; do not accept a classic key; preserve case; controller may separately request early access. If image-backed service/provenance is absent: no full readiness. Selection and protocol are concrete; general live feasibility remains conditional.

Sources: [Scoped key capabilities](https://render.com/docs/scoped-api-keys), [public API](https://render.com/docs/api), [prebuilt image deployment](https://render.com/docs/deploying-an-image), [OpenAPI](https://api-docs.render.com/openapi/render-public-api-1.json). Provider docs are current evidence of documented facilities, not this account's access. Future beta changes require requalification.

## Controller proof, not key possession
Before disclosing host evidence, GET /v1/users identifies the key-associated user; GET /v1/owners/{ownerId} fixes workspace identity; GET /v1/owners/{ownerId}/members verifies active ADMIN role for that user. Require the independently authenticated GoldGraft contact to verify the same provider-reported email (or separately link that identity with an email challenge); do not equate a supplied email to verification. Role may be stricter than Developer intentionally for initial relationship disclosure. Personal/default workspace role semantics must be qualified; if ADMIN membership cannot be proved, hold. Workspaces Read is required, not write. Fresh role check before Start; downgrade/revoke invalidates. A user possessing another person's key but not that independently authenticated identity cannot approve. Controller then explicitly approves requester/shop/service/env/recipients. Sources: [authenticated user](https://api-docs.render.com/reference/get-user), [workspace members](https://api-docs.render.com/reference/retrieve-owner-members).

Key assurance: no documented scope-introspection endpoint was established. Qualification must prove how effective scope configuration can be authenticated/currently verified on the selected beta version (provider-supported metadata or validated controller setup plus denial evidence under authorised disposable tests). Never infer read-only from key syntax or successful reads. Until this evidence exists, mark grant unqualified and block live use. This is a live provider-assurance gate, not permission to accept classic keys.
