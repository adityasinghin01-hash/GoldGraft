# Format changes (owner: Aditya)

## C1 — initial v1 plug pack, 2 November 2026

This is the first coded version of design 00–09. No existing version is replaced.
Python in `contracts/src/goldgraft_contracts/` owns the wire shapes. Future format
changes require a new registry version, regenerated schemas/types, and updated
examples, fixtures, and fakes in the same change.

### Decisions

1. Versions are registry keys (`Name/1`), JSON Schema IDs, and filenames, rather
   than extra wire fields absent from the design. `MoneyEvent` is `CMEL/1`;
   `MoneyContract` is `Contract/1`. Their Python aliases are `CMEL` and `Contract`.
   Nested helpers are embedded in `$defs`; they are not independent ledger artifacts.
2. All objects forbid extra fields, including helpers. JSON bags are restricted to
   explicitly opaque content: scenario carts/expectations, raw bodies/DB rows,
   parity diffs, and dashboard filters. An explicit recursive JSON union gives both
   exports real JSON types, including scalars, arrays, and null. Named maps such as versions, selectors,
   health checks, headers, and minutes by stage have typed values.
3. Identifiers/refs, scripts, predicates, template refs, cycle/status/source, and
   unspecified summaries are nonempty strings; scripts are data, never executed.
   Locations use three disjoint object shapes. Misses and handoff queue items are
   string descriptions/refs because the design gives no item structure.
4. Counts/sequence/time offsets are strict nonnegative integers; file lines,
   switch versions, timeouts and ports are positive integers. Probabilities are
   finite numbers in [0,1]; timestamps require an explicit timezone. Optional
   fields accept null and preserve omission when serializing. Negative Money
   values remain valid: the design specifies an integer without a sign restriction.
5. Transaction `Money.minor` and handoff `amount` are strict integers. The currency
   table is the 25 codes explicitly listed at
   https://developer.paypal.com/api/codes/currency/ (checked 2026-11-02), including
   RUB as listed there. This records documented codes, not merchant eligibility.
   HUF, JPY and TWD use PayPal's zero-decimal convention (including the override of
   ISO minor digits for HUF/TWD). Other listed codes use two digits. Codes outside
   that table are rejected. There are no unconfirmed codes in the table.
6. `BudgetRecord.usd/cap_usd` and certificate `cost.usd` retain the design's numeric
   USD accounting fields as finite nonnegative numbers. They describe API usage
   costs, not payment amounts. Certificate `time` maps stage names to minutes.
7. Ledger inline data uses a separate `payload` field, mutually exclusive with a
   non-null `payload_ref`. The limit is 16,384 bytes of compact UTF-8 JSON
   (`ensure_ascii=False`, separators `,` and `:`). Inline bodies are validated via
   the registry; referenced bodies must be resolved and passed to `validate` by
   the ledger service before acceptance. Contracts perform no storage/network I/O.
   Hash fields enforce lowercase SHA-256 hex shape; foundation computes/verifies
   hash contents and the chain. Placeholder example hashes are not attestations.
8. Rule severities: CRITICAL = R01–R06, R08, R11, R12; MAJOR = R07, R09, R10,
   R13, R14, R15; MINOR = R16, exactly as brief C1 specifies. Base rule titles use
   their plain rule text; predicate ideas remain strings, not a new DSL engine.
9. A contract adds `shop_id` to its rules. The set of rules is an ordered JSON list
   with unique rule IDs, preserving deterministic output. There is no implicit
   deduplication or discarded rule.
10. Step is the exact one-key union `{driver_step: str}` | `{api_step: str}` |
    `{paypal_mock_response_code: str}`. Cart and expect are JSON objects; parity
    diffs are JSON values. Recipe scenarios are template refs, not instantiated
    scenarios. Proven/flake-free run counts may be below three to represent an
    unfinished build; assurance gates belong to services.
11. Mapping alternatives expand into one `MappingRow` per target kind: 16 design
    rows become 21 rows. Ellipsized NVP names are expanded with their documented
    prefixes. The two ledger-copy kinds use source PAYPAL_LEDGER when mapped;
    PAYPAL_LEDGER is a Source, not a Kind. MMO-12 stores ordered rules_broken lists.
12. `Connection` has required nullable repo/site and requires at least one.
    secrets_ref uses a `doppler://` reference; JobSpec additionally accepts
    `vault://` and `secret://`. The contract never carries credential values.
13. RunnableShop uses `image_digests: {service: digest}` and `health: {page: bool}`.
    Driver selectors are `{name: selector}`. Plan items use touchpoint IDs.
    TargetPlan adds `deltas: [{id, mapping_id, description}]` (default empty), because
    S1 declares them and the Judge consumes them; bare delta IDs cannot convey
    allowed differences. Origin rules remain lists of strings. Enum VAULT is
    optional by membership in the target_experience list; `?` is not part of it.
