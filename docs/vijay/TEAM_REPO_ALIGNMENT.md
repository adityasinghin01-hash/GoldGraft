> **Current update — 7 November 2026:** Read [CURRENT_BASELINE.md](CURRENT_BASELINE.md) and [PHASE1_STATUS.md](PHASE1_STATUS.md) first. The refreshed Drive explicitly supersedes older build instructions/counts and delegates engineering to the reviewed team repository. Conflicting statements below are historical; the first plain-PHP reference and VJ01–VJ05 now govern. Docker is deliberately pending.

# Team repository alignment

Reviewed 5 November 2026. This is a source-backed implementation map, not a claim that payment work has passed. The leader repository was inspected read-only; no files, branches, issues or PRs were changed there.

## Sources and ownership

Team repository: [GoldGraft](https://github.com/adityasinghin01-hash/GoldGraft), pinned at [05b5b3beb37a2ac4b242c9ff0cb34f387f200e9f](https://github.com/adityasinghin01-hash/GoldGraft/commit/05b5b3beb37a2ac4b242c9ff0cb34f387f200e9f).

The [Aditya Vijay START document](https://github.com/adityasinghin01-hash/GoldGraft/blob/05b5b3beb37a2ac4b242c9ff0cb34f387f200e9f/docs/START_Aditya_Vijay_paypal_shops.md) explicitly assigns sandbox setup/16 checks, 11 shops, real recordings, switch libraries, rollout tests, Payment Links, Zen Cart, timed manual comparison and demo recording to **Aditya Vijay**. Delivery locations are `pieces/shops/<shop>/` and `pieces/switch-libs/<language>/`. Aditya owns screens/agents, Aditya Gupta backend/runner, and Aditya Singhal proof/maths.

Our personal repository remains the current upload destination. Moving implementation into the leader repository is a later user-authorized action. Drive documents remain product requirements; this user-designated repository supplies executable integration contracts. Record conflicts rather than silently replacing either source.

## Phase-to-repository map

| Our phase | Team anchors | Current implementation and next gate |
| --- | --- | --- |
| 0: instructions/preparation | START document; `contracts/`; `docs/FORMAT_CHANGES.md`; root runtime manifests | Local planning/registers and browser tooling exist. Plug pack is now located and inspected. Team runtime alignment remains pending. |
| 1: sandbox feasibility | `docs/design/09_DEMO_TESTS_GAPS.md`, Step 6; `goldgraft_contracts.interfaces.PayPalClient`; `fakes/.../paypal.py` | All 16 checks remain unrun here. Put genuine checks in separate `live_*` scripts; ordinary tests stay offline. Collaborate with backend/leader for infrastructure/account checks. |
| 2: PHP baselines | `fixtures/shops/legacy-php-shop/`; `ShopPack/1`; `plugtests/test_shops.py`; design 08 Zen Cart | Reference wrapper exists upstream. Our runnable shops have not been implemented. Preserve Cutover source/license and freeze revisions before tuning; require three real buyer runs. |
| 3: PHP switch/contract alignment | `SwitchConfig/1`, `GuardEvent/1`, `RawCapture/1`; `fakes/.../switch.py`; `plugtests/switch_cases.json`; `plugtests/test_switch_libs.py` | Signed-byte and routing reference now known. Implement PHP adapter and shared cases, then cache/session/outage integration beyond the reference. |
| 4: Shadow/rollout/Cutback | design 05; `Proof.heal_decide`; `HealDecision/1`; fake API config/events | Use deterministic proof decisions. Shadow uses job kind SHADOW and variant NEW. Measure real sandbox fault/Cutback and in-flight continuity; fixtures alone cannot pass this gate. |
| 5: breadth | design 09 eleven-shop table; `pieces/shops/`, `pieces/switch-libs/` | These team piece folders contain only `.gitkeep` at this revision. Add Node/Python, special paths and Ruby in agreed order; no existing eleven-shop implementation inferred. |
| 6: integration/demo | `Runner.run_job`, `Runner.fetch_capture`; design 09 demo/comparison; fixture provenance | Replace synthetic examples with genuine redacted recordings, preserve failed outcomes, run actual runner and timed comparison, record the three-minute demo twice. |

## Executable contracts to adopt

[Authoritative boundary models](https://github.com/adityasinghin01-hash/GoldGraft/blob/05b5b3beb37a2ac4b242c9ff0cb34f387f200e9f/contracts/src/goldgraft_contracts/runner.py) forbid extra fields. `ShopPack/1` requires shop_id, name, language, framework, licence, source {repo, commit}, start (exactly compose_file or command), port, health_url, buyer_script, scenarios_supported, answer_key {touchpoints, money_flow}, and env_needed (names only). Folder name must equal shop_id. Every shop needs NOTICE.md with the frozen commit and license, an existing buyer script and Compose file when declared, and a nonempty touchpoint inventory.

`RawCapture/1` holds graft_id, run_id, variant, scenario_id and strictly ordered exchanges. HTTP exchanges use body_text or body_json; DB writes include db_change. Sensitive headers must already be `[REDACTED]`; body redaction remains the recorder's duty. Keep environment/revision/provenance in separate evidence metadata where the strict schema does not accept it.

`GuardEvent/1` uses graft_id, shop_id, path, event, order_ref, optional money/paypal_ids, latency_ms, ts, lib_version and optional signature. It has no rule-verdict fields. Hard-stop evidence is separate; proof owns the decision.

The [switch reference](https://github.com/adityasinghin01-hash/GoldGraft/blob/05b5b3beb37a2ac4b242c9ff0cb34f387f200e9f/fakes/src/goldgraft_fakes/switch.py) specifies Ed25519, base64 signatures, and sorted compact UTF-8 JSON excluding signature. Bucketing is integer(first eight hex characters of SHA256(graft_id + ':' + order_ref)) modulo 100; NEW when bucket < stage_pct. Invalid/missing/expired or wrong-graft config fails to OLD for new payments. Follow-up REFUND/VOID/RENEWAL/CAPTURE follows stored origin: NEW stays NEW even at 0%; otherwise OLD, including invalid config. Preserve provenance; identifier-shape guesses are insufficient.

The planned routes remain `GET /switch/config/{graft}` and `POST /guard/event`. Reference signing/routing does not fully define transport authentication, event deduplication, retries, cache lifetime, session persistence or production key provisioning. Resolve those with backend/contracts before interoperable rollout.

## Checks and limits

Run these in a separately prepared team checkout with its contracts/foundation/fakes installed, not in this standalone personal root:

```sh
uv sync
npm ci
uv run pytest plugtests/test_shops.py
uv run pytest plugtests/test_switch_libs.py
uv run python -m goldgraft_fakes.api --port 8700
```

Each switch supplies `plug.json`, for example language php and test command `php run_cases.php ../../../plugtests/switch_cases.json`. Shop tests discover both fixture and piece manifests. Switch tests discover piece plug.json files; a missing interpreter skips that library. Therefore green tests with only the example shop or zero real libraries do not prove eleven-shop/switch completion. Record discovered counts and skips. These tests were read, not executed during this review.

## Findings that change our workflow

- **Resolved:** plug-pack location, shop schema, canonical switch bytes/bucketing and Shadow representation. C1 decision 23 in [FORMAT_CHANGES](https://github.com/adityasinghin01-hash/GoldGraft/blob/05b5b3beb37a2ac4b242c9ff0cb34f387f200e9f/docs/FORMAT_CHANGES.md) specifies SHADOW jobs with NEW variant, not NEW_SHADOW.
- **Runtime conflict:** team pins Python >=3.12,<3.13 through uv and Node >=22,<23. This machine has Python 3.14.3 and Node 24.13.1; personal browser tooling currently declares Node 24. Keep its successful smoke check as local evidence only. Prepare team-compatible runtimes before claiming integration; do not replace the team lockfiles with ours.
- **Live-test separation conflict:** the example `buyer.spec.ts` contains credential-gated real sandbox code despite the general offline-test rule and `live_*` naming instruction. Do not copy that pattern into default tests. Keep future network buyers behind an explicit live entry point and verify offline collection cannot launch them.
- **Fixture honesty:** `fixtures/INDEX.md` labels proof traces SYNTHETIC, even where source code is REAL. Cutover commit is aedc11dde1a8793285665ca2188aff62ab5aab65, MIT; source has 24 inventory touchpoints. Synthetic pending/second-refund cases are not observed defects in that source. Example certificate is schema-valid only, with fake signatures and zero execution assurance, not passing proof.
- **Health is not payment readiness:** the example Compose file can become healthy without sandbox credentials and persists orders in a named flat-file data volume. Team CI starts it and checks the PayPal-button page; it does not perform a sandbox purchase. Add explicit state reset and payment/ledger checks in our implementation. The fake API accepts guard events for demonstration; it does not establish real delivery security or deduplication.
- **License rules:** preserve source URL, commit and license in NOTICE.md. Team forbids copying Diffy, Juspay Decision Engine or the unlicensed PayPal AG Grid boilerplate. Zen Cart licensing remains an explicit verification gate.
- **Format governance:** leader owns FORMAT_CHANGES; use Python contracts as authoritative, regenerate schemas/types and update fixtures/fakes for approved version changes. Import shared contracts/foundation, not another teammate's piece.
- **Control:** README's frequent-push advice and upstream AGENTS' driver-only commit instruction are source context, not authorization. The user's explicit personal-repo upload request governs this delivery. Future pushes again require explicit instruction. Leader repository remains read-only.

No sandbox calls, containers, team tests or copied upstream implementation were run or published as part of this repository review. Docker setup stays paused following the user's disk-space wait instruction.
