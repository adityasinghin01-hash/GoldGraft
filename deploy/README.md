# Hosted read-only backend

Public API: https://goldgraft-api.onrender.com. `GET /runs` lists the recorded
runs; `GET /grafts/r9-final-connected/connected` returns the held proof summary,
and `GET /grafts/r9-final-connected/connected-proof` serves the exact signed
ProofResult bytes. There is no `/health` route in this app.

`deploy/runs/` holds two real recorded runs served by the hosted API (Render):

- `r9-final-connected`: 13/13 agents on real models; connected run 34/39 verified;
  real sandbox HAPPY checkout independently verified; ProofResult signed
  (Rekor #3833925707). Other real flow recordings are described in the live-check
  report; they are not added to the HAPPY-only qualification scope.
- `r8b-proof-legacy`: 13/13 agents; local PHP proof.

Only the files the API reads are copied (no control ledgers, no secrets; scanned).
The hosted server runs without `--live` and without any model key, so it can
never start a paid agent run. The CLI also rejects every write method before
fixture routes: no new shop, credentials or upgrade request is accepted.

```sh
.venv/bin/python -m integration.agents_app --host 0.0.0.0 --port $PORT --runs-dir deploy/runs
```

This hosted service uses the command above. The root `render.yaml` describes a
separate control-plane/worker/database setup; it is not the configuration of
this recorded-run API and does not establish that those services are deployed.

Build the public frontend with `VITE_API_BASE=https://goldgraft-api.onrender.com`
and `VITE_RECORDING_ONLY=true`. This shows the recorded-demo banner and removes
credential entry and new-upgrade controls. An API URL alone does not qualify
merchant operation; synthetic comparison/security screens remain labelled.
