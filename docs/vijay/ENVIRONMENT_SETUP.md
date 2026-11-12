> **Current runtime — 8 November 2026:** Portable PHP on D: and existing Playwright now pass actual local shop/HTTP/restart/browser checks without Docker. Drive/team baseline rechecked with no newer changes in inspected active sources. See [portable runtime and evidence](PORTABLE_RUNTIME.md). Docker/Linux and genuine payment qualification remain pending; older Docker-blocked statements below are historical.

> **Local build update — 7 November 2026:** Docker CLI/Compose are now installed and the PHP lab recipe is implemented. Engine startup is blocked by current Windows/WSL readiness, with a pending restart. See [local build status](LOCAL_BUILD_STATUS.md). Earlier Docker deferral below is historical.

> **Current update — 7 November 2026:** Read [CURRENT_BASELINE.md](CURRENT_BASELINE.md) and [PHASE1_STATUS.md](PHASE1_STATUS.md) first. The refreshed Drive explicitly supersedes older build instructions/counts and delegates engineering to the reviewed team repository. Conflicting statements below are historical; the first plain-PHP reference and VJ01–VJ05 now govern. Docker is deliberately pending.

# Local Docker and Playwright setup

Setup observations from 5 November 2026. This file records local installation evidence. The subsequent personal-repository upload is explicitly user-authorized; future uploads still require instruction.

## Playwright — installed and verified

- @playwright/test is pinned to **1.64.1** in package.json/package-lock.json.
- Project-local Chromium **156.0.8078.4**, FFmpeg and Windows support binaries are in ignored .context/playwright-browsers/.
- The CLI wrapper sets the same local browser cache for installation and commands. Use the wrappers rather than plain npx commands that may select a different cache.
- Verification passed: headless Chromium launch, interaction with an in-memory page, and cookie isolation between two contexts. No external site, account, PayPal API or payment was exercised.

Commands from the workspace root:

```powershell
npm.cmd ci --ignore-scripts --cache .context/npm-cache
npm.cmd run setup:browser
npm.cmd run check:browser
npm.cmd run playwright -- --version
```

The setup uses the regular Chromium binary with the documented chromium channel/new headless mode. The installer uses --no-shell to avoid downloading an additional headless-shell browser. Future buyer configurations must use the same channel/cache, or explicitly install the matching alternative. Headed usage can use the regular Chromium binary already downloaded.

The host reports Windows 10 Home Single Language 22H2, build 19045. Current Playwright installation documentation lists Windows 11+; the local smoke check passed, but it does not establish official support or every future PayPal-flow compatibility. Revalidate on the eventual supported runner.

## Docker/WSL — not ready

- Docker is absent from PATH and the checked all-users/per-user install locations. Compose and the daemon have not been verified.
- The official AMD64 Docker installer download failed when C: ran out of space. The incomplete 362,475,065-byte file was removed; no installer was executed or accepted as valid.
- WSL initially returned no modern version details and status exit code 50. The authorised setup command was wsl.exe --install --no-distribution --web-download.
- Setup reported that Virtual Machine Platform was installed. WSL setup was interrupted during the remaining download after disk exhaustion; do not claim WSL 2 is operational. No Linux distribution was requested and no reboot was initiated.
- After removing the partial Docker download, C: had approximately **0.46 GB** free and D: **77.9 GB**. These are transient observations. Free adequate system-drive space before retrying; 10 GB is a practical requested working-space target, not a quoted vendor minimum.

Next steps after space is available:

1. Recheck disk availability and WSL status/features. Complete current official WSL setup; report any reboot requirement and let the user control the restart.
2. Re-download the official Docker Desktop installer and verify its digital signature before running it. Large download/data locations can use D: after an explicit target is chosen and permissions are available; Windows/WSL still need C: space.
3. Install the documented Linux-container backend. Confirm OS/edition support against current vendor requirements; do not claim support or silently choose an old unsupported release.
4. The user handles service-agreement acceptance and account sign-in. No terms have been accepted by the agent.
5. Check Docker CLI, Compose and server readiness. Only after the daemon works should a small trusted test container be used to verify execution.

Docker Hub sign-in is separate from installing Docker Desktop/WSL. Playwright requires no account or browser plugin for project automation. Official setup and Docker Hub sign-in browser tabs were opened for the user.

## Sources

- [Playwright installation and system requirements](https://playwright.dev/docs/intro)
- [Chromium channel and --no-shell](https://playwright.dev/docs/browsers#chromium-new-headless-mode)
- [Docker Desktop Windows setup](https://docs.docker.com/desktop/setup/install/windows-install/)
- [Docker WSL prerequisites](https://docs.docker.com/desktop/features/wsl/)

Historical Phase 0 observations remain distinguishable from the newer setup results in [PHASE0_STATUS.md](PHASE0_STATUS.md). All 16 sandbox feasibility checks remain unrun.

## Team repository review — 5 November 2026

See [team repository alignment](TEAM_REPO_ALIGNMENT.md) for the pinned source, exact Aditya Vijay ownership, phases 0–6, executable contract details and unresolved integration gates. This review adds context; it does not mark payment implementation complete.
