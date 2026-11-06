> Reviewed team baseline, 6 November 2026: this connection proposal is subject to the review addendum, implementation bridge and lifecycle atomic protocols linked from [engineering START](../START_HERE.md). Earlier programme status/owner restrictions in this frozen source are historical. No current API/implemented capability is created by this text.

# Isolation and broker responsibilities

Status: paper engineering specification, 6 November 2026. Nothing here is a deployed feature or current API unless explicitly labelled CURRENT. Proposed components/interfaces require later implementation and contract approval. Plan 1 ends at verified first sandbox operation; agent internals and Plans 2–6 remain outside scope.

Decision T09: E2B managed Firecracker microVM per tenant/job as execution substrate, separate from Render merchant host and control plane. Ordinary container-only reuse and automatic unqualified GitHub Actions runner fallback rejected. Vendor docs support microVM isolation/network controls; this is not our escape/isolation validation. E2B account/DPA/region, approved template digest, termination behaviour and API version remain provisioning/qualification dependencies.

Default guest internet access must be overridden: deny all egress, allow only dedicated broker gateway, no public sandbox ingress. E2B documentation shows network control defaults; qualification must independently cover IPv4/IPv6, DNS/connect/redirect and platform management/metadata addresses. Require app-layer mTLS/capabilities as well as network rules. If deny-all plus broker-only transport cannot be enforced on selected tier, no work starts. Use no private network peering, privileged host mounts, Docker daemon socket or ambient provider credentials. Every job has fresh filesystem and synthetic data; no cross-tenant cache. Base template signed/versioned and contains prequalified PHP/runtime helpers; no merchant packages run before Start.

Brokers (all PROPOSED):
| Broker | Permitted action and forbidden capability |
|---|---|
| Source | Trusted snapshot reader bound to case/repo/commit; no Git remote writes or arbitrary URLs. Initial provider token remains read-only. |
| Dependency | After Start only, fetch pinned allowlisted hashes from fixed registries; private authenticated packages unsupported initially; no arbitrary Internet or shell proxy. |
| Sandbox payment | Known test identities/transactions, typed action allowlist; no live merchant/payment authority. Inject provider auth in trusted HTTP gateway without returning credentials. Reject attempts to reuse credential-bearing headers outside pinned sandbox routes. |
| Model | Named eligible API/model/policy, minimised payload and budget; no provider secrets in guest. |
| Evidence | Upload bounded typed blobs under exact job prefix; no public reads, sign-key retrieval or arbitrary store path. |
| Runtime lifecycle | Trusted controller creates/stops VM and checks termination; guest cannot create/reconfigure VMs or renew its own authority. |

PayPal broker must transparently preserve actual NVP/REST request/authentication semantics and test-account identity; it cannot fake provider responses and call them authenticated proof. Qualification compares expected credential path against real sandbox requests after separate authorisation. Unsupported auth pattern stops affected proof. Token-bearing responses stay inside scoped untrusted fixture context with redacted evidence, never reusable merchant secrets.

Initial limits (policy, unmeasured): 2 concurrent jobs per tenant; 30min per VM allocation including setup; 60s broker request timeout; dependency fetch 5min cap; 100MiB diagnostic artifacts; model spend cap configured explicitly by service operator before Ready (unset means hold, no invented free tier). Worker renews limited lease from controller, never beyond acquisition TTL or cancellation. Stop first fences new broker actions, then termination API; report pending until external acknowledgement/reconciliation.

Trusted supervisor captures first baseline manifest verification outside shop-controlled process. SERVICE_AND_STORAGE_SPEC.md fixes trusted management-channel ordering before untrusted shop/model execution and keeps receipt signing outside the VM. Service verifies receipt identity/channel and manifest digest. Guest stdout claiming “started” is not authoritative. Pre-Start may inspect prequalified template inventory/capacity, not create merchant-source execution. OS patching, signed images and escape testing are operational obligations.

Sources: [E2B isolation](https://docs.e2b.dev/faq/security-and-compliance), [network defaults/control](https://docs.e2b.dev/network/internet-access). Vendor certification is not application conformance. Region/retention evidence must be retrieved before private-source transfer.
