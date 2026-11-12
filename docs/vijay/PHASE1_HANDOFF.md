# Phase 1 counterpart handoff — 8 November 2026

Current correction, 12 November: backend and runner are present, and proof PR1 is merged with a documented fixture adapter. The earlier .gitkeep-only finding below is historical. Real broker/isolation/recorder/callback qualification and accepted new SI01 formats remain open. See [TEAM_UPDATE_2026-11-12.md](TEAM_UPDATE_2026-11-12.md); no general code-location clarification is still needed.

**Local preparation: ready for counterpart integration. Full Phase 1: HOLD.** This is an unsent handoff document, not a teammate agreement, approved wire record, payment proof or authorization to deploy.

## Source-backed dependency finding

The Drive current guide remains modified 6 November 2026 09:29:50 UTC. Connected team main still resolves to `da2b5f02d5559c510de6b3b9d81e58400bdf6c89`. Its recursive tree has only `.gitkeep` in `pieces/backend` and `pieces/runner`. The user separately confirmed those implementations are not ready. This finding is limited to inspected main and the user's confirmation, not a claim that no private branch could exist.

Normative engineering references: [Vijay VJ01/VJ02](https://github.com/adityasinghin01-hash/GoldGraft/blob/da2b5f02d5559c510de6b3b9d81e58400bdf6c89/docs/START_Aditya_Vijay_paypal_shops.md), [shared dependencies](https://github.com/adityasinghin01-hash/GoldGraft/blob/da2b5f02d5559c510de6b3b9d81e58400bdf6c89/docs/engineering/work/SHARED_INTERFACES_AND_DEPENDENCIES.md), [baseline reproduction](https://github.com/adityasinghin01-hash/GoldGraft/blob/da2b5f02d5559c510de6b3b9d81e58400bdf6c89/docs/engineering/lifecycle/BASELINE_REPRODUCTION.md).

## Available inputs from Vijay

- Fifteen unchanged MIT application files in `pieces/shops/legacy-php-shop/vendor/src`, original licence and source manifest; 22-file complete static inventory in `phase1/source_inventory.json`.
- PHP 8.3 pinned Docker recipe, independently working trusted-reference Windows lab and separate per-run synthetic state. Windows checks do not qualify a Linux execution image or malicious-code isolation.
- Fourteen scenarios with acceptance references, expected semantics and explicit unrun status; [live execution runbook](../../pieces/shops/legacy-php-shop/phase1/LIVE_RUNBOOK.md).
- Private local sandbox REST/NVP seller, buyer and recipient configuration. Operator-reported OAuth and GetBalance PASS; credentials are not included in this handoff or transferred to shop code.
- Python 3.12: 30 offline tests passed. Node 22.23.4 + PHP 8.3.36 + Chromium 156.0.8078.4: actual offline cart/access/restart checks passed, run `20261108T125243238137Z`.

## Required counterpart deliverables

| Owner | Required before real payment qualification |
| --- | --- |
| Gupta GU02 | Qualified sandbox broker, account/environment/run binding, allowed operations, secret custody, bounded request policy and reconciliation behaviour |
| Gupta GU03 | Protected runner with exact source/image/runtime identity, independent OLD/OLD_TWIN/NEW state, actual recorder, trusted callback gateway and authenticated operation/termination records |
| Singh SI01 | Approved versioned new bootstrap/evidence formats wherever existing Python contracts are insufficient; no invented replacement fields |
| Singhal SH01/SH02 | Real-capture mapping, independent money rules and deterministic verdict/evidence completeness integration |

The existing `Runner.run_job(JobSpec) -> JobResult`, `Runner.fetch_capture(ref) -> RawCapture`, and `PayPalClient.nvp/rest` protocols were inspected. They are current typed boundaries, not implemented services or proof of account authority. Existing `JobResult.runner_identity` requires GitHub workflow/SHA/run fields; a Windows component run cannot fabricate them. New lifecycle formats await SI01.

## Resume sequence

1. Inspect the actual counterpart revision, implementation and approved current schemas; preserve role boundaries and record compatibility gaps.
2. Verify sandbox authority, fixed source/runtime/build identity, protected helper access, callback ingress, quotas and recorder redaction before dispatching any payment effect.
3. Execute the live runbook with distinct run/order identities and retain every required failure or unavailable capability. Never use offline answers as real recordings.
4. Obtain proof-owner results from actual captures; report baseline defects separately from desired correctness. Only then reassess the full Phase 1 gate.

Safe local status command (no network, prints names/status only):

```cmd
python scripts\phase1_status.py --config .secrets\sandbox.json
```

Exit 2 is intentional while the full phase is held. It does not invoke a provider, shop or remote workflow. This work was initially prepared locally; the user subsequently requested publication of the continuation to the personal repository. Publication does not close the payment gates. The earlier publication was `60f6ab2626f07eba46c943ab2cb9f656af79bc5d`; later publication identity is recorded in Git history and the delivery response. Use [TEAM_INPUTS_NEEDED.md](TEAM_INPUTS_NEEDED.md) as the request to take to the leader.
