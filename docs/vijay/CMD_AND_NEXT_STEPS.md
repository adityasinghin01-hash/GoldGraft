# CMD restart and next steps

Latest complete offline workflow: `scripts\finish-local.cmd`. It adds actual counterpart and shop-socket/proof checks, then builds the local handoff ZIP. All prerequisites are recorded in [FINAL_LOCAL_STATUS.md](FINAL_LOCAL_STATUS.md). This does not run real providers, push or deploy.

12 November: the separate NEW candidate can be checked with `scripts\check-candidate.cmd`. It runs native PHP, persistent state, staged-origin continuity and a private Playwright browser flow using scripted responses only. No credential entry, Docker, download or provider call is required. [LOCAL_PHASE_DELIVERY.md](LOCAL_PHASE_DELIVERY.md) supersedes older implementation/dependency statements below.

Closing the credential wizard or CMD does not remove saved `.secrets/sandbox.json`. Presence was checked on 9 November: REST seller, NVP seller, buyer and recipient are all configured with no missing/invalid fields. This is a local presence check; the operator's earlier OAuth/GetBalance PASS remains separately recorded. Do not re-enter secrets unnecessarily.

## Check saved setup

Open CMD and run each line separately:

```cmd
cd /d "C:\Users\Aditya\Documents\ChatGPT\paypal"
scripts\sandbox-status.cmd
```

All four groups should show configured true. The command prints field names/status only and makes no provider request. PayPal Sandbox is remote; it does not require a CMD window to remain open. Configuration is loaded explicitly by relevant scripts rather than stored only in a terminal session.

## Run all implemented local checks

```cmd
scripts\check-all-local.cmd
```

This runs offline tests, switches, a synthetic rollout-decision consumer, USD cart validation, current-model shop manifest validation, shop start/buyer/stop and read-only synthetic state inspection. Green means local components passed, not payment/runtime/whole-phase qualification. Missing state fixtures or contract dependencies remain HOLD, not a silent successful skip.

## Optional: keep the offline reference shop running

In the first CMD window:

```cmd
cd /d "C:\Users\Aditya\Documents\ChatGPT\paypal"
scripts\start-offline-shop.cmd
```

Leave that window open while using this optional local server. In a second CMD window:

```cmd
cd /d "C:\Users\Aditya\Documents\ChatGPT\paypal"
scripts\buyer-offline-shop.cmd
```

The buyer supplies local lab authorization privately and checks only cart/access behaviour. Direct unauthenticated browser access returns 401 by design. All payment/callback execution remains disabled. Stop this local server with Ctrl+C in its own window; its source/state copies are disposable and no PayPal transaction is reset. This is separate from your saved credential setup.

## Only if credentials later need changing

```cmd
python scripts\sandbox_config.py --configure
```

Use right-click to paste hidden input; Enter keeps an existing value. Never paste secrets in chat or use normal PayPal login credentials in these API/buyer fields.

## Further work

Fetch [TEAM_INPUTS_NEEDED.md](TEAM_INPUTS_NEEDED.md) from the team leader: actual GU02/GU03 broker/runner/recorder/gateway code and setup, approved SI01 interfaces where required, and actual SH01/SH02 mapping/proof invocation. No credentials are needed in the reply. The remaining genuine payment, candidate integration, rollout/apply, state migration and independent exit qualification cannot complete before those dependencies exist.

Current local stage-consumer work is described in [PHASE4_LOCAL.md](PHASE4_LOCAL.md); it does not replace proof or authenticate/apply real decisions. No push is authorized by running these commands.
