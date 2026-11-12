<?php
declare(strict_types=1);
require_once __DIR__ . '/Checkout.php';
require_once __DIR__ . '/../../../switch-libs/php/switch.php';
use GoldGraft\Candidate\Checkout;
use GoldGraft\Candidate\Hold;

// Every provider-shaped object in this file is scripted test data. No HTTP code.
$checks = [];
function check(string $name, bool $ok): void {
    global $checks;
    if (!$ok) throw new RuntimeException('assertion_failed:' . $name);
    $checks[] = $name;
}
function held(string $name, callable $f): void {
    try { $f(); } catch (Hold) { check($name, true); return; }
    throw new RuntimeException('hold_expected:' . $name);
}
final class ScriptedRest {
    public array $calls = [];
    public array $responses = [];
    public function __invoke(string $method, string $path, ?array $body, array $headers): array {
        $this->calls[] = [$method, $path, $body, $headers];
        if (!$this->responses) throw new RuntimeException('no_scripted_response');
        $next = array_shift($this->responses);
        if ($next instanceof Throwable) throw $next;
        return $next;
    }
}
function created(string $local, string $pid = 'ORDER-TEST', string $status = 'CREATED'): array {
    return ['id' => $pid, 'status' => $status, 'intent' => 'CAPTURE', 'purchase_units' => [[
        'reference_id' => $local, 'payee' => ['merchant_id' => 'TESTSELLER'],
        'amount' => ['currency_code' => 'USD', 'value' => '25.00']
    ]]];
}
function captured(string $local, string $status = 'COMPLETED'): array {
    $v = created($local); $v['status'] = 'COMPLETED';
    $v['purchase_units'][0]['payments'] = ['captures' => [[
        'id' => 'CAPTURE-TEST', 'status' => $status, 'final_capture' => true,
        'amount' => ['currency_code' => 'USD', 'value' => '25.00']
    ]]];
    return $v;
}
function refundData(string $status = 'COMPLETED'): array {
    return ['id' => 'REFUND-TEST', 'status' => $status, 'amount' => ['currency_code' => 'USD', 'value' => '25.00']];
}
function make(string $name, ScriptedRest $r): Checkout {
    global $dir;
    return new Checkout($dir . '/' . $name . '.sqlite', ['tee' => '25.00', 'mug' => '12.50'], 'TESTSELLER', $r);
}
function ready(string $id, ScriptedRest $r): Checkout {
    $s = make($id, $r); $s->open($id, ['tee' => 1]);
    $r->responses[] = [201, created($id)]; $s->create($id); return $s;
}
function paid(string $id, ScriptedRest $r): Checkout {
    $s = ready($id, $r); $r->responses[] = [201, captured($id)]; $s->capture($id); return $s;
}

if ($argc !== 2 || !is_dir($argv[1]) || count(glob($argv[1] . '/*'))) {
    fwrite(STDERR, "Supply an empty private test directory.\n"); exit(2);
}
$dir = $argv[1];

$r = new ScriptedRest(); $s = ready('happy', $r);
check('create-not-paid', !$s->view('happy')['fulfillable']);
check('server-amount-and-payee', $r->calls[0][2]['purchase_units'][0]['amount']['value'] === '25.00'
    && $r->calls[0][2]['purchase_units'][0]['payee']['merchant_id'] === 'TESTSELLER');
