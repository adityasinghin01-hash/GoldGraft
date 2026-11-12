// Offline component buyer only. No PayPal authentication or payment operations.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
const root = new URL('../../../', import.meta.url);
const path = process.argv[2] ?? fileURLToPath(new URL('.context/local-shop.json', root));
const state = JSON.parse(readFileSync(path, 'utf8'));
assert.equal(state.kind, 'LOCAL_OFFLINE_SHOP');
assert.equal(state.payments, 'disabled');
assert.equal(state.runtime_qualified, false);
process.env.GOLDGRAFT_LAB_BASE_URL = state.base_url;
process.env.GOLDGRAFT_LAB_KEY_FILE = state.key_file;
await import('../../../scripts/check-reference-browser.mjs');
