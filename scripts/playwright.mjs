import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const cli = require.resolve('@playwright/test/cli');
const result = spawnSync(process.execPath, [cli, ...process.argv.slice(2)], {
  stdio: 'inherit',
  env: {
    ...process.env,
    PLAYWRIGHT_BROWSERS_PATH: fileURLToPath(new URL('../.context/playwright-browsers', import.meta.url)),
  },
});
if (result.error) {
  console.error(result.error.message);
}
process.exit(result.status ?? 1);
