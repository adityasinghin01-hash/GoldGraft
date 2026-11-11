# Phase 0 — concrete driver request

**Superseded ownership:** Aditya subsequently made Claude frontend-only and
assigned Codex all non-frontend work, review, commits/pushes and handoff.
This is a historical source-preparation record; Codex now finishes and commits
the main integration, and completes the remaining GU/SH/VJ component gaps.

Prepared for Claude; not sent externally. No approval is sought for a vague
future operation: the exact revisions, preserved state and preflight are below.

**Source-preparation request now closed:** Aditya instructed Codex to use main.
Main is attached to the build workspace and the exact incoming merge is prepared
without commit. The old original checkout is detached with its dirty files
preserved. Both obsolete integration branch names were removed locally and on
GitHub. Claude's remaining Git step is to review/commit/push the prepared result;
do not rerun the older source-migration request below. See
[current workspace record](MAIN_WORKSPACE_CHANGE_2026-11-11.json).

## Integrate the current teammate revision

Build workspace: `/Users/aditya/dev/GoldGraft-plan5-build`.
Branch: `codex/agents-from-scribe-20261111`.

| Revision | Exact value |
|---|---|
| Agent head | `c9f9ee9a5477660f06f03e4891832f9ce722be71` |
| Main input | `aee298f31b13a6a6c76d28845b43763b948add7b` |
| Common ancestor | `d5572353f9b17777316b238833910b4385e78419` |
| Conflict-free scratch candidate tree | `3387868630cf4df9349577b7ce92e7a883dcb6e8` |

The scratch preflight does not include uncommitted documentation. Preserve the
dirty docs and new plan/audit/evidence files listed by `git status`; no stash,
reset, wholesale checkout or unrelated reformatting. Review how to retain them
before performing the driver-owned merge/commit. The preflight is not a merge
performed in the user's working branch.

Read-only rechecks:

```sh
git status --short
git rev-parse HEAD
git -C /private/tmp/goldgraft-github-audit-20261111 merge-tree --write-tree c9f9ee9a5477660f06f03e4891832f9ce722be71 aee298f31b13a6a6c76d28845b43763b948add7b
```

The last command may write Git tree objects in the scratch clone; it creates
no commit or branch merge. If either input changes, recompute and review the
new result; do not assume this tree still applies.

## Counterpart requirements to return

Gupta: actual implementations for the existing 23 v2 service routes and durable
TaskControl/runtime artifact/tool bindings; source/custody/readiness; isolated
execution/capture; authenticated callback handling; actual image/publish/deploy;
state/effect/recovery/exit evidence. Existing legacy APIs and success-generating
provider scaffolds do not close this handoff.

Singhal: actual independently authenticated lifecycle observations and safe
projection/API consumer; real domain/payment witnesses consumed by proof;
merchant certificate verification/re-fetch once those inputs are qualified.

Vijay: actual pinned reference recipe/driver, scenario and mutation coverage,
payment/origin/pending/refund/state/exit witnesses, and relevant sponsor inputs.

Return each counterpart's commit, exact protocol implementation, meaningful
negative checks, evidence class and unresolved gates. Codex integrates through
contracts; no request is made to expose secrets or let the model invent evidence.

## Budget preparation, not a cap request

Current ledger is clear at $3.353287/$10; no money reset. Three role stress
forecasts exceed their remaining envelopes. After actual tool contexts exist,
Codex must produce exact free sizing and a proposed bounded paid allocation
before dispatch. Keep all current caps and original failure/repeat denominators.
Do not raise a cap or release a hold as part of this source integration.
