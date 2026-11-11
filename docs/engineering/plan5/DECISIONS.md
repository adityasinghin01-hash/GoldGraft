# Plan5 decisions and reconciliations

Paper decisions, 6 November 2026; implementation not started. User authorised Phase5.1→5.2 and responded “Do whatever is better” to the platform recommendation. This permits design judgment, not installation, provisioning, model use or deployment.

| ID | Settled decision and reason | Boundary / revisit condition |
|---|---|---|
| P5D01 | Python3.12 coordinator with explicit task graph, schema validation and broker-only tools. Use the existing Python contract/foundation ecosystem and GU03 durable control rather than add a workflow platform. | No framework or platform account is required for offline assembly. Revisit only if measured scheduler/operating requirements exceed this bounded design. |
| P5D02 | Keep all13 verified logical names. They are typed role configurations, not13 permanent processes or thirteen always-on conversations. | `Simon`/`Nessie` have no verified identity in the inspected material; do not create aliases or extra roles. Clarification can rename display labels without changing authority. |
| P5D03 | Deterministic scheduler governs readiness and task transitions. Gardener may propose a plan; a fixed operation/role catalog and DAG validator admit it. No unrestricted spawning or free-form role-to-role control channel. | Dynamic subtask count ≤32 per run initially; task identities and dependencies are durable. |
| P5D04 | One durable control authority in GU03; agent runtime owns decision policy and typed proposals, not a second case/job/effect database. | Local persistent control fake is a labelled offline contract stand-in. It cannot establish Postgres/outbox/provider durability. |
| P5D05 | Grafter alone changes candidate source. Adversary writes scenarios and disposable mutant forks only. Builder submits qualified runner recipes; no guest controls host, registry or live credentials. | Remote source publication is a separate GU04 effect, even if called “branch write.” |
| P5D06 | Independent deterministic proof from Singhal decides evidence sufficiency. Model critique is advisory; no agent can certify, sign or grant apply. | Reuse inspected proof branch, do not rebuild its maths or infer live signing. |
| P5D07 | Start launches the bounded admitted sandbox programme; subsequent routine tasks advance automatically. Controllers act at material input/processing/apply/recovery boundaries. | No confirmation for each read/test; no approval inferred from a model or old consent. |
| P5D08 | Preserve the existing React18/Vite/TypeScript/CSS Modules frontend direction and useful copy; replace incompatible state/auth/secret/Done semantics. Antigravity implements it after explicit start. | Visual palette/type styling remains a separate later choice; no arbitrary screen-count target. |
| P5D09 | Existing-site support is conditional admission. Render is the first reference adapter, not mandatory merchant migration or general host coverage. | Bare PHP fixture is not a qualified current live-shop migration. |
| P5D10 | Delivery is a coordinator over GU/VJ/SH contracts. Success requires exact tested image/config/state, merchant ownership and independent post-denial continuity evidence. | No service-only relay/key/registry dependency may remain essential after exit. |
| P5D11 | Persist final service image/config under approved effects, then compare independent restart results to that final identity. A one-off deploy override cannot satisfy final configuration. | Targeted reconciliation P5R02 below, subject to actual adapter qualification. |
| P5D12 | Model provider is accessed through GU02's qualified model broker. Retain the existing Anthropic processing-policy target; do not assume API entitlement, retention, model ID, region or price. | Model profile must name an evaluated available version before model-backed component checks. No consumer-chat or unapproved-provider fallback. |

## Platform study outcome

| Route studied | What it contributes | Why it is not the selected baseline |
|---|---|---|
| Existing Python + durable GU control | Small explicit state machine; existing contracts, SQLAlchemy foundation and offline fakes; one authority for state | Selected. We still must construct task atomicity, policy, wakeups and tests; current tracker is not sufficient merely because it has leases. |
| LangGraph | Graph composition, thread checkpoints, interruption and persistence | Viable alternative, but its checkpoints do not settle external effects. Additional checkpoint/control coordination has little benefit for the first fixed task graph. |
| Temporal | Event-history replay, timers, workers and activity scheduling | Strong future option for long-lived complex workflows; adds service/worker/versioning operations to manual assembly. Would wrap, not replace, the authority/effect broker. |
| n8n queue/wait workflow | Visual nodes, execution management and waiting | Queue mode adds database/Redis/workers; visual wiring still requires a coded guarded tool/effect core. Not a payment authority or isolation boundary. |
| Hybrid | Visual operational projection over typed service | Adds two places to debug routing/retries initially. Add only for a measured noncritical operator need, never a second source of truth. |

Primary mechanisms studied: [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence), [fault tolerance](https://docs.langchain.com/oss/python/langgraph/fault-tolerance), [Temporal executions](https://docs.temporal.io/workflow-execution), [n8n queue mode](https://docs.n8n.io/hosting/scaling/queue-mode/). These are product documentation, not evidence that any is deployed or qualified in GoldGraft. Detailed independent company/source comparisons are in the private research ledger.

## Specific reconciliations against frozen/old wording

| ID | Old assumption | Settled interpretation |
|---|---|---|
| P5R01 | “Do not redesign agent internals in paper work”; old handoff maps5.1 directly to build | Current explicit user scope authorises research/design now.5.3 alone implements; new pack supersedes old Singh sequence, not normative safety. |
| P5R02 | Deploy hook/image override is treated as persistent final runtime | Verify persistent image reference, pull rights, effective config and redeploy settings separately; approved final configuration must survive independent restart. [Render deploy hooks](https://render.com/docs/deploy-hooks) document per-deploy overrides; actual target support is still untested. |
| P5R03 | Old lane fallback or PR/certificate means complete | Missing runtime/source/evidence creates a named limited result/hold; full completion predicates remain unchanged. |
| P5R04 | Always13 active LLMs; historical hardcoded models/$caps |13 role charters with conditional activation, serial candidate writer, independent tests/proof. Evaluate actual provider profiles; historical cost/time figures are not budgets or measured promises. |
| P5R05 | “Simon and Nessie” | No matching roles in canonical tool roster/fakes/docs or inspected frontend inventory. Keep exact canonical names, record uncertainty; no invented mapping. |
| P5R06 | Desktop “no login”, generic key forms, local-only case list, public payment IDs, automatic old cutback | Server-authorised saved case; provider/controller flow; protected one-time credential intake only where qualified; private evidence; state-aware recovery. Keep original Desktop bytes as reference. |
| P5R07 | In-process timeout proves stopped | Current foundation tracker can return while a thread continues. Fencing, backend cancellation and trusted actual termination are required before “Stopped.” |

No conflicting old wording is silently adopted. Meaningful future change to role ownership/platform updates this decision log and affected contract/test plans before implementation proceeds.
