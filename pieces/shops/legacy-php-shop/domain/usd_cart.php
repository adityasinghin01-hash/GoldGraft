<?php
// Proposed shop-domain primitive; not installed into the frozen baseline or a NEW checkout.
declare(strict_types=1);
namespace GoldGraft\ShopDomain;

function usd_minor(string $amount): int {
    if (!preg_match('/^(0|[1-9][0-9]{0,6})\.([0-9]{2})$/D', $amount, $m)) {
        throw new \InvalidArgumentException('invalid_usd_amount');
    }
    return (int)$m[1] * 100 + (int)$m[2];
}

function usd_text(int $minor): string {
    if ($minor < 0 || $minor > 999999999) throw new \InvalidArgumentException('usd_amount_out_of_bounds');
    return intdiv($minor, 100) . '.' . str_pad((string)($minor % 100), 2, '0', STR_PAD_LEFT);
}

function cart_total(array $catalogue, array $cart): array {
    if (!$cart || count($cart) > 100) throw new \InvalidArgumentException('invalid_cart');
    $total = 0;
    foreach ($cart as $sku => $quantity) {
        if (!is_string($sku) || !array_key_exists($sku, $catalogue)
                || !is_int($quantity) || $quantity < 1 || $quantity > 99) {
            throw new \InvalidArgumentException('invalid_cart_item');
        }
        $price = $catalogue[$sku];
        if (!is_string($price)) throw new \InvalidArgumentException('invalid_catalogue');
        $total += usd_minor($price) * $quantity;
        if ($total > 999999999) throw new \InvalidArgumentException('cart_total_out_of_bounds');
    }
    if ($total === 0) throw new \InvalidArgumentException('zero_cart');
    return ['currency' => 'USD', 'minor' => $total, 'amount' => usd_text($total)];
}
