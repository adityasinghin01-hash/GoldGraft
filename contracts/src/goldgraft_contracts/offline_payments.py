"""Python-only ports for PR6's synthetic payments; no provider or wire qualification."""

from typing import Any, Protocol


class PaymentAccessDenied(ValueError):
    """An offline payment credential reference could not be admitted."""


class OfflinePaymentResponse(Protocol):
    status_code: int
    data: dict[str, Any]
    simulated: bool


class OfflinePayments(Protocol):
    evidence_class: str

    def resolve_and_verify(self, secret_ref: str) -> dict[str, str]: ...

    def execute_nvp(
        self,
        operation: str,
        params: dict[str, str],
        *,
        secret_ref: str,
        idempotency_key: str | None = None,
        graft_id: str = "default",
    ) -> OfflinePaymentResponse: ...

    def execute_orders_v2(
        self,
        action: str,
        payload: dict[str, Any],
        *,
        secret_ref: str,
        idempotency_key: str | None = None,
        graft_id: str = "default",
    ) -> OfflinePaymentResponse: ...
