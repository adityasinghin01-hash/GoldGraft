# Plan4 resolutions

All findings below are paper design findings, not observed product bugs. Specified corrections are applied; later implementation/account/runtime conformance remains open. Independent review original is retained unchanged, not rewritten to pretend the first draft was correct.

| Finding | Correction / residual gate |
|---|---|
| IR01 Critical | ATOMIC_DELIVERY_PROTOCOLS IR01 + LC34: qualified pre-first-mutation export/drain/all-writer fence/H/replay; missing primitive holds full migration; original bare live fixture unqualified. |
| IR02 Important | IR02 + LC35: canonical target reservations across cases/graph dependencies, resource epochs/unknown retention/shared grant asset classification. |
| IR03 Important | IR03 + LC36: trusted isolated artifact-build/export, exact OCI image testing, separate private registry publish/pull/config/trigger/ownership authority. |
| IR04 Important | IR04 + LC37: IPN unverified bounded durable receipt→ack→postback validation/business effect, separate REST path; contradictory core phrase removed. |
| IR05 Important | IR05 + LC38: initial Reader unchanged; independent resource ApplyAuthority, immutable ActionPlan+ApprovalSet and cardinality1 per-effect slots/expiry/retries/revoke. |
| IR06 Important | DirectArtifact route + LC33 and route-aware schema/state/custody added; no forced Git or fake head/PR. |
| IR07 Important | IR07 + LC39: prequalified independent merchant exit executor and staged ordinary/evidence-read revocation; no removed-key reuse; absent executor holds exit. |
| F01–F12 | Existing explicit controls/holds and connection/ownership/contract addenda applied; cloud effective create/update/delete/share denial clarified; current evidence labels preserved. |
| F13 | Same DirectArtifact correction as IR06; immutable private merchant source/registry destination and separate triggers/authority, current operational gate open. |

No implementation/live/provider gate is closed by this resolution. Reopen design when a required export/handler/approval/registry/exit primitive cannot be qualified. Plan2 must publish reviewed corrections and exact work deltas; do not sell full migration on absent capabilities.
