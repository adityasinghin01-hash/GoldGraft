<?php
declare(strict_types=1);
require __DIR__ . '/usd_cart.php';
use function GoldGraft\ShopDomain\cart_total;
use function GoldGraft\ShopDomain\usd_minor;
use function GoldGraft\ShopDomain\usd_text;
function checked(bool $value): void { if (!$value) throw new RuntimeException('cart_component_failed'); }
$count = 0;
foreach (['0.00' => 0, '0.01' => 1, '0.10' => 10, '25.00' => 2500, '9999999.99' => 999999999] as $text => $minor) {
    checked(usd_minor($text) === $minor && usd_text($minor) === $text); $count++;
}
$catalogue = ['tee' => '25.00', 'mug' => '12.50', 'poster' => '18.00', 'tiny' => '0.10'];
checked(cart_total($catalogue, ['tee' => 2, 'mug' => 1]) === ['currency' => 'USD', 'minor' => 6250, 'amount' => '62.50']); $count++;
checked(cart_total($catalogue, ['tiny' => 3])['minor'] === 30); $count++;
foreach (['-1.00', '1e2', '01.00', '1.001', '1', '1.0', '1,00', ' 1.00', 'NaN', '10000000.00'] as $bad) {
    $denied = false;
    try { usd_minor($bad); } catch (InvalidArgumentException $e) { $denied = true; }
    checked($denied); $count++;
}
foreach ([[], ['tee' => -1], ['tee' => 0], ['tee' => 1.0], ['tee' => '1'], ['tee' => true],
           ['tee' => 100], ['attacker_price' => 1], ['tee' => ['qty' => 1]]] as $bad) {
    $denied = false;
    try { cart_total($catalogue, $bad); } catch (InvalidArgumentException $e) { $denied = true; }
    checked($denied); $count++;
}
$denied = false;
try { cart_total(['huge' => '9999999.99'], ['huge' => 2]); } catch (InvalidArgumentException $e) { $denied = true; }
checked($denied); $count++;
echo json_encode(['status' => 'PASS', 'cases' => $count, 'evidence' => 'OFFLINE_SHOP_DOMAIN',
    'baseline_modified' => false, 'checkout_qualified' => false, 'provider_calls' => 0]) . "\n";
