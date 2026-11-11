# Phase5.3 B0 — preservation and isolated workspace

10 November 2026. **B0 complete; B1–B7 not started.** This report supersedes historical “Phase5.3 not started” notices only for the B0 setup described here. The latest user instruction is one phase at a time, with this report before B1. Codex performed B0 directly; no sub-agents or frontend builder were launched.

## Workspace and inspected base

- Construction root: `/Users/aditya/dev/GoldGraft-plan5-build`.
- Branch: `plan5-build-20261110`.
- Inspected accepted base: `0365c5e1adcb1875a7f72c99dc7c63631501e131`, the observed remote main on 10 November 2026.
- Original root remains `/Users/aditya/dev/GoldGraft`, on main at `05b5b3beb37a2ac4b242c9ff0cb34f387f200e9f`, with its existing dirty/untracked work intact.
- Existing Plan2 publication worktree retained at its original revision.
- A Git linked worktree was created at the explicitly required path. The available managed-worktree creator has no destination argument; no managed attachment existed. No reset, clean, stage, commit, push, merge or remote publication occurred.

The selected base includes the merged GU backend/runner and Node switch contributions. Code inspection confirms that the current runner loads saved fixture captures and supplies a fixed workflow identity, custody stores values in an in-memory dictionary, lifecycle/control state is in memory, and callback handling checks header presence/deduplication without the qualified durable IPN/webhook verification protocol. These limitations were independently reinspected; source inspection and baseline tests do not qualify real payment, isolation or delivery behavior.

Proof PR1 remains open/unmerged at `e4b2594f5079ba7cac92b5a3a6dcdb447f02cdd0`. Its proof source and handoff were inspected through Git objects; they were not merged, copied over main, or executed. No separate newer VJ implementation was established from the inspected remote heads. Unpushed/local teammate work remains unknown, not presumed absent.

## Preservation and documentation reconciliation

- 496 files backed up with SHA256 and byte readback: 420 original-checkout files, 57 Desktop frontend files and 19 Desktop design-research files; 8,526,329 bytes total.
- Three fresh-path restore probes passed. Backup bytes, manifests, source inspections and command traces remain in a private report directory outside the repository.
- Final verification: all 496 source/backup pairs unchanged; original status, HEAD and index unchanged; no added original/protected files.
- The original source inventory excludes Git internals, virtual environments, installed dependencies and disposable caches. It includes existing local ledger data and source/reference files. This is a development-file backup, not merchant database-recovery qualification.
- All 16 reviewed local Plan5 specification/prompt files were copied byte-for-byte.
- Four entry files received only reviewed Plan5 notices: the engineering START, frontend START, baseline/status and Singh Plan5/6 handoff.
- Current remote publication/sponsor wording was retained. Stale local README/PROGRAMME publication claims, the old export manifest, incidental package-document formatting and an equivalent sponsor-link edit were not copied.
- Every overwritten build entry had its accepted-base bytes backed up and verified first.

The copied specifications retain their dated paper-stage text. This B0 report records actual execution; the current user instruction and 10 November launch prompt govern scope and precedence. Normative authority, money, state, privacy and exit constraints remain unchanged.

## Tooling, dependencies and baseline checks

| Item | Actual result |
|---|---|
| Python | Native ARM Python 3.12.16, explicitly selected |
| uv | 0.11.28 |
| Node / npm | v22.23.2 / 10.9.8 |
| Python setup | `uv sync --locked --python /Users/aditya/.local/bin/python3.12` passed; isolated `.venv`, 40 installed packages |
| TypeScript tooling | `npm ci --ignore-scripts --no-audit --no-fund` passed; 46 installed packages |
| Existing offline suite | `.venv/bin/python -m pytest -q -p b0_offline_guard`: **1,448 passed**, one dependency warning |
| Existing lint | `.venv/bin/ruff check . --output-format json`: **passed**, no findings |
| Existing types | `npm run check:types`: **passed** |
| Python network guard | **0 attempted IP connections** during the baseline suite |

The pytest guard is a private external test harness, supplied through PYTHONPATH, rather than a product-code change. Live mode and externally selected piece adapters were disabled. The existing local Node switch harness uses native crypto and synthetic shared cases; no Docker, merchant code, model, provider or payment job was started. Passing legacy tests proves only their existing limited component behaviors. It does not test future Plan5 roles, schemas, persistent stand-ins or delivery coordination.

Initial offline installs lacked cached packages. Subsequent sandbox DNS failures were recorded; explicit tool approvals allowed the locked downloads. Lifecycle scripts were disabled for npm. Neither lockfile was changed. The host's default `python3` is x86_64 and caused an Xcode Git launcher error in the initial private backup script; rerunning with the required native Python3.12 resolved it without system changes.

The warning is Starlette's deprecation of its httpx-based TestClient. No dependency upgrade was made to suppress it. Full exporter regeneration is a B1 check and was not run in B0; existing schema/Python parity tests and TypeScript compilation passed.

## Stop and next phase

No product code, generated exports, fixtures, lockfiles, personal reference files or secrets were edited. Model spend: **$0; zero inference calls and zero spend reservations created**. FRONTEND_READY has not been published; the frontend is not ready to start from these legacy interfaces.

Next, only upon the user's instruction: B1, strict shared contracts/routes/ports with coherent generated schemas/types/OpenAPI, examples, fixtures and compatibility negatives. Continue in the isolated root. Recheck any new team revisions before relevant counterpart work. No Plan6, account change, deployment, payment/provider qualification or publication is implied by B0 completion.
