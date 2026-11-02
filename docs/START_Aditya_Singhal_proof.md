# START HERE — Aditya Singhal · Proof + maths

## Your job in one line
Build the **proof library**: the code that decides — with maths, never with AI — whether the new PayPal code handles money exactly as well as the old code, how strong that proof is, when it is safe to move more buyers, and the tamper-proof certificate at the end.

## GoldGraft in two lines
Old online shops use old PayPal code that PayPal is retiring. GoldGraft's AI agents rewrite it to PayPal's newest version; **your library is the judge** that proves the rewrite is safe. Full picture: [README](../README.md), [docs/design/00_SYSTEM.md](design/00_SYSTEM.md).

## What you own
| Part | In plain words | Design |
|---|---|---|
| Money language mapper (`to_cmel`) | turns a recorded run (old or new PayPal messages) into one common list of money events (INTENT, CAPTURE, REFUND, SHOP_PAID …) | [01_DATA.md §3](design/01_DATA.md) — the mapping table |
| Union Judge (`judge`) | compares old shop, old shop run twice (to learn what is just "noise" like random IDs), new shop, and PayPal's own records → a verdict: PASS, PASS_FIXED (old shop had a bug, new one fixed it), PROBLEM, UNVERIFIED, N/A | [04_UNION_PROOF.md U2](design/04_UNION_PROOF.md) |
| Money rules R01–R16 | e.g. "a shop marks an order paid only if PayPal shows one completed capture" | [01_DATA.md §4](design/01_DATA.md), `contracts/.../base_rules.py` |
| Proof strength (`proof_strength`) | we plant 12 kinds of money bugs in the new code; score = bugs caught ÷ bugs planted | [01_DATA.md §5](design/01_DATA.md) (MMO-12), [04 U3](design/04_UNION_PROOF.md) |
| Go-live maths (`heal_decide`) | Beta-Binomial: move buyers 1% → 10% → 50% → 100% only when P(new success rate ≥ old − 2%) ≥ 0.95 with ≥ 30 new payments; switch back at once on any money-rule break | [05 H2](design/05_HEAL_HANDOFF_FLEET.md) |
| Recipe confidence (`recipe_confidence`) | mean of Beta(passes+1, fails+1) | [05 B1](design/05_HEAL_HANDOFF_FLEET.md) |
| Certificate (`verify_certificate` + signing) | a public, re-checkable record; changing one byte must make it fail | [01_DATA.md §6](design/01_DATA.md) |

## Your folder
`pieces/proof/`. Pure Python, no servers, no internet, no AI. Import only from `contracts/`.

## The exact functions you implement
They are written down in `contracts/src/goldgraft_contracts/interfaces.py` (class `Proof`). Your class must have the same method names and argument types — that is what makes it plug in.

## What you test against: answer keys (no other piece needed)
All in `fixtures/proof/legacy-php-shop/` (see `fixtures/INDEX.md`; every file is labelled SYNTHETIC or REAL):
| Folder | Input → expected output |
|---|---|
| `raw/` → `cmel/` | recorded runs → the money events your mapper must produce |
| `cmel/` + `contract.json` + `target_plan.json` → `expected/*.verdict.json` | the verdict your judge must give for each scenario (9 scenarios, every grade appears at least once) |
| `mutants/` → `expected/proof_strength.json` | planted bugs + which tests caught them → the score |
| `heal/case_*.events.json` → `heal/case_*.expected.json` | payment streams → go-live decision (probabilities included; `fixtures/tools/heal_reference.py` is an exact reference) |
| `certificate/` | a valid certificate and a tampered one |

The real recordings from the PayPal sandbox will be added by Aditya Vijay; your tests should then pass on those too.

## Your plug-in test (your "done")
```bash
GOLDGRAFT_PROOF=pieces.proof.proof:Proof uv run pytest plugtests/test_proof.py
```
Without the variable it runs against the stand-in (which just looks answers up). When it passes with your class, your piece plugs in.

## Dates
3–6 Nov build · **6 Nov night: plug-in test green** · 7–8 Nov Aditya plugs in · 8 Nov freeze.

## Ask Aditya when
an answer key looks wrong to you (tell him which file and why — answer keys can have mistakes), or you need a format change.
