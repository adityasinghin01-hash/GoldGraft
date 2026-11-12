<?php
require_once __DIR__ . '/../lib/paypal_orders.php';
require_once __DIR__ . '/../lib/orders_store.php';
header('Content-Type: application/json');
$input = json_decode(file_get_contents('php://input'), true) ?: [];
$order = orders_get($input['token'] ?? '');
if (!$order || $order['status'] !== 'PAID') { http_response_code(400); exit; }
$r = gg_refund_capture($order['transaction_id'], $order['amount'], SHOP_CURRENCY, $order['token'] . ':refund');
if (!$r['ok'] || $r['refund_status'] !== 'COMPLETED') { http_response_code(502); exit; }
$order['status'] = 'REFUNDED'; $order['refund_id'] = $r['refund_id']; orders_save($order);
echo json_encode(['ok'=>true, 'refundId'=>$r['refund_id']]);
