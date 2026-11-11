"""Opt-in evidence routes composed with the host's identity and evidence stores."""

from collections.abc import Callable, Iterable, Mapping
from hashlib import sha256
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from pieces.proof.lifecycle_evidence import Observation, Requirement, review_lifecycle
from pieces.proof.review_projection import public_review

type Visibility = Literal["private", "public"]
type Authorize = Callable[[Request, str, Visibility], bool]
type LoadEvidence = Callable[
    [str], tuple[Mapping[str, Requirement], Iterable[tuple[Observation, bytes]]] | None
]


def mount_evidence_routes(
    app: FastAPI, *, authorize: Authorize, load_evidence: LoadEvidence
) -> None:
    """The host supplies current case grants and authenticated observation records."""

    @app.get("/cases/{case_id}/evidence/{visibility}", include_in_schema=False)
    def get_evidence(request: Request, case_id: str, visibility: Visibility):
        headers = {"Cache-Control": "private, no-store"}
        if authorize(request, case_id, visibility) is not True:
            return JSONResponse({"detail": "Evidence unavailable"}, 404, headers=headers)
        record = load_evidence(case_id)
        if record is None:
            return JSONResponse({"detail": "Evidence unavailable"}, 404, headers=headers)

        requirements, evidence = record
        if any(item.subject.case_id != case_id for item in requirements.values()):
            return JSONResponse({"detail": "Evidence unavailable"}, 404, headers=headers)
        observations = [
            item for item, payload in evidence
            if item.subject.case_id == case_id
            and sha256(payload).hexdigest() == item.evidence_digest
        ]
        review = review_lifecycle(requirements, observations)
        result = review if visibility == "private" else public_review(review)
        return JSONResponse(jsonable_encoder(result), headers=headers)