check('request-key-persisted-before-dispatch', strlen($r->calls[0][3]['PayPal-Request-Id']) === 32);
$r->responses[] = [201, captured('happy')]; $s->capture('happy');
check('completed-capture-paid', $s->view('happy')['fulfillable']);
check('distinct-operation-keys', $r->calls[0][3]['PayPal-Request-Id'] !== $r->calls[1][3]['PayPal-Request-Id']);
$s->create('happy'); $s->capture('happy');
check('duplicate-create-and-capture-no-dispatch', count($r->calls) === 2);
$s = make('happy', $r);
check('restart-keeps-capture-and-origin', $s->view('happy')['capture_id'] === 'CAPTURE-TEST' && $s->view('happy')['origin'] === 'NEW');
$s->capture('happy'); check('restart-no-second-charge', count($r->calls) === 2);
held('intent-cart-conflict', fn () => $s->open('happy', ['mug' => 2]));
check('cancel-after-paid-does-not-unpay', $s->cancel('happy')['state'] === 'PAID');
$r->responses[] = [201, refundData()]; $s->refund('happy'); $s->refund('happy');
check('full-refund-one-dispatch', count($r->calls) === 3 && $s->view('happy')['state'] === 'REFUNDED');
check('refund-original-capture', $r->calls[2][1] === '/v2/payments/captures/CAPTURE-TEST/refund');
check('refund-exact-amount', $r->calls[2][2] === ['amount' => ['currency_code' => 'USD', 'value' => '25.00']]);
check('refunded-not-fulfillable', !$s->view('happy')['fulfillable']);
$r->responses[] = [200, refundData('PENDING')]; held('refund-regression-held', fn () => $s->reconcile('happy'));
check('regression-does-not-overwrite-refund', $s->view('happy')['refund_state'] === 'COMPLETED');

$r = new ScriptedRest(); $s = ready('cancel', $r); $s->cancel('cancel');
held('cancel-denies-capture', fn () => $s->capture('cancel'));
check('cancel-no-provider-mutation', count($r->calls) === 1 && !$s->view('cancel')['fulfillable']);

$r = new ScriptedRest(); $s = ready('pending', $r); $r->responses[] = [201, captured('pending', 'PENDING')]; $s->capture('pending');
check('pending-not-paid', $s->view('pending')['state'] === 'PENDING' && !$s->view('pending')['fulfillable']);
$r->responses[] = [200, captured('pending')['purchase_units'][0]['payments']['captures'][0]];
$s->reconcile('pending'); check('pending-refetch-completed', $s->view('pending')['fulfillable']);
check('refetch-no-idempotency-key', $r->calls[2][0] === 'GET' && $r->calls[2][2] === null && $r->calls[2][3] === []);
$r->responses[] = [200, captured('pending', 'PENDING')['purchase_units'][0]['payments']['captures'][0]];
held('stale-pending-cannot-regress-paid', fn () => $s->reconcile('pending'));

foreach (['DECLINED', 'FAILED'] as $status) {
    $id = strtolower($status); $r = new ScriptedRest(); $s = ready($id, $r);
    $r->responses[] = [201, captured($id, $status)]; $s->capture($id); $s->capture($id);
    check($id . '-no-fulfilment-or-new-key', !$s->view($id)['fulfillable'] && count($r->calls) === 2);
}
$r = new ScriptedRest(); $s = make('action', $r); $s->open('action', ['tee' => 1]);
$r->responses[] = [201, created('action', 'ORDER-TEST', 'PAYER_ACTION_REQUIRED')]; $s->create('action');
check('payer-action-not-paid', $s->view('action')['state'] === 'ACTION_REQUIRED' && !$s->view('action')['fulfillable']);

$r = new ScriptedRest(); $s = ready('lost', $r); $r->responses[] = new RuntimeException('pretend-timeout-with-secret');
held('lost-capture-response-held', fn () => $s->capture('lost'));
$s = make('lost', $r); held('lost-after-restart-no-blind-retry', fn () => $s->capture('lost'));
check('lost-only-one-capture-dispatch', count($r->calls) === 2);
$r->responses[] = [200, captured('lost')]; $s->reconcile('lost');
check('lost-recovered-through-get', $s->view('lost')['fulfillable'] && $r->calls[2][0] === 'GET');
$s->capture('lost'); check('reconciled-capture-stays-idempotent', count($r->calls) === 3);

$r = new ScriptedRest(); $s = make('create-lost', $r); $s->open('create-lost', ['tee' => 1]);
$r->responses[] = new RuntimeException('timeout'); held('lost-create-held', fn () => $s->create('create-lost'));
held('lost-create-cannot-new-key', fn () => $s->create('create-lost'));
held('lost-create-needs-lookup', fn () => $s->reconcile('create-lost'));
check('lost-create-one-dispatch', count($r->calls) === 1);

