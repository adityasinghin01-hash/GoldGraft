/**
 * Test runner for Node.js switch library against plugtests/switch_cases.json.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { decideRoute } from './switch.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const casesArg = process.argv[2] || '../../../plugtests/switch_cases.json';
const casesPath = path.resolve(__dirname, casesArg);

const casesData = JSON.parse(fs.readFileSync(casesPath, 'utf8'));
const now = new Date(casesData.now);
const publicKeyB64 = casesData.public_key_b64;
const graftId = casesData.graft_id;

let failed = 0;
const total = casesData.cases.length;

for (const c of casesData.cases) {
  const got = decideRoute(c.config, publicKeyB64, {
    graftId,
    orderRef: c.order_ref,
    now,
    action: c.action,
    origin: c.origin
  });

  if (got !== c.expect) {
    console.error(`FAIL: ${c.name} (expected ${c.expect}, got ${got})`);
    failed++;
  }
}

if (failed > 0) {
  console.error(`\n${failed}/${total} cases failed!`);
  process.exit(1);
}

console.log(`All ${total} switch cases passed successfully in Node.js!`);
process.exit(0);

