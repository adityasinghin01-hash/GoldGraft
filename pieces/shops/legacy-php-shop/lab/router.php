<?php
// Local offline lab wrapper; the vendored application stays byte-for-byte unchanged.
declare(strict_types=1);

function lab_json(int $status, array $body): void {
    http_response_code($status);
    header('Content-Type: application/json');
    header('Cache-Control: no-store');
    header('X-Content-Type-Options: nosniff');
    echo json_encode($body);
}

$sourceRoot = getenv('GOLDGRAFT_LAB_SOURCE_ROOT') ?: '/opt/shop/src';
$keyFile = getenv('GOLDGRAFT_LAB_KEY_FILE') ?: '/run/secrets/lab_key';
header("Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-src 'none'; frame-ancestors 'none'; base-uri 'none'");
$path = rawurldecode(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH) ?: '/');
if ($path === '/__lab/health' && $_SERVER['REQUEST_METHOD'] === 'GET') {
    lab_json(200, ['status' => 'ok', 'mode' => 'offline-lab', 'payments' => 'disabled']);
    return true;
}
$key = @file_get_contents($keyFile);
$provided = $_SERVER['HTTP_X_GOLDGRAFT_LAB_KEY'] ?? '';
if ($key === false || !preg_match('/^[a-f0-9]{64}$/D', trim($key))) {
    lab_json(503, ['error' => 'lab_configuration_missing']);
    return true;
}
if (!hash_equals(trim($key), $provided)) {
    lab_json(401, ['error' => 'lab_access_required']);
    return true;
}
// Never invoke a payment or callback helper in this offline build.
if (!in_array($_SERVER['REQUEST_METHOD'], ['GET', 'HEAD'], true)) {
    lab_json(503, ['error' => 'payment_and_callback_execution_disabled']);
    return true;
}
$pages = ['/' => 'index.php', '/index.php' => 'index.php',
          '/success.php' => 'success.php', '/cancel.php' => 'cancel.php',
          '/api/orders.php' => 'api/orders.php'];
if (isset($pages[$path])) {
    require $sourceRoot . '/' . $pages[$path];
    return true;
}
// No return-false static fallback: only the fixed, non-secret public assets below.
$assets = ['shop.css' => 'text/css', 'tee.svg' => 'image/svg+xml',
           'mug.svg' => 'image/svg+xml', 'poster.svg' => 'image/svg+xml'];
foreach ($assets as $name => $mime) {
    if ($path === '/assets/' . $name) {
        header('Content-Type: ' . $mime);
        header('X-Content-Type-Options: nosniff');
        readfile($sourceRoot . '/assets/' . $name);
        return true;
    }
}
lab_json(404, ['error' => 'route_not_available']);
return true;
