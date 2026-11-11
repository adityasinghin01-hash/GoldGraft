# Guarded Plan5 agents

Start with `docs/engineering/plan5/START_HERE.md`. Supported offline capabilities,
limits, evidence and deferred connections are in
`docs/engineering/plan5/B4_OFFLINE_AGENTS_REPORT.md`.

All development CLIs are offline. They use the existing guarded runtime and
injected persistent fakes; they cannot turn an API key into a qualified service.
Use a fresh private state path for a new fixture; retain unknown/failed state for
reconciliation instead of deleting it.

```sh
uv run --locked --no-sync python -m pieces.agents.component_cli run --role Builder --state-file /private/tmp/goldgraft-builder-new.sqlite
uv run --locked --no-sync python -m pieces.agents.component_cli inspect --role Builder --state-file /private/tmp/goldgraft-builder-new.sqlite
uv run --locked --no-sync python -m pieces.agents.workflow_cli run --state-file /private/tmp/goldgraft-core-new.sqlite
uv run --locked --no-sync python -m pieces.agents.workflow_cli inspect --state-file /private/tmp/goldgraft-core-new.sqlite
uv run --locked --no-sync python -m pieces.agents.workflow_cli resume --state-file /private/tmp/goldgraft-core-new.sqlite
```

Surveyor and Herald retain their specialised CLIs/profiles and source/projection
checks. `component_cli --help` lists the other eleven roles. Ordinary tests deny
network access. Model competence and real GU/VJ/SH/provider behavior are separate,
NOT RUN gates. Do not send credentials, notifications or live jobs through these
fixtures.