foreach (['amount', 'currency', 'order', 'reference', 'capture', 'missing', 'multiple'] as $fault) {
    $id = 'bad-' . $fault; $r = new ScriptedRest(); $s = ready($id, $r); $d = captured($id);
    switch ($fault) {
        case 'amount': $d['purchase_units'][0]['payments']['captures'][0]['amount']['value'] = '0.01'; break;
        case 'currency': $d['purchase_units'][0]['payments']['captures'][0]['amount']['currency_code'] = 'EUR'; break;
        case 'order': $d['id'] = 'OTHER-ORDER'; break;
        case 'reference': $d['purchase_units'][0]['reference_id'] = 'other'; break;
        case 'capture': $d['purchase_units'][0]['payments']['captures'][0]['id'] = '../unsafe'; break;
        case 'missing': unset($d['purchase_units'][0]['payments']); break;
        case 'multiple': $d['purchase_units'][0]['payments']['captures'][] = $d['purchase_units'][0]['payments']['captures'][0]; break;
    }
    $r->responses[] = [201, $d]; held($fault . '-capture-held', fn () => $s->capture($id));
    check($fault . '-cannot-fulfil', !$s->view($id)['fulfillable']);
}
foreach (['merchant', 'amount', 'intent'] as $fault) {
    $id = 'create-' . $fault; $r = new ScriptedRest(); $s = make($id, $r); $s->open($id, ['tee' => 1]); $d = created($id);
    if ($fault === 'merchant') $d['purchase_units'][0]['payee']['merchant_id'] = 'OTHERSELLER';
    if ($fault === 'amount') $d['purchase_units'][0]['amount']['value'] = '25.001';
    if ($fault === 'intent') $d['intent'] = 'AUTHORIZE';
    $r->responses[] = [201, $d]; held('create-' . $fault . '-held', fn () => $s->create($id));
}
foreach ([422, 429, 500] as $http) {
    $id = 'http-' . $http; $r = new ScriptedRest(); $s = ready($id, $r); $r->responses[] = [$http, ['name' => 'DECLINE']];
    held($id . '-held', fn () => $s->capture($id)); held($id . '-no-new-key', fn () => $s->capture($id));
}
$r = new ScriptedRest(); $s = paid('refund-pending', $r); $r->responses[] = [201, refundData('PENDING')]; $s->refund('refund-pending');
check('refund-pending-not-refunded-or-fulfillable', $s->view('refund-pending')['state'] === 'PAID' && !$s->view('refund-pending')['fulfillable']);
$s = make('refund-pending', $r); $r->responses[] = [200, refundData()]; $s->reconcile('refund-pending');
check('refund-refetch-survives-restart', $s->view('refund-pending')['state'] === 'REFUNDED');
$s->refund('refund-pending'); check('refund-restart-no-duplicate', count($r->calls) === 4);

$r = new ScriptedRest(); $s = paid('refund-lost', $r); $r->responses[] = new RuntimeException('timeout');
held('unknown-refund-held', fn () => $s->refund('refund-lost'));
$r->responses[] = [200, captured('refund-lost')['purchase_units'][0]['payments']['captures'][0]]; $s->reconcile('refund-lost');
check('capture-complete-not-proof-of-no-refund', $s->view('refund-lost')['hold'] !== null && !$s->view('refund-lost')['fulfillable']);
held('unknown-refund-no-new-key', fn () => $s->refund('refund-lost'));

$r = new ScriptedRest(); $s = ready('parallel', $r);
$r->responses[] = [201, captured('parallel')];
// Re-enter through a separate connection during dispatch: the intent is already durable.
$rest = function ($method, $path, $body, $headers) use ($r) {
    $other = make('parallel', $r);
    held('concurrent-capture-denied-before-dispatch', fn () => $other->capture('parallel'));
    return $r($method, $path, $body, $headers);
};
$s = new Checkout($dir . '/parallel.sqlite', ['tee' => '25.00'], 'TESTSELLER', $rest); $s->capture('parallel');
check('concurrent-one-provider-capture', count($r->calls) === 2);

