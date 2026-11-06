> **Status update — 6 November 2026.** The original body below is historical reference and is superseded for current target behaviour by reviewed engineering documents. Read [engineering baseline](../engineering/START_HERE.md), [current/proposed boundary](../engineering/CURRENT_VS_PROPOSED.md) and [atomic lifecycle protocols](../engineering/lifecycle/ATOMIC_DELIVERY_PROTOCOLS.md). Paper only; no implementation or live qualification. Earlier schedules/coverage/Done claims in the retained body are not current status.

---

# P12 · 00 — GoldGraft, the whole system on paper (Claude, 1 Nov 2026)
Files: 00 system · 01 data · 02 Gate + Rootstock · 03 Scion · 04 Union Proof · 05 Heal + Handoff + Fleet · 06 agents + services · 07 frontend + API · 08 Zen Cart trace · 09 demo + gaps.

## 1. One picture
```
 MERCHANT / PAYPAL TEAM / JUDGE
   │ repo URL · site URL · "Graft Probe"
   ▼
┌──────────────────────── CONTROL PLANE (Render, always on) ─────────────────────────┐
│ Web app (React) ── API (REST + SSE) ── Key Guard (Doppler) ── Budget Governor       │
│                         │                                                           │
│                 STAGE MACHINE (durable, Postgres)  ◀──events──▶  GRAFT LEDGER       │
│                         │                                       (append-only,       │
│                         │ assigns                                hash-chained)      │
│          ┌──────────────┴────────────── AGENTS (Claude Agent SDK, Render Workflows)│
│          │ Gardener · Surveyor · Builder · Explorer · Scribe · Architect · Grafter  │
│          │ Adversary · Healer · Librarian · Herald · Orchard Analyst · Sentinel     │
│          └──────────────┬───────────────────────────────────────────────────────── │
│                         │ dispatch heavy run (workflow_dispatch, signed job spec)   │
└─────────────────────────┼───────────────────────────────────────────────────────────┘
                          ▼
┌──────── RUNNER (GitHub Actions VM, fresh per job, public repo = free) ─────────────┐
│  CAGE (gVisor) ┌──────────────┐   capture proxy ── rate limiter (45 req/min/IP)    │
│                │ shop  OLD    │──▶ (mitmproxy / Keploy) ──────────────┐            │
│                │ shop  OLD'   │   (noise twin)                        │            │
│                │ shop  NEW    │                                       ▼            │
│                └──────▲───────┘   cloudflared tunnel ◀── returns, IPN, webhooks    │
│                       │ buyer                                    PAYPAL SANDBOX    │
│        Playwright driver / KERNEL headful browser  ───────────▶ NVP · WPS · IPN    │
│                                                                  Orders v2 · v6    │
│  Deterministic: Recipe Runner · Union Judge · MMO-12 runner · Capture→CMEL         │
│  Signer (Sigstore keyless, GitHub OIDC) ──▶ Rekor public log                       │
└────────────────────────────────────────────────────────────────────────────────────┘
        │ artifacts + evidence (R2)            │ PR (GitHub App, least privilege)
        ▼                                      ▼
  Graft Card · Certificate page · Orchard (AG Studio)      merchant repo
```

## 2. The Graft Cycle as a durable stage machine
```
CREATED → GATED → SURVEYED → BUILT ──────────────┐
                     │          └▶ LANE:NO-RUNTIME ┤ (map + plan + rewrite + static; certificate = PARTIAL)
                     └▶ LANE:NO-CODE ─▶ LINKS_PROVEN ─▶ DELIVERED
BUILT → RECORDED → CONTRACTED → ATTACK_PLANNED → GRAFTED → PROVING ⇄ REPAIRING (≤2)
PROVING → CERTIFIED (or PARTIAL / FAILED) → PR_OPEN → MERGED (merchant consent)
MERGED → SHADOW → HEAL_1 → HEAL_10 → HEAL_50 → LIVE_100 → CLEANUP_PR → DONE
any HEAL_* ──money break──▶ CUTBACK ──fix──▶ GRAFTED
every arrow = 1 ledger entry; every stage worker is idempotent on (graft_id, stage, attempt); crash → resume at last entry
```

## 3. Trust boundaries (who may do what)
| Zone | May | May never |
|---|---|---|
| Control plane | store state, call LLMs, sign switch configs, open PRs (GitHub App) | run shop code |
| Runner VM | run shop code in Cage, call PayPal **sandbox**, sign certificates (OIDC identity) | hold live PayPal keys, reach anything except registries (build phase) + PayPal sandbox + tunnel |
| Quarantined agents (Surveyor, Builder, Explorer, Scribe) | read untrusted repo/site text | trigger privileged actions; their output is schema-checked data only |
| Privileged steps (verdict, sign, PR, switch) | — | be decided by an LLM |

## 4. Design audit (artificers-forge §12, applied)
| Area | Check | GoldGraft answer |
|---|---|---|
| Capacity | peak load | demo: ≤20 parallel runner jobs (GitHub Free limit); PayPal sandbox ≤45 req/min per runner IP |
| Hot path | timeouts, bounded retries | every agent/tool call has a timeout + exponential backoff with jitter; repair ≤2 rounds |
| Caching | hot reads | prompt cache on the shared PayPal-docs prefix; OAuth tokens cached; base images cached |
| Database | indexes, backup | ledger indexed by (graft_id, seq); daily export to R2 |
| Async | idempotent consumers, dead-letter | stage workers idempotent; failed stage → `FAILED` with reason (dead-letter) visible on Graft Card |
| Failure | SPOFs, degradation | KERNEL down → local headless; PayPal 429 → pause + reroute; LLM error → retry/fallback model; control plane down → runners finish + write to R2, ledger catches up |
| Observability | logs, metrics, alerts | structured logs with graft_id; Sentry (student pack); per-stage time + $ on the Graft Card |
| Security | auth, rate limit, secrets vault, egress | GitHub login; quotas; Doppler; runner egress allowlist (P10) |
| Cost | idle shutdown | Budget Governor caps; runners are ephemeral |
