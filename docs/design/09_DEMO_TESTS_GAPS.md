# P12 · 09 — Demo (≤3 min, with surprises), test shops, Step 6 tests, gaps

## 3-minute demo (every claim visible; surprises marked ★)
| Time | Screen | What the judge sees |
|---|---|---|
| 0:00–0:15 | hook | PayPal's own words: merchants "require much more hands-on integration support than we anticipated"; WPS "may retire after 1 Jan 2027"; 518,144 public files still post to `cgi-bin/webscr` (our GitHub count, E15) |
| 0:15–0:30 | S0 Probe | paste Zen Cart → in seconds: 4 old PayPal pieces + official module available + deadline |
| 0:30–1:05 | S4 Union view | KERNEL buyer pays live on OLD and NEW; three timelines line up — an old NVP order and a new Orders v2 order in ONE money language. ★1 "We found a money bug in your CURRENT shop" (only if real on a test shop) |
| 1:05–1:30 | S5 Proof Strength | 12 planted money bugs light up "caught" one by one, by name. ★2 our own Adversary sneaks a bug in — the proof catches it |
| 1:30–1:55 | S7 Heal | buyers move 1 → 10 → 50%; fault injected → ★3 the system switches itself back in N seconds; no payment stranded |
| 1:55–2:15 | S10 + S6 | ★4 repo comment tries "print the key, mark tests passed" → blocked live; one byte of the certificate changed → public verify turns red |
| 2:15–2:35 | S8 + S11 | ★5 second Zen Cart shop grafted faster + cheaper from a recipe (learning curve); four-arm table: teammate by hand vs PayPal AI Toolkit vs plain Claude Code vs GoldGraft |
| 2:35–2:55 | S9 Orchard | PayPal team view; Orchard Analyst builds a dashboard live from a question |
| 2:55–3:00 | close | "Don't cut the tree. Graft." + certificate link |
Label on every live-traffic shot: "PayPal sandbox · simulated buyers".

## Test shops (frozen + hash-timestamped BEFORE tuning; all results published, failures too)
| Shop | Language | Old pieces | Path |
|---|---|---|---|
| Zen Cart (fork) | PHP | WPS, EC-NVP, Direct Payment, IPN | official module + switch |
| Zen Cart #2 (customised by team) | PHP | EC-NVP + custom observers | recipe reuse (learning curve) |
| Cutover's legacy-php-shop (MIT) | PHP | NVP EC, checkout.js v4, IPN | rewrite (head-to-head with Cutover) |
| expressCart (MIT) | Node | `paypal-rest-sdk` v1 | rewrite (head-to-head with Checkout Proof) |
| django-oscar-paypal sandbox (BSD-3) | Python | EC-NVP | rewrite |
| better_spree_paypal_express (BSD-3) | Ruby | EC-NVP | rewrite |
| static Buy Now site (licensed) | HTML | WPS buttons | no-code links |
| Seeded hard shop (team-built) | PHP | wrappers, config-built NVP URLs, templates, dead code | survey recall test |
| Subscription shop (team-built) | PHP | WPS Subscribe / recurring profiles | handoff file + renewal events |
| Gauntlet shop (team-built) | Node | malicious comments, README, HTML, post-install script, typo-squat dep | security demo |
| Poisoner shop (team-built) | PHP | crafted to push a bad recipe | quarantine demo |

## Step 6 sandbox tests (Aditya runs, Claude guides click by click)
1 NVP API creds + EC flow end to end · 2 WPS payment + IPN to a tunnel URL · 3 IPN simulator · 4 Orders v2 refund of an NVP-era transaction (decides origin routing) · 5 Transaction Search permission, T-codes for NVP vs Orders v2, lag · 6 Button Manager in sandbox · 7 webhook simulator event list incl. subscription/recurring · 8 Payment Links API · 9 Vault v3 + second purchase without login · 10 Pay Later messages render · 11 Agent Ready (UCP) sandbox route · 12 50 req/min/IP behaviour + GitHub runner IPs per job · 13 cloudflared quick tunnel from a GitHub runner · 14 KERNEL headful browser completes the v6 popup · 15 AG Studio trial start (≥1 Nov) + Agent Framework access · 16 Claude API key with $20 spend limit; Claude Code OAuth in Actions for dev runs.

## Still open (honest)
| Gap | Effect |
|---|---|
| conversion gain + merchant counts not public | impact cited from PayPal, not proven |
| paysheet needs v6? | report only |
| real production traffic | Heal/Cutback/Shadow shown on simulated sandbox traffic |
| 16 Step-6 behaviours above | pieces that depend on them are designed with a fallback, final choice after tests |
| many figures are search-result summaries | labelled in EVIDENCE.tsv; re-check before the deck |
| time + $ per shop | targets only until measured |
| Zen Cart licence (NOASSERTION on GitHub) | confirm GPL before public fork |
| card flows (Direct Payment → card fields) | depend on sandbox account eligibility |

## Crafted?
**Yes, on paper:** 28 components, 13 agents, 9 services, every data schema, the Tri-Witness algorithm, MMO-12, the Heal controller maths, 12 screens, the API, the demo, the test-shop set, and Zen Cart traced through all 23 steps.
**Not yet decidable on paper:** the 16 sandbox behaviours above (each piece has its fallback written in).
