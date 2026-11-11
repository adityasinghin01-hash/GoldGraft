# All-agents AI build plan — 11 November2026 (Claude, autonomous)

Aditya: "Test all of the models … rule-based can't work on each and every
circumstance … build one by one, complete one by one … without my input. Start."
Budget: $10 project cap for all 13 agents; $8.84 remained before this plan
(Surveyor spent $1.160890; Herald/Sentinel $0). Per-agent envelopes are in
SEQUENTIAL_AGENT_QUALIFICATION_PLAN; Herald's $0.25 and Sentinel's $0.40 are now
available for their own AI tests. No new accounts: Zapier is done; other sponsors
are deferred.

## Shared step S0 (once, before agent 4)
- `pieces/backend/model_gateway/component_port.py`: ComponentGateway + ComponentModelPort
  reusing the Surveyor ledger, receipts, unknown handling, caching and count bound.
  Role-generic wire: role prompt + component transport policy; tools = the role's
  allowed tools + `submit_output` (expected Alert/PlanProposal/… JSON schema) + `report_hold`.
  The Surveyor broker is unchanged.
- `scripts/live_component_model_eval.py`: composes the existing component profile
  with the gateway (real_model ticket, admission, context, staging), like Surveyor's.
- The runtime still enforces the role's planned read set; final outputs pass the
  role's invariant review (grounding/safety), not text equality with the rules. The
  rule-based synthesis is kept as the independent reference scorer.

## Per agent (order: Herald*, Sentinel*, Gardener, Builder, Explorer, Scribe,
## Architect, Grafter, Adversary, Healer, Librarian, Orchard Analyst)
1. Offline: read the module; write gap tests (red); fix; green.
2. Review: exact-equality → invariant validation where judgment is the job; hard
   safety rules unchanged.
3. Eval cases: the sample + variations + hostile/missing/conflicting negatives, with
   independent labels.
4. Free sizing dry run (count_tokens), then a paid pilot once per case (Haiku first;
   Sonnet when Haiku fails a named question twice), then ×3 repeats for passing cases.
5. Output use + reopen audit; report/card; BUILD_STATUS; memory.
(*) Herald/Sentinel: AI test of the existing closed contracts (model chooses and
explains; validators unchanged).

## Status tracker
`~/reports/goldgraft-all-agents-20261111/STATUS.json` (updated after every step).
