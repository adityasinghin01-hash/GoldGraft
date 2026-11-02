# P12 · 04 — Union Proof (prove), built by hand

---
## U1 Adversary (attacker, independent)
**Job** — try to break the new code's money handling, and plant a bug for every rule.
**In** — Contract, Root Map, NEW code (to place mutants), PayPal-Mock-Response catalogue (from PayPal docs + Checkout Proof's confirmed codes), currency table, scenario templates (Scion Bank).
**Out** — `ScenarioSet` + `MutantSet` (01 §5).
**Inside**
1. From every rule: ≥1 scenario that exercises it; families: HAPPY, CANCEL, DECLINE (`INSTRUMENT_DECLINED`), PAYER_ACTION (`PAYER_ACTION_REQUIRED`), DOUBLE (two tabs), LOST_RESPONSE, TAMPER (amount/currency), PENDING, REFUND, REFUND_TWICE, NOTIFY_FORGED, NOTIFY_DUP, RESTART, RENEWAL, EDGE_CURRENCY.
2. Property tests: random carts (prices, quantities, currencies) → R02/R03/R05 must hold for all.
3. Mutants: for each rule pick the MMO op that breaks it, place it in the NEW code (ast-grep template per language), compile check.
4. **Assurance filter** (Meta TestGen idea): a scenario counts only if it passes on the OLD shop when the rule held there (or exposes an old bug), runs flake-free 3×, and touches a money path not already covered.
5. Equivalence filter: a mutant that changes no CMEL event in any scenario and is judged equivalent → dropped (counted).
**Who** — Adversary (Sonnet). Never shares context with Grafter.
**Fails →** a rule with no killable mutant → rule flagged "unguarded" on the certificate (lowers proof strength).
**Drawing**
```
rule ─▶ scenario(s) ─▶ assurance filter (old-shop pass, 3× flake-free, new coverage)
  └──▶ mutant (MMO op) ─▶ placed in NEW ─▶ equivalence filter ─▶ MutantSet
```
**Check (Zen Cart)** — e.g. R07 pending: mock `PENDING` capture → old shop sets pending status → new must too; mutant M2 (skip status check) on the `paypalr` path must flip it to paid → scenario kills it.

---
## U2 Union Judge (no AI) — the Tri-Witness algorithm (GG-2)
**Job** — give every scenario an honest verdict from old, old-twin, new and PayPal's ledger.
**In** — CMEL OLD, OLD_TWIN, NEW per scenario; ledger reads for both; Contract; TargetPlan deltas.
**Out** — `Verdict` per scenario + summary.
**Inside**
```
N   = fields that differ between OLD and OLD_TWIN                      // learned noise (IDs, times)
E'  = apply declared deltas D to OLD  (e.g. TOKEN→order_id, IPN→webhook)  // expected new-vocabulary stream
Vn  = rules violated by NEW ∪ ledger(NEW)
Vo  = rules violated by OLD ∪ ledger(OLD)
P   = diff(E', NEW) on money-relevant events, masking N

if evidence missing (ledger read failed, run didn't finish)     → UNVERIFIED
elif scenario not applicable                                      → N/A
elif Vn ≠ ∅                                                       → PROBLEM (rule ids + event refs)
elif Vo ≠ ∅                                                       → PASS_FIXED  (old shop's bug reported; parity waived for those rules)
elif P ≠ ∅ and not covered by D                                   → PROBLEM (parity)
else                                                              → PASS
precedence: Contract > Parity > Noise ; stricter verdict wins when two checks disagree (WeChat rule)
```
**Who** — deterministic service (D1), unit-tested on golden fixtures.
**Fails →** unknown event shape → UNVERIFIED (never silently PASS).
**Drawing**
```
OLD ──┐ diff → N (noise)
OLD'──┘
OLD ──deltas──▶ E' ─┐
NEW ────────────────┼─▶ parity P (mask N)
ledger(NEW) ─▶ rules Vn ─┐
ledger(OLD) ─▶ rules Vo ─┼─▶ grade
                         P┘
```
**Check (Zen Cart)** — happy path: E' (SetExpressCheckout→INTENT, DoExpressCheckoutPayment→CAPTURE) vs NEW (`paypalr` create→INTENT, capture→CAPTURE): same amount/currency, one capture, SHOP_PAID — PASS; noise masked: token/order id, txn/capture id, times.

---
## U3 Proof Strength (money mutants, GG-3)
**Job** — measure how strong the proof is, not just whether it passed.
**In** — MutantSet, ScenarioSet, Judge.
**Out** — `proof_strength{total, equivalent_dropped, killed, score}`, per-rule guard status (the triangle).
**Inside** — for each mutant: build NEW+mutant → run only the scenarios linked to its rule (keeps sandbox calls low) → killed if any verdict turns PROBLEM → score = killed / (total − equivalent_dropped). Certificate needs score ≥ 0.95 and every CRITICAL rule guarded.
**Who** — deterministic runner.
**Fails →** sandbox rate limit → queue across runners; never skip mutants silently.
**Check (Zen Cart)** — 12 mutants on the `paypalr` path + switch observer (e.g. M8 skip webhook signature → NOTIFY_FORGED scenario kills it).

---
## U4 Repair Loop
**Job** — fix failures from evidence, without letting the writer see the attack plan.
**In** — PROBLEM verdicts (rule ids, event refs, diffs, PayPal debug ids).
**Out** — new commits; loop ≤2 rounds (then Opus once).
**Inside** — Gardener groups failures by rule → Grafter gets an evidence pack → commits → only failing + linked scenarios re-run first, then the full set.
**Who** — Grafter + Judge + Gardener.
**Fails →** still failing → PARTIAL certificate listing each open rule.

---
## U5 Certification Zone + Certificate (GG-8)
**Job** — issue a certificate only when the proof is complete, and make it impossible to fake.
**In** — all verdicts, proof strength, survey recall, security scan results, cost/time.
**Out** — `Certificate` (01 §6) + public page + Rekor entry.
**Inside**
1. **Round 1 (smoke, NPCI "Comfort" idea)** — happy path + 3 failure scenarios; must pass to spend on round 2.
2. **Round 2 (full, "UAT")** — every scenario + mutants.
3. Gate: 0 PROBLEM; UNVERIFIED only on non-critical rules; proof strength ≥0.95; survey recall ≥0.95; 0 secrets in prompts/logs/diffs; deps all allowlisted.
4. Sign on the runner (Sigstore keyless; identity = our workflow + commit sha) → Rekor → certificate page. Local runs cannot sign.
5. Re-verify (anyone): signature + Rekor + ledger hash chain; PayPal re-fetch of listed order/capture ids (needs the shop's sandbox read access — done server-side for our demo shops).
**Who** — deterministic (D6 Signer); Herald writes the page text.
**Fails →** any gate red → PARTIAL with reasons (no certificate).
**Drawing**
```
round 1 ─pass─▶ round 2 ─▶ gate ─pass─▶ sign (OIDC) ─▶ Rekor ─▶ certificate page ─▶ PR
   └fail─▶ repair             └fail─▶ PARTIAL report
```
