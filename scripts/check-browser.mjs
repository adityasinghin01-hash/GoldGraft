import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';

process.env.PLAYWRIGHT_BROWSERS_PATH = fileURLToPath(
  new URL('../.context/playwright-browsers', import.meta.url),
);
const { chromium } = await import('@playwright/test');
const browser = await chromium.launch({ channel: 'chromium', headless: true });
try {
  const first = await browser.newContext();
  const second = await browser.newContext();
  await first.addCookies([{ name: 'setup-check', value: 'first-context', url: 'https://goldgraft.invalid' }]);
  assert.equal((await second.cookies('https://goldgraft.invalid')).length, 0);
  const page = await first.newPage();
  await page.setContent('<button onclick="document.querySelector(\'output\').textContent=\'Browser ready\'">Verify</button><output></output>');
  await page.getByRole('button', { name: 'Verify', exact: true }).click();
  assert.equal(await page.locator('output').textContent(), 'Browser ready');
  console.log(JSON.stringify({ status: 'PASS', browser: 'chromium', version: browser.version(), checks: ['launch', 'local DOM interaction', 'isolated contexts'], paymentTestsRun: false }));
} finally {
  await browser.close();
}
