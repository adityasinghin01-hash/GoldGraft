"""Closed claim catalog and grounded text renderer; no status mutation or sending."""

from typing import Literal

from goldgraft_contracts.agents import HeraldText
from goldgraft_contracts.plan5_common import (
    Count,
    Digest,
    Id,
    P5Record,
    Positive,
    Ref,
    Refs,
    Utc,
    canonical_bytes,
    content_digest,
    reject_secret,
)
from pydantic import Field, StrictBool

STATUS_TEXT = {
    "queued": "Work is queued; execution is not confirmed.",
    "working": "Work is in progress; results are not yet verified.",
    "inventory_ready": "The source inventory is accepted for further analysis.",
    "waiting_input": "Work is waiting for required input.",
    "held": "Work is held until the recorded prerequisite is resolved.",
    "unknown": "The outcome is unknown; reconciliation is required before further action.",
    "cancellation_pending": "Cancellation is pending; termination is not yet confirmed.",
    "cancelled": "Cancellation is confirmed for the scoped task; earlier effects are not undone.",
    "review_ready": "Evidence is ready for review; separate approval is still required.",
    "delivery_pending": "Delivery is pending; a working merchant outcome is not yet verified.",
    "synthetic_complete": (
        "The synthetic delivery sample is complete; no live merchant completion is established."
    ),
}
ASSET_TEXT = {
    "callback_handler": "callback handler",
    "application_state": "application state",
    "registry_access": "private registry access",
    "temporary_access": "temporary service access",
}
REASON_TEXT = {
    "NONE": "",
    "SOURCE_MISSING": " The source controller must supply the missing component.",
    "PROOF_MISSING": " Independent proof evidence is still required from SH.",
    "AUTHORITY_REVOKED": " Current authority must be restored through GU before work resumes.",
    "OUTCOME_UNKNOWN": " GU must reconcile the original request identity.",
    "BUDGET_EXHAUSTED": (
        " The project budget checkpoint requires review; no extra call is authorised."
    ),
    "TERMINATION_PENDING": (
        " GU must confirm termination before cancellation is reported as complete."
    ),
    "EXIT_PENDING": " Independent exit evidence remains pending.",
}
LIMITATION = (
    " Source-only offline evidence; runtime, payment and live-site outcomes remain unverified."
)
REASON_STATES = {
    "SOURCE_MISSING": {"held", "waiting_input"},
    "PROOF_MISSING": {"held", "waiting_input", "delivery_pending"},
    "AUTHORITY_REVOKED": {"held"},
    "OUTCOME_UNKNOWN": {"held", "unknown"},
    "BUDGET_EXHAUSTED": {"held", "waiting_input"},
    "TERMINATION_PENDING": {"held", "cancellation_pending"},
    "EXIT_PENDING": {"held", "delivery_pending"},
}


class ProjectionEntry(P5Record):
    case_id: Id
    run_id: Id
    generation: Positive
    subject_digest: Digest
    source_ref: Ref
    source_payload_digest: Digest
    source_version: Positive
    payload: dict[Literal["source_indicators"], Count] = Field(max_length=1)


class HeraldInputs(P5Record):
    case_id: Id
    run_id: Id
    generation: Positive
    subject_digest: Digest
    run_ref: Ref
    input_refs: Refs
    projection: Literal["private_status", "public_safe"]
    status: Literal[
        "queued",
        "working",
        "inventory_ready",
        "waiting_input",
        "held",
        "unknown",
        "cancellation_pending",
        "cancelled",
        "review_ready",
        "delivery_pending",
        "synthetic_complete",
    ]
    observed_at: Utc
    projection_version: Positive
    kind: Literal["GRAFT_CARD", "PR_BODY", "HANDOFF", "VERDICT_EXPLAIN"] = "GRAFT_CARD"
    reason_code: Literal[
        "NONE",
        "SOURCE_MISSING",
        "PROOF_MISSING",
        "AUTHORITY_REVOKED",
        "OUTCOME_UNKNOWN",
        "BUDGET_EXHAUSTED",
        "TERMINATION_PENDING",
        "EXIT_PENDING",
    ] = "NONE"
    ledger_entries: dict[Digest, ProjectionEntry] = Field(max_length=1)
    evidence_refs: Refs
    proof_subject: Digest | None = None
    proof_complete: StrictBool = False
    retained: list[
        Literal["callback_handler", "application_state", "registry_access", "temporary_access"]
    ] = Field(default_factory=list, max_length=4)
    removed: list[
        Literal["callback_handler", "application_state", "registry_access", "temporary_access"]
    ] = Field(default_factory=list, max_length=4)
    pending: list[
        Literal["callback_handler", "application_state", "registry_access", "temporary_access"]
    ] = Field(default_factory=list, max_length=4)


