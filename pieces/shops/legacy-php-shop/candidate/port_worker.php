<?php
declare(strict_types=1);
require_once __DIR__ . '/Checkout.php';
use GoldGraft\Candidate\Checkout;
// Private stdio composition port; no HTTP listener or credentials. The owning
// host must authenticate/authorize its backend binding before using real mode.
function send_frame(array $value): void { echo json_encode($value, JSON_THROW_ON_ERROR) . "\n"; flush(); }
try {
    if ($argc !== 2) throw new RuntimeException('private_database_required');
    $line = fgets(STDIN, 65537);
    if ($line === false || strlen($line) > 65536) throw new RuntimeException('invalid_frame');
    $input = json_decode($line, true, 32, JSON_THROW_ON_ERROR);
    if (!is_array($input) || !in_array($input['action'] ?? null, ['open', 'create', 'capture', 'refund', 'reconcile', 'view', 'cancel'], true)) {
        throw new RuntimeException('invalid_action');
    }
    $rest = function ($method, $path, $body, $headers): array {
        send_frame(['kind' => 'rest', 'method' => $method, 'path' => $path,
                    'body' => $body === [] ? new stdClass() : $body, 'headers' => (object)$headers]);
        $line = fgets(STDIN, 262145);
        if ($line === false || strlen($line) > 262144) throw new RuntimeException('invalid_backend_frame');
        $reply = json_decode($line, true, 64, JSON_THROW_ON_ERROR);
        if (($reply['kind'] ?? null) !== 'reply' || !is_int($reply['status'] ?? null) || !is_array($reply['data'] ?? null)) {
            throw new RuntimeException('backend_held');
        }
        return [$reply['status'], $reply['data']];
    };
    $shop = new Checkout($argv[1], ['tee' => '25.00', 'mug' => '12.50', 'poster' => '18.00'], $input['merchant_id'], $rest);
    $value = $input['action'] === 'open' ? $shop->open($input['id'], $input['cart']) : $shop->{$input['action']}($input['id']);
    send_frame(['kind' => 'result', 'status' => 'OK', 'order' => $value]);
} catch (Throwable) { send_frame(['kind' => 'result', 'status' => 'HOLD']); }
