// Buyer script for the legacy shop, HAPPY path (Playwright Test).
// LIVE: needs the real PayPal sandbox + a sandbox BUYER account, so it runs only when
// PAYPAL_SANDBOX_BUYER_EMAIL and PAYPAL_SANDBOX_BUYER_PASSWORD are set (never committed).
// Without them the test checks only that the shop page and PayPal button load.
// The old checkout.js button opens a PayPal popup; the real piece runs this headful on
// KERNEL (design 09 test 14). Selectors on PayPal's own pages may change: re-check them
// in the sandbox before relying on this (owner: all-rounder teammate).
import { expect, test } from "@playwright/test";

const SHOP = process.env.SHOP_BASE_URL ?? "http://localhost:8081";
const BUYER = process.env.PAYPAL_SANDBOX_BUYER_EMAIL;
const PASSWORD = process.env.PAYPAL_SANDBOX_BUYER_PASSWORD;

test("shop page loads with the old PayPal button", async ({ page }) => {
  await page.goto(`${SHOP}/index.php`);
  await expect(page.locator("#paypal-button")).toBeVisible();
  await expect(page.locator("input[data-sku]").first()).toBeVisible();
});

test("HAPPY: buyer pays one tee in the sandbox", async ({ page, context }) => {
  test.skip(!BUYER || !PASSWORD, "live sandbox buyer credentials not set");
  await page.goto(`${SHOP}/index.php`);
  await page.locator('input[data-sku="tee"]').fill("1");
  const popupPromise = context.waitForEvent("page");
  await page.frameLocator("iframe[name^='xcomponent__ppbutton']").locator("[role=button]").first().click();
  const popup = await popupPromise;
  await popup.waitForLoadState();
  await popup.locator("#email").fill(BUYER!);
  await popup.locator("#btnNext").click().catch(() => {});
  await popup.locator("#password").fill(PASSWORD!);
  await popup.locator("#btnLogin").click();
  await popup.locator("#payment-submit-btn, [data-testid='submit-button-initial']").first().click();
  await expect(page.locator("#result")).toContainText("Payment complete", { timeout: 60_000 });
});