$r = new ScriptedRest(); $s = make('minimal', $r); $s->open('minimal', ['tee' => 1]);
$r->responses = [[201, ['id' => 'ORDER-TEST', 'status' => 'CREATED']], [200, created('minimal')]];
$s->create('minimal');
check('minimal-create-requires-real-port-readback', count($r->calls) === 2 && $r->calls[1][0] === 'GET'
    && $s->view('minimal')['state'] === 'CREATED');
$r->responses[] = [201, captured('minimal')]; $s->capture('minimal');
$r->responses[] = [201, ['id' => 'REFUND-TEST', 'status' => 'COMPLETED']]; $r->responses[] = [200, refundData()];
$s->refund('minimal');
check('minimal-refund-needs-money-readback', count($r->calls) === 5 && $r->calls[4][0] === 'GET'
    && $s->view('minimal')['state'] === 'REFUNDED');

$r = new ScriptedRest(); $s = make('minimal-held', $r); $s->open('minimal-held', ['tee' => 1]);
$r->responses = [[201, ['id' => 'ORDER-TEST', 'status' => 'CREATED']], new RuntimeException('readback-unavailable')];
held('minimal-create-readback-outage-held', fn () => $s->create('minimal-held'));
held('unverified-minimal-order-cannot-capture', fn () => $s->capture('minimal-held'));
check('minimal-outage-keeps-id-and-no-fulfilment', $s->view('minimal-held')['provider_order_id'] === 'ORDER-TEST'
    && !$s->view('minimal-held')['fulfillable']);
$r->responses[] = [200, created('minimal-held')]; $s->create('minimal-held');
check('minimal-create-retry-is-get-only', count($r->calls) === 3 && $r->calls[2][0] === 'GET');

$r = new ScriptedRest(); $s = ready('unexpected-capture', $r); $r->responses[] = [200, captured('unexpected-capture')];
held('unrequested-capture-needs-correspondence-review', fn () => $s->reconcile('unexpected-capture'));

$r = new ScriptedRest(); $s = make('collision', $r);
$s->open('first', ['tee' => 1]); $r->responses[] = [201, created('first')]; $s->create('first');
$s->open('second', ['tee' => 1]); $r->responses[] = [201, created('second')];
held('same-provider-order-cannot-bind-two-intents', fn () => $s->create('second'));
check('resource-collision-preserves-first', $s->view('first')['provider_order_id'] === 'ORDER-TEST'
    && $s->view('second')['provider_order_id'] === null);

$r = new ScriptedRest(); $s = ready('nonfinal', $r); $d = captured('nonfinal');
$d['purchase_units'][0]['payments']['captures'][0]['final_capture'] = false;
$r->responses[] = [201, $d]; held('nonfinal-capture-outside-first-scope', fn () => $s->capture('nonfinal'));

// Actual switch library + actual candidate, synthetic signed configs only.
$pair = sodium_crypto_sign_keypair(); $secret = sodium_crypto_sign_secretkey($pair);
$public = base64_encode(sodium_crypto_sign_publickey($pair)); $now = '2026-11-12T12:00:00Z';
$configs = [];
foreach ([0, 1, 10, 50, 100] as $index => $stage) {
    $c = ['graft_id' => 'candidate-test', 'stage_pct' => $stage, 'version' => $index + 1,
        'origin_rules' => [], 'expires_at' => '2026-11-12T13:00:00Z'];
    $c['signature'] = base64_encode(sodium_crypto_sign_detached(\GoldGraft\SwitchLib\signed_bytes($c), $secret));
    $configs[$stage] = $c;
}
$cache = new \GoldGraft\SwitchLib\VerifiedConfigCache('candidate-test', $public);
foreach ([0, 1, 10, 50, 100] as $stage) {
    check('stage-' . $stage . '-accepted', $cache->accept($configs[$stage], $now));
    foreach (['intent-a', 'intent-b', 'intent-c'] as $ref) {
        $actual = \GoldGraft\SwitchLib\decide($cache->current($now), $public, 'candidate-test', $ref, $now);
        $expected = \GoldGraft\SwitchLib\bucket('candidate-test', $ref) < $stage ? 'NEW' : 'OLD';
        check('stage-' . $stage . '-' . $ref . '-stable', $actual === $expected);
    }
}
$r = new ScriptedRest(); $s = ready('cutback', $r);
$cutback = $configs[0]; $cutback['version'] = 6;
$cutback['signature'] = base64_encode(sodium_crypto_sign_detached(\GoldGraft\SwitchLib\signed_bytes($cutback), $secret));
check('cutback-new-admission-old', $cache->accept($cutback, $now)
    && \GoldGraft\SwitchLib\decide($cache->current($now), $public, 'candidate-test', 'cutback', $now) === 'OLD');
