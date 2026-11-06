> Reviewed team baseline, 6 November 2026: this connection proposal is subject to the review addendum, implementation bridge and lifecycle atomic protocols linked from [engineering START](../START_HERE.md). Earlier programme status/owner restrictions in this frozen source are historical. No current API/implemented capability is created by this text.

# Durable Start and verified operation

Status: paper engineering specification, 6 November 2026. Nothing here is a deployed feature or current API unless explicitly labelled CURRENT. Proposed components/interfaces require later implementation and contract approval. Plan 1 ends at verified first sandbox operation; agent internals and Plans 2–6 remain outside scope.

Decision T11: PostgreSQL 18 durable transactions plus transactional outbox; first dispatcher is a service-owned polling worker using row locking/lease rather than an extra external queue. Existing foundation ledger/tracker is reused through contracts only after compatibility/transaction review. Current SQLite-oriented abstract protocol and synchronous worker lease semantics do not establish real process termination. This dispatch is lifecycle plumbing, not agent orchestration.

## Accepted action transaction
Client obtains a server-issued random action identity for displayed readiness; stores no credential in browser. CURRENT Idempotency-Key header reused, scoped to tenant/case/actor/operation. Canonical request includes proposed readiness/scope digest through new versioned Start interface, not CURRENT note field. Transaction locks case/action/readiness, checks current membership/binding epochs/expiry/cancel tombstone/source+host invalidation, inserts one immutable action/accepted job/outbox and private receipt with unique constraints, appends acceptance evidence and commits before acknowledgement. Outbox dispatch never precedes commit. Recheck provider state immediately before transaction; bind observed epochs, fail when recheck unavailable. Provider revocation may race in-flight calls: no impossible atomic cross-provider guarantee; broker checks again and reports uncertainty.

Same key+same canonical action returns original receipt, including after lost response; same key+different payload returns 409. Different key while equivalent active work exists returns existing action reference or conflict, not a duplicate job. Cross-case key cannot retrieve another receipt. Initial metadata TTL for action/tombstone 30 days; expired retry returns gone/reauthorise rather than silently creating new work. Client status is query of original action.

## Dispatcher/worker
Dispatcher claims committed outbox row with SELECT FOR UPDATE SKIP LOCKED, then external operation may repeat; unique job/generation deduplicates worker allocation and reconciliation. Lease 60s, renewal 20s initial policies; retry schedule bounded (1, 2, 4, 8, 16, 30s plus jitter, stop after 10 attempts then hold), no user time promise. Lease expiry increments fencing generation transactionally before replacement; old worker/broker actions and receipts rejected. Allocation crash may leave orphan VM: reconcile by service job/generation tags; never claim external exactly-once allocation. Outbox retains outcome/attempts, no infinite silent retry.

Worker external input: scoped job identity/generation, source/work manifest, readiness and scope digest, policy/runtime/fixture versions, limits, snapshot capability and receipt channel. No provider credentials. It authenticates to controller and rechecks current job/authority before privileged operations. Internal agents decide their own work later; the interface defines no agent topology/prompts.

See SERVICE_AND_STORAGE_SPEC.md for the precise trusted verification/receipt-collection boundary: no guest signing/provider management credentials, verifier runs before any shop-controlled executable.

## Actual first operation
Control-plane receipt of a lease or created VM means claimed/provisioning only. Trusted supervisor inside qualified VM reads the permitted pinned work manifest and required baseline bytes, computes digest matching accepted snapshot, and returns authenticated BaselineRead evidence containing job/generation/worker identity, source and scope digests, observed manifest digest, operation kind, start/finish times, result and template identity. Controller verifies assignment/current fence, signed or authenticated channel, expected digest, freshness, uniqueness and evidence storage before emitting OPERATION_STARTED. Missing/mismatched digest => failure/hold. A forged guest stdout event cannot count. This proves that baseline operation, not a model call, payment test or upgrade success. User copy says sandbox work started; if product claims model/agent inference began it must collect a separate actual gateway-call acknowledgement tied to this job.

## Stop/revoke and unknown outcomes
Stop is authenticated and binds the same action identity even before accepted receipt. Durable cancellation-intent row/tombstone orders with acceptance under the same lock. If Stop wins, Start is cancelled without dispatch. If acceptance wins, fence generation and deny new broker calls, then request termination; display Cancellation pending until qualified supervisor/provider termination confirms. Provider revocation follows local denial and remote acknowledgement separately. In-flight payment/model calls may have happened; reconcile and report unknown, never claim rollback. Full payment/deployment recovery is Plan 3.

## State and recovery table
| Fact | Visible result and next action |
|---|---|
| No committed receipt | Submitting; timeout becomes Checking status using original action. Never auto-new Start. |
| Committed accepted row | Accepted. Waiting for a worker; recover private receipt after login. |
| Allocation or lease only | Preparing sandbox; no Started claim. |
| Current valid baseline operation evidence | Sandbox work has started; Details identifies exact proven operation. |
| Cancel tombstone before acceptance | Cancelled; new action needs fresh review and key. |
| Fenced but remote termination missing | Cancellation pending; keep reconciliation, block fresh effects. |
| Lost connection/ambiguous receipt | Status unknown/Checking status, not failed/successful by guess. |
| Session expired/laptop closed | Saved case; reauthenticate and authorise replay, no automatic restart. |

Authoritative event sequence is server committed per case; SSE is a replay projection, not the database. CURRENT Last-Event-ID resumes after sequence; retention gap returns a fresh authorised snapshot/replay cursor via proposed protocol, no silent skipped evidence. Redact role-specific projection; no public receipt. Existing Graft.started_at is not operation evidence.

Source for DB primitive: [PostgreSQL SELECT locking](https://www.postgresql.org/docs/current/sql-select.html); transaction/outbox protocol above is GoldGraft's design, not a claim PostgreSQL provides external exactly-once effects.

## Closure consistency rules
Use [CONNECTION_CONTROL_PROPOSAL.md](CONNECTION_CONTROL_PROPOSAL.md). Persist ActionIntent before either Start or Stop; pre-accept cancellation has null work_id/generation and still durable case/actor/readiness binding. Immutable WorkAcceptance receipt is distinct from current WorkStatus. Retry returns original acceptance without restarting; status/reconciliation returns current cancellation/stopped/unknown facts. Only current authenticated BASELINE_READ evidence advances operation_started. This fixes earlier draft fields without changing any current API.
