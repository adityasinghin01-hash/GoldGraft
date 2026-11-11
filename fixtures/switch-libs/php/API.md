# GoldGraft switch library — PHP, PayPal Orders v2 (installed at lib/paypal_orders.php)

require_once __DIR__ . '/../lib/paypal_orders.php';   (from api/*.php; from the shop root use '/lib/paypal_orders.php')

gg_create_order(array $items, string $total, string $currency, string $returnUrl, string $cancelUrl, string $referenceId)
  $items = list of ['name' => string, 'unit_amount' => '12.50', 'quantity' => int]
  returns ['ok' => bool, 'id' => order id (use it where the old EC TOKEN was used), 'raw' => array]
gg_capture_order(string $orderId, string $requestId)
  returns ['ok' => bool, 'capture_id' => ?string, 'capture_status' => 'COMPLETED'|'PENDING'|..., 'amount', 'currency', 'payer_id', 'payer_email', 'raw']
  Money rule: only capture_status === 'COMPLETED' marks an order PAID; PENDING must be stored as PENDING.
gg_refund_capture(string $captureId, string $amount, string $currency, string $requestId)
  returns ['ok' => bool, 'refund_id' => ?string, 'refund_status' => ?string, 'raw' => array]
gg_verify_webhook(array $headers, string $rawBody) -> bool   (replaces IPN cmd=_notify-validate)
  headers come from getallheaders(); the event body is JSON (event_type, resource).
