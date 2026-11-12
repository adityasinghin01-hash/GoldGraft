<?php
declare(strict_types=1);
require __DIR__ . '/switch.php';
function check(bool $ok): void { if (!$ok) { throw new RuntimeException('cache_check_failed'); } }
$d = json_decode(file_get_contents($argv[1]), true, 512, JSON_THROW_ON_ERROR);
$c = new \GoldGraft\SwitchLib\VerifiedConfigCache($d['graft_id'], $d['key']);
check($c->accept($d['initial'], $d['now']));
$d['initial']['stage_pct'] = 100;
check($c->current($d['now'])['stage_pct'] === 1);
check(!$c->accept($d['older'], $d['now']));
check(!$c->accept($d['same_version_changed'], $d['now']));
check(!$c->accept($d['expired'], $d['now']));
check($c->current($d['now'])['stage_pct'] === 1);
$returned = $c->current($d['now']); $returned['stage_pct'] = 100;
check($c->current($d['now'])['stage_pct'] === 1);
check($c->accept($d['newer'], $d['now']));
check($c->current($d['now'])['version'] === 4);
check($c->current($d['expires']) === null);
check(\GoldGraft\SwitchLib\route_existing('CAPTURE', 'NEW') === 'NEW');
$denied = false;
try { \GoldGraft\SwitchLib\route_existing('REFUND', null); } catch (InvalidArgumentException $e) { $denied = true; }
check($denied);
echo json_encode(['cases' => 12, 'failures' => [], 'evidence' => 'LOCAL_SYNTHETIC_CACHE']) . "\n";