def validation_context(inputs):
    return {
        "ledger_entries": {
            h: row.model_dump(mode="json") for h, row in inputs.ledger_entries.items()
        }
    }


def _validated_facts(value):
    """Apply claim/provenance checks to every text consumer, including previews."""
    reject_secret(canonical_bytes(value).decode())
    facts = HeraldInputs.model_validate(value)
    if not facts.input_refs or not facts.evidence_refs:
        raise ValueError("MISSING_EVIDENCE committed projection")
    if facts.reason_code != "NONE" and facts.status not in REASON_STATES[facts.reason_code]:
        raise ValueError("MISSING_EVIDENCE conflicting status and reason")
    if facts.status == "review_ready" and (
        not facts.proof_complete or facts.proof_subject != facts.subject_digest
    ):
        raise ValueError("MISSING_EVIDENCE exact-subject review proof")
    assets = facts.retained + facts.removed + facts.pending
    if len(assets) != len(set(assets)):
        raise ValueError("DENIED conflicting asset disposition")
    for digest, row in facts.ledger_entries.items():
        if (
            content_digest(row) != digest
            or (
                row.case_id,
                row.run_id,
                row.generation,
                row.subject_digest,
                row.source_ref,
                row.source_version,
            )
            != (
                facts.case_id,
                facts.run_id,
                facts.generation,
                facts.subject_digest,
                facts.input_refs[0],
                facts.projection_version,
            )
            or any(type(v) is not int or v < 0 for v in row.payload.values())
        ):
            raise ValueError("DENIED numeric projection provenance")
    return facts


def _reparsed(facts):
    """JSON-shaped facts after strict Python-mode revalidation of an in-memory model.

    JSON serialization silently turns an unchecked bool count into 1, so the
    unchanged object is revalidated before any JSON-shaped reparse.
    """
    HeraldInputs.model_validate(facts.model_dump(mode="python", by_alias=True, warnings=False))
    return facts.model_dump(mode="json", warnings=False)


def validate_inputs(task, value):
    facts = _validated_facts(value)
    if (facts.case_id, facts.run_id, facts.generation, facts.subject_digest, facts.input_refs) != (
        task.case_id,
        task.run_id,
        task.generation,
        task.task.expected_subject,
        task.task.input_refs,
    ):
        raise ValueError("DENIED Herald scope/subject/input")
    if task.task.output_slot != "text." + facts.projection:
        raise ValueError("DENIED output projection slot")
    return facts


def supported_texts(facts):
    # Reparse bytes-shaped values: model_copy can carry unchecked model updates.
    facts = _validated_facts(_reparsed(facts))
    lead = STATUS_TEXT[facts.status] + REASON_TEXT[facts.reason_code]
    numbers = []
    if facts.status == "inventory_ready" and facts.ledger_entries:
        digest, row = next(iter(facts.ledger_entries.items()))
        if "source_indicators" in row.payload:
            value = row.payload["source_indicators"]
            lead += f" Inventory contains {value} source indicators."
            numbers = [
                {"entry_hash": digest, "json_pointer": "/payload/source_indicators", "value": value}
            ]
    limitation = LIMITATION
    dispositions = ""
    for label, names in [
        ("Retained", facts.retained),
        ("Removed", facts.removed),
        ("Pending", facts.pending),
    ]:
        if names:
            dispositions += f" {label}: " + ", ".join(ASSET_TEXT[name] for name in names) + "."
    return (
        lead + limitation + dispositions,
        "Status update: " + lead + limitation + dispositions,
    ), numbers


def model_facts(facts):
    """The closed claim catalog and call policy a model needs; never the assembled text."""
    return {
        "run_ref": facts["run_ref"],
        "projection": facts["projection"],
        "call_policy": "Call status.read(run_ref) and evidence.summary(run_ref, projection); "
        "both are reads and may go in one response. Once tool_progress lists both, never "
        "read again: submit HeraldText/1 once.",
        "catalog": {
            "status_text": STATUS_TEXT,
            "reason_text": REASON_TEXT,
            "asset_text": ASSET_TEXT,
            "limitation": LIMITATION,
        },
        "assembly": (
            "lead = status_text[status] + reason_text[reason_code]. Only if status is "
            "inventory_ready and the single ledger entry's payload has source_indicators N: "
            "lead += ' Inventory contains N source indicators.' and numbers_used = "
            "[{entry_hash: <that ledger key>, json_pointer: '/payload/source_indicators', "
            "value: N}]; otherwise numbers_used = [] and no number appears. dispositions = for "
            "(Retained, retained), (Removed, removed), (Pending, pending) in that order, when "
            "the list is non-empty: ' <Label>: ' + asset_text names joined by ', ' + '.'. "
            "text = lead + limitation + dispositions (concise) or 'Status update: ' + that "
            "(detailed). Copy every catalog string exactly, character for character. kind = "
            "facts.kind; created_at = facts.observed_at; other metadata from "
            "reference_metadata."
        ),
    }


