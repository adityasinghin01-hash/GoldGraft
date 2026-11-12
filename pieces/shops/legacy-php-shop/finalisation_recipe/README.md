# VJ04 merchant-owned final runtime domain recipe

12 November continuation: `../candidate/` now provides a separate local NEW domain implementation with durable origin/operation state, resource re-fetch and process-restart checks without temporary transport. This supersedes the older "no modern replacement" statement at the bottom of this historical recipe. It does not qualify a merchant runtime, old-state migration, callback ownership or independent service exit. See the candidate README and current local delivery report.

Local proposed recipe from current VJ04, baseline/payment constraints and atomic IR01/IR03/IR05. It is not a finalised merchant service, action plan, signed proof or permission to deploy. Gupta owns artifact/apply/state mechanisms; Singhal owns exact-subject evidence. No secret, real customer record or executable host mutation is included.

| Dependency | Required final observation | Hold condition |
| --- | --- | --- |
| Source/runtime | Exact tested source/build inputs and deployable image/config under merchant control | A rebuilt/changed image, unknown provenance, health-only or source-only result |
| State | Persistent orders, economic intent/origin/idempotency and callback state survives a qualified restart | Ephemeral storage, concurrent flat-file writers, unverified bootstrap or stale restore |
| Original payment rail | Required historical NVP IDs/account/environment/refunds and IPN routes remain available | Guessing origin from ID shape or assuming v2 refunds can handle NVP objects |
| In-flight sessions | Original browser return/capture and refund obligations continue during/after cutback | New admission stopped while old handlers disappear |
| New payment rail | Actual NEW app/listener/capture/refund behaviour tested under approved scope | Fixture, simulator or credential success substituted for real payment evidence |
| Configuration | Stable final routing and required original-origin handling independent of temporary service | Switch-config expiry would revert the whole site or break callbacks |
| Credentials/custody | Required runtime access merchant-owned and privately provisioned | Runtime depends on a temporary GoldGraft worker token or public/private data leak |
| Assets | Merchant pull/runtime/state/registry rights preserved; exclusive-run cleanup scoped | Deleting shared app/key/callback/artifact or retiring legacy obligations by elapsed time alone |
| Evidence | Deterministic proof binds actual subject, required scope and unresolved paths | Unknown/missing provider read or mismatched source/image masquerading as complete |
| Exit | Prequalified independent merchant executor/current action plan exists | Hidden last-minute workflow install, revoked credential reuse or manual finishing |

Final code/route/state changes need their exact current controller approvals and approved effect slots. Any financial compensation requires separate authority; a rollback approval is not refund authority. Runtime/source finalisation cannot erase already-created provider effects. Unknown historical coverage keeps the original supported path and prevents premature cleanup.

No modern replacement checkout is claimed by this recipe. The frozen baseline stays unchanged; independent USD/cart primitives under `domain/` are proposed components awaiting qualified candidate integration.
