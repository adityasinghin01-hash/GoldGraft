<?php
declare(strict_types=1);
require __DIR__ . '/switch.php';
$data = json_decode(file_get_contents($argv[1]), true, 512, JSON_THROW_ON_ERROR);
$failures = [];
foreach ($data['cases'] as $case) {
    $actual = \GoldGraft\SwitchLib\decide($case['config'], $data['public_key_b64'], $data['graft_id'],
        $case['order_ref'], $data['now'], $case['action'], $case['origin']);
    if ($actual !== $case['expect']) $failures[] = $case['name'];
}
echo json_encode(['language' => 'php', 'cases' => count($data['cases']), 'failures' => $failures,
    'evidence' => 'SYNTHETIC_SWITCH_CONFORMANCE']) . "\n";
exit($failures ? 1 : 0);
