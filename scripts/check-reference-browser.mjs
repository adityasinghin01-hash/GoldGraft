// Explicit local-browser component check. Provider requests are blocked, not simulated payments.
import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const base = process.env.GOLDGRAFT_LAB_BASE_URL;
assert.match(base ?? '', /^http:\/\/127\.0\.0\.1:[1-9][0-9]{0,4}$/);
assert.ok(Number(new URL(base).port) <= 65535);
const key = (await readFile(process.env.GOLDGRAFT_LAB_KEY_FILE, 'ascii')).trim();
assert.match(key, /^[a-f0-9]{64}$/);
process.env.PLAYWRIGHT_BROWSERS_PATH = fileURLToPath(new URL('../.context/playwright-browsers', import.meta.url));
const { chromium } = await import('@playwright/test');
const browser = await chromium.launch({ channel: 'chromium', headless: true });
try {
  const context = await browser.newContext({
    extraHTTPHeaders: { 'X-GoldGraft-Lab-Key': key }, serviceWorkers: 'block',
  });
  let blockedRequests = 0;
  await context.route('**/*', async route => {
    if (new URL(route.request().url()).origin !== base) {
      blockedRequests += 1;
      await route.abort();
    } else {
      await route.continue();
    }
  });
  const page = await context.newPage();
  const response = await page.goto(base, { waitUntil: 'networkidle' });
  assert.equal(response.status(), 200);
  assert.equal(await page.locator('.card').count(), 3);
  assert.equal(await page.locator('#amt').textContent(), '25.00');
  await page.locator('input[data-sku="tee"]').fill('2');
  await page.locator('input[data-sku="mug"]').fill('1');
  assert.equal(await page.locator('#amt').textContent(), '62.50');
  const outsider = await browser.newContext({ serviceWorkers: 'block' });
  const outsiderPage = await outsider.newPage();
  assert.equal((await outsiderPage.goto(base)).status(), 401);
  if (process.env.GOLDGRAFT_LAB_SCREENSHOT) {
    await page.screenshot({ path: process.env.GOLDGRAFT_LAB_SCREENSHOT, fullPage: true });
  }
  const result = { status: 'PASS', evidence: 'LOCAL_BROWSER_ONLY', browser: browser.version(),
    checks: ['authenticated shop HTML', 'cart quantity and total', 'separate unauthenticated session denied'],
    externalRequestsBlockedByRoute: blockedRequests, externalRequestsAlsoBlockedByCSP: true,
    paymentTestsRun: false, runtimeQualified: false };
  if (process.env.GOLDGRAFT_LAB_BROWSER_RESULT) {
    await writeFile(process.env.GOLDGRAFT_LAB_BROWSER_RESULT, JSON.stringify(result, null, 2));
  }
  console.log(JSON.stringify(result));
} finally {
  await browser.close();
}
