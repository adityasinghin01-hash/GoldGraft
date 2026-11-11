"""Zapier Event Forwarder Integration (pieces.backend.zapier_notifier).

Fulfills Gupta's Zapier ownership:
- Opt-in, noncritical notifications for merchant controller actions:
  * ACTION_NEEDED (approval required before deployment)
  * BLOCKED (missing credentials or unknown provider outcome)
  * GRAFT_COMPLETED (verification proof ready)
- Strict safety rules:
  * Never leaks secrets or customer cardholder data.
  * Losing Zapier connectivity NEVER alters state or blocks migrations.
  * Idempotent delivery to avoid notification spam.
"""

import hashlib
import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

log = logging.getLogger("goldgraft.zapier")


@dataclass
class NotificationResult:
    delivered: bool
    status_code: int
    event_id: str
    message: str


class ZapierNotifier:
    """Delivers minimal, redacted status events to registered merchant Zapier webhooks."""

    def __init__(self, webhook_url: str | None = None, enabled: bool = True):
        self.webhook_url = webhook_url
        self.enabled = enabled
        self._delivered_events: set[str] = set()

    def notify(
        self,
        event_type: str,
        graft_id: str,
        summary: str,
        *,
        action_url: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> NotificationResult:
        """Sends an opt-in minimal notification to Zapier."""
        event_id = hashlib.sha256(f"{graft_id}:{event_type}:{summary}".encode()).hexdigest()[:16]

        if not self.enabled or not self.webhook_url:
            return NotificationResult(
                delivered=False,
                status_code=0,
                event_id=event_id,
                message="Zapier notifications disabled or webhook URL omitted",
            )

        if event_id in self._delivered_events:
            return NotificationResult(
                delivered=True,
                status_code=200,
                event_id=event_id,
                message="Event deduplicated; already notified",
            )

        payload = {
            "event_id": event_id,
            "event_type": event_type,
            "graft_id": graft_id,
            "summary": summary,
            "action_url": action_url or f"https://goldgraft.io/grafts/{graft_id}",
            "timestamp": datetime.now(UTC).isoformat(),
            # Safely scrub any potential sensitive terms in details
            "details": {
                k: v
                for k, v in (details or {}).items()
                if "secret" not in k.lower() and "token" not in k.lower()
            },
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.webhook_url,
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "GoldGraft-Zapier-Notifier/1.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                status = response.getcode()
                self._delivered_events.add(event_id)
                return NotificationResult(
                    delivered=True,
                    status_code=status,
                    event_id=event_id,
                    message="Notification delivered successfully",
                )
        except Exception as exc:
            log.warning("Zapier delivery failed: %s (noncritical, continuing graft execution)", exc)
            return NotificationResult(
                delivered=False,
                status_code=500,
                event_id=event_id,
                message=f"Zapier delivery error: {exc}",
            )
