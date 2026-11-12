<?php
// Scripted webhook probe only. Production ingress belongs to CallbackGateway.
require_once __DIR__ . '/lib/paypal_orders.php';
$raw = file_get_contents('php://input');
if (!gg_verify_webhook(getallheaders(), $raw)) { http_response_code(400); exit; }
http_response_code(200);
