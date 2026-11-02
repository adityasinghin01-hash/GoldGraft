# P12 · 05 — Heal, Handoff, Fleet, cross-cutting pieces, built by hand

---
## H1 Shadow Graft (GG-6)
**Job** — test the new code on real carts before any buyer moves, without charging anyone twice.
**In** — carts seen on the OLD path (items, amounts, currency only — no buyer data), sampled (e.g. 1 in 10).
**Out** — shadow verdicts: did the NEW code build the same order and capture the same money in the sandbox?
**Inside** — Graft Switch `emit(INTENT)` on old path → control plane queues a shadow job → runner runs the NEW code path for that cart against the PayPal **sandbox** with a sandbox buyer (KERNEL browser) → CMEL(NEW_SHADOW) vs the OLD path's real outcome (amount, currency, items) → Judge (parity only; contract on the sandbox side).
**Who** — Healer reads results; capture + Judge deterministic.
**Fails →** sandbox rate limit → sample less; mismatch → stay at 0%, Grafter gets evidence.
**Drawing**
```
real buyer ─▶ OLD path ─▶ PayPal (real)      cart copy (amounts only) ─▶ NEW path ─▶ PayPal SANDBOX
                     └──────────── compare amount · currency · items ◀──────────────┘
```
**Check (Zen Cart)** — demo: "live" Zen Cart on old module with simulated buyers; shadow runs of the `paypalr` path in sandbox; all parity PASS → stage 1%.

---
## H2 Heal Controller (GG-5, deterministic)
**Job** — move buyers 0 → 1 → 10 → 50 → 100% only when the numbers say it is safe.
**In** — live events from Graft Switch + guard results + PayPal webhooks.
**Out** — signed SwitchConfig updates; stage entries in the ledger.
**Inside**
```
hard stops (any one ⇒ CUTBACK now): money-rule break on a NEW payment (R01–R12), unverified notification acted on, guard unreachable > 60 s
soft signals per stage: success rate (approved → captured), 5xx rate, p95 latency
promote when:  n_new ≥ n_min(stage)  AND  P(p_new ≥ p_old − 0.02) ≥ 0.95   (Beta-Binomial posterior, both paths)
cutback when:  P(p_new < p_old − 0.02) ≥ 0.95  OR any hard stop
demo: n_min = 30 per stage, simulated sandbox traffic, clearly labelled; real: n_min by merchant volume + soak time
```
**Who** — code (D2). Healer may pause or request Cutback; it can never promote.
**Fails →** too little traffic → stage waits (never promotes on thin data).
**Drawing**
```
events ─▶ guard (per payment: ledger lookup + rules) ─hard break─▶ CUTBACK
   └────▶ posterior (old vs new) ─safe─▶ next stage (signed config)
```

---
## H3 Cutback (deterministic)
**Job** — switch back in seconds, without stranding a payment.
**Inside** — write SwitchConfig `stage_pct = 0` (signed) → libraries pick it up ≤15 s (or instant via push) → in-flight NEW sessions finish NEW and are each re-checked by the guard → ledger entry with time-to-cutback → Grafter gets evidence → graft returns to GRAFTED.
**Check (Zen Cart, demo)** — inject fault (flip M1 on the live new path) → first mismatched payment → Cutback; time shown on screen.

---
## H4 Contract Cleanup
**Job** — remove the switch and old code once the new path has fully taken over.
**Inside** — after LIVE_100 + soak (real: e.g. 14 days; demo: compressed) → PolyglotPiranha-style flag removal + ast-grep deletion of old flows → keep the **origin adapter** for legacy refunds until the last legacy capture is outside its refund window (or remove now if Step 6 proves Orders v2 can refund NVP captures) → PR → proof re-runs on the cleaned code.
**Check (Zen Cart)** — leave `paypalwpp` installed but not selectable until legacy orders age out; then uninstall.

---
## F1 PayPal Handoff File
**Job** — hand PayPal exactly what only PayPal can do, ready to act on.
**Out** — `handoff.json/csv`: `{type: BILLING_AGREEMENT|RECURRING_PROFILE, id, customer_ref, amount, currency, cycle, next_billing, status, source}` + validation summary (counts, totals per currency, duplicates, inactive) + freeze-window advice (no edits during PayPal's conversion; Stripe PAN-import lesson).
**Who** — deterministic extraction + Herald text.
**Check (Zen Cart)** — none in the demo store unless recurring is configured; shown on a seeded subscription shop.

## F2 Graft Card + PR
**Job** — explain everything in plain words, with proof attached.
**Out** — Graft Card (stages, every number explained, cost $, minutes, old/new mark per payment) + PR body (what changed, why, certificate link, how to roll back, PayPal-only items).
**Who** — Herald (Haiku); numbers copied from ledger, never generated.

---
## B1 Scion Bank Learner (GG-7)
**Job** — turn each success into a reusable, safe recipe.
**Inside** — certificate issued → Librarian generalises the diff into an ast-grep / PolyglotPiranha script + env recipe + scenario templates (SPELL-style) → **self-check**: re-apply to the original old code → must reproduce a passing proof → status QUARANTINE → ACTIVE after passing on K = 2 independent shops → confidence = Beta(passes+1, fails+1) mean → RETIRE on repeated failure; runtime misses from R1 become new detection rules.
**Who** — Librarian (Sonnet, Batch API −50%) + deterministic self-check.
**Check (Zen Cart)** — `zencart/legacy→paypalr` recipe stored; second Zen Cart shop: env ≈1 min, plan reused, Grafter writes only store-specific bits → time + $ drop shown (learning curve).

## B2 Orchard (PayPal team view)
**Job** — show PayPal's integration team the whole fleet and what each shop needs.
**Views** — funnel by stage · money by old family (T-codes) · deadline risk (WPS "may retire after 1 Jan 2027") · blockers · PayPal-only queue (handoff files) · cost/time per shop · learning curve.
**Who** — AG Studio dashboards; Orchard Analyst (Sonnet) answers questions by building dashboards through the Studio Agent Framework (talking to AG Studio's built-in agents).
**Honest label** — shows our test shops only.

## B3 Agent-ready Check
**Job** — tell the merchant whether the upgraded shop can take AI-assistant checkouts.
**Inside** — Orders v2 present + Google Pay eligibility + PayPal Agent Ready prerequisites (UCP with PayPal) → readiness list; sandbox route = GAP (Step 6), so reported as "ready by prerequisites", not "tested".

---
## X1 Cage
**Inside** — GitHub-hosted runner VM (fresh per job) → gVisor `runsc` for shop containers → phases: BUILD (package registries allowed, no secrets) → RUN (egress only PayPal sandbox hosts + tunnel; secrets mounted) → CPU/memory/time limits → any egress breach = kill + Sentinel alert.
## X2 Time Travel (renewals)
**Inside** — PayPal sandbox has no test clocks (Stripe has) → exercise renewal handlers with the webhook simulator and IPN simulator (recurring events — exact event list = Step 6 test); real renewal timing marked UNVERIFIED.
## X3 Knowledge Sync
**Inside** — nightly: fetch PayPal llms.txt indexes, RulesHub commits, AI Toolkit references → diff → new grounding version (recorded on each certificate) → Librarian re-validates recipes whose mappings changed.
