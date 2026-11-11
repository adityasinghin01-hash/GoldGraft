# Next-agent efficiency playbook — measured on Surveyor (11 November2026)

Goal: each later agent reaches its ceiling with fewer paid calls, inside its own
envelope of the $10 project budget for all 13 agents. Every rule below comes from
a measured Surveyor result.

| # | Do this | Why (measured on Surveyor) |
|---|---|---|
| 1 | **Free work first:** deterministic/offline runs, then a sizing dry run through the real runtime + gateway using the provider's free `count_tokens` and scripted outputs | Found 3 blocking limits at $0 (byte bound, 24 KB synthetic context, 4-turn cap) that would otherwise have failed paid runs |
| 2 | **Bound input by provider token count, not bytes** | Count matched actual input on **197/197** responses; the byte bound wasted ~⅔ of every paid 24k-token turn |
| 3 | **Cache the fixed tools+system prefix** (one `cache_control` on the system block; price writes 1.25× and reads 0.05× on Sonnet 5.5) | Same cases 26–37% cheaper with identical results; run each series back-to-back so the 5-minute cache stays warm |
| 4 | **Route the model before dispatch from the task's shape**; never escalate as a retry | Haiku 41/41 at ≤2 files (~$0.002/run); fails at ≥3 files (puts 5–7 calls in one response). Sonnet 8/8 at 5–16 files (~$0.07–0.17 cached) |
| 5 | **Give the model derived progress** (unread items, `ready_to_submit`, `next_calls`), never answers | Repeat reads stopped: 37 → 27 turns per 14-case round (−26%); 5 failing single-file cases became 2-turn passes |
| 6 | **Record closed rejection labels** (`tool_call_count`, `undeclared_tool`, …) and block counts in the signed audit | One cheap run identified the 7-call cause instead of guessing |
| 7 | **Stop a tuning line after two failed variants**, then change the model or the profile | Two prompt variants for the 4-call cap failed; switching to Sonnet fixed it at once |
| 8 | **Pilot once per case; repeat only passing cases**; run hold/negative cases at zero cost with a provider that raises on any call | 30/30 holds proved for $0; paid repeats went only to cases that had already passed |
| 9 | **Enforce the agent's envelope before every paid run** (prep refuses when spent + estimate > allocation); one reservation at a time | Surveyor stopped exactly inside its extended $1.25 envelope |
| 10 | **Never replay an unknown request**; author a separate case instead | Kept the original unknown intact while still covering its case |

Not yet built, with estimated upside:
- A second cache breakpoint after stable task inputs (put them before the growing
  observations in their own block). Should raise savings further on long loops.
- The Message Batches API (50% off) for multi-case evaluation rounds: send turn N for
  every case in one batch. Only worth it where hours of latency are acceptable.

Per-agent starting point: Herald needs no paid model (closed catalog, deterministic
fallback). Its envelope can fund Zapier delivery checks once Aditya connects an
approved destination.
