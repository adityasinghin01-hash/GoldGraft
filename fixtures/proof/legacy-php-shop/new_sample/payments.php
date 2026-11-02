<?php
// SYNTHETIC MIT sample, hand-written from PayPal Orders v2 / Payments v2 docs.
// Not a deployment. Injected $http and $store supply HTTP, durable transactions,
// an atomic order lock and unique notification IDs. No network in fixture tests.
// Sources: https://developer.paypal.com/api/orders/v2
// https://developer.paypal.com/api/payments/v2
// https://developer.paypal.com/api/webhooks/v1
function decimalUSD(int $minor): string {
    return intdiv($minor, 100) . '.' . str_pad((string)($minor % 100), 2, '0', STR_PAD_LEFT);
}
function createOrder($http, $store, string $ref, array $browser): array {
    $minor = $store->catalogueTotalMinor($ref); // M7: server owns amount
    $currency = 'USD';
    $result = $http('POST', '/v2/checkout/orders', [
        'intent' => 'CAPTURE', 'purchase_units' => [[
            'reference_id' => $ref, 'amount' => ['currency_code' => $currency, 'value' => decimalUSD($minor)]
        ]]
    ], ['PayPal-Request-Id' => $ref . ':create']);
    $store->save($ref, ['order_id' => $result['id'], 'minor' => $minor, 'currency' => $currency, 'refunded_minor' => 0]);
    return $result;
}
function captureOrder($http, $store, string $ref): array {
    return $store->locked($ref, function () use ($http, $store, $ref) { // M4
        $order = $store->get($ref);
        if (isset($order['capture_id'])) return $order; // cached replay
        $remote = $http('GET', '/v2/checkout/orders/' . $order['order_id'], [], []);
        if ($remote['status'] !== 'APPROVED') throw new RuntimeException('unapproved'); // M3
        $store->saveApproval($ref, $remote); // M11: durable before capture
        $requestId = $ref . ':capture'; // M5: stable across response loss
        $result = $http('POST', '/v2/checkout/orders/' . $order['order_id'] . '/capture', [],
                        ['PayPal-Request-Id' => $requestId]);
        $capture = $result['purchase_units'][0]['payments']['captures'][0];
        $amountMatches = $capture['amount']['value'] === decimalUSD($order['minor']); // M6
        $currencyMatches = $capture['amount']['currency_code'] === $order['currency']; // M1
        if (!$amountMatches || !$currencyMatches) throw new RuntimeException('money mismatch');
        if ($capture['status'] !== 'COMPLETED') { // M2
            $store->setPending($ref, $capture['id']);
            return $result;
        }
        $store->setPaid($ref, $capture['id']);
        return $result;
    });
}
function refundOrder($http, $store, string $ref): array {
    return $store->locked($ref, function () use ($http, $store, $ref) {
        $order = $store->get($ref);
        if ($order['refunded_minor'] >= $order['minor']) throw new RuntimeException('already refunded'); // M12
        $result = $http('POST', '/v2/payments/captures/' . $order['capture_id'] . '/refund', [
            'amount' => ['currency_code' => $order['currency'], 'value' => decimalUSD($order['minor'])]
        ], ['PayPal-Request-Id' => $ref . ':refund']);
        if ($result['status'] !== 'COMPLETED') throw new RuntimeException('refund not completed');
        $store->recordRefund($ref, $result['id'], $order['minor']);
        return $result;
    });
}
function webhook($http, $store, array $headers, array $event, string $webhookId): void {
    $headers = array_change_key_case($headers, CASE_LOWER); // M10
    $verification = $http('POST', '/v1/notifications/verify-webhook-signature', [
        'auth_algo' => $headers['paypal-auth-algo'], 'cert_url' => $headers['paypal-cert-url'],
        'transmission_id' => $headers['paypal-transmission-id'],
        'transmission_sig' => $headers['paypal-transmission-sig'],
        'transmission_time' => $headers['paypal-transmission-time'],
        'webhook_id' => $webhookId, 'webhook_event' => $event
    ], []);
    if ($verification['verification_status'] !== 'SUCCESS') return; // M8
    if ($event['event_type'] !== 'PAYMENT.CAPTURE.COMPLETED') return;
    $resource = $event['resource'];
    $orderId = $resource['supplementary_data']['related_ids']['order_id']; // M9
    // The transaction atomically claims the event ID and checks the trusted resource
    // amount/currency against the local order and its durable approval before paid.
    // A resource is trusted ONLY after SUCCESS; M8 deliberately violates that premise.
    $store->verifiedNotification($event['id'], $orderId, $resource);
}
