<?php
declare(strict_types=1);
namespace GoldGraft\Candidate;

require_once __DIR__ . '/../domain/usd_cart.php';
use function GoldGraft\ShopDomain\cart_total;
use function GoldGraft\ShopDomain\usd_minor;

/** A shop-domain hold. Never contains a raw provider response or credential. */
final class Hold extends \RuntimeException {}

/**
 * Separate USD, one-time NEW candidate component; never modifies vendor/.
 *
 * The injected callable mirrors current PayPalClient.rest(method,path,body,headers)
 * and returns [httpStatus, decodedObject]. No transport, credentials, callback
 * authentication, service authority or live entry point is implemented here.
 * A qualified backend adapter must supply those independently.
 */
final class Checkout {
    private \PDO $db;
    private \Closure $rest;
    private array $catalogue;
    private string $merchant;

    public function __construct(string $database, array $catalogue, string $merchant, callable $rest) {
        if (!preg_match('/^[A-Z0-9]{5,32}$/D', $merchant)) throw new Hold('invalid_sandbox_merchant');
        if ($database === ':memory:' || !is_dir(dirname($database)) || is_link($database)
            || (file_exists($database) && (!is_file($database) || filesize($database) === 0))) {
            throw new Hold('persistent_private_database_required');
        }
        // Caller owns a private, writable state directory outside served source.
        // Existing corrupt/non-SQLite files fail closed; they are never replaced.
        $existing = file_exists($database);
        $this->db = new \PDO('sqlite:' . $database, null, null, [\PDO::ATTR_ERRMODE => \PDO::ERRMODE_EXCEPTION]);
        if ($existing) {
            $tables = $this->db->query("SELECT name FROM sqlite_master WHERE type='table'")->fetchAll(\PDO::FETCH_COLUMN);
            if (array_diff(['candidate_meta', 'candidate_orders', 'candidate_operations', 'candidate_resources'], $tables)) {
                throw new Hold('existing_database_schema_unknown');
            }
        }
        $this->db->exec('PRAGMA busy_timeout=5000; PRAGMA synchronous=FULL; PRAGMA foreign_keys=ON;');
        $this->db->exec('CREATE TABLE IF NOT EXISTS candidate_meta (id INTEGER PRIMARY KEY CHECK(id=1), merchant TEXT NOT NULL)');
        $this->db->exec('CREATE TABLE IF NOT EXISTS candidate_orders (id TEXT PRIMARY KEY, body TEXT NOT NULL)');
        $this->db->exec('CREATE TABLE IF NOT EXISTS candidate_operations (order_id TEXT NOT NULL REFERENCES candidate_orders(id), kind TEXT NOT NULL, request_id TEXT NOT NULL UNIQUE, status TEXT NOT NULL, PRIMARY KEY(order_id,kind))');
        $this->db->exec('CREATE TABLE IF NOT EXISTS candidate_resources (kind TEXT NOT NULL, resource_id TEXT NOT NULL, order_id TEXT NOT NULL REFERENCES candidate_orders(id), PRIMARY KEY(kind,resource_id))');
        $this->catalogue = $catalogue;
        $this->merchant = $merchant;
        $this->rest = \Closure::fromCallable($rest);
        $this->atomic(function () use ($merchant) {
            $row = $this->db->query('SELECT merchant FROM candidate_meta WHERE id=1')->fetchColumn();
            if ($row !== false && $row !== $merchant) throw new Hold('merchant_binding_changed');
            $this->db->prepare('INSERT OR IGNORE INTO candidate_meta VALUES (1,?)')->execute([$merchant]);
        });
    }

    private function atomic(callable $fn): mixed {
        $this->db->exec('BEGIN IMMEDIATE');
        try { $value = $fn(); $this->db->exec('COMMIT'); return $value; }
        catch (\Throwable $e) { $this->db->exec('ROLLBACK'); throw $e; }
    }

    private static function identifier(mixed $value): string {
        if (!is_string($value) || !preg_match('/^[A-Za-z0-9-]{1,64}$/D', $value)) throw new Hold('invalid_identifier');
        return $value;
    }