14. LinksPack buttons require exactly one of old_form_fields/hosted_button_id.
    Proofs have separate order_id/capture_id fields. Untouched choices preserve
    the design's exact `Donate` / `Subscribe` spelling.
15. Standalone U3 `proof_strength{total,...}` is `ProofStrength/1`; certificate's
    nested strength retains `mutants_total`. F1's unnamed handoff row is named
    `HandoffRecord/1`, and its collection plus validation summary/freeze advice is
    `HandoffPack/1`. Handoff amount is minor units with a separate currency.
16. Agent outputs are explicitly **minimal v1, owner Aditya may extend** in every
    requested docstring. They share id/graft_id/Producer/created_at; their remaining
    fields follow the task descriptions. Stage values come from design 00. Lane
    strings are FULL, NO-RUNTIME and NO-CODE (the `LANE:` label is not stored).
17. Herald numbers use `{entry_hash, json_pointer, value}`. A nonempty numbers_used
    requires validation context `ledger_entries: {hash: decoded_entry}`; every
    value must exactly match the referenced numeric value. Text with no numbers
    uses an empty list. The producer is responsible for listing every number in
    its text; this format does not infer numeric claims from natural language.
18. JobSpec timeouts are `{build_s, run_s, total_s}`; its required nullable signature
    is the signing placeholder. JobResult uses `started`/`finished` timestamps,
    string artifact refs and an optional plain error; completion cannot precede
    start. JobResult runner_identity adds run_id; Certificate retains workflow/sha.
19. RawCapture names its exchange list `exchanges`. DB keys are JSON objects
    (supporting composite keys); before/after are nullable JSON objects. DB entries
    still have method/url/headers, using producer-defined DB operation/URI strings.
    HTTP bodies require exactly one of text/JSON (empty text and JSON null are
    valid); DB-only writes may omit both. Exchange seq increases strictly.
20. Secret header names are matched case-insensitively, including authorization,
    cookies, API keys, auth assertions, and names containing secret/token/api-key.
    Non-redacted values are rejected, not silently rewritten. Body redaction and
    custom secret-header catalogues remain recorder responsibilities.
21. ShopPack start is a strict union of compose_file or command. Answer-key
    touchpoints reuse RootMap's model. env_needed contains environment-variable
    names only; `KEY=value` is rejected. Manifests are JSON-shaped data; YAML loading
    belongs to the shop piece. Guard paypal_ids reuses PayPalRefs.
22. Heal success values are counts bounded by their sample counts. HOLD preserves
    stage, STEP_UP chooses the next 0→1→10→50→100 stage, CUTBACK selects zero, and a
    hard_stop requires CUTBACK. The model does not calculate posterior probabilities
    or make promotion decisions. Fractions/booleans are rejected as stage values.
23. Design 05 mentions NEW_SHADOW while 01 explicitly permits only OLD/OLD_TWIN/NEW.
    CMEL and JobSpec keep 01's exact variants; shadow work is identified by job kind
    SHADOW and uses variant NEW. No undeclared enum was added.
24. Certificate scenario counts must add up; problem and secrets_found are zero.
    Mutant counts must be consistent. Models do not enforce the certification gate,
    execute predicates, check expiry against the current clock, verify signatures,
    or recompute confidence/proof scores: those are deterministic service duties.
25. Generation bundles all schemas once to avoid duplicate TypeScript declarations.
    Object conditions are distributed across union branches for TypeScript so common
    required fields are preserved; forbidden sibling payload/body keys become never.
    Boundary exports are named `NameV1`. JSON Schema captures structural constraints;
    custom Python validators enforce byte limits, provenance, counts, redaction,
    transitions, and referenced-payload checks. TypeScript declarations provide
    compile-time types, not runtime validation; Python remains authoritative.
26. The generated-file checker compares pre/post regeneration with git --no-index
    as well as tracked git diff. This detects missing/stale/new generated files
    even before the repository's first commit, without staging or committing them.
    Existing correct untracked outputs are allowed in this bootstrap checkout.
27. Added jsonschema and TypeScript as dev dependencies to validate every schema
    example and compile the generated declarations. Tests remain offline.

## C2 — StageChange/1, 2 November 2026 (requested by Aditya in brief C2)

New boundary; no existing v1 format is changed. `StageChange/1` records graft_id,
required nullable from_stage (null only at creation, enforced by the tracker),
to_stage, positive integer attempt, nonempty reason, actor {kind: agent|service,
name}, and evidence_refs. Attempt is the destination stage's visit number,
including re-entry after repair/cutback; transport retries keep the same attempt.
C1's Stage enum remains unchanged. StageChange alone also accepts LANE_NO_CODE,
LANE_NO_RUNTIME, LANE_MAP_ONLY; this avoids silently widening existing v1 formats.
The example, standalone JSON Schema and generated TypeScript accompany the model.
The demo JSONL under fixtures/events/ exercises this new format; C4 owns all
other fixtures and there are no existing StageChange fakes to update.

