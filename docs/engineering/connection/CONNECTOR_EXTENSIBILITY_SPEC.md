> Reviewed team baseline, 6 November 2026: this connection proposal is subject to the review addendum, implementation bridge and lifecycle atomic protocols linked from [engineering START](../START_HERE.md). Earlier programme status/owner restrictions in this frozen source are historical. No current API/implemented capability is created by this text.

# Provider-independent connector architecture

User clarification: GoldGraft is a connection service intended to connect across source locations, hosting providers and split application environments. Render is the first reference adapter, not the product boundary or a 70% coverage claim. This amendment supersedes Render-specific assumptions in the common connection model. No additional live adapter has been built or qualified.

## Common case; replaceable adapters
One saved case owns a resource graph, not a single hosting slot. Nodes represent source repositories, frontend deployments, backend services, databases/configuration references, notification endpoints and environments. Edges describe builds-from, routes-to, stores-state-in and receives-callbacks-for. Each node has its own current controller grant, private-data recipients, provider/native immutable ID, environment, scope and evidence age. Different people and providers can control different nodes. A GitHub repo is source, not hosting; a Render frontend is not proof the backend is connected.

Core services consume typed capabilities/evidence rather than branching on provider names. Provider registration is a deployment-approved allowlist; a user-supplied provider URL cannot install an adapter or choose a token endpoint. Adapters translate provider-native IDs, consent/callback/key mechanisms and observations into the common contract. Do not force an API-key provider into fictional OAuth or discard stronger provider authority checks to make one uniform screen.

PROPOSED adapter protocol, not existing code:
- describe_capabilities(adapter_version) -> source-read / deployment-read / artifact-identity / route-read / effective-config-evidence / controller-role / revocation-observation capabilities, limitations and qualification reference.
- begin_connection(case_id, actor_id, contribution_id) -> provider-owned consent, scoped-key setup, controller handoff or unsupported result; never generic password/admin collection.
- verify_connection(bound_continuation, credential_handle) -> provider principal, exact granted scope, immutable resource identities, current role evidence and grant epoch. Possession alone cannot approve disclosure.
- enumerate_authorised_resources(connection_ref, cursor) -> private controller-only resource candidates; no unrelated findings disclosed to requester.
- acquire_source(resource_binding, revision, policy) -> trusted bounded source manifest where this adapter supports source; hosting adapters need not acquire source.
- inspect_environment(resource_binding) -> typed deployment/artifact/routing/config evidence with observed/provider-reported/attested distinctions and explicit missing links.
- revalidate(resource_bindings, evidence_versions) -> current, changed, revoked, unavailable or unknown per resource, never a silent global pass.
- disconnect(connection_ref) -> local denial plus separate provider acknowledgement/pending/unsupported state. No assumption all providers support programmatic revoke.

Each call receives authenticated service context and checks current case/actor/resource/scope/generation. No arbitrary HTTP proxy, remote execution or remote writes follows from a capability name. Every provider's credential and network path remains brokered. Initial grants must remain genuinely read-only. Later publication adapters are separate and must check deployment/CI side effects before any write.

## Capability-driven readiness
Resolve the whole required resource graph. Every required source-to-running-component edge needs its own correspondence chain, and each actor/recipient binding must be approved. All required nodes/edges must pass current readiness; optional or unsupported must be visible. If frontend is connected but backend/notification/data dependencies are missing, show those missing components and hold full Start. Provider-specific evidence can differ; minimum proof requirements cannot be downgraded to fit a weaker adapter. Adding a new provider should require a new adapter, qualification profile and fixtures, not a new case identity/Start/cancellation protocol or a copied UI journey.

## How to demonstrate the claim later
1. Offline architecture proof: run the same case/readiness/Start conformance suite with the Render stand-in and a distinctly shaped synthetic second-provider stand-in. Change only adapter registration/configuration. Demonstrate split frontend/backend providers, separate controllers, partial capability, drift and revocation. Label this simulated extensibility, not a real second integration.
2. Real connection proof: qualify Render on authorised resources, then qualify a second independently implemented named host through its real permission/controller/artifact/runtime flow. The second provider requires targeted selection/research; no implementation or live support claimed here. Capture resource graph and evidence without exposing secrets. A second live adapter is required before claiming demonstrated multi-host operation.
3. Coverage register: list each source/host/runtime combination as proposed, implemented, account-tested, correspondence-qualified and end-to-end-tested separately. Include exact versions, limitations and unsupported combinations. No “connects to everything” availability badge from architecture or two examples.

Product wording: “GoldGraft connects your shop’s code and hosting through supported connectors.” Product direction: expand connectors across providers while preserving the same saved case and authority model. Render is the first reference; arbitrary-provider coverage remains a target requiring each adapter's qualification.

## Proposed build targets
contracts/src/goldgraft_contracts/connector_adapters.py: AdapterCapabilities/ResourceNode/ResourceEdge/ResourceBinding/AdapterObservation formats. pieces/connector/providers/base.py and registry.py: protocol plus approved adapter registry. pieces/connector/resource_graph.py: dependency resolution and completeness. Existing proposed github_reader.py/render_reader.py implement these boundaries. No imports between pieces. Registry is server-owned; browser sees only safe supported capability projections. New work proposals belong to Singh; Singhal may review conformance evidence. No new Gupta/Vijay work.

## Non-Git source amendment
Source acquisition must accept a proposed SourceSnapshot/1 across Git/local_folder/cloud_files/host_export, with route-specific authority/provenance and generic snapshot digest. Fixed Connect code step and complete source path design are in [FIXED_JOURNEY_AND_SOURCE_ROUTES.md](FIXED_JOURNEY_AND_SOURCE_ROUTES.md). Direct cloud-file permissions cannot be assumed genuinely read-only; unsupported grants hold or use controller-selected local files.

## Complete required context and separate proof gates
[CODE_AND_ENVIRONMENT_HANDOFF.md](CODE_AND_ENVIRONMENT_HANDOFF.md) is the concrete required-source/dependency/config/state package contract. Receiving code, proving current website correspondence and reproducing the unchanged site are separate. Static preflight cannot claim the last; executable baseline reproduction and upgrade/delivery occur after Start under the updated Plan3 requirements. Missing required components remain managed case dependencies, not silently excluded paths.
