<?php
// GoldGraft switch library: PayPal Orders v2, Payments v2 and Webhooks for plain-PHP shops.
// MIT licence. Hand-written by the GoldGraft team from PayPal's public REST documentation;
// not written by a model. Sandbox by default; credentials come from the environment only.
//   https://developer.paypal.com/api/rest/authentication/
//   https://developer.paypal.com/api/orders/v2/
//   https://developer.paypal.com/api/payments/v2/
//   https://developer.paypal.com/api/webhooks/v1/
require_once __DIR__ . '/../config.php';

if (!defined('PAYPAL_REST_BASE')) {
    define('PAYPAL_REST_BASE', getenv('PAYPAL_REST_BASE') ?: 'https://api-m.sandbox.paypal.com');
}

function gg_paypal_token() {
    static $token = null;
    if ($token !== null) {
        return $token;
    }
    $ch = curl_init(PAYPAL_REST_BASE . '/v1/oauth2/token');
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_USERPWD => (getenv('PAYPAL_CLIENT_ID') ?: '') . ':' . (getenv('PAYPAL_CLIENT_SECRET') ?: ''),
        CURLOPT_POSTFIELDS => 'grant_type=client_credentials',
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 30,
    ]);
    $out = json_decode((string) curl_exec($ch), true);
    curl_close($ch);
    $token = is_array($out) && isset($out['access_token']) ? $out['access_token'] : '';
    return $token;
}

// One REST call. Returns ['status' => HTTP status, 'body' => decoded JSON array].
function gg_paypal_rest($method, $path, $body = null, $requestId = null) {
    $headers = ['Content-Type: application/json', 'Authorization: Bearer ' . gg_paypal_token()];
    if ($requestId !== null) {
        $headers[] = 'PayPal-Request-Id: ' . $requestId; // idempotent retries
    }
    $ch = curl_init(PAYPAL_REST_BASE . $path);
    curl_setopt_array($ch, [
        CURLOPT_CUSTOMREQUEST => $method,
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 30,
    ]);
    if ($body !== null) {
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($body));
    }
    $raw = curl_exec($ch);
    $status = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    $decoded = json_decode((string) $raw, true);
    return ['status' => $status, 'body' => is_array($decoded) ? $decoded : []];
}

// Create an order (replaces SetExpressCheckout). Amounts are strings with two decimals.
// $items: list of ['name' => string, 'unit_amount' => '12.50', 'quantity' => int].
// Returns ['ok' => bool, 'id' => order id (the new "token"), 'raw' => body].
function gg_create_order(array $items, $total, $currency, $returnUrl, $cancelUrl, $referenceId) {
    $lines = [];
    foreach ($items as $it) {
        $lines[] = [
            'name' => $it['name'],
            'quantity' => (string) $it['quantity'],
            'unit_amount' => ['currency_code' => $currency, 'value' => $it['unit_amount']],
        ];
    }
    $r = gg_paypal_rest('POST', '/v2/checkout/orders', [
        'intent' => 'CAPTURE',
        'purchase_units' => [[
            'reference_id' => $referenceId,
            'amount' => [
                'currency_code' => $currency,
                'value' => $total,
                'breakdown' => ['item_total' => ['currency_code' => $currency, 'value' => $total]],
            ],
            'items' => $lines,
        ]],
        'application_context' => [
            'return_url' => $returnUrl,
            'cancel_url' => $cancelUrl,
            'shipping_preference' => 'NO_SHIPPING',
        ],
    ], $referenceId . ':create');
    return [
        'ok' => $r['status'] === 201 || $r['status'] === 200,
        'id' => isset($r['body']['id']) ? $r['body']['id'] : null,
        'raw' => $r['body'],
    ];
}

// Capture an approved order (replaces GetExpressCheckoutDetails + DoExpressCheckoutPayment).
// A capture is COMPLETED or PENDING (or DECLINED): only COMPLETED means the shop was paid.
function gg_capture_order($orderId, $requestId) {
    $r = gg_paypal_rest('POST', '/v2/checkout/orders/' . rawurlencode($orderId) . '/capture', new stdClass(), $requestId);
    $cap = isset($r['body']['purchase_units'][0]['payments']['captures'][0])
        ? $r['body']['purchase_units'][0]['payments']['captures'][0] : [];
    return [
        'ok' => $r['status'] === 201 || $r['status'] === 200,
        'capture_id' => isset($cap['id']) ? $cap['id'] : null,
        'capture_status' => isset($cap['status']) ? $cap['status'] : null,
        'amount' => isset($cap['amount']['value']) ? $cap['amount']['value'] : null,
        'currency' => isset($cap['amount']['currency_code']) ? $cap['amount']['currency_code'] : null,
        'payer_id' => isset($r['body']['payer']['payer_id']) ? $r['body']['payer']['payer_id'] : '',
        'payer_email' => isset($r['body']['payer']['email_address']) ? $r['body']['payer']['email_address'] : '',
        'raw' => $r['body'],
    ];
}

// Refund a completed capture (replaces RefundTransaction).
function gg_refund_capture($captureId, $amount, $currency, $requestId) {
    $r = gg_paypal_rest('POST', '/v2/payments/captures/' . rawurlencode($captureId) . '/refund', [
        'amount' => ['currency_code' => $currency, 'value' => $amount],
    ], $requestId);
    $status = isset($r['body']['status']) ? $r['body']['status'] : null;
    return [
        'ok' => $status === 'COMPLETED' || $status === 'PENDING',
        'refund_id' => isset($r['body']['id']) ? $r['body']['id'] : null,
        'refund_status' => $status,
        'raw' => $r['body'],
    ];
}

// Verify a webhook with PayPal (replaces IPN's cmd=_notify-validate post-back).
function gg_verify_webhook(array $headers, $rawBody) {
    $h = array_change_key_case($headers, CASE_LOWER);
    $pick = function ($k) use ($h) { return isset($h[$k]) ? $h[$k] : ''; };
    $event = json_decode($rawBody, true);
    $r = gg_paypal_rest('POST', '/v1/notifications/verify-webhook-signature', [
        'auth_algo' => $pick('paypal-auth-algo'),
        'cert_url' => $pick('paypal-cert-url'),
        'transmission_id' => $pick('paypal-transmission-id'),
        'transmission_sig' => $pick('paypal-transmission-sig'),
        'transmission_time' => $pick('paypal-transmission-time'),
        'webhook_id' => getenv('PAYPAL_WEBHOOK_ID') ?: '',
        'webhook_event' => is_array($event) ? $event : new stdClass(),
    ]);
    return isset($r['body']['verification_status']) && $r['body']['verification_status'] === 'SUCCESS';
}
