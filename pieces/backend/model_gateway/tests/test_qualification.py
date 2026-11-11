"""Recorded qualification is version-bound evidence, not an enable-spend boolean."""

import hashlib
import json

import pytest


def test_missing_or_tampered_qualification_never_enables_live_calls(tmp_path):
    from pieces.backend.model_gateway.profile import Profile
    from pieces.backend.model_gateway.qualification import verify_qualification

    with pytest.raises(ValueError, match="QUALIFICATION"):
        verify_qualification(tmp_path / "absent.json", Profile())
    source = tmp_path / "source.py"
    source.write_text("approved code\n")
    log = tmp_path / "checks.log"
    log.write_text("passed\n")
    record = tmp_path / "record.json"
    record.write_text(
        json.dumps(
            {
                "exit_code": 0,
                "log": str(log),
                "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
            }
        )
    )
    document = {
        "purpose": "synthetic_component_only",
        "profile": Profile().ref,
        "files": [{"path": str(source), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}],
        "checks": [
            {"path": str(record), "sha256": hashlib.sha256(record.read_bytes()).hexdigest()}
        ],
    }
    marker = tmp_path / "qualified.json"
    marker.write_text(json.dumps(document))
    assert verify_qualification(marker, Profile())
    source.write_text("unreviewed change\n")
    with pytest.raises(ValueError, match="QUALIFICATION"):
        verify_qualification(marker, Profile())
