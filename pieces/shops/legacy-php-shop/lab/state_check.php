<?php
// Synthetic persistence marker, deliberately separate from financial order state.
declare(strict_types=1);
if (PHP_SAPI !== 'cli') { http_response_code(404); exit(1); }
$sourceRoot = getenv('GOLDGRAFT_LAB_SOURCE_ROOT') ?: '/opt/shop/src';
$path = $sourceRoot . '/data/__lab_persistence.json';
$mode = $argv[1] ?? '';
if ($mode === 'seed') {
    $value = ['marker' => 'goldgraft-offline-persistence-v1', 'synthetic_only' => true];
    if (file_put_contents($path, json_encode($value), LOCK_EX) === false) { exit(1); }
} elseif ($mode !== 'verify') { exit(2); }
$value = json_decode(@file_get_contents($path) ?: '', true);
if (($value['marker'] ?? '') !== 'goldgraft-offline-persistence-v1' ||
    ($value['synthetic_only'] ?? false) !== true) { exit(1); }
echo json_encode(['status' => 'PASS', 'evidence' => 'synthetic_persistence_only']) . "\n";
