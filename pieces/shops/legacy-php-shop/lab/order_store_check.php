<?php
// Exercise unchanged legacy storage with synthetic records only. CLI, never a web route.
declare(strict_types=1);
if (PHP_SAPI !== 'cli') { http_response_code(404); exit(1); }
$source = getenv('GOLDGRAFT_LAB_SOURCE_ROOT');
$runId = getenv('GOLDGRAFT_OFFLINE_RUN_ID');
if (!$source || !$runId || !preg_match('/^[A-Za-z0-9_-]{1,100}$/D', $runId)) { exit(2); }
require $source . '/lib/orders_store.php';
$mode = $argv[1] ?? '';
$path = orders_path();
$first = ['token' => 'OFFLINE-' . $runId . '-A', 'amount' => '25.00',
          'status' => 'CREATED', 'synthetic_only' => true, 'component_note' => 'updated'];
$second = ['token' => 'OFFLINE-' . $runId . '-B', 'amount' => '12.50',
           'status' => 'CREATED', 'synthetic_only' => true];
if ($mode === 'seed') {
    if (file_exists($path)) { exit(3); } // Never replace an existing order store.
    $initial = $first;
    $initial['component_note'] = 'initial';
    orders_save($initial);
    orders_save($second);
    orders_save($first); // Update existing key without losing the other record.
} elseif ($mode === 'corrupt') {
    if (file_exists($path)) { exit(3); }
    $invalid = '{synthetic-invalid-json';
    if (file_put_contents($path, $invalid) === false) { exit(1); }
    $empty = orders_all() === [];
    echo json_encode(['evidence' => 'SYNTHETIC_LOCAL_ORDER_STORE',
        'classification' => $empty ? 'BASELINE_DEFECT_OBSERVED' : 'NOT_REPRODUCED',
        'observation' => 'invalid_json_silently_read_as_empty_store',
        'observed' => $empty, 'input_preserved' => file_get_contents($path) === $invalid,
        'payment_operations' => 0]) . "\n";
    exit(0);
} elseif ($mode !== 'verify') { exit(2); }
if (orders_get($first['token']) !== $first || orders_get($second['token']) !== $second
        || count(orders_all()) !== 2 || orders_get('OFFLINE-MISSING') !== null) { exit(1); }
echo json_encode(['status' => 'PASS', 'evidence' => 'SYNTHETIC_LOCAL_ORDER_STORE',
    'records' => 2, 'update_retained_other_record' => true,
    'missing_key_returns_null' => true, 'payment_operations' => 0]) . "\n";
