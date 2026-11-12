<?php
// Offline compatibility fixture. Durable application is in candidate/Checkout.php.
require_once __DIR__ . '/../lib/paypal_orders.php';
require_once __DIR__ . '/../lib/orders_store.php';
header('Content-Type: application/json');
$input = json_decode(file_get_contents('php://input'), true) ?: [];
$order = orders_get($input['token'] ?? '');
if (!$order) { http_response_code(404); exit; }
if (in_array($order['status'], ['PAID','REFUNDED','PENDING'], true)) { echo json_encode(['ok'=>true]); exit; }
$r = gg_capture_order($order['token'], $order['token'] . ':capture');
if (!$r['ok'] || !$r['capture_id']) { http_response_code(502); exit; }
if ($r['amount'] !== $order['amount'] || $r['currency'] !== SHOP_CURRENCY) { http_response_code(409); exit; }
$order['status'] = $r['capture_status'] === 'COMPLETED' ? 'PAID' : 'PENDING';
$order['transaction_id'] = $r['capture_id']; $order['payer_id'] = $r['payer_id']; $order['payer_email'] = $r['payer_email'];
orders_save($order);
echo json_encode(['ok' => true, 'transactionId' => $r['capture_id'], 'amount' => $order['amount']]);
