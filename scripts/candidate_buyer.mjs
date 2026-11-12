import fs from 'node:fs';
import { chromium, request } from '@playwright/test';

const config = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const base = new URL(config.base_url);
if (base.protocol !== 'http:' || base.hostname !== '127.0.0.1' || config.mode !== 'OFFLINE_SCRIPTED') throw Error('loopback_scripted_only');
const assert = (ok, reason) => { if (!ok) throw Error(reason); };
const anonymous = await request.newContext({baseURL: base.origin});
assert((await anonymous.get('/')).status() === 401, 'anonymous_access_denied');
await anonymous.dispose();
const browser = await chromium.launch({channel: 'chromium', headless: true});
try {
  const context = await browser.newContext({extraHTTPHeaders: {'X-Candidate-Lab-Key': config.lab_key}});
  let deniedExternal = 0;
  await context.route('**/*', route => {
    if (new URL(route.request().url()).origin !== base.origin) { deniedExternal++; return route.abort(); }
    return route.continue();
  });
  const page = await context.newPage();
  await page.goto(base.origin);
  assert(await page.getByText('Offline scripted lab.', {exact: true}).isVisible(), 'offline_label_required');
  const act = async (button, expected) => {
    const reply = page.waitForResponse(r => r.url().endsWith('/__candidate/action') && r.request().method() === 'POST');
    await page.locator('#' + button).click();
    const response = await reply;
    const value = await response.json();
    assert(response.status() === 200 && value.mode === 'OFFLINE_SCRIPTED' && value.payment_qualified === false, 'evidence_label_invalid');
    assert(value.order.state === expected, 'unexpected_' + button + '_state');
    return value.order;
  };
  await act('create', 'CREATED');
  await act('create', 'CREATED');
  const paid = await act('capture', 'PAID');
  assert(paid.fulfillable === true, 'completed_scripted_capture_state');
  await act('capture', 'PAID');
  await act('refund', 'REFUNDED');
  const repeated = await act('refund', 'REFUNDED');
  assert(repeated.capture_id === paid.capture_id && !repeated.fulfillable, 'original_capture_and_refund_state');
  await act('reconcile', 'REFUNDED');
  const cancelPage = await context.newPage();
  await cancelPage.goto(base.origin);
  await cancelPage.locator('#create').click();
  await cancelPage.locator('#status').filter({hasText: 'CREATED'}).waitFor();
  await cancelPage.locator('#cancel').click();
  await cancelPage.waitForFunction(() => document.querySelector('#result').textContent.includes('"buyer_cancelled": true'));
  await cancelPage.locator('#capture').click();
  await cancelPage.locator('#status').filter({hasText: 'HOLD'}).waitFor();
  for (const path of ['/Checkout.php', '/offline_router.php', '/ipn.php', '/candidate.sqlite']) {
    assert((await context.request.get(base.origin + path)).status() === 404, 'private_route_not_exposed');
  }
  assert(deniedExternal === 0, 'unexpected_external_request');
  await context.close();
  console.log(JSON.stringify({status: 'PASS', evidence: 'OFFLINE_SCRIPTED_CANDIDATE_BROWSER',
    actions: 10, private_route_checks: 4, anonymous_denied: true, provider_calls: 0,
    payment_qualified: false, fresh_context: true}));
} finally { await browser.close(); }