check('cutback-inflight-remains-new', \GoldGraft\SwitchLib\route_existing('CAPTURE', $s->view('cutback')['origin']) === 'NEW');
$r->responses[] = [201, captured('cutback')]; $s->capture('cutback');
check('cutback-preserves-capture', $s->view('cutback')['fulfillable']);
$expired = '2026-11-12T14:00:00Z';
check('expired-config-new-admission-old', \GoldGraft\SwitchLib\decide($cache->current($expired), $public, 'candidate-test', 'cutback', $expired) === 'OLD');
$r->responses[] = [201, refundData()]; $s->refund('cutback');
check('expired-config-existing-refund-new', $r->calls[2][1] === '/v2/payments/captures/CAPTURE-TEST/refund'
    && $s->view('cutback')['state'] === 'REFUNDED');
check('old-origin-retained-at-full-stage', \GoldGraft\SwitchLib\route_existing('REFUND', 'OLD') === 'OLD');
try { \GoldGraft\SwitchLib\route_existing('REFUND', null); throw new RuntimeException('unknown_origin_accepted'); }
catch (InvalidArgumentException) { check('missing-origin-never-guessed', true); }
sodium_memzero($secret); // Ephemeral test key, never saved or printed.

held('merchant-change-denied-on-restart', fn () => new Checkout($dir . '/parallel.sqlite', ['tee' => '25.00'], 'OTHERSELLER', $r));
file_put_contents($dir . '/corrupt.sqlite', 'invalid database preserved');
try { make('corrupt', $r); throw new RuntimeException('corruption_accepted'); }
catch (PDOException) { check('corrupt-state-preserved', file_get_contents($dir . '/corrupt.sqlite') === 'invalid database preserved'); }
held('memory-database-not-persistent', fn () => new Checkout(':memory:', ['tee' => '25.00'], 'TESTSELLER', $r));
$foreign = new PDO('sqlite:' . $dir . '/foreign.sqlite'); $foreign->exec('CREATE TABLE unrelated (id TEXT)'); $foreign = null;
held('unrelated-sqlite-not-treated-as-empty-shop', fn () => make('foreign', $r));
file_put_contents($dir . '/empty.sqlite', '');
held('empty-existing-database-held', fn () => make('empty', $r));
$r = new ScriptedRest(); $s = ready('tampered-runtime', $r);
$db = new PDO('sqlite:' . $dir . '/tampered-runtime.sqlite');
$raw = $db->query('SELECT body FROM candidate_orders')->fetchColumn(); $data = json_decode($raw, true, 32, JSON_THROW_ON_ERROR);
$data['origin'] = 'OLD'; $db->prepare('UPDATE candidate_orders SET body=?')->execute([json_encode($data)]); $db = null;
held('runtime-rejects-stored-origin-tamper', fn () => $s->view('tampered-runtime'));
echo json_encode(['status' => 'PASS', 'checks' => count($checks), 'names' => $checks,
    'evidence' => 'OFFLINE_SCRIPTED_DOMAIN_COMPONENT', 'provider_calls' => 0,
    'payment_qualified' => false], JSON_THROW_ON_ERROR) . PHP_EOL;
