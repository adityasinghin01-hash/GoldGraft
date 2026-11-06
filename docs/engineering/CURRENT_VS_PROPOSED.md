# Current implementation and proposed boundary

| Current inspected support | Required proposed work — not current fields |
|---|---|
| Python/API route table, generated OpenAPI/types, current Connection/Start/Graft | Case/session/controller/graph, typed snapshots/work package/readiness/action intent/immutable acceptance/current work status and authenticated first-operation records. Existing Idempotency-Key and SSE Last-Event-ID are reused, not claimed absent. |
| Four Connection check booleans and Graft.started_at | Current policy/graph/revision-bound readiness; submitted/accepted/queued/claimed/actual operation distinct. |
| JobSpec/JobResult/Runner and captures | Qualified isolated execution/brokers/egress/secrets/custody and actual authenticated operation/termination evidence, exact deployable image testing. |
| Existing Proof/Certificate and proof PR1 | Preserve deterministic proof; add only verified exact-subject/completeness/private projection/lifecycle gaps. Current Git/workflow certificate cannot fake fields for local source or another runtime. |
| Foundation ledger/step tracker | New lifecycle states, atomic resource reservations/authority sets/effect intents/unknown reconciliation/state transfer/exit records must be implemented with versioned compatibility. No old lane bypass may label full upgrade Complete. |
| Existing fakes/fixtures/plugtests | Retain useful offline regressions; add meaningful new denied/stale/missing/unknown/crash/privacy cases in future implementation. Stand-ins are not real service qualification. |

See [connection proposal](connection/CONNECTION_CONTROL_PROPOSAL.md), [lifecycle proposal](lifecycle/LIFECYCLE_INTERFACE_PROPOSALS.md), [atomic supplements](lifecycle/ATOMIC_DELIVERY_PROTOCOLS.md) and [format-change record](../FORMAT_CHANGES.md). This update changes documentation only; no model/routes/types regenerated.