    private function load(string $id): array {
        self::identifier($id);
        $s = $this->db->prepare('SELECT body FROM candidate_orders WHERE id=?'); $s->execute([$id]);
        $raw = $s->fetchColumn();
        if ($raw === false) throw new Hold('unknown_local_order');
        $value = json_decode($raw, true, 64, JSON_THROW_ON_ERROR);
        if (!is_array($value) || ($value['id'] ?? null) !== $id) throw new Hold('invalid_order_state');
        if (($value['origin'] ?? null) !== 'NEW' || ($value['api_family'] ?? null) !== 'orders-v2'
            || ($value['environment'] ?? null) !== 'sandbox' || ($value['merchant_id'] ?? null) !== $this->merchant
            || ($value['currency'] ?? null) !== 'USD' || !is_string($value['amount'] ?? null)
            || !is_bool($value['buyer_cancelled'] ?? null)
            || !in_array($value['state'] ?? null, ['OPEN', 'CREATE_UNKNOWN', 'CREATE_RECHECK', 'CREATED', 'ACTION_REQUIRED',
                'CAPTURE_UNKNOWN', 'PENDING', 'PAID', 'DECLINED', 'FAILED', 'REFUNDED', 'PARTIALLY_REFUNDED'], true)) {
            throw new Hold('stored_origin_or_state_invalid');
        }
        if (usd_minor($value['amount']) === 0) throw new Hold('invalid_stored_amount');
        return $value;
    }

    private function save(array $o): void {
        $this->db->prepare('UPDATE candidate_orders SET body=? WHERE id=?')->execute([
            json_encode($o, JSON_THROW_ON_ERROR), $o['id']
        ]);
    }

    public function view(string $id): array {
        $o = $this->load($id);
        $o['fulfillable'] = $o['state'] === 'PAID' && $o['hold'] === null && $o['refund_state'] === null;
        return $o;
    }

    /** Stable checkout intent supplied by the trusted caller, not browser totals. */
    public function open(string $id, array $cart): array {
        self::identifier($id); ksort($cart);
        $money = cart_total($this->catalogue, $cart);
        return $this->atomic(function () use ($id, $cart, $money) {
            $s = $this->db->prepare('SELECT 1 FROM candidate_orders WHERE id=?'); $s->execute([$id]);
            if ($s->fetchColumn()) {
                $o = $this->load($id);
                if ($o['cart'] !== $cart || $o['amount'] !== $money['amount']) throw new Hold('checkout_intent_conflict');
                return $this->view($id);
            }
            $o = ['id' => $id, 'cart' => $cart, 'currency' => 'USD', 'amount' => $money['amount'],
                  'origin' => 'NEW', 'api_family' => 'orders-v2', 'environment' => 'sandbox',
                  'merchant_id' => $this->merchant, 'state' => 'OPEN', 'provider_order_id' => null,
                  'capture_id' => null, 'refund_id' => null, 'refund_state' => null,
                  'buyer_cancelled' => false, 'hold' => null];
            $this->db->prepare('INSERT INTO candidate_orders VALUES (?,?)')->execute([$id, json_encode($o, JSON_THROW_ON_ERROR)]);
            return $this->view($id);
        });
    }

    /** Browser return/cancel is informational, never financial evidence. */
    public function cancel(string $id): array {
        return $this->atomic(function () use ($id) {
            $o = $this->load($id); $o['buyer_cancelled'] = true; $this->save($o); return $this->view($id);
        });
    }

    private function exchange(string $method, string $path, ?array $body, array $headers = []): array {
        try { $r = ($this->rest)($method, $path, $body, $headers); }
        catch (\Throwable) { throw new Hold('provider_outcome_unknown'); }
        if (!is_array($r) || count($r) !== 2 || !is_int($r[0]) || $r[0] < 200 || $r[0] >= 300 || !is_array($r[1])) {
            throw new Hold('provider_outcome_unverified');
        }
        return $r[1];
    }

