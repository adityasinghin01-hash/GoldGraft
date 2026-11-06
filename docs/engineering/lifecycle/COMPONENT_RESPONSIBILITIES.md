# Team boundaries and existing-code preservation

Status: Plan3 engineering on paper, 6 November 2026. No implementation, account change, deployment, live payment/model/worker job or agent-internal design. CURRENT means inspected existing contract; all new lifecycle states/interfaces/modules below are PROPOSED. Vendor/account/runtime qualification gates remain open.

| Person | Lifecycle responsibility and boundary |
|---|---|
| Singh | Shared format/policy ownership, saved-case review/approval/status/handover UI and external agent inputs/results integration. Internal agent communication/orchestration/prompts/algorithms deferred until own Plan5. Final integration Plan6. |
| Gupta | Backend authority/durable effects/outbox/fence, runtime/recorder/brokers, provider publisher/deploy/current observations, recovery/exit mechanisms. Credentials/signer remain trusted service boundary. No proof verdict from model. |
| Singhal | Inspect/reuse proof PR and maths; exact old/new/domain/mutation/evidence adequacy and private/public projections, no forced reimplementation. Does not fetch source or kill workers; evidence schema validators alone do not prove provider/isolation. |
| Vijay | Supported shop source/build/runtime manifests, synthetic state/true sandbox flow fixtures, recorder-domain expected evidence, origin/callback/state/switch/finalisation compatibility and safe recovery scenarios. No automatic all11 shops expansion. |

Mechanisms and domain recipes exchange shared contract data, not cross-piece imports. Proposals reference existing proof modules to adapt only if current source review shows a gap. No assignment/messages/merges occur during paper engineering; Plan2 produces exact keep/adapt/add/defer deltas against then-current work. External account/controller/provider actions remain named gates; source/host/payment authorities can be different people. Live mutation/financial actions require their explicit scope.
