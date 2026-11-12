<?php
declare(strict_types=1);
// PRIVATE OFFLINE HARNESS ONLY. Never install this router as a merchant app.
// Its sole provider port is scripted; it cannot contact PayPal.
require_once __DIR__ . '/Checkout.php';
use GoldGraft\Candidate\Checkout;

$path = parse_url($_SERVER['REQUEST_URI'] ?? '', PHP_URL_PATH);
header('Cache-Control: no-store'); header('X-Content-Type-Options: nosniff');
header("Content-Security-Policy: default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; form-action 'none'");
function reply(int $status, array $body): never {
    http_response_code($status); header('Content-Type: application/json'); echo json_encode($body, JSON_THROW_ON_ERROR); exit;
}
if ($path === '/__candidate/health' && $_SERVER['REQUEST_METHOD'] === 'GET') reply(200, ['mode' => 'OFFLINE_SCRIPTED', 'provider_calls' => 0]);
$key = getenv('CANDIDATE_LAB_KEY');
if (!$key || !hash_equals($key, $_SERVER['HTTP_X_CANDIDATE_LAB_KEY'] ?? '')) reply(401, ['error' => 'lab_access_required']);
if (!in_array($path, ['/', '/__candidate/action'], true)) reply(404, ['error' => 'route_not_served']);
if ($path === '/' && $_SERVER['REQUEST_METHOD'] === 'GET') {
    header('Content-Type: text/html; charset=utf-8');
    readfile(__DIR__ . '/offline.html'); exit;
}
if ($path !== '/__candidate/action' || $_SERVER['REQUEST_METHOD'] !== 'POST') reply(405, ['error' => 'method_not_allowed']);
if (($_SERVER['CONTENT_TYPE'] ?? '') !== 'application/json' || (int)($_SERVER['CONTENT_LENGTH'] ?? 0) > 4096) reply(400, ['error' => 'invalid_request']);
try {
    $input = json_decode(file_get_contents('php://input'), true, 16, JSON_THROW_ON_ERROR);
    if (!is_array($input) || !is_string($input['id'] ?? null) || !in_array($input['action'] ?? null,
        ['create', 'capture', 'cancel', 'refund', 'reconcile'], true)) reply(400, ['error' => 'invalid_request']);
    $dir = getenv('CANDIDATE_LAB_STATE');
    if (!$dir || !is_dir($dir)) throw new RuntimeException('private_state_missing');
    // Small persistent scripted counterpart, owned exclusively by this harness.
    $fake = new PDO('sqlite:' . $dir . '/scripted.sqlite', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $fake->exec('CREATE TABLE IF NOT EXISTS scripted (path TEXT PRIMARY KEY, body TEXT NOT NULL)');
    $rest = function (string $method, string $endpoint, ?array $body, array $headers) use ($fake): array {
        if ($method === 'GET') {
            $q = $fake->prepare('SELECT body FROM scripted WHERE path=?'); $q->execute([$endpoint]); $value = $q->fetchColumn();
            return $value === false ? [404, []] : [200, json_decode($value, true, 32, JSON_THROW_ON_ERROR)];
        }
        $save = function (string $resource, array $data) use ($fake) {
            $fake->prepare('INSERT OR REPLACE INTO scripted VALUES (?,?)')->execute([$resource, json_encode($data, JSON_THROW_ON_ERROR)]);
        };
        if ($method === 'POST' && $endpoint === '/v2/checkout/orders') {
            $id = 'TESTORDER-' . substr(hash('sha256', $headers['PayPal-Request-Id']), 0, 16);
            $data = ['id' => $id, 'status' => 'CREATED', 'intent' => 'CAPTURE', 'purchase_units' => $body['purchase_units']];
            $save('/v2/checkout/orders/' . $id, $data); return [201, $data];
        }
        if ($method === 'POST' && preg_match('~^/v2/checkout/orders/([A-Za-z0-9-]+)/capture$~D', $endpoint, $m)) {
            $q = $fake->prepare('SELECT body FROM scripted WHERE path=?'); $q->execute(['/v2/checkout/orders/' . $m[1]]);
            $raw = $q->fetchColumn(); if ($raw === false) return [404, []];
            $data = json_decode($raw, true, 32, JSON_THROW_ON_ERROR); $data['status'] = 'COMPLETED';
            $capture = ['id' => 'TESTCAPTURE-' . substr(hash('sha256', $m[1]), 0, 16), 'status' => 'COMPLETED',
                        'final_capture' => true, 'amount' => $data['purchase_units'][0]['amount']];
            $data['purchase_units'][0]['payments'] = ['captures' => [$capture]];
            $save('/v2/checkout/orders/' . $m[1], $data); $save('/v2/payments/captures/' . $capture['id'], $capture);
            return [201, $data];
        }
        if ($method === 'POST' && preg_match('~^/v2/payments/captures/([A-Za-z0-9-]+)/refund$~D', $endpoint, $m)) {
            $q = $fake->prepare('SELECT body FROM scripted WHERE path=?'); $q->execute(['/v2/payments/captures/' . $m[1]]);
            $raw = $q->fetchColumn(); if ($raw === false) return [404, []];
            $capture = json_decode($raw, true, 32, JSON_THROW_ON_ERROR);
            if ($capture['status'] !== 'COMPLETED') return [422, []];
            $data = ['id' => 'TESTREFUND-' . substr(hash('sha256', $m[1]), 0, 16), 'status' => 'COMPLETED', 'amount' => $body['amount']];
            $capture['status'] = 'REFUNDED'; $save('/v2/payments/captures/' . $m[1], $capture);
            $save('/v2/payments/refunds/' . $data['id'], $data); return [201, $data];
        }
        return [400, []];
    };
    $shop = new Checkout($dir . '/candidate.sqlite', ['tee' => '25.00', 'mug' => '12.50', 'poster' => '18.00'], 'TESTSELLER', $rest);
    if ($input['action'] === 'create') $shop->open($input['id'], ['tee' => 1]);
    $state = $shop->{$input['action']}($input['id']);
    reply(200, ['mode' => 'OFFLINE_SCRIPTED', 'payment_qualified' => false, 'order' => $state]);
} catch (Throwable) { reply(409, ['mode' => 'OFFLINE_SCRIPTED', 'error' => 'order_held', 'payment_qualified' => false]); }