    /**
     * Commit intent BEFORE dispatch. Parallel/restarted duplicates cannot send a
     * second mutation. Unknown effects require GET reconciliation, not a new key.
     */
    private function mutate(string $id, string $kind, callable $prepare, callable $accept): array {
        $plan = $this->atomic(function () use ($id, $kind, $prepare) {
            $o = $this->load($id);
            $s = $this->db->prepare('SELECT status FROM candidate_operations WHERE order_id=? AND kind=?');
            $s->execute([$id, $kind]); $prior = $s->fetchColumn();
            if ($prior === 'DONE') return null;
            if ($prior !== false) throw new Hold('prior_dispatch_requires_reconciliation');
            $p = $prepare($o); // Validate state before reserving anything.
            $request = bin2hex(random_bytes(16)); // 32 chars; persisted, unique per operation.
            $this->db->prepare('INSERT INTO candidate_operations VALUES (?,?,?,?)')->execute([$id, $kind, $request, 'DISPATCHED']);
            if ($kind === 'refund') $o['refund_state'] = 'UNKNOWN'; else $o['state'] = strtoupper($kind) . '_UNKNOWN';
            $this->save($o);
            return [$p[0], $p[1], $request];
        });
        if ($plan === null) return $this->view($id);
        try {
            $data = $this->exchange('POST', $plan[0], $plan[1], ['PayPal-Request-Id' => $plan[2], 'Prefer' => 'return=representation']);
            return $this->atomic(function () use ($id, $kind, $data, $accept) {
                $o = $this->load($id); $accept($o, $data); $o['hold'] = null; $this->save($o);
                $this->done($id, $kind); return $this->view($id);
            });
        } catch (\Throwable) {
            $this->atomic(function () use ($id) { $o = $this->load($id); $o['hold'] = 'mutation_needs_reconciliation'; $this->save($o); });
            throw new Hold('mutation_needs_reconciliation');
        }
    }

    private function done(string $id, string $kind): void {
        $this->db->prepare("UPDATE candidate_operations SET status='DONE' WHERE order_id=? AND kind=?")->execute([$id, $kind]);
    }

    private function bind(string $id, string $kind, string $resource): void {
        $s = $this->db->prepare('SELECT order_id FROM candidate_resources WHERE kind=? AND resource_id=?');
        $s->execute([$kind, $resource]); $prior = $s->fetchColumn();
        if ($prior !== false && $prior !== $id) throw new Hold('resource_already_bound_to_another_order');
        $this->db->prepare('INSERT OR IGNORE INTO candidate_resources VALUES (?,?,?)')->execute([$kind, $resource, $id]);
    }

    private function money(array $o, mixed $money): void {
        if (!is_array($money) || ($money['currency_code'] ?? null) !== 'USD'
            || !is_string($money['value'] ?? null) || usd_minor($money['value']) !== usd_minor($o['amount'])) {
            throw new Hold('provider_money_mismatch');
        }
    }

    private function unit(array $o, array $data): array {
        $units = $data['purchase_units'] ?? null;
        if (!is_array($units) || count($units) !== 1 || !is_array($units[0] ?? null)
            || ($units[0]['reference_id'] ?? null) !== $o['id']) throw new Hold('order_binding_mismatch');
        return $units[0];
    }

