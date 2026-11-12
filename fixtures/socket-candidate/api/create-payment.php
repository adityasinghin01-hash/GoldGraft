<?php
// Reviewed operator fixture for offline socket compatibility; not merchant code.
require_once __DIR__ . '/../lib/paypal_orders.php';
require_once __DIR__ . '/../lib/orders_store.php';
header('Content-Type: application/json');
$cart = json_decode(file_get_contents('php://input'), true) ?: [];
$minor = 0; $items = [];
foreach ($cart as $sku => $qty) {
    if (!isset($PRODUCTS[$sku])) continue;
    if (!is_int($qty) || $qty < 1 || $qty > 99) { http_response_code(400); exit; }
    $price = $PRODUCTS[$sku]['price'];
    $minor += ((int)str_replace('.', '', $price)) * $qty;
    $items[] = ['name' => $PRODUCTS[$sku]['name'], 'unit_amount' => $price, 'quantity' => $qty];
}
if (!$minor) { http_response_code(400); exit; }
$total = sprintf('%d.%02d', intdiv($minor,100), $minor % 100);
$r = gg_create_order($items, $total, SHOP_CURRENCY, SHOP_BASE_URL . '/success.php', SHOP_BASE_URL . '/cancel.php', 'fixture-' . bin2hex(random_bytes(8)));
if (!$r['ok'] || !$r['id']) { http_response_code(502); exit; }
orders_save(['token' => $r['id'], 'amount' => $total, 'status' => 'CREATED', 'created' => date('c')]);
echo json_encode(['token' => $r['id']]);
