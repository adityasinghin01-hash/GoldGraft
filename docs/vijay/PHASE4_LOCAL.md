# Local rollout-decision consumer

12 November continuation: the separate PHP candidate now runs with the actual PHP switch library in synthetic 0/1/10/50/100, Cutback and expiry tests. Persisted NEW capture/refund origins survive admission changes. See [LOCAL_PHASE_DELIVERY.md](LOCAL_PHASE_DELIVERY.md). This adds component integration, not authenticated operational apply, Shadow evidence or measured live Cutback.

Implemented independently using the unchanged current `HealDecision` Python model at team revision `da2b5f02d5559c510de6b3b9d81e58400bdf6c89`. New lifecycle formats and real integration remain pending their actual approved counterparts.

`pieces/switch-libs/python/rollout.py` consumes a dict through the existing model and returns only a proposed stage. It rejects a wrong graft, stale from-stage, illegal/skipped transition, invalid success counts, boolean current stage and a hard stop incorrectly paired with promotion. Current-model validation owns transition/count rules; Vijay's component does not recreate proof maths or determine whether traffic is sufficient.

`scripts/check_rollout.py` verifies the pinned model source bytes, then exercises twelve synthetic cases: the four promotions 0→1→10→50→100, HOLD, CUTBACK and six negative conditions. Synthetic statistics are labelled test inputs, not measured traffic or a real proof-owner verdict. It writes only an ignored local report, performs zero provider calls and applies zero decisions.

The component **does not** authenticate the sender, bind evidence to runtime/generation/resource fences, grant permission, sign/publish config, deliver guard events, run Shadow traffic, apply routing or measure real Cutback. Those are required before operational integration. No real rollout/Phase 4 gate is passed by this consumer test.

Run with the isolated Python 3.12 environment:

```cmd
D:\DevTools\GoldGraft\switch-venv\Scripts\python.exe scripts\check_rollout.py
```

The full local command also includes this check: `scripts\check-all-local.cmd`. New shared models are not added or changed. The consumer imports only the current shared contract; it is not backend or proof implementation.