    public function create(string $id): array {
        $result = $this->mutate($id, 'create', function (array $o) {
            if ($o['state'] !== 'OPEN' || $o['buyer_cancelled']) throw new Hold('create_not_allowed');
            return ['/v2/checkout/orders', ['intent' => 'CAPTURE', 'purchase_units' => [[
                'reference_id' => $o['id'], 'payee' => ['merchant_id' => $this->merchant],
                'amount' => ['currency_code' => 'USD', 'value' => $o['amount']]
            ]]]];
        }, function (array &$o, array $data) {
            $provider = self::identifier($data['id'] ?? null);
            $status = $data['status'] ?? null;
            if (!in_array($status, ['CREATED', 'SAVED', 'APPROVED', 'PAYER_ACTION_REQUIRED'], true)) throw new Hold('unexpected_create_status');
            if (!array_key_exists('purchase_units', $data)) {
                // Current backend broker may return PayPal's minimal response.
                // Persist its identity, then require a fresh GET before capture.
                $this->bind($o['id'], 'order', $provider); $o['provider_order_id'] = $provider;
                $o['state'] = 'CREATE_RECHECK'; return;
            }
            $unit = $this->unit($o, $data);
            $this->money($o, $unit['amount'] ?? null);
            if (($unit['payee']['merchant_id'] ?? null) !== $this->merchant || ($data['intent'] ?? null) !== 'CAPTURE') {
                throw new Hold('merchant_or_intent_mismatch');
            }
            $this->bind($o['id'], 'order', $provider);
            $o['provider_order_id'] = $provider;
            $o['state'] = $status === 'PAYER_ACTION_REQUIRED' ? 'ACTION_REQUIRED' : 'CREATED';
        });
        return $result['state'] === 'CREATE_RECHECK' ? $this->reconcile($id) : $result;
    }

    private function acceptCapture(array &$o, array $capture): void {
        $intent = $this->db->prepare("SELECT 1 FROM candidate_operations WHERE order_id=? AND kind='capture'");
        $intent->execute([$o['id']]);
        if (!$intent->fetchColumn()) throw new Hold('capture_without_recorded_operation');
        $cid = self::identifier($capture['id'] ?? null); $this->money($o, $capture['amount'] ?? null);
        if (($capture['final_capture'] ?? null) !== true) throw new Hold('single_final_capture_required');
        if ($o['capture_id'] !== null && $o['capture_id'] !== $cid) throw new Hold('capture_binding_changed');
        $state = ['COMPLETED' => 'PAID', 'PENDING' => 'PENDING', 'DECLINED' => 'DECLINED', 'FAILED' => 'FAILED',
                  'REFUNDED' => 'REFUNDED', 'PARTIALLY_REFUNDED' => 'PARTIALLY_REFUNDED'][$capture['status'] ?? ''] ?? null;
        if ($state === null) throw new Hold('unknown_capture_status');
        $allowed = match ($o['state']) {
            'PAID' => ['PAID', 'PARTIALLY_REFUNDED', 'REFUNDED'],
            'PARTIALLY_REFUNDED' => ['PARTIALLY_REFUNDED', 'REFUNDED'],
            'REFUNDED' => ['REFUNDED'],
            'DECLINED', 'FAILED' => [$o['state']],
            default => ['PAID', 'PENDING', 'DECLINED', 'FAILED', 'PARTIALLY_REFUNDED', 'REFUNDED']
        };
        if (!in_array($state, $allowed, true)) throw new Hold('capture_status_regression');
        $this->bind($o['id'], 'capture', $cid);
        $o['capture_id'] = $cid; $o['state'] = $state;
    }

    private function captureFromOrder(array &$o, array $data): void {
        if (($data['id'] ?? null) !== $o['provider_order_id']) throw new Hold('provider_order_mismatch');
        $u = $this->unit($o, $data); $captures = $u['payments']['captures'] ?? null;
        if (!is_array($captures) || count($captures) !== 1 || !is_array($captures[0] ?? null)) throw new Hold('capture_missing_or_ambiguous');
        $this->acceptCapture($o, $captures[0]);
    }

    public function capture(string $id): array {
        return $this->mutate($id, 'capture', function (array $o) {
            if (!in_array($o['state'], ['CREATED', 'ACTION_REQUIRED'], true) || $o['buyer_cancelled'] || $o['hold'] !== null) {
                throw new Hold('capture_not_allowed');
            }
            return ['/v2/checkout/orders/' . self::identifier($o['provider_order_id']) . '/capture', []];
        }, fn (array &$o, array $d) => $this->captureFromOrder($o, $d));
    }