C2 ledger decisions: canonical JSON allows finite floats (Python's shortest
round-trip repr; NaN/Infinity rejected), because probabilities, confidences and
USD usage costs are fractional. Money stays integer-only: the formats reject
float money before anything is stored. (Corrected by Claude on 2 Nov: the first
version rejected every float, which would have blocked HealDecision and
BudgetRecord entries.)
Step-tracker lane arrows (Claude, 2 Nov): SURVEYED → LANE_NO_RUNTIME (Builder
cannot run the shop) and BUILT → LANE_NO_RUNTIME (built but cannot be driven);
LANE_NO_RUNTIME → PARTIAL → PR_OPEN; LANE_MAP_ONLY → DELIVERED (map + plan are
the delivery); LANE_NO_CODE → LINKS_PROVEN → DELIVERED. Any stage → FAILED with
a reason (dead letter).
The required entry_hash formula is unchanged; an internal full-envelope checksum
also detects edits to ts/schema/inputs/graft_id/payload_ref, which that formula
omits. Hashes can collide across grafts with identical content at identical seq:
get(hash) raises AmbiguousHash in that case; get(hash, graft_id=...) disambiguates.

## C3 — API contract, 2 November 2026 (built by Claude)

- `contracts/src/goldgraft_contracts/api.py`: API-only view models (request/response
  shapes for the 12 screens): Problem (RFC 7807), ProbeRequest, ShopCreate, Shop,
  ConnectRequest, StartGraftRequest, Graft + GraftCard (every number has a plain
  note), ScenarioList, CmelView, ProofView, CertificateVerifyResult, HealState,
  InjectFaultRequest/Result, Ack, RecipeList, LearningCurve, OrchardView,
  OrchardAsk/Answer, GauntletRun, Comparison. Boundary formats are reused unchanged.
- `contracts/src/goldgraft_contracts/api_routes.py`: the 24 endpoints of design 07 as
  DATA. The stand-in and the real backend both register routes from this table.
- Generated: `contracts/api/openapi.json` (scripts/export_openapi.py) and
  `contracts/ts/goldgraft-api.d.ts` (openapi-typescript 7.13.0, MIT), both covered by
  `scripts/check_generated.sh` and the TypeScript check.