def render_text(task, facts, *, detailed=False):
    """Deterministic fallback, also the default while no real model is qualified."""
    facts = validate_inputs(task, _reparsed(facts))
    texts, numbers = supported_texts(facts)
    return HeraldText.model_validate(
        {
            "id": "herald-"
            + content_digest(
                {
                    "task": task.task.task_id,
                    "input": task.input_digest,
                    "projection": facts.model_dump(mode="json"),
                }
            )[:16],
            "graft_id": task.run_id,
            "created_at": facts.observed_at.isoformat(),
            "producer": {
                "kind": "agent",
                "name": "Herald",
                "version": "1",
                "model": "deterministic-offline",
            },
            "kind": facts.kind,
            "text": texts[1 if detailed else 0],
            "numbers_used": numbers,
        },
        context=validation_context(facts),
    ).model_dump(mode="json")


def deterministic_renderer(task, value):
    return render_text(task, HeraldInputs.model_validate(value))


def validate_result(task, payload, facts, observations):
    result = HeraldText.model_validate(payload, context=validation_context(facts))
    if (
        (result.graft_id, result.producer.name, result.producer.kind.value)
        != (
            task.run_id,
            "Herald",
            "agent",
        )
        or result.kind.value != facts.kind
        or result.created_at != facts.observed_at
    ):
        raise ValueError("DENIED Herald output identity")
    texts, numbers = supported_texts(facts)
    if result.text not in texts or result.model_dump(mode="json")["numbers_used"] != numbers:
        raise ValueError("MISSING_EVIDENCE unsupported prose or number")
    if any(type(number.value) is not int for number in result.numbers_used):
        raise ValueError("MISSING_EVIDENCE count must remain an integer")
    expected = {
        "kind": "status_projection",
        "status": facts.status,
        "projection_version": facts.projection_version,
    }
    summary = {
        "kind": "evidence_summary",
        "projection": facts.projection,
        "facts_digest": content_digest(facts),
    }
    values = []
    for observation in observations:
        if observation.get("evidence_class") != "scripted":
            raise ValueError("DENIED evidence class")
        values.append(observation.get("value"))
    if len(values) != 2 or expected not in values or summary not in values:
        raise ValueError("MISSING_EVIDENCE unread or changed projection")
    return result


def inspect_text(payload, facts):
    text = HeraldText.model_validate(payload, context=validation_context(facts))
    texts, numbers = supported_texts(facts)
    if (
        text.text not in texts
        or text.created_at != facts.observed_at
        or text.model_dump(mode="json")["numbers_used"] != numbers
        or any(type(number.value) is not int for number in text.numbers_used)
        or (text.graft_id, text.producer.name, text.producer.kind.value, text.kind.value)
        != (
            facts.run_id,
            "Herald",
            "agent",
            facts.kind,
        )
    ):
        raise ValueError("DENIED unsupported inspected text")
    view = {
        "role": "Herald",
        "kind": text.kind.value,
        "text": text.text,
        "projection": facts.projection,
        "evidence_class": "scripted",
        "model_api_calls": 0,
        "authoritative_status_changed": False,
        "notifications_sent": 0,
    }
    if facts.projection == "private_status":
        view["evidence_refs"] = list(facts.evidence_refs)
        view["numbers_used"] = text.model_dump(mode="json")["numbers_used"]
    return view


def notification_preview(facts, *, opted_in=False):
    """Minimal opt-in preview for future GU/Zapier use; never sends or authorises."""
    if not opted_in:
        return None
    return {
        # Draft format is presentation, not a different committed logical event.
        "event_key": content_digest(facts.model_dump(mode="json", exclude={"kind"})),
        "text": supported_texts(facts)[0][0],
        "projection": facts.projection,
        "delivery": "NOT SENT",
        "authority": "NONE",
    }
