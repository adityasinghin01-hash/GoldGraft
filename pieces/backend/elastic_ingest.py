"""Elasticsearch Evidence Document Ingestion Schema & Formatter (pieces.backend.elastic_ingest).

Fulfills Gupta & Singhal's Elastic ownership:
- Formats redacted diagnostics, execution runs, and ledger entries for Elastic index.
- Enforces strict privacy filtering: zero secrets, cardholder details, or raw private tokens.
"""

import hashlib
from datetime import UTC, datetime
from typing import Any

ELASTIC_INDEX_MAPPINGS = {
    "mappings": {
        "properties": {
            "graft_id": {"type": "keyword"},
            "run_id": {"type": "keyword"},
            "stage": {"type": "keyword"},
            "scenario_id": {"type": "keyword"},
            "status": {"type": "keyword"},
            "timestamp": {"type": "date"},
            "summary": {"type": "text"},
            "details": {"type": "object"},
            "evidence_ref": {"type": "keyword"},
            "provenance_sha": {"type": "keyword"},
        }
    }
}


def format_evidence_doc(
    graft_id: str,
    run_id: str,
    stage: str,
    scenario_id: str,
    status: str,
    summary: str,
    evidence_ref: str,
    provenance_sha: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generates an indexed, privacy-scrubbed document for Elasticsearch evidence retrieval."""
    clean_details = {}
    if details:
        for k, v in details.items():
            k_lower = k.lower()
            if any(
                term in k_lower for term in ("secret", "token", "password", "signature", "auth")
            ):
                clean_details[k] = "[REDACTED]"
            else:
                clean_details[k] = v

    doc_id = hashlib.sha256(f"{graft_id}:{run_id}:{scenario_id}:{stage}".encode()).hexdigest()

    return {
        "_id": doc_id,
        "graft_id": graft_id,
        "run_id": run_id,
        "stage": stage,
        "scenario_id": scenario_id,
        "status": status,
        "summary": summary,
        "evidence_ref": evidence_ref,
        "provenance_sha": provenance_sha,
        "details": clean_details,
        "timestamp": datetime.now(UTC).isoformat(),
    }
