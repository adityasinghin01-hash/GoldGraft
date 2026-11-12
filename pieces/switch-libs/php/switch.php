<?php
declare(strict_types=1);
namespace GoldGraft\SwitchLib;

const FOLLOW_UPS = ['REFUND', 'VOID', 'RENEWAL', 'CAPTURE'];

function signed_bytes(array $config): string {
    unset($config['signature']);
    ksort($config, SORT_STRING);
    return json_encode($config, JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_LINE_TERMINATORS);
}

function timestamp(string $value): \DateTimeImmutable {
    if (!preg_match('/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,6})?(?:Z|([+-])(\d{2}):(\d{2}))$/D', $value, $parts)) {
        throw new \InvalidArgumentException('invalid_timestamp');
    }
    if ((int)$parts[1] < 1 || !checkdate((int)$parts[2], (int)$parts[3], (int)$parts[1]) ||
        (int)$parts[4] > 23 || (int)$parts[5] > 59 || (int)$parts[6] > 59 ||
        (int)($parts[8] ?? 0) > 23 || (int)($parts[9] ?? 0) > 59) throw new \InvalidArgumentException('invalid_timestamp');
    $date = new \DateTimeImmutable($value);
    $errors = \DateTimeImmutable::getLastErrors();
    if ($errors && ($errors['warning_count'] || $errors['error_count'])) throw new \InvalidArgumentException('invalid_timestamp');
    return $date;
}

function decoded(string $value, int $size): string {
    $raw = base64_decode($value, true);
    if ($raw === false || strlen($raw) !== $size || base64_encode($raw) !== $value) throw new \InvalidArgumentException('invalid_base64');
    return $raw;
}

function config_valid(mixed $config, string $key, string $graftId, string $now): bool {
    try {
        if (!is_array($config)) return false;
        $keys = array_keys($config); sort($keys, SORT_STRING);
        if ($keys !== ['expires_at', 'graft_id', 'origin_rules', 'signature', 'stage_pct', 'version'] ||
            !is_string($config['graft_id']) || $config['graft_id'] === '' || $config['graft_id'] !== $graftId ||
            !is_int($config['stage_pct']) || !in_array($config['stage_pct'], [0, 1, 10, 50, 100], true) ||
            !is_int($config['version']) || $config['version'] < 1 || $config['version'] > 9007199254740991 ||
            !is_array($config['origin_rules']) || !array_is_list($config['origin_rules'])) return false;
        foreach ($config['origin_rules'] as $rule) if (!is_string($rule) || $rule === '') return false;
        if (!is_string($config['signature']) || !is_string($config['expires_at']) || !function_exists('sodium_crypto_sign_verify_detached')) return false;
        return sodium_crypto_sign_verify_detached(decoded($config['signature'], 64), signed_bytes($config), decoded($key, 32))
            && timestamp($now) < timestamp($config['expires_at']);
    } catch (\Throwable $error) { return false; }
}

function bucket(string $graftId, string $orderRef): int {
    return (int)hexdec(substr(hash('sha256', $graftId . ':' . $orderRef), 0, 8)) % 100;
}

function decide(mixed $config, string $key, string $graftId, string $orderRef, string $now, string $action = 'PAY', ?string $origin = null): string {
    if (in_array($action, FOLLOW_UPS, true)) return $origin === 'NEW' ? 'NEW' : 'OLD';
    if (!config_valid($config, $key, $graftId, $now)) return 'OLD';
    return bucket($graftId, $orderRef) < $config['stage_pct'] ? 'NEW' : 'OLD';
}

function route_existing(string $action, ?string $origin): string {
    if (!in_array($action, FOLLOW_UPS, true) || !in_array($origin, ['OLD', 'NEW'], true)) throw new \InvalidArgumentException('stored_origin_required');
    return $origin;
}

final class VerifiedConfigCache {
    private ?array $config = null;
    public function __construct(private string $graftId, private string $key) {}
    public function accept(mixed $config, string $now): bool {
        if (!config_valid($config, $this->key, $this->graftId, $now)) return false;
        if ($this->config !== null && ($config['version'] < $this->config['version'] ||
            ($config['version'] === $this->config['version'] && signed_bytes($config) !== signed_bytes($this->config)))) return false;
        $this->config = $config;
        return true;
    }
    public function current(string $now): ?array {
        return config_valid($this->config, $this->key, $this->graftId, $now) ? $this->config : null;
    }
}
