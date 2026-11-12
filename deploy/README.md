# Hosted read-only backend

`deploy/runs/` holds two real recorded runs served by the hosted API (Render):

- `r9-final-connected`: 13/13 agents on real models; connected run 33/39 verified;
  ProofResult signed (Rekor #3832763566).
- `r8b-proof-legacy`: 13/13 agents; local PHP proof.

Only the files the API reads are copied (no control ledgers, no secrets; scanned).
The hosted server runs without `--live` and without any model key, so it can
never start a paid agent run:

```sh
.venv/bin/python -m integration.agents_app --host 0.0.0.0 --port $PORT --runs-dir deploy/runs
```