- Decisions: `GET /heal/{graft_id}` returns JSON, or SSE when `Accept:
  text/event-stream`; `POST /certificates/{id}/verify` needs no Idempotency-Key (it
  changes nothing); webhooks are not keyed — they are de-duplicated by
  PAYPAL-TRANSMISSION-ID / X-GitHub-Delivery and need their signature headers;
  `GET /learning-curve` added (named on screen S8, missing from 07's API table);
  in the OpenAPI file the recursive JsonValue type is "any JSON value" (TypeScript
  cannot express the recursion there).


## C-P1 — connection-control proposal, 6 November 2026 — NOT IMPLEMENTED

[Canonical connection proposal](engineering/connection/CONNECTION_CONTROL_PROPOSAL.md), subject to [review addendum](engineering/review/CONNECTION_REVIEW_ADDENDUM.md), covers saved cases/current controller authority/provider callbacks, source snapshots/resource graph/complete WorkPackage, static readiness, immutable Start acceptance/current status, generation-fenced cancellation and real operation evidence. Existing Idempotency-Key/SSE resume remain current features. Connection booleans and started_at are not sufficient new semantics.

Owner Singh, future SI01 bootstrap. Implement strict Python models/typed references and registry/route versions, current compatibility or explicit old-path denial, then generate schema/TS/OpenAPI with examples/fakes/fixtures/negative validation in one approved change. No code or generated files changed here. Do not guess field availability from these names.

## C-P3 — lifecycle and reviewed atomic supplements, 6 November 2026 — NOT IMPLEMENTED

[Lifecycle proposal](engineering/lifecycle/LIFECYCLE_INTERFACE_PROPOSALS.md) and normative [atomic protocols](engineering/lifecycle/ATOMIC_DELIVERY_PROTOCOLS.md) define exact artifact/provenance/private review, separate ApplyAuthority/ActionPlan/ApprovalSet, cross-case TargetReservation/resource epochs, per-effect slots/unknown reconciliation, StateCutover and independent ExitCheckPlan evidence. Protected Git and direct-artifact routes differ; Git fields nullable on the latter. Existing Certificate Git/workflow assumptions cannot encode these new profiles by invented values or expose private review data publicly.

LC-A1 protected apply is a separately approved future policy, not granted by Start or initial Reader access. Shared bootstrap must align models/routes/registry/generated types/examples/fakes/fixtures/tests and compatibility. Downstream lifecycle consumers cannot implement incompatible Markdown guesses. Actual provider permissions/financial/state/isolation/exit qualification remains open.

## P5-C1 — additive Plan5 shared boundary, 10 November 2026

Authorised by Aditya's explicit B1 start. Construction is isolated in
`GoldGraft-plan5-build` at inspected base `0365c5e1adcb1875a7f72c99dc7c63631501e131`.
The original checkout and frozen authoring/reference sources remain preserved.

- New Python modules `plan5_common`, `connector_adapters`, `work_package`,
  `connection_control`, `lifecycle`, `agent_runtime`, `plan5_tools`, `plan5_validation`,
  `plan5_schema` and `plan5_openapi` implement the proposed shared declarations,
  accepting-boundary validation and export metadata. They contain no agents,
  prompts, scheduler, model SDK, provider clients or delivery engine.
- `PLAN5_REGISTRY` adds 135 exact schema keys, including typed nested/request/tool
  argument records. All new keys use `/1`, except **ChangeList/2**. The 42 legacy
  keys and payload examples retain their original semantics and bytes. The
  generated fixture index enumerates every new key, payload path and actual hash.
- ChangeList/2 distinguishes snapshot provenance (null branch/commits) from Git
  provenance (real-format branch/commits, still requiring provider validation).
  Producer ownership is Grafter; existing ChangeList/1 is unchanged.
- Task/model/tool declarations, subject manifests/derivations and GU-facing
  Protocols are shared interfaces only. ModelBudget/1 adds integer micro-USD
  accounting with a $15 target/$20 cumulative ceiling; it is not permission to
  spend. CollectorAcceptance/1 names the service-only baseline-operation receipt.
- Strict counts, UTC, digests, source/OCI identity, conditional forms, bounded
  collections, safe paths, role/tool/output declarations and DAGs are checked.
  Contextual helpers validate authenticated tenant/case/run/generation/producer,
  exact bytes/subjects/lineage, required package scope, upload coverage, draft
  claim prerequisites and split-controller approval/epoch/image binding.
  GU still owns authenticated lookup, atomic persistence and authority-at-use;
  these pure checks do not implement those mechanisms.
- `PLAN5_ROUTES` declares 23 exact v2 operations separately from legacy `ROUTES`.
  Requests, success/error codes, session/draft/service identity, CSRF,
  idempotency, multipart upload and SSE metadata export together. These routes
  are explicitly **contract-only**, not installed backend handlers. The service
  route guard denies legacy demo Start/connect/tools/lanes; the v2 tool catalog
  never falls through to legacy operations. Stage/1 and JobKind/1 are unchanged.
- Python exporters regenerate JSON schemas, boundary TypeScript, OpenAPI and API
  TypeScript. OpenAPI uses prefixed v2 components to avoid conflating legacy
  serialization schemas with new validation schemas. Fixture lookup now accepts
  explicit versions without changing unversioned `/1` behavior.
- `make_plan5_examples.py` generates 135 positive and 19 deliberate negative
  synthetic examples and indexed hashes; `--check` detects drift without writes.
  It preserves independently owned later fixture entries/modes. B2 persistent
  stand-ins and frontend fixture modes are not built by B1.
- Generated parity compares current bytes with regenerated bytes, so an
  intentional uncommitted migration can pass without a forbidden commit.
  Normal pytest denies IP-network connections; validation adapters expose closed
  errors rather than raw private inputs. Live qualification remains separate.

Exact implementation/export inventories, actual checks, decisions and remaining
limits are recorded in `engineering/plan5/B1_BUILD_REPORT.md` and its hash manifest.
No FRONTEND_READY, runtime/model competence, counterpart qualification or merchant
completion is implied. Aditya will create agents by hand later with guidance;
this B1 change does not create them.

## 10 November 2026 — Herald accepting-boundary numeric context

No wire fields or schema versions changed. `HeraldText/1` already requires
resolved ledger context for `numbers_used`; the pure `validate_artifact` helper
now accepts optional `validation_context` from the trusted accepting service.
Omitting context still rejects referenced numbers. Model JSON never supplies
that context. Runtime, staging and persistent offline acceptance resolve the
same scoped projection journal before validating Herald numbers; the fake
journal derives counts from actually committed Surveyor output bytes.

This is internal accepting-adapter plumbing, not a new ledger/proof authority,
real GU qualification or numeric trust obtained from prose. Frontend inputs
were marked updating before editing this shared Python helper; revision2 will
publish fresh hashes only after actual checks. Existing schemas/types/fixtures
and legacy validation behaviour remain unchanged.
