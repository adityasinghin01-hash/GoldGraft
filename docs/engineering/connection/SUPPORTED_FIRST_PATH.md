> Reviewed team baseline, 6 November 2026: this connection proposal is subject to the review addendum, implementation bridge and lifecycle atomic protocols linked from [engineering START](../START_HERE.md). Earlier programme status/owner restrictions in this frozen source are historical. No current API/implemented capability is created by this text.

# First supported user, shop and runtime

Status: paper engineering specification, 6 November 2026. Nothing here is a deployed feature or current API unless explicitly labelled CURRENT. Proposed components/interfaces require later implementation and contract approval. Plan 1 ends at verified first sandbox operation; agent internals and Plans 2–6 remain outside scope.

Decision T01: beneficiary is a code-owning merchant; primary initiator is a nontechnical owner who knows the shop URL. Source/host maintainer may be a different person and contributes in the same case. The requester need not know GitHub, image digests or PayPal credentials. Controller authority and permitted recipients must be independently established.

Decision T02: first engineering reference is the existing Cutover MIT `legacy-php-shop`, source pin `aedc11dde1a8793285665ca2188aff62ab5aab65`. Current Dockerfile uses `php:8.3-apache`; future qualified image must pin linux/amd64 base digest, OS packages and source manifest. Mutable historical base tag is not an approved runtime digest. Existing compose is input, not a Render deployment file. Data is a flat-file store (`data/orders.json`), not MySQL. Writable data/IPN log paths must be isolated from code.

First host is Render, explicitly selected by Aditya. First qualified deployment form is an image-backed Render web service using a digest, with source-to-image provenance available. This does not mean an existing Git-backed service is silently migrated. Git-backed services without retrievable artifact identity remain Setup needed for this initial adapter; future support requires a separate capability qualification.

Required full stated one-time-payment sandbox scope: create/approve/capture/return/cancel; pending/declined; duplicate submit; full refund/repeated-refund protection; IPN/webhook authenticity and duplicate handling; persisted order/payment correspondence. Existing fixture scenarios are evidence-design inputs, not observed provider behaviour. Existing sample has unauthenticated order/refund helpers and floating arithmetic; do not expose it as a production merchant shop or treat current code as safe. Its USD fixture scope does not establish multicurrency handling.

No support claim for subscriptions/billing-agreement migration, historical live transaction continuity, live merchant credentials, externally owned checkout, arbitrary PHP/framework versions, host-only/local source or multicomponent enterprise commerce. A merchant requiring these is not served by this first scope; never label its complete upgrade Ready. Zen Cart remains a historical target, not interchangeable with this plain-PHP reference.

Preparation prerequisites for the later reference build: sandbox-only identities; protected lab access; trusted gateway for callbacks; no public unauthenticated order helper; qualified source/image/runtime marker; separate synthetic seed. Creating these is future implementation, not completed or assigned to Vijay.

## Distinct source identities
The inspected reference source is in GoldGraft repo at `05b5b3beb37a2ac4b242c9ff0cb34f387f200e9f`, application/build root `fixtures/shops/legacy-php-shop/`, served source `src/`. Upstream Cutover `aedc11dde1a8793285665ca2188aff62ab5aab65` identifies vendored provenance, not the running GoldGraft repo deployment commit. Future qualification of protected helpers/runtime identity and image pinning will necessarily create a different approved build revision; its actual commit/image digest must be recorded then, never invented here. No GoldGraft branch/repository is written to obtain it during Plan1.

## Scope clarification
The service architecture is multi-provider. This file selects only the first reference combination; Render is not a required merchant hosting provider and merchants are not required to migrate there. Required components can be split across hosts. Unimplemented adapters remain visible setup dependencies, not proof the product only serves Render or proof all providers work. See CONNECTOR_EXTENSIBILITY_SPEC.md.

## Product scope versus first route
Non-Git source is a required product design case, not dismissed as rare. GitHub/Render PHP remains the first implementation reference only. Alternative source paths, authority limits and future qualification requirements are specified in FIXED_JOURNEY_AND_SOURCE_ROUTES.md. No merchant must move code to GitHub to fit the product direction; unqualified routes remain explicit setup dependencies.
