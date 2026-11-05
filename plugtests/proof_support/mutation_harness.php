<?php

require $argv[1];

final class Store {
    public array $row = [];
    public array $approvals = [];
    public array $refunds = [];
    public array $notifications = [];
    public int $locks = 0;
    public int $catalogue = 2500;

    public function catalogueTotalMinor(string $ref): int { return $this->catalogue; }
    public function save(string $ref, array $row): void { $this->row = $row; }
    public function get(string $ref): array { return $this->row; }
    public function locked(string $ref, callable $action): array {
        $this->locks++;
        return $action();
    }
    public function saveApproval(string $ref, array $remote): void {
        $this->approvals[$ref] = $remote;
    }
    public function setPaid(string $ref, string $id): void {
        $this->row['status'] = 'paid';
        $this->row['capture_id'] = $id;
    }
    public function setPending(string $ref, string $id): void {
        $this->row['status'] = 'pending';
        $this->row['capture_id'] = $id;
    }
    public function recordRefund(string $ref, string $id, int $minor): void {
        if (!isset($this->refunds[$id])) {
            $this->refunds[$id] = true;
            $this->row['refunded_minor'] += $minor;
        }
    }
    public function verifiedNotification(string $eventId, string $orderId, array $resource): void {
        if (!isset($this->notifications[$eventId])
            && isset($this->approvals['shop-order'])
            && $orderId === $this->row['order_id']
            && $resource['amount']['currency_code'] === $this->row['currency']
            && $resource['amount']['value'] === decimalUSD($this->row['minor'])) {
            $this->notifications[$eventId] = true;
            $this->setPaid('shop-order', $resource['id']);
        }
    }
}

function rejected(callable $action, string $reason): bool {
    try {
        $action();
        return false;
    } catch (RuntimeException $error) {
        if ($error->getMessage() !== $reason) {
            throw $error;
        }
        return true;
    }
}

function runScenario(string $scenario): bool {
    $ref = 'shop-order';
    $store = new Store();
    $captureRequests = [];
    $refundRequests = 0;
    $created = [];
    if ($scenario === 'EXACT_AMOUNT') {
        $store->catalogue = 9007199254740901;
    }

    $http = function ($method, $path, $body, $headers) use (
        $scenario, $store, &$captureRequests, &$refundRequests, &$created
    ) {
        if ($path === '/v2/checkout/orders') {
            $created = $body['purchase_units'][0]['amount'];
            return ['id' => 'paypal-order'];
        }
        if ($method === 'GET') {
            return ['status' => $scenario === 'UNAPPROVED' ? 'CREATED' : 'APPROVED'];
        }
        if (str_ends_with($path, '/capture')) {
            $captureRequests[] = $headers['PayPal-Request-Id'];
            if ($scenario === 'UNAPPROVED') {
                throw new RuntimeException('unapproved');
            }
            if (in_array($scenario, ['LOST_RESPONSE', 'DURABLE_APPROVAL'], true)
                && count($captureRequests) === 1) {
                throw new RuntimeException('connection interrupted');
            }
            $amount = $scenario === 'EXACT_AMOUNT'
                ? decimalUSD($store->catalogue + 1) : '25.00';
            return ['purchase_units' => [['payments' => ['captures' => [[
                'id' => 'paypal-capture',
                'status' => $scenario === 'PENDING' ? 'PENDING' : 'COMPLETED',
                'amount' => [
                    'currency_code' => $scenario === 'WRONG_CURRENCY' ? 'EUR' : 'USD',
                    'value' => $amount,
                ],
            ]]]]]];
        }
        if (str_ends_with($path, '/refund')) {
            $refundRequests++;
            return ['id' => 'paypal-refund', 'status' => 'COMPLETED'];
        }
        if ($path === '/v1/notifications/verify-webhook-signature') {
            $valid = $scenario !== 'FORGED_WEBHOOK' && $body['transmission_sig'] === 'signed';
            return ['verification_status' => $valid ? 'SUCCESS' : 'FAILURE'];
        }
        throw new LogicException("Unexpected request: $method $path");
    };

    createOrder($http, $store, $ref, ['minor' => 1, 'currency' => 'EUR']);
    $capture = fn() => captureOrder($http, $store, $ref);

    switch ($scenario) {
        case 'WRONG_CURRENCY':
        case 'EXACT_AMOUNT':
            return rejected($capture, 'money mismatch') && !isset($store->row['capture_id']);
        case 'PENDING':
            $capture();
            return ($store->row['status'] ?? null) === 'pending';
        case 'UNAPPROVED':
            return rejected($capture, 'unapproved') && !isset($store->row['capture_id']);
        case 'LOCKED_CAPTURE':
            $capture();
            $capture();
            return $store->locks === 2 && count($captureRequests) === 1;
        case 'LOST_RESPONSE':
            if (!rejected($capture, 'connection interrupted')) {
                return false;
            }
            $capture();
            return count($captureRequests) === 2 && $captureRequests[0] === $captureRequests[1];
        case 'DURABLE_APPROVAL':
            return rejected($capture, 'connection interrupted') && isset($store->approvals[$ref]);
        case 'BROWSER_QUOTE':
            return $created === ['currency_code' => 'USD', 'value' => '25.00'];
        case 'FORGED_WEBHOOK':
        case 'VALID_WEBHOOK':
        case 'MIXED_CASE_WEBHOOK':
            $store->saveApproval($ref, ['status' => 'APPROVED']);
            $headers = [
                'paypal-auth-algo' => 'test', 'paypal-cert-url' => 'test',
                'paypal-transmission-id' => 'event', 'paypal-transmission-sig' => 'signed',
                'paypal-transmission-time' => 'test',
            ];
            if ($scenario === 'MIXED_CASE_WEBHOOK') {
                $headers = array_change_key_case($headers, CASE_UPPER);
            }
            webhook($http, $store, $headers, [
                'id' => 'event',
                'event_type' => 'PAYMENT.CAPTURE.COMPLETED',
                'resource' => [
                    'id' => 'paypal-capture',
                    'supplementary_data' => ['related_ids' => ['order_id' => 'paypal-order']],
                    'amount' => ['currency_code' => 'USD', 'value' => '25.00'],
                ],
            ], 'test-webhook');
            return (($store->row['status'] ?? null) === 'paid') === ($scenario !== 'FORGED_WEBHOOK');
        case 'REFUND_TWICE':
            $capture();
            refundOrder($http, $store, $ref);
            return rejected(fn() => refundOrder($http, $store, $ref), 'already refunded')
                && $refundRequests === 1 && $store->row['refunded_minor'] === 2500;
        default:
            throw new LogicException("Unknown scenario: $scenario");
    }
}

try {
    echo runScenario($argv[2]) ? 'PASS' : 'PROBLEM';
} catch (TypeError $error) {
    fwrite(STDERR, $error->getMessage() . PHP_EOL);
    echo 'UNVERIFIED';
}
