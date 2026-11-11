# Gupta Sponsor Tool Status & Integration Report

**Owner**: Aditya Gupta (`pieces/backend`, `pieces/runner`)  
**Assigned Tools**: Render, Postman, Elastic, Zapier, Kernel  
**Branch**: `feat/aditya-gupta-broker-runner-handoff`  
**Compliance**: [SPONSOR_UTILISATION_AND_OWNERSHIP.md](engineering/work/SPONSOR_UTILISATION_AND_OWNERSHIP.md)

---

## 1. Tool Status Summary

| Tool | Role & Scope | Config / Code Location | Plan / Quota | Status |
|---|---|---|---|---|
| **Render** | Control-plane web, background worker, managed PostgreSQL ledger | [`render.yaml`](../render.yaml) | Free tier / Event resource (512MB RAM, shared CPU) | **READY** |
| **Postman** | API routes, idempotency, lifecycle replay & security checks | [`postman/GoldGraft_Collection.json`](../postman/GoldGraft_Collection.json), [`postman/GoldGraft_Environment.template.json`](../postman/GoldGraft_Environment.template.json) | Free / Team workspace | **READY** |
| **Zapier** | Opt-in noncritical approval, blocked-state & completion notices | [`pieces/backend/zapier_notifier.py`](../pieces/backend/zapier_notifier.py) | Free tier (100 tasks/month, 5 zaps) | **READY** |
| **Elastic** | Privacy-scrubbed diagnostic & evidence indexing | [`pieces/backend/elastic_ingest.py`](../pieces/backend/elastic_ingest.py) | Serverless Trial / Standard index | **READY** |
| **Kernel** | Sandboxed browser checkout & replay capture | Integrated via `PaymentBroker` + `SandboxRecorder` | Free Developer Tier / Event sandbox | **IN_PROGRESS** (Awaiting Vijay's browser test bench) |

---

## 2. Implementation & Safety Highlights

1. **Render (`render.yaml`)**:
   - Defines declarative infrastructure: `goldgraft-control-plane` web service (`pieces.backend.app:app`), `goldgraft-isolated-worker` background process, and `goldgraft-ledger-db` PostgreSQL.
   - Enforces Doppler custody references (`CUSTODY_SECRET_PROVIDER=doppler`) and rate limits.
2. **Postman (`postman/`)**:
   - 5 end-to-end assertions covering probe scanning, idempotency-enforced shop creation, Doppler credential isolation, lifecycle graft starting, and proof verification.
   - Environment template leaves all secrets strictly empty (`""`) to prevent token leakage.
3. **Zapier (`pieces/backend/zapier_notifier.py`)**:
   - Minimal notification payloads (`ACTION_NEEDED`, `BLOCKED`, `GRAFT_COMPLETED`).
   - Deduplicates events to avoid webhook floods.
   - Fail-safe: Zapier network failures log a warning and never block graft execution or state progression.
4. **Elastic (`pieces/backend/elastic_ingest.py`)**:
   - Index mapping for `graft_id`, `run_id`, `stage`, `scenario_id`, `evidence_ref`.
   - Strict redactor replaces passwords, signatures, and secrets with `[REDACTED]`.

---

## 3. Test & Verification Evidence

All 4 sponsor integrations are covered by automated unit tests in [`plugtests/test_sponsor_gupta.py`](../plugtests/test_sponsor_gupta.py):

```bash
uv run pytest plugtests/test_sponsor_gupta.py -v
```

**Result**:
```
plugtests/test_sponsor_gupta.py::test_render_yaml_configuration PASSED
plugtests/test_sponsor_gupta.py::test_postman_collection_and_env PASSED
plugtests/test_sponsor_gupta.py::test_zapier_notifier_offline_dedupe PASSED
plugtests/test_sponsor_gupta.py::test_elastic_evidence_formatter PASSED
======================== 4 passed in 1.00s ========================
```

Overall test suite: **98 passed, 0 failures**.

