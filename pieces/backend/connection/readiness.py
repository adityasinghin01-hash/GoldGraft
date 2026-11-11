"""Connection Readiness and Pre-flight Inspection (GU02).

Implements:
1. Pre-flight verification of Case, Authority, Providers, and Secrets.
2. Returns structured ConnectionReadiness report (READY, HELD, BLOCKED).
3. Holds operation immediately if required credentials or permissions are unverified.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class ReadinessCheck:
    name: str
    status: str  # "OK", "HELD", "FAILED"
    message: str


@dataclass
class ConnectionReadiness:
    case_id: str
    overall_status: str  # "READY", "HELD", "BLOCKED"
    checks: list[ReadinessCheck] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class ReadinessInspector:
    """Performs pre-flight checks before allowing a graft or upgrade job to proceed."""

    def inspect(
        self,
        case_id: str,
        *,
        has_case: bool,
        has_authority: bool,
        has_secrets: bool,
        is_read_only_safe: bool = True,
    ) -> ConnectionReadiness:
        checks: list[ReadinessCheck] = []

        if not has_case:
            checks.append(ReadinessCheck("case_membership", "FAILED", "Connection case not found"))
        else:
            checks.append(ReadinessCheck("case_membership", "OK", "Valid case membership"))

        if not has_authority:
            checks.append(ReadinessCheck("authority_grant", "HELD", "Missing required authority"))
        else:
            checks.append(ReadinessCheck("authority_grant", "OK", "Authorized grant scope"))

        if not has_secrets:
            checks.append(ReadinessCheck("secret_custody", "HELD", "Missing sandbox credentials"))
        else:
            checks.append(ReadinessCheck("secret_custody", "OK", "Secrets securely vaulted"))

        if not is_read_only_safe:
            checks.append(
                ReadinessCheck("escalation_guard", "FAILED", "Escalation to write unauthorized")
            )
        else:
            checks.append(ReadinessCheck("escalation_guard", "OK", "Escalation boundaries safe"))

        statuses = {c.status for c in checks}
        if "FAILED" in statuses:
            overall = "BLOCKED"
        elif "HELD" in statuses:
            overall = "HELD"
        else:
            overall = "READY"

        return ConnectionReadiness(
            case_id=case_id,
            overall_status=overall,
            checks=checks,
        )

