import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "candidate_adapter", ROOT / "pieces/shops/legacy-php-shop/candidate/broker_adapter.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ScriptedBroker:
    mode = "synthetic"

    def __init__(self):
        self.calls = []
        self.response = SimpleNamespace(
            evidence_class="scripted",
            simulated=True,
            outcome="ok",
            status_code=200,
            data={"id": "TEST"},
        )

    def execute_orders_v2(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.response


class CandidateAdapterTests(unittest.TestCase):
    def setUp(self):
        self.broker = ScriptedBroker()
        self.adapter = module.BrokerRestAdapter(
            self.broker, graft_id="test", secret_ref="doppler://test"
        )
        self.headers = {"PayPal-Request-Id": "test-operation", "Prefer": "return=representation"}

    def test_capture_maps_exact_id_and_identity_to_current_broker(self):
        self.adapter.rest("POST", "/v2/checkout/orders/TESTORDER/capture", {}, self.headers)
        self.assertEqual(
            self.broker.calls,
            [
                (
                    ("capture", {"order_id": "TESTORDER"}),
                    {
                        "secret_ref": "doppler://test",
                        "graft_id": "test",
                        "idempotency_key": "test-operation",
                    },
                )
            ],
        )

    def test_refund_uses_original_capture_and_never_embeds_path_in_body(self):
        self.adapter.rest(
            "POST",
            "/v2/payments/captures/TESTCAPTURE/refund",
            {"amount": {"currency_code": "USD", "value": "25.00"}},
            self.headers,
        )
        self.assertEqual(
            self.broker.calls[0][0],
            (
                "refund",
                {"capture_id": "TESTCAPTURE", "amount": {"currency_code": "USD", "value": "25.00"}},
            ),
        )

    def test_reads_are_uncached_and_have_no_mutation_identity(self):
        for family, action, field in [
            ("checkout/orders", "get_order", "order_id"),
            ("payments/captures", "get_capture", "capture_id"),
            ("payments/refunds", "get_refund", "refund_id"),
        ]:
            for _ in range(2):
                self.adapter.rest("GET", "/v2/" + family + "/TEST")
            self.assertEqual(self.broker.calls[-1][0], (action, {field: "TEST"}))
            self.assertIsNone(self.broker.calls[-1][1]["idempotency_key"])
        self.assertEqual(len(self.broker.calls), 6)

    def test_unsafe_routes_and_ambient_credentials_are_rejected_before_dispatch(self):
        for method, path, body, headers in [
            ("POST", "https://api.paypal.com/v2/checkout/orders", {}, self.headers),
            ("POST", "/v2/checkout/orders/../capture", {}, self.headers),
            ("POST", "/v1/payments/payment", {}, self.headers),
            ("DELETE", "/v2/checkout/orders/TEST", None, {}),
            ("POST", "/v2/checkout/orders/TEST/capture", {}, {}),
            ("GET", "/v2/checkout/orders/TEST", None, self.headers),
            (
                "POST",
                "/v2/checkout/orders/TEST/capture",
                {},
                {**self.headers, "Authorization": "SENTINEL"},
            ),
        ]:
            with self.subTest(path=path), self.assertRaises(module.AdapterHold):
                self.adapter.rest(method, path, body, headers)
        self.assertEqual(self.broker.calls, [])

    def test_scripted_cannot_be_relabelled_real(self):
        with self.assertRaises(module.AdapterHold):
            module.BrokerRestAdapter(
                self.broker,
                graft_id="test",
                secret_ref="doppler://test",
                evidence_mode="real_sandbox",
            )
        self.broker.response.simulated = False
        with self.assertRaises(module.AdapterHold):
            self.adapter.rest("GET", "/v2/checkout/orders/TEST")

    def test_uncertain_outcome_is_not_returned_as_success(self):
        self.broker.response.outcome = "unknown"
        with self.assertRaises(module.AdapterHold):
            self.adapter.rest("GET", "/v2/checkout/orders/TEST")

    def test_offline_port_refuses_mode_change_before_dispatch(self):
        self.broker.mode = "sandbox"
        with self.assertRaises(module.AdapterHold):
            self.adapter.rest("GET", "/v2/checkout/orders/TEST")
        self.assertEqual(self.broker.calls, [])

    def test_response_is_not_filled_or_mutable_alias(self):
        _, value = self.adapter.rest("GET", "/v2/checkout/orders/TEST")
        self.assertEqual(value, {"id": "TEST"})
        value["status"] = "COMPLETED"
        self.assertNotIn("status", self.broker.response.data)

    def test_create_and_currency_scope(self):
        body = {
            "intent": "CAPTURE",
            "purchase_units": [
                {"reference_id": "local", "amount": {"currency_code": "USD", "value": "25.00"}}
            ],
        }
        self.adapter.rest("POST", "/v2/checkout/orders", body, self.headers)
        self.assertEqual(self.broker.calls[0][0], ("create", body))
        body["purchase_units"][0]["amount"]["currency_code"] = "EUR"
        with self.assertRaises(module.AdapterHold):
            self.adapter.rest("POST", "/v2/checkout/orders", body, self.headers)


if __name__ == "__main__":
    unittest.main()
