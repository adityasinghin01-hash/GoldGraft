// Actual local Newman run. No account, cloud upload, PayPal request or private JSON report.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
const root = new URL('../../../', import.meta.url);
const state = JSON.parse(readFileSync(process.argv[2], 'utf8'));
assert.equal(state.kind, 'LOCAL_OFFLINE_SHOP');
assert.equal(state.payments, 'disabled');
assert.match(state.base_url, /^http:\/\/127\.0\.0\.1:[1-9][0-9]{0,4}$/);
assert.ok(Number(new URL(state.base_url).port) <= 65535);
const key = readFileSync(state.key_file, 'ascii').trim();
assert.match(key, /^[a-f0-9]{64}$/);
const collection = JSON.parse(readFileSync(new URL('offline-shop.postman_collection.json', import.meta.url), 'utf8'));
const allowed = new Set(['GET /__lab/health', 'GET /', 'GET /config.php', 'POST /api/create-payment.php']);
for (const item of collection.item) {
  assert.ok(allowed.has(`${item.request.method} ${item.request.url.replace('{{base_url}}', '')}`));
  assert.ok(item.request.url.startsWith('{{base_url}}/'));
  for (const event of item.event ?? []) {
    assert.equal(event.listen, 'test');
    assert.ok(!/sendRequest|require\s*\(|eval\s*\(/.test(event.script.exec.join('\n')));
  }
}
const require = createRequire('D:/DevTools/GoldGraft/sponsor-tools/package.json');
const newman = require('newman');
const summary = await new Promise((resolve, reject) => {
  newman.run({ collection, environment: { values: [
    { key: 'base_url', value: state.base_url, enabled: true },
    { key: 'lab_key', value: key, enabled: true },
  ] }, reporters: [], timeoutRequest: 3000, timeoutScript: 1000,
  ignoreRedirects: true, insecure: false }, (error, result) => error ? reject(error) : resolve(result));
});
const failures = summary.run.failures.length;
console.log(JSON.stringify({ status: failures ? 'FAIL' : 'PASS',
  runner: `newman ${require('newman/package.json').version}`, evidence: 'LOCAL_OFFLINE_SHOP_HTTP_CHECKS',
  requests: summary.run.stats.requests.total, assertions: summary.run.stats.assertions.total,
  failures, provider_calls: 0, payment_scenarios_completed: 0, credential_values_printed: false }));
process.exitCode = failures ? 1 : 0;
