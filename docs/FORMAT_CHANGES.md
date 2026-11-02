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
