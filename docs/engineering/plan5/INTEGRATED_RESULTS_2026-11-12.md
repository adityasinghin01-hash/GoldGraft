# Integrated agent runs — results

Every row is one connected run with real model calls (scripted runner for builds and
payment scenarios). Status follows the agent chain; side branches are reported per agent.

| Run | Shop | Status | Agents passed | AI cost | Code written |
|---|---|---|---|---|---|
| i1-smoke | legacy-php-shop | held_at_survey | 1 of 2 | $0.001 | no |
| i1-smoke2 | legacy-php-shop | held_at_orchard-aggregate | 12 of 13 | $0.242 | no |
| r1-eval-nvp | eval-nvp | completed | 11 of 12 | $0.109 | no |
| r1-eval-nvp-noconsent | eval-nvp | completed | 11 of 12 | $0.103 | no |
| r1-legacy-1 | legacy-php-shop | completed | 11 of 12 | $0.241 | no |
| r1-legacy-2 | legacy-php-shop | completed | 10 of 12 | $0.206 | no |
| r1-legacy-3 | legacy-php-shop | completed | 11 of 13 | $0.205 | no |
| r1-legacy-4 | legacy-php-shop | held_at_baseline-old-twin | 5 of 5 | $0.132 | no |
| r1-legacy-5 | legacy-php-shop | held_at_survey | 1 of 2 | $0.124 | no |
| r2-realcode-1 | legacy-php-shop | held_at_survey | 1 of 2 | $0.137 | no |
| r2-realcode-2 | legacy-php-shop | held_at_survey | 1 of 2 | $0.057 | no |
| r2-realcode-3 | legacy-php-shop | held_at_scribe-final | 6 of 6 | $0.138 | no |
| r2-realcode-4 | legacy-php-shop | held_at_grafter | 7 of 8 | $0.324 | no |
| r2-realcode-5 | legacy-php-shop | held_at_grafter | 7 of 8 | $0.187 | no |
| r2-realcode-6 | legacy-php-shop | held_at_grafter | 7 of 8 | $0.310 | no |
| r2-realcode-7 | legacy-php-shop | completed | 13 of 13 | $0.376 | yes |
| r3-eval-nvp-1 | eval-nvp | completed | 13 of 13 | $0.215 | yes |
| r3-legacy-1 | legacy-php-shop | completed | 13 of 13 | $0.402 | yes |
| r3-legacy-2 | legacy-php-shop | completed | 13 of 13 | $0.390 | yes |
| r4-final-legacy | legacy-php-shop | completed | 13 of 13 | $0.450 | yes |
| web-eval-nvp-20261112-001734 | eval-nvp | held_at_followup-0 | 6 of 6 | $0.016 | no |
| web-legacy-php-shop-20261112-001347 | legacy-php-shop | completed | 13 of 13 | $0.374 | yes |

Total AI cost of these runs: $4.739361

| Model | Agent steps | AI cost | Share |
|---|---|---|---|
| sonnet | 66 | $4.301 | 91% |
| haiku8 | 167 | $0.358 | 8% |
| haiku | 56 | $0.080 | 2% |

(haiku = claude-haiku-5-5 with up to 4 turns; haiku8 = the same model with up to 8 turns;
sonnet = claude-sonnet-5-5. Run totals equal the sum of step costs, which equal the
ledger's change over these runs.)

| Agent | Passed / attempts | Models | AI cost | Holds (codes) |
|---|---|---|---|---|
| Adversary | 24/24 | haiku8, sonnet | $0.523 | — |
| Architect | 15/15 | sonnet | $0.415 | — |
| Builder | 30/30 | haiku8 | $0.093 | — |
| Explorer | 63/65 | haiku8 | $0.140 | INVALID_MODEL_OUTPUT×1, MISSING_EVIDENCE×1 |
| Gardener | 22/22 | haiku | $0.023 | — |
| Grafter | 12/15 | haiku8, sonnet | $0.991 | INVALID_MODEL_OUTPUT×3 |
| Healer | 10/12 | haiku8, sonnet | $0.215 | INVALID_MODEL_OUTPUT×2 |
| Herald | 18/18 | haiku | $0.027 | — |
| Librarian | 8/13 | haiku8, sonnet | $0.127 | DENIED×3, INVALID_MODEL_OUTPUT×2 |
| Orchard Analyst | 6/8 | haiku8 | $0.006 | DENIED×2 |
| Scribe | 32/33 | haiku8 | $0.044 | DENIED×1 |
| Sentinel | 12/12 | haiku | $0.020 | — |
| Surveyor | 18/22 | haiku, sonnet | $2.115 | MISSING_EVIDENCE×3, INVALID_MODEL_OUTPUT×1 |

Hold codes: DENIED = a deterministic gate refused (small cohort, no consent: correct);
INVALID_MODEL_OUTPUT / TURN_LIMIT = the model's answer was refused (counts toward the
two-strike Sonnet rule); MISSING_EVIDENCE = required input or reading incomplete.
