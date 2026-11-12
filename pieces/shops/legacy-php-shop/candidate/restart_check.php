<?php
declare(strict_types=1);
require_once __DIR__ . '/Checkout.php';
use GoldGraft\Candidate\Checkout;
// Invoked in a second PHP process after the scripted suite has fully exited.
if ($argc !== 2 || !is_dir($argv[1])) exit(2);
$calls = 0; $checked = 0;
$deny = function () use (&$calls): array { $calls++; throw new RuntimeException('transport_absent'); };
foreach (['happy' => 'REFUNDED', 'lost' => 'PAID', 'refund-pending' => 'REFUNDED'] as $id => $expected) {
    $s = new Checkout($argv[1] . '/' . $id . '.sqlite', ['tee' => '25.00', 'mug' => '12.50'], 'TESTSELLER', $deny);
    if ($s->view($id)['state'] !== $expected || $s->view($id)['origin'] !== 'NEW') exit(3);
    $s->capture($id); // Existing DONE operation must not dispatch after restart.
    if ($s->view($id)['state'] !== $expected) exit(4);
    $checked++;
}
if ($calls !== 0) exit(5);
echo json_encode(['status' => 'PASS', 'process_restart_records' => $checked, 'transport_calls' => $calls,
    'evidence' => 'LOCAL_CANDIDATE_RESTART_WITHOUT_SERVICE', 'exit_qualified' => false]) . PHP_EOL;