    private function acceptRefund(array &$o, array $data): void {
        $rid = self::identifier($data['id'] ?? null);
        if ($o['refund_id'] !== null && $o['refund_id'] !== $rid) throw new Hold('refund_binding_changed');
        $status = $data['status'] ?? null;
        if (!in_array($status, ['COMPLETED', 'PENDING', 'FAILED', 'CANCELLED'], true)) throw new Hold('unknown_refund_status');
        if (!array_key_exists('amount', $data) && $o['refund_id'] === null) {
            $this->bind($o['id'], 'refund', $rid); $o['refund_id'] = $rid; $o['refund_state'] = 'RECHECK'; return;
        }
        $this->money($o, $data['amount'] ?? null);
        if ($o['refund_state'] === 'COMPLETED' && $status !== 'COMPLETED') throw new Hold('refund_status_regression');
        $this->bind($o['id'], 'refund', $rid);
        $o['refund_id'] = $rid; $o['refund_state'] = $status;
        if ($status === 'COMPLETED') $o['state'] = 'REFUNDED';
    }

    /** This component refunds NEW capture IDs only. OLD obligations stay on NVP. */
    public function refund(string $id): array {
        $result = $this->mutate($id, 'refund', function (array $o) {
            if ($o['state'] !== 'PAID' || $o['refund_state'] !== null || $o['hold'] !== null) throw new Hold('refund_not_allowed');
            return ['/v2/payments/captures/' . self::identifier($o['capture_id']) . '/refund', [
                'amount' => ['currency_code' => 'USD', 'value' => $o['amount']]
            ]];
        }, fn (array &$o, array $d) => $this->acceptRefund($o, $d));
        return $result['refund_state'] === 'RECHECK' ? $this->reconcile($id) : $result;
    }

    /** GET-only reconciliation. Never consumes callbacks or browser assertions. */
    public function reconcile(string $id): array {
        $before = $this->load($id);
        if ($before['provider_order_id'] === null) throw new Hold('unknown_create_requires_operator_lookup');
        $resource = $before['refund_id'] !== null ? 'refund' : ($before['capture_id'] !== null ? 'capture' : 'order');
        $pid = $before[$resource === 'order' ? 'provider_order_id' : $resource . '_id'];
        $path = $resource === 'order' ? '/v2/checkout/orders/' : '/v2/payments/' . ($resource === 'capture' ? 'captures/' : 'refunds/');
        $data = $this->exchange('GET', $path . self::identifier($pid), null);
        return $this->atomic(function () use ($id, $resource, $pid, $data) {
            $o = $this->load($id);
            if (($data['id'] ?? null) !== $pid) throw new Hold('reconciliation_resource_mismatch');
            if ($resource === 'refund') {
                $this->acceptRefund($o, $data); $this->done($id, 'refund');
            } elseif ($resource === 'capture') {
                $this->acceptCapture($o, $data); $this->done($id, 'capture');
            } else {
                $u = $this->unit($o, $data); $this->money($o, $u['amount'] ?? null);
                if (($u['payee']['merchant_id'] ?? null) !== $this->merchant || ($data['intent'] ?? null) !== 'CAPTURE') {
                    throw new Hold('merchant_or_intent_mismatch');
                }
                if (isset($u['payments']['captures'])) {
                    $this->captureFromOrder($o, $data); $this->done($id, 'capture');
                } elseif ($o['state'] === 'CREATE_RECHECK' && in_array($data['status'] ?? null,
                    ['CREATED', 'SAVED', 'APPROVED', 'PAYER_ACTION_REQUIRED'], true)) {
                    $o['state'] = $data['status'] === 'PAYER_ACTION_REQUIRED' ? 'ACTION_REQUIRED' : 'CREATED';
                    $this->done($id, 'create');
                } else { throw new Hold('capture_missing_or_ambiguous'); }
            }
            // An unknown refund without a refund ID cannot be resolved by merely
            // reading the capture as COMPLETED. Preserve its hold and journal.
            if ($o['refund_state'] !== 'UNKNOWN') $o['hold'] = null;
            $this->save($o); return $this->view($id);
        });
    }
}
